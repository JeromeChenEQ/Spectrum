"""Audio analysis service using one OpenAI call with fallback simulation."""

import base64
import json
import logging
import re
from typing import Any, Dict

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
You process emergency senior-aid audio in one pass.
Return valid JSON with keys:
- detected_language
- transcript
- english_translation
- severity (URGENT, UNCERTAIN, or NON-URGENT)
- confidence_score
- keywords
- distress_indicators
Classify severity carefully for helpdesk triage.
""".strip()


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


def _simulate_result() -> Dict[str, str | bool]:
    """Fallback result when OpenAI is unavailable in local environment."""
    return {
        "detected_language": "English",
        "transcript": "Please help, I slipped near the bathroom and cannot stand.",
        "english_translation": "Please help, I slipped near the bathroom and cannot stand.",
        "severity": "URGENT",
    }


def analyze_audio_single_call(audio_bytes: bytes, mime_type: str = "audio/wav") -> Dict[str, str | bool]:
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

    try:
        response = client.chat.completions.create(
            model="gpt-4o-audio-preview",
            messages=[
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
                                "Transcribe speech in original language, translate to English, and classify "
                                "severity as URGENT, UNCERTAIN, or NON-URGENT. Return JSON only."
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
                }
            ],
        )
        message_content = response.choices[0].message.content if response.choices else ""
        parsed = json.loads(_extract_json_text(_extract_chat_message_text(message_content)))

        return {
            "detected_language": parsed.get("detected_language", "Unknown"),
            "transcript": parsed.get("transcript", ""),
            "english_translation": parsed.get("english_translation", ""),
            "severity": parsed.get("severity", "NON-URGENT"),
            "confidence_score": parsed.get("confidence_score", 0.0),
            "keywords": parsed.get("keywords", ""),
            "distress_indicators": parsed.get("distress_indicators", "")
        }
    except Exception as error:
        log.exception("OpenAI audio analysis failed")
        raise RuntimeError(f"OpenAI audio analysis failed: {error}") from error
