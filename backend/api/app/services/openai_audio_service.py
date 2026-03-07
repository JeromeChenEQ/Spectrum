"""Audio analysis service using one OpenAI call with fallback simulation."""

import base64
import io
import json
import logging
import re
import struct
from typing import Any, Dict
import wave

from openai import OpenAI
from app.config import settings

log = logging.getLogger(__name__)

# Reuse a single OpenAI client across calls
_client: OpenAI | None = None


def _get_client() -> OpenAI | None:
    """Return a cached OpenAI client, or None if no API key is set."""
    global _client
    if _client is not None:
        return _client

    if not settings.openai_api_key:
        log.debug("No OpenAI API key configured (settings.openai_api_key is empty)")
        return None

    try:
        # Attempt to create the client and cache it.
        _client = OpenAI(api_key=settings.openai_api_key)
        log.info("OpenAI client instantiated")
        return _client
    except Exception as error:
        # Log full exception but do not expose the key itself.
        masked = settings.openai_api_key[:6] + "..." if settings.openai_api_key else "(empty)"
        log.exception("Failed to instantiate OpenAI client (key=%s)", masked)
        raise RuntimeError(f"Failed to instantiate OpenAI client: {error}") from error

SYSTEM_PROMPT = """
You process senior-aid audio in one pass.
Return valid JSON with keys:
- detected_language (human-readable language name, e.g. English, Chinese, Cantonese, Hokkien; empty string if no speech detected)
- transcript (empty string if no speech detected)
- english_translation (empty string if no speech detected)
- severity (URGENT, UNCERTAIN, or NON-URGENT)
- confidence_score (0.0 to 1.0)
- keywords (array of short strings)
- distress_indicators (array of short strings)
- speech_detected (boolean)

IMPORTANT:
- If the audio contains only noise, silence, or no intelligible speech, set detected_language, transcript and english_translation to empty string, severity to NON-URGENT, confidence_score to 0.0, and speech_detected to false.
- Do NOT invent or hallucinate speech that is not clearly present.
- Only classify as URGENT if there is clear verbal distress detected.
- Return JSON only. No markdown and no prose.
""".strip()

LANGUAGE_CODE_TO_NAME = {
    "en": "English",
    "en-us": "English",
    "en-gb": "English",
    "zh": "Chinese",
    "zh-cn": "Chinese",
    "zh-hans": "Chinese",
    "zh-sg": "Chinese",
    "zh-hk": "Chinese",
    "zh-tw": "Chinese",
    "zh-hant": "Chinese",
    "cmn": "Mandarin",
    "yue": "Cantonese",
    "nan": "Hokkien",
    "hak": "Hakka",
    "ta": "Tamil",
    "hi": "Hindi",
    "ms": "Malay",
}


def _detect_audio_format(audio_bytes: bytes, mime_type: str) -> str:
    """Detect real audio format from bytes, then fall back to MIME type."""
    if len(audio_bytes) >= 12 and audio_bytes[:4] == b"RIFF" and audio_bytes[8:12] == b"WAVE":
        return "wav"
    if audio_bytes.startswith(b"ID3") or (len(audio_bytes) >= 2 and audio_bytes[0] == 0xFF):
        return "mp3"
    if audio_bytes.startswith(b"OggS"):
        return "ogg"
    if audio_bytes.startswith(b"\x1A\x45\xDF\xA3"):
        return "webm"

    normalized = (mime_type or "").lower()
    if "wav" in normalized or "wave" in normalized:
        return "wav"
    if "mpeg" in normalized or "mp3" in normalized:
        return "mp3"
    if "ogg" in normalized:
        return "ogg"
    if "webm" in normalized:
        return "webm"
    return ""


def _extract_json_text(raw_text: str) -> str:
    """Extract JSON object from model text output."""
    if not raw_text:
        return "{}"

    stripped = raw_text.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        return stripped

    match = re.search(r"\{.*\}", stripped, re.DOTALL)
    if match:
        return match.group(0)

    return "{}"


def _extract_chat_message_text(content: Any) -> str:
    """Extract text from chat completion message content."""
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        text_parts: list[str] = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                text_parts.append(str(part.get("text", "")))
        return "\n".join(text_parts).strip()

    return ""


def _normalize_score(value: Any) -> float:
    """Coerce confidence_score into [0.0, 1.0]."""
    try:
        score = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, score))


def _normalize_text(value: Any) -> str:
    """Normalize unknown scalar to stripped text."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def _normalize_string_list(value: Any) -> list[str]:
    """Normalize list-like output into array[str]."""
    if isinstance(value, list):
        return [item.strip() for item in value if isinstance(item, str) and item.strip()]
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return []


def _normalize_severity(value: Any) -> str:
    """Map severity aliases to supported values."""
    raw = _normalize_text(value).upper().replace("_", "-")
    if raw in {"URGENT", "UNCERTAIN", "NON-URGENT"}:
        return raw
    if raw in {"EMERGENCY", "HIGH"}:
        return "URGENT"
    if raw in {"ROUTINE", "LOW", "NONURGENT"}:
        return "NON-URGENT"
    return "NON-URGENT"


def _contains_cjk(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text))


def _normalize_detected_language(value: Any, transcript: str, english_translation: str) -> str:
    """Convert language codes/aliases into stable human-readable names."""
    raw = _normalize_text(value)
    if not raw:
        if _contains_cjk(transcript):
            return "Chinese"
        if transcript and transcript == english_translation:
            return "English"
        return ""

    normalized = raw.lower().replace("_", "-").strip()
    if normalized in LANGUAGE_CODE_TO_NAME:
        return LANGUAGE_CODE_TO_NAME[normalized]

    # Handle values like "zh (chinese)" or "english (us)".
    prefix = normalized.split(" ", 1)[0]
    if prefix in LANGUAGE_CODE_TO_NAME:
        return LANGUAGE_CODE_TO_NAME[prefix]

    lowered_words = set(re.findall(r"[a-z]+", normalized))
    if {"english", "eng"} & lowered_words:
        return "English"
    if {"chinese", "mandarin"} & lowered_words:
        return "Chinese"
    if "cantonese" in lowered_words:
        return "Cantonese"
    if "hokkien" in lowered_words:
        return "Hokkien"
    if "teochew" in lowered_words:
        return "Teochew"
    if "tamil" in lowered_words:
        return "Tamil"
    if "hindi" in lowered_words:
        return "Hindi"

    # Keep custom recognized language names, but title-case for consistency.
    return raw.title()


def _no_speech_result(confidence_score: float = 0.0) -> Dict[str, Any]:
    """Standardized no-speech payload."""
    return {
        "detected_language": "",
        "transcript": "",
        "english_translation": "",
        "severity": "NON-URGENT",
        "confidence_score": min(_normalize_score(confidence_score), 0.2),
        "keywords": [],
        "distress_indicators": [],
        "speech_detected": False,
    }


def _looks_like_no_speech(transcript: str, translation: str, confidence_score: float) -> bool:
    """Identify model output that likely came from noise/silence."""
    merged = f"{transcript} {translation}".strip()
    if not merged:
        return True

    token_count = len(re.findall(r"[A-Za-z0-9]+", merged))
    if token_count < 4 and confidence_score < 0.35:
        return True
    return False


def _is_probably_silent_wav(audio_bytes: bytes) -> bool:
    """Very lightweight WAV silence gate to avoid sending pure noise/silence to LLM."""
    try:
        with wave.open(io.BytesIO(audio_bytes), "rb") as wav_file:
            frame_count = wav_file.getnframes()
            sample_width = wav_file.getsampwidth()
            frame_rate = wav_file.getframerate()
            channels = wav_file.getnchannels()
            if frame_count <= 0 or sample_width <= 0 or frame_rate <= 0:
                return True
            if sample_width not in (1, 2, 4):
                return False

            chunk_size = max(frame_rate // 2, 1)
            loud_chunks = 0
            total_chunks = 0
            while True:
                raw_chunk = wav_file.readframes(chunk_size)
                if not raw_chunk:
                    break
                total_chunks += 1
                rms = _compute_pcm_rms(raw_chunk, sample_width, channels)
                if rms >= 180:
                    loud_chunks += 1

            return total_chunks > 0 and loud_chunks == 0
    except Exception:
        return False


def _compute_pcm_rms(raw_chunk: bytes, sample_width: int, channels: int) -> float:
    """Compute RMS for PCM bytes without audioop (compatible with newer Python)."""
    if not raw_chunk:
        return 0.0

    if sample_width == 1:
        # 8-bit PCM is unsigned; center to signed range.
        samples = [byte - 128 for byte in raw_chunk]
    elif sample_width == 2:
        count = len(raw_chunk) // 2
        if count == 0:
            return 0.0
        fmt = f"<{count}h"
        samples = struct.unpack(fmt, raw_chunk[: count * 2])
    elif sample_width == 4:
        count = len(raw_chunk) // 4
        if count == 0:
            return 0.0
        fmt = f"<{count}i"
        samples = struct.unpack(fmt, raw_chunk[: count * 4])
    else:
        return 0.0

    if channels > 1 and len(samples) >= channels:
        mono_samples = []
        for i in range(0, len(samples) - (len(samples) % channels), channels):
            frame = samples[i : i + channels]
            mono_samples.append(sum(frame) / channels)
        samples = mono_samples

    if not samples:
        return 0.0

    mean_square = sum(sample * sample for sample in samples) / len(samples)
    return mean_square ** 0.5


def _build_messages(audio_base64: str, audio_format: str) -> list[dict[str, Any]]:
    return [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        "Transcribe speech in original language, translate to English, classify severity, "
                        "and return JSON only. Use full detected language name (not ISO code). "
                        "If no intelligible speech, return NON-URGENT with empty text."
                    ),
                },
                {
                    "type": "input_audio",
                    "input_audio": {
                        "data": audio_base64,
                        "format": audio_format,
                    },
                },
            ],
        },
    ]


RESPONSE_JSON_SCHEMA = {
    "name": "senioraid_audio_result",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "detected_language": {"type": "string"},
            "transcript": {"type": "string"},
            "english_translation": {"type": "string"},
            "severity": {"type": "string", "enum": ["URGENT", "UNCERTAIN", "NON-URGENT"]},
            "confidence_score": {"type": "number", "minimum": 0, "maximum": 1},
            "keywords": {"type": "array", "items": {"type": "string"}},
            "distress_indicators": {"type": "array", "items": {"type": "string"}},
            "speech_detected": {"type": "boolean"},
        },
        "required": [
            "detected_language",
            "transcript",
            "english_translation",
            "severity",
            "confidence_score",
            "keywords",
            "distress_indicators",
            "speech_detected",
        ],
    },
}


def _create_completion(client: OpenAI, audio_base64: str, audio_format: str):
    """Call OpenAI, preferring strict schema output but falling back if unsupported."""
    messages = _build_messages(audio_base64, audio_format)
    try:
        return client.chat.completions.create(
            model="gpt-4o-audio-preview",
            temperature=0,
            response_format={"type": "json_schema", "json_schema": RESPONSE_JSON_SCHEMA},
            messages=messages,
        )
    except Exception as error:
        log.warning("Structured output unavailable, falling back to JSON parsing: %s", error)
        return client.chat.completions.create(
            model="gpt-4o-audio-preview",
            temperature=0,
            messages=messages,
        )


def _apply_guardrails(parsed: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize model output and enforce anti-hallucination behavior."""
    transcript = _normalize_text(parsed.get("transcript"))
    english_translation = _normalize_text(parsed.get("english_translation"))
    detected_language = _normalize_detected_language(
        parsed.get("detected_language"), transcript, english_translation
    )
    confidence_score = _normalize_score(parsed.get("confidence_score"))
    severity = _normalize_severity(parsed.get("severity"))
    keywords = _normalize_string_list(parsed.get("keywords"))
    distress_indicators = _normalize_string_list(parsed.get("distress_indicators"))
    speech_detected = bool(parsed.get("speech_detected", bool(transcript or english_translation)))

    if not speech_detected or _looks_like_no_speech(transcript, english_translation, confidence_score):
        return _no_speech_result(confidence_score)

    # Reduce false urgent from ambiguous speech by requiring stronger confidence.
    if severity == "URGENT" and confidence_score < 0.55:
        severity = "UNCERTAIN"

    return {
        "detected_language": detected_language,
        "transcript": transcript,
        "english_translation": english_translation,
        "severity": severity,
        "confidence_score": confidence_score,
        "keywords": keywords,
        "distress_indicators": distress_indicators,
        "speech_detected": True,
    }


def _simulate_result() -> Dict[str, Any]:
    """Fallback result when OpenAI is unavailable in local environment."""
    return {
        "detected_language": "",
        "transcript": "",
        "english_translation": "",
        "severity": "NON-URGENT",
        "confidence_score": 0.0,
        "keywords": [],
        "distress_indicators": [],
        "speech_detected": False,
    }


def analyze_audio_single_call(audio_bytes: bytes, mime_type: str = "audio/wav") -> Dict[str, Any]:
    """Analyze audio with one AI request and return normalized JSON fields."""
    if not settings.openai_api_key:
        result = _simulate_result()
        return result
    client = _get_client()

    audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
    audio_format = _detect_audio_format(audio_bytes, mime_type)
    if audio_format not in {"wav", "mp3", "ogg", "webm"}:
        raise ValueError(
            "Unsupported or invalid audio format. Upload a valid WAV, MP3, OGG, or WEBM file."
        )
    if audio_format == "wav" and _is_probably_silent_wav(audio_bytes):
        return _no_speech_result(0.0)

    try:
        response = _create_completion(client, audio_base64, audio_format)
        message_content = response.choices[0].message.content if response.choices else ""
        parsed = json.loads(_extract_json_text(_extract_chat_message_text(message_content)))

        return _apply_guardrails(parsed)
    except Exception as error:
        log.exception("OpenAI audio analysis failed")
        raise RuntimeError(f"OpenAI audio analysis failed: {error}") from error
