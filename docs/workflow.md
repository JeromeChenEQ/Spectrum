# Workflow Mapping

## Trigger
- Senior presses button on home box.
- Device records a WAV clip (10 seconds typical; backend allows up to configured max).

## Sending
- Device sends `POST /api/v1/alerts/from-device` with `box_id` and `audio_file`.
- Device never calls OpenAI directly.

## AI Processing (Single Call)
- Backend calls `gpt-4o-audio-preview` once.
- Response includes: detected language, transcript, English translation, severity.

## Storage
- Backend writes to MySQL tables:
  - `boxes`: resident metadata
  - `alerts`: each press result and status

## Dashboard
- React dashboard reads alerts via REST.
- Dashboard receives realtime updates over WebSocket.
- Alerts sorted by severity: EMERGENCY -> URGENT -> ROUTINE.
- Operator acknowledges alert from the UI.