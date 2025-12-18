# AI-Powered Stock & Macro Market Monitor (Full Stack)

Full-stack app that monitors **stocks**, **country/index markets**, and **macro indicators**, and generates simple **AI/ML predictions** (direction + expected return + confidence) using a modular prediction engine.

- **Backend**: Python + FastAPI + SQLAlchemy + Alembic + APScheduler
- **DB**: SQLite by default (Postgres-ready via `DATABASE_URL`)
- **ML**: scikit-learn (RandomForest) + pandas feature engineering
- **Frontend**: React + TypeScript (Vite) + Recharts
- **Mode toggle**: `APP_MODE=dev|prod` (dev uses deterministic mock data provider)

---

## Repo layout

- `backend/`: FastAPI API + scheduler + prediction engine
- `frontend/`: React/TS dashboard UI

---

## Backend setup (Python 3.10+)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
cp .env.example .env
python3 -m alembic upgrade head
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

- **Swagger/OpenAPI**: `http://localhost:8000/docs`

### Important env vars (`backend/.env`)

- **APP_MODE**: `dev` (mock provider) or `prod` (placeholder; swap real providers later)
- **DATABASE_URL**: optional override (otherwise uses `SQLITE_PATH`)
- **API_KEY_\***: placeholders for future providers (unused in dev)

---

## Frontend setup

```bash
cd frontend
npm install
npm run dev
```

- UI runs on `http://localhost:5173`
- Dev proxy forwards `/api/*` to `http://localhost:8000`

---

## End-to-end flow (what works now)

1) **Refresh mock data** (prices + macro) and auto-create a demo watchlist:

- `POST /api/admin/refresh-data`

2) **Generate predictions** for watchlist items + country outlook:

- `POST /api/admin/retrain`

3) **View in UI**:

- Overview cards: `/api/overview`
- Watchlist table: `/api/watchlist/summary`
- Instrument detail charts: `/api/prices/{symbol}` and `/api/predictions/{symbol}`
- Alerts panel: `/api/alerts`

---

## Main API endpoints (MVP)

- `GET /api/stocks`, `GET /api/indexes`
- `GET /api/countries`, `GET /api/countries/{country}/macro`
- `GET/POST/DELETE /api/watchlist/stocks/{symbol}`
- `GET/POST/DELETE /api/watchlist/countries/{index_symbol}` (implemented as index watchlist)
- `GET /api/prices/{symbol}?instrument_type=stock|index`
- `GET /api/predictions/{symbol}?target_type=stock|index`
- `GET /api/predictions/country/{country_code}`
- `POST /api/admin/refresh-data`, `POST /api/admin/retrain`
- `GET /api/alerts`, `PATCH /api/alerts/{id}`, `POST /api/alert-rules`

---

## Dev auth behavior

In **dev mode**, market endpoints auto-create a `demo` user and do not require a token. In **prod mode**, the market endpoints require a valid Bearer access token (JWT).
