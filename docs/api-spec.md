# API Specification

Base URL: `http://localhost:8000`

## Health
### `GET /health`
Response:
```json
{ "status": "ok" }
```

## Device Upload
### `POST /api/v1/alerts/from-device`
Content-Type: `multipart/form-data`

Fields:
- `box_id` (number, required)
- `audio_file` (WAV file, required)

Response `201`:
```json
{
  "alert_id": 101,
  "box_id": 1,
  "detected_language": "Cantonese",
  "transcript": "...",
  "english_translation": "...",
  "severity": "URGENT",
  "status": "open",
  "created_at": "2026-03-07T12:34:56"
}
```

## Alert Listing
### `GET /api/v1/alerts`
Returns alerts sorted by newest first.

## Acknowledge
### `PATCH /api/v1/alerts/{alert_id}/acknowledge`
Response `200`:
```json
{
  "alert_id": 101,
  "status": "acknowledged"
}
```

## WebSocket
### `GET /api/v1/alerts/ws`
Server pushes JSON events:
- `{ "type": "alert_created", "payload": {...alert...} }`
- `{ "type": "alert_acknowledged", "payload": {"alert_id": 101} }`