# Spectrum SeniorAid Button

Senior emergency alert system built with:
- Python FastAPI backend
- JavaScript React dashboard
- Supabase PostgreSQL database

## Workflow Implemented
1. Senior presses device button and records audio clip (10s typical, up to 60s configurable).
2. Device uploads WAV file to FastAPI backend over HTTPS.
3. Backend makes a single AI call to process transcript, translation, and severity.
4. Backend stores results in Supabase PostgreSQL tables: `boxes` and `alerts`.
5. React dashboard receives new alerts in realtime over WebSocket.
6. Dashboard sorts alerts by severity: EMERGENCY -> URGENT -> ROUTINE.
7. Staff can acknowledge an alert.

## Repository Layout
- `backend/api/`: FastAPI service and OpenAI integration.
- `dashboard/`: React dashboard (Vite).
- `database/`: PostgreSQL schema and seed scripts for Supabase.
- `docs/`: architecture, API, and conventions.

## Quick Start
1. Run SQL scripts in Supabase SQL editor:
   - `database/schema.sql`
   - `database/seed.sql` (optional)
2. Configure backend:
   - `cd backend/api`
   - copy `.env.example` to `.env`
   - set `OPENAI_API_KEY`, `SUPABASE_DB_URL`, and `SUPABASE_DB_PASSWORD`
3. Start backend:
   - `pip install -r requirements.txt`
   - `uvicorn app.main:app --reload --port 8000`
4. Start dashboard:
   - `cd dashboard`
   - `npm install`
   - `npm run dev`

## Database Note
Use Supabase PostgreSQL transaction pooler URL for `SUPABASE_DB_URL`.
If your URL includes `[YOUR-PASSWORD]`, set `SUPABASE_DB_PASSWORD` and the backend will inject it safely.
