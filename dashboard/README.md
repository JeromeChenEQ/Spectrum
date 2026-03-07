# React Dashboard

## Run
```bash
npm install
npm run dev
```

## Features
- Auto-loads alerts from FastAPI.
- Opens WebSocket to receive realtime new alerts and acknowledge updates.
- Sorts cards by severity (URGENT -> UNCERTAIN -> NON-URGENT).
- Lets helpdesk operator acknowledge open alerts.