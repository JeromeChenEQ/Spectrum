# Architecture

## Components
1. Senior Device (external hardware)
- Captures audio clip when emergency button is pressed.
- Uploads WAV file to backend endpoint.

2. FastAPI Backend (`backend/api`)
- Receives multipart upload (`box_id`, WAV file).
- Calls OpenAI once for transcript + translation + severity classification.
- Inserts alert into MySQL.
- Pushes new alert events via WebSocket to connected dashboard clients.

3. MySQL Database (`database/schema.sql`)
- `boxes`: device/resident metadata.
- `alerts`: each emergency event and processing result.

4. React Dashboard (`dashboard`)
- Fetches current alerts from REST API.
- Subscribes to backend WebSocket for realtime alerts.
- Sorts cards by severity and allows acknowledge action.

## Severity Logic
Allowed values:
- `EMERGENCY`
- `URGENT`
- `ROUTINE`

## Language Support
Prompt and response schema support:
- Hokkien
- Teochew
- Cantonese
- Tamil
- Hindi
- English