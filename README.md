# Starter — Habit Tracker

A tiny FastAPI + SQLite service for habits and daily check-ins. You'll add two features
on branches, open PRs, and run an AI reviewer.

## Setup
```bash
pip install -r requirements.txt
pytest                      # 3 tests should pass
uvicorn main:app --reload   # http://localhost:8000  (docs at /docs)
```

## Endpoints
- `POST /habits` `{ "name": ... }`
- `GET /habits`
- `POST /habits/{id}/checkin` `{ "day": "2026-09-22" }`
- `GET /habits/{id}/checkins`
- `GET /habits/{id}/streak` (consecutive check-in days ending today, or yesterday if there is no check-in today yet)

## Files
- `main.py` — the app
- `test_main.py` — pytest suite
- `docs/TASKS.md` — the two features to implement
