# FastAPI Backend

## Run
```bash
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

## Core Responsibilities
- Receive senior-device audio upload via HTTPS.
- Process audio in one AI request for transcript + translation + severity.
- Store alerts in MySQL.
- Broadcast new alerts to dashboard via WebSocket.