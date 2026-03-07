# FastAPI Backend

## Run
```bash
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

Required env values:
- `SUPABASE_DB_URL` (or `DB_URL` / `DATABASE_URL`)
- `SUPABASE_DB_PASSWORD` (or `DB_PASSWORD`, if URL has password placeholder)
- `DB_SSLMODE` (use `require` for Supabase)
- `OPENAI_API_KEY`

## Core Responsibilities
- Receive senior-device audio upload via HTTPS.
- Process audio in one AI request for transcript + translation + severity.
- Store alerts in Supabase PostgreSQL.
- Broadcast new alerts to dashboard via WebSocket.
