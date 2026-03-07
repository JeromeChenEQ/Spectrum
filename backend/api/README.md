# FastAPI Backend

## Run
```bash
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

Dependency note:
- Uses `pg8000` (pure-Python PostgreSQL driver) via SQLAlchemy.
- No `psycopg2-binary` compilation step required.

Required env values:
- `SUPABASE_DB_URL` (or `DB_URL` / `DATABASE_URL`)
- `SUPABASE_DB_PASSWORD` (or `DB_PASSWORD`, if URL has password placeholder)
- `DB_SSLMODE` (use `require` for Supabase)
- `DB_SSL_VERIFY` (`true` recommended)
- `DB_SSL_CA_FILE` (optional custom CA bundle path; defaults to certifi bundle)
- `OPENAI_API_KEY`

## Core Responsibilities
- Receive senior-device audio upload via HTTPS.
- Process audio in one AI request for transcript + translation + severity.
- Store alerts in Supabase PostgreSQL.
- Broadcast new alerts to dashboard via WebSocket.
