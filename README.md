# WindProcure IQ: UK Day-Ahead Wind Forecast Decision Support

A web app for a UK utility's day-ahead power buying team. It answers two questions:

1. **What was the latest wind forecast available when we had to bid?** For any delivery day, the app shows the national wind generation forecast exactly as it stood at the decision cutoff on the day before, next to what was actually generated.
2. **How much can we trust that forecast?** It quantifies forecast error (MAE, RMSE, bias, P90 shortfall) by day, by time of day and by forecast horizon, so procurement decisions can account for a measured error.

Data: Elexon BMRS only, national level: `FUELHH` (fuelType `WIND`) for actuals and `WINDFOR` for forecasts. Scope: purchase decisions made in January 2026, which means delivery days **2 January to 1 February 2026**.

| | |
| :--- | :--- |
| **Live app** | https://qwertyu-delta.vercel.app |
| **API docs (Swagger)** | https://windprocure-api.onrender.com/docs |
| **Video walkthrough** | https://youtu.be/qO-TAGCj2Zk |

---

## 1. Key findings for January 2026 decisions

Based on the latest forecast published at or before **11:00 UTC on D-1** (1,488 half-hours):

| Metric | Value |
| :--- | :--- |
| MAE | 2,016 MW (17.9% of mean metered wind output) |
| RMSE | 2,510 MW |
| Mean bias (forecast − actual) | **+1,730 MW**: forecast was above actual in 84% of half-hours |
| P90 / P95 shortfall | 4,172 MW / 5,347 MW |

Error grows with forecast horizon, which is the accuracy given up by committing a day ahead:

| Horizon (forecast issued at least h hours before delivery) | 1h | 12h | 24h | 36h | 48h |
| :--- | ---: | ---: | ---: | ---: | ---: |
| MAE (MW) | 1,694 | 1,804 | 1,945 | 2,154 | 2,316 |
| P90 absolute error (MW) | 3,439 | 3,649 | 3,812 | 4,139 | 4,752 |

The persistent over-forecast matters most for the desk: on average, roughly 1.7 GW less wind arrived than the day-ahead forecast promised, which is volume that has to be covered elsewhere. A likely contributor is that `FUELHH` reports metered output after any curtailment, while `WINDFOR` forecasts generation potential. This is worth confirming with the client before applying a bias correction.

---

## 2. Definitions and assumptions

| Topic | Choice |
| :--- | :--- |
| Decision cutoff | D-1 at 11:00 UTC by default; selectable in the UI and via `cutoff_hour`. In January, UK local time equals UTC. |
| Forecast used | For each delivery half-hour, the latest `WINDFOR` forecast with `publishTime <= cutoff`. Later forecasts are never used. |
| Resolution | `FUELHH` is half-hourly and `WINDFOR` is hourly. Each hourly forecast value is also applied to the following half-hour (a step hold), so every metered half-hour is compared. |
| Error sign | `error = forecast − actual`. Positive means wind delivered less than forecast (a shortfall). |
| Relative MAE | MAE divided by mean metered wind output over the same periods (data-derived, not an assumed capacity). |
| Horizon analysis | For horizon h, the latest forecast published at least h hours before each delivery half-hour. |
| Procurement what-if | Illustrative only. Demand is a user input (not Elexon data). The safety buffer for each settlement period is α × P90 of shortfalls on the 14 fully settled days ending at D-2. Nothing from D-1 or D itself is used. |

---

## 3. Architecture

```
Elexon BMRS (FUELHH, WINDFOR)
        │  scripts/ingest_data.py   (real data only; fails loudly on any API error)
        ▼
PostgreSQL ── wind_actuals    (start_time unique)
           └─ wind_forecasts  (unique start_time + publish_time, index for point-in-time lookups)
        │  point-in-time SQL (DISTINCT ON … ORDER BY publish_time DESC)
        ▼
FastAPI ── /decision  /evaluation  /procurement  /health
        │  JSON
        ▼
React + TypeScript (Vite, Zustand, Recharts, Tailwind)
```

- **Ingestion** is a separate CLI step, so the API never calls Elexon on a user request. Loads are idempotent (`ON CONFLICT DO NOTHING`), and `--reset` reloads from scratch.
- **Point-in-time join**: one SQL query derives each row's cutoff (`D-1 + cutoff_hour`) from the delivery timestamp, so the same query serves a single day or the whole month.
- **Metrics** are computed in Python (NumPy) in `MetricsCalculator`, which keeps them unit-testable and independent of the database.

### Stack

| Layer | Technologies |
| :--- | :--- |
| Frontend | React 18, TypeScript, Vite, Zustand, Recharts, Tailwind CSS, Vitest + React Testing Library |
| Backend | Python, FastAPI, Pydantic v2, async SQLAlchemy 2 + asyncpg, NumPy, httpx, Pytest |
| Database | PostgreSQL 17 (Docker locally, Neon in the cloud) |
| DevOps | Docker, Docker Compose, Vercel (frontend), Render (backend Docker image) |

---

## 4. Directory structure

```
.
├── docker-compose.yml          # PostgreSQL + FastAPI backend
├── README.md
├── backend/
│   ├── Dockerfile              # Multi-stage Python image, runs as non-root user
│   ├── requirements.txt
│   ├── pytest.ini
│   ├── .env.example            # Environment variables template
│   ├── app/
│   │   ├── main.py             # FastAPI app, CORS, startup table creation
│   │   ├── core/
│   │   │   ├── config.py       # Settings (DB URL, cutoff hour, evaluation window, horizons)
│   │   │   └── database.py     # Async engine and session dependency
│   │   ├── models/
│   │   │   ├── actual.py       # wind_actuals table (FUELHH WIND)
│   │   │   ├── forecast.py     # wind_forecasts table (WINDFOR)
│   │   │   └── schemas.py      # Pydantic request/response models
│   │   ├── services/
│   │   │   ├── elexon_service.py      # Elexon BMRS client
│   │   │   ├── as_of_engine.py        # Point-in-time and horizon SQL
│   │   │   ├── metrics_calculator.py  # MAE, RMSE, bias, percentiles, diurnal/daily/horizon roll-ups
│   │   │   └── procurement_advisor.py # Illustrative thermal requirement with historical buffer
│   │   └── api/v1/
│   │       ├── router.py
│   │       └── endpoints/      # health.py, decision.py, evaluation.py, procurement.py
│   ├── scripts/
│   │   ├── ingest_data.py      # Loads Elexon data into PostgreSQL
│   │   └── init_db.py          # Creates tables
│   └── tests/
│       ├── conftest.py         # Test client on a dedicated, seeded test database
│       ├── seed.py             # Small hand-checkable dataset
│       ├── test_api_endpoints.py
│       ├── test_elexon_service.py  # Elexon client against mocked HTTP responses
│       └── test_services.py
└── frontend/
    ├── vercel.json             # SPA rewrites + /api proxy to the backend
    ├── vite.config.ts          # Dev server proxies /api to localhost:8000
    └── src/
        ├── App.tsx
        ├── components/         # Navbar, KpiCards, SettlementChart, AccuracyLab, ProcurementTab
        ├── store/useTraderStore.ts
        ├── services/api.ts
        ├── types/index.ts
        └── test/               # Vitest + React Testing Library
```

---

## 5. Running locally

Prerequisites: Docker and Node.js 18+.

```bash
# 1. Start PostgreSQL and the FastAPI backend
docker compose up --build -d

# 2. Load Elexon data (about 15 seconds; no API key needed)
docker compose exec backend python scripts/ingest_data.py --reset

# 3. Start the frontend
cd frontend
npm install
npm run dev
```

- App: http://localhost:5173
- API docs: http://localhost:8000/docs

To run the backend without Docker, create `backend/.env` from `.env.example`, then run `pip install -r requirements.txt`, `python scripts/ingest_data.py --reset` and `uvicorn app.main:app --reload`.

---

## 6. Tests

```bash
# Backend: unit tests + API tests on a seeded test database
# (uses the docker-compose Postgres on localhost:5433 and creates `wind_procure_iq_test`;
#  override with TEST_DATABASE_URL)
cd backend && pytest -q

# Frontend
cd frontend && npm test
```

The API tests seed a small dataset with a forecast published **after** the cutoff and check that it is never used. They also check that the procurement buffer ignores D-1 and D.

---

## 7. Deployment

- **Database**: Neon PostgreSQL, loaded with `DATABASE_URL=... python scripts/ingest_data.py --reset`.
- **Backend**: the `backend/Dockerfile` image on Render. A long-running FastAPI service with a connection pool fits a container host better than serverless functions, and Heroku no longer has a free tier.
- **Frontend**: Vercel, root directory `frontend`. `vercel.json` proxies `/api/*` to the backend, so the browser only talks to one origin.

---

## 8. API reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Service status, database connectivity and row counts. |
| `GET` | `/decision/day-ahead?delivery_date=&cutoff_hour=` | 48 half-hours of the forecast as of the cutoff vs actuals, with day KPIs. |
| `GET` | `/evaluation/monthly?start_date=&end_date=&cutoff_hour=` | Window metrics, profile by settlement period and daily roll-up. Defaults to 2 Jan to 1 Feb 2026. |
| `GET` | `/evaluation/daily-log` | Daily roll-up only. |
| `GET` | `/evaluation/horizon?start_date=&end_date=` | Error statistics by forecast horizon (1 to 48 hours). |
| `POST` | `/procurement/advisor` | Illustrative thermal requirement with a historical P90 buffer. |

---

## 9. Update after submission

After submitting, I found that the ingestion script had a fallback that generated synthetic forecasts whenever an Elexon request came back incomplete. Some of those synthetic rows reached the deployed database and were being selected instead of real forecasts, which inflated the error figures shown in the original video (for example, a day MAE of 11.8 GW instead of the real 1.1 GW on 15 January). Fixes:

- Removed the synthetic fallback. Ingestion now uses real Elexon data only and stops on any API error. The database was reloaded.
- The procurement buffer previously used the delivery day's own actuals (look-ahead). It now uses only days settled before the decision.
- The evaluation window now matches decisions made in January (delivery 2 Jan to 1 Feb).
- Added the forecast-horizon analysis.
- Tests now run on a seeded test database and assert the point-in-time and no-look-ahead rules.

The screens and workflow are the same as in the video; only the numbers changed.

---

## 10. AI tooling disclosure

In accordance with the challenge guidelines, **Claude Code** and **Google Antigravity** were used as AI pair-programming assistants for domain research on Elexon BMRS datasets, scaffolding, code review and architectural discussion. All logic, queries and metrics were reviewed and verified against the raw Elexon data and the test suite.
