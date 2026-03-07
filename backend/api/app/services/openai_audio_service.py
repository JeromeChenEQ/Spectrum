"""Audio analysis service using one OpenAI call with fallback simulation."""

import base64
import json
import logging
from typing import Dict

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
    except Exception:
        # Log full exception but do not expose the key itself.
        masked = settings.openai_api_key[:6] + "..." if settings.openai_api_key else "(empty)"
        log.exception("Failed to instantiate OpenAI client (key=%s)", masked)
        return None

SYSTEM_PROMPT = """
You process emergency senior-aid audio in one pass.
Return valid JSON with keys:
- detected_language
- transcript
- english_translation
- severity (EMERGENCY, URGENT, or ROUTINE)
Classify severity carefully for helpdesk triage.
""".strip()


def _simulate_result() -> Dict[str, str | bool]:
    """Fallback result when OpenAI is unavailable in local environment."""
    return {
        "detected_language": "English",
        "transcript": "Please help, I slipped near the bathroom and cannot stand.",
        "english_translation": "Please help, I slipped near the bathroom and cannot stand.",
        "severity": "EMERGENCY",
    }


def analyze_audio_single_call(audio_bytes: bytes, mime_type: str = "audio/wav") -> Dict[str, str | bool]:
    """Analyze audio with one AI request and return normalized JSON fields."""
    client = _get_client()
    if client is None:
        result = _simulate_result()
        result["is_simulated_ai"] = True
        return result
    audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

    try:
        response = client.chat.completions.create(
            model="gpt-4o-audio-preview",
            response_format={"type": "json_object"},
            timeout=30,
            messages=[
                {
                    "role": "system",
                    "content": [{"type": "text", "text": SYSTEM_PROMPT}],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_audio",
                            "input_audio": {
                                "data": audio_base64,
                                "format": "wav",
                            },
                        }
                    ],
                },
            ],
        )
        content = response.choices[0].message.content or "{}"
        parsed = json.loads(content)

        return {
            "detected_language": parsed.get("detected_language", "Unknown"),
            "transcript": parsed.get("transcript", ""),
            "english_translation": parsed.get("english_translation", ""),
            "severity": parsed.get("severity", "ROUTINE"),
            "is_simulated_ai": False,
        }
    except Exception:
        log.exception("OpenAI audio analysis failed, falling back to simulated result")
        result = _simulate_result()
        result["is_simulated_ai"] = True
        return result