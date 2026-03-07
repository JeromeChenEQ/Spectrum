"""Audio analysis service using one OpenAI call with fallback simulation."""

import base64
import json
from typing import Dict

from openai import OpenAI
from app.config import settings

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
    if not settings.openai_api_key:
        result = _simulate_result()
        result["is_simulated_ai"] = True
        return result

    client = OpenAI(api_key=settings.openai_api_key)
    audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

    try:
        response = client.chat.completions.create(
            model="gpt-4o-audio-preview",
            response_format={"type": "json_object"},
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
        parsed = json.loads(response.object)

        return {
            "detected_language": parsed.get("detected_language", "Unknown"),
            "transcript": parsed.get("transcript", ""),
            "english_translation": parsed.get("english_translation", ""),
            "severity": parsed.get("severity", "ROUTINE"),
            "is_simulated_ai": False,
        }
    except Exception:
        result = _simulate_result()
        result["is_simulated_ai"] = True
        return result