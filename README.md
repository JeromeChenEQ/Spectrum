# Spectrum SeniorAid Button

Senior emergency alert system built with:
- Python FastAPI backend
- JavaScript React dashboard
- MySQL database

## Workflow Implemented
1. Senior presses device button and records audio clip (10s typical, up to 60s configurable).
2. Device uploads WAV file to FastAPI backend over HTTPS.
3. Backend makes a single AI call to process transcript, translation, and severity.
4. Backend stores results in MySQL tables: `boxes` and `alerts`.
5. React dashboard receives new alerts in realtime over WebSocket.
6. Dashboard sorts alerts by severity: EMERGENCY -> URGENT -> ROUTINE.
7. Staff can acknowledge an alert.

## Repository Layout
- `backend/api/`: FastAPI service and OpenAI integration.
- `dashboard/`: React dashboard (Vite).
- `database/`: MySQL schema and seed scripts.
- `docs/`: architecture, API, and conventions.

## Quick Start
1. Run SQL scripts in MySQL:
   - `database/schema.sql`
   - `database/seed.sql` (optional)
2. Configure backend:
   - `cd backend/api`
   - copy `.env.example` to `.env`
   - set `OPENAI_API_KEY` and MySQL values
3. Start backend:
   - `pip install -r requirements.txt`
   - `uvicorn app.main:app --reload --port 8000`
4. Start dashboard:
   - `cd dashboard`
   - `npm install`
   - `npm run dev`

## Important Note
Your workflow text referenced Supabase/PostgreSQL. This implementation keeps the same behavior but uses MySQL as requested.