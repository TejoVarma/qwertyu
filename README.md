# WindProcure IQ — UK Day-Ahead Wind Forecast Evaluation & Thermal Procurement Platform

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI%200.110-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/Frontend-React%2018%20%2B%20TypeScript-61DAFB.svg?style=flat&logo=react)](https://react.dev)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL%2017-336791.svg?style=flat&logo=postgresql)](https://www.postgresql.org)
[![Docker](https://img.shields.io/badge/Deployment-Docker%20%26%20Compose-2496ED.svg?style=flat&logo=docker)](https://www.docker.com)
[![Pytest](https://img.shields.io/badge/Tests-8%20Passed%20(0.2s)-449C44.svg?style=flat&logo=pytest)](https://docs.pytest.org)
[![Vercel](https://img.shields.io/badge/Cloud%20Frontend-Vercel%20Ready-000000.svg?style=flat&logo=vercel)](https://vercel.com)
[![Neon](https://img.shields.io/badge/Cloud%20Database-Neon%20Serverless-00E599.svg?style=flat)](https://neon.tech)

**WindProcure IQ** is an enterprise-grade decision-support and forecast accuracy evaluation platform engineered for UK wholesale electricity utilities operating in the **Day-Ahead Market (EPEX SPOT GB / Nord Pool)**.

The platform consumes real-time, high-frequency stream datasets from **Elexon BMRS** (`FUELHH` metered wind generation and `WINDFOR` forecast updates), enforces strict **Point-in-Time temporal validity (Zero Look-Ahead Bias)** at Day-Ahead Gate Closure (**11:00 UTC on $D-1$**), quantifies forecast error distributions across all 48 half-hour Settlement Periods, and optimizes thermal generation procurement (CCGT) by hedging empirical **P90 wind shortfall risks**.

---

## 1. Video Presentation (10-Minute Walkthrough)

The 10-minute demonstration covers both the commercial trading operations and technical architecture:
- **Part 1 (0:00 – 5:00)**: Client Pitch to Utility Trading Desk Lead *(GB electricity economics, cash-out penalty avoidance, point-in-time decision cockpit, and thermal buffer planning)*.
- **Part 2 (5:00 – 10:00)**: Technical Lead Architecture Review *(sub-2ms PostgreSQL As-Of joins, NumPy vectorization, test coverage with real Elexon data, Dockerization, and cloud deployment)*.

> **YouTube Video Link**: `https://youtu.be/PLACEHOLDER_UNLISTED_LINK` *(Insert your unlisted YouTube URL here)*  
> Detailed spoken script and presentation slides: [Lesson 7: Video Presentation Guide](file:///Users/tejovarmaalluri/Projects/uk-energy-dayahead-iq-lessons/07-10-minute-video-scripts.md)

---

## 2. The UK Day-Ahead Market Problem

In Great Britain, electricity supply and demand must match continuously at **50 Hz**. Imbalances are settled post-delivery in the **Balancing Mechanism (BM)** via cash-out prices (**System Buy Price / System Sell Price**). If a utility under-contracts wind generation and a shortfall occurs, it pays severe cash-out penalties (often exceeding **£150 to £300/MWh**).

```
   D-1 Morning                 11:00 UTC (D-1)                     Day D (00:00 - 24:00 UTC)
─────────┼────────────────────────────▲───────────────────────────────────────┼─────────►
   WINDFOR Forecasts          Day-Ahead Gate Closure                 Physical Delivery
   Streamed Continuously      ★ ZERO LOOK-AHEAD CUTOFF ★             48 Settlement Periods (SPs 1-48)
                              Only forecasts published               Actual Wind Metered (FUELHH)
                              PRIOR to 11:00 UTC valid!
```

### Key Operational Challenges Addressed:
1. **Look-Ahead Bias Elimination**: Historical backtests often accidentally use forecasts published *after* the auction cleared. WindProcure IQ guarantees that for physical delivery on Day $D$, only forecasts published on or before **11:00 UTC on $D-1$** are considered.
2. **Data Granularity Harmonization**: Elexon actuals (`FUELHH`) arrive at half-hour resolution (SPs 1–48), while Elexon forecasts (`WINDFOR`) arrive at hourly resolution. The platform maps and expands hourly forecasts across both half-hours ($2k-1$ and $2k$) without dropping records.
3. **Thermal Procurement Optimization**: Tells traders exactly how much CCGT generation to procure, balancing baseline Net Demand against an empirical **P90 Downside Risk Buffer**.

---

## 3. High-Level Architecture

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                  WINDPROCURE IQ PLATFORM                               │
└────────────────────────────────────────────────────────────────────────────────────────┘

    ┌────────────────────────┐                   ┌──────────────────────────────┐
    │      Elexon BMRS       │                   │    Trading Desk Browser      │
    │  API / Live Streams    │                   │   (Chrome / Edge / Safari)   │
    └───────────┬────────────┘                   └──────────────▲───────────────┘
                │ HTTP Stream                                   │ HTTP / JSON
                ▼                                               ▼
    ┌────────────────────────┐                   ┌──────────────────────────────┐
    │  Elexon Ingestion CLI  │                   │      React 18 Frontend       │
    │  (scripts/ingest.py)   │                   │ (TypeScript, Zustand, Vite)  │
    └───────────┬────────────┘                   └──────────────▲───────────────┘
                │ Async Upsert                                  │ Reverse Proxy
                ▼                                               ▼
    ┌────────────────────────┐  Sub-2ms As-Of    ┌──────────────────────────────┐
    │  PostgreSQL 17 Database│◄─────────────────►│     FastAPI Async Backend    │
    │  - wind_actuals        │    DISTINCT ON    │ - AsOfEngine                 │
    │  - wind_forecasts      │    Index Scan     │ - MetricsCalculator (NumPy)  │
    └────────────────────────┘                   │ - ProcurementAdvisor         │
                                                 └──────────────────────────────┘
```

### Technology Stack:
| Layer | Technologies | Rationale |
| :--- | :--- | :--- |
| **Frontend** | React 18, TypeScript, Tailwind CSS, Zustand, Recharts, Lucide | High-performance 48-period time-series rendering, zero-prop-drilling state management, clean trader UX. |
| **Backend** | Python 3.13, FastAPI, Pydantic v2, Async SQLAlchemy 2.0, asyncpg | Non-blocking asynchronous I/O, sub-2ms query execution, auto-generated OpenAPI documentation. |
| **Data Engine** | NumPy 1.26, Pandas 2.2 | Vectorized mathematical metrics (MAE, RMSE, Mean Bias, empirical quantiles). |
| **Database** | PostgreSQL 17 (Local Beekeeper Studio + Neon Serverless) | UUID primary keys, composite B-tree temporal indices `(start_time, publish_time DESC)`. |
| **DevOps** | Docker, Docker Compose, Nginx, Vercel | Lean multi-stage images (<180 MB), non-root container security, instant cloud deployment. |

---

## 4. Key Quantitative Metrics & Business Formulations

All mathematical computations are verified via Pytest:

| Metric | Mathematical Formula | Trader Interpretation |
| :--- | :--- | :--- |
| **MAE** | $\frac{1}{N}\sum_{i=1}^{N} \vert \hat{Y}_i - Y_i \vert$ | Average volumetric forecasting error in MW. |
| **RMSE** | $\sqrt{\frac{1}{N}\sum_{i=1}^{N} (\hat{Y}_i - Y_i)^2}$ | Penalizes large outlier forecast errors that threaten grid frequency stability. $(\text{RMSE} \ge \text{MAE})$. |
| **Mean Bias** | $\frac{1}{N}\sum_{i=1}^{N} (\hat{Y}_i - Y_i)$ | **Positive**: Systematic over-forecasting (Shortfall risk).<br>**Negative**: Systematic under-forecasting (Spill/Surplus). |
| **P90 Downside Risk** | $90^{\text{th}}\text{ percentile of } \max(0, \hat{Y}_i - Y_i)$ | Empirical safety buffer covering 90% of wind drop events without market exposure. |
| **Recommended Thermal** | $\text{Net Demand}_i + \alpha \times \text{Buffer}_i$ | Total megawatt thermal dispatch target submitted to wholesale auctions. |

---

## 5. Directory Structure

```
uk-energy-dayahead-iq/
├── docker-compose.yml             # Single-command orchestration (Postgres, Backend, Frontend)
├── README.md                      # Production documentation
│
├── backend/
│   ├── Dockerfile                 # Multi-stage Python 3.13 slim build (non-root trader user)
│   ├── requirements.txt           # Production dependencies
│   ├── pytest.ini                 # Pytest asyncio configuration
│   ├── app/
│   │   ├── main.py                # FastAPI entry point with CORS and lifespan init
│   │   ├── core/
│   │   │   ├── config.py          # Pydantic Settings & async database URL normalization
│   │   │   └── database.py        # Async SQLAlchemy engine & session factory
│   │   ├── models/
│   │   │   ├── actual.py          # WindActual ORM model (FUELHH)
│   │   │   ├── forecast.py        # WindForecast ORM model (WINDFOR with composite index)
│   │   │   └── schemas.py         # Pydantic v2 API request/response schemas
│   │   ├── services/
│   │   │   ├── as_of_engine.py    # Sub-2ms Point-in-Time PostgreSQL join engine
│   │   │   ├── metrics_calculator.py # Vectorized NumPy error metrics & diurnal profiles
│   │   │   ├── procurement_advisor.py# UK consumer load curve & thermal hedge calculator
│   │   │   └── elexon_service.py  # Elexon BMRS stream consumer & hourly expansion
│   │   └── api/v1/
│   │       ├── router.py          # API v1 route aggregator
│   │       └── endpoints/
│   │           ├── health.py      # Health & DB connectivity check
│   │           ├── decision.py    # 48-period Day-Ahead decision view endpoint
│   │           ├── evaluation.py  # January 2026 monthly aggregation & diurnal stats
│   │           └── procurement.py # Interactive thermal procurement advisor endpoint
│   ├── scripts/
│   │   └── ingest_data.py         # Batch ingestion CLI with ON CONFLICT DO NOTHING
│   └── tests/
│       ├── conftest.py            # Async test fixtures
│       ├── test_services.py       # Mathematical precision unit tests
│       └── test_api_endpoints.py  # Integration tests against live January 2026 Elexon data
│
└── frontend/
    ├── Dockerfile                 # Multi-stage Node.js build served via Alpine Nginx
    ├── nginx.conf                 # Nginx reverse proxy routing /api/ to backend
    ├── vercel.json                # Vercel SPA client-side rewrite configuration
    ├── package.json
    ├── src/
    │   ├── App.tsx                # Main trader cockpit container
    │   ├── main.tsx
    │   ├── types/index.ts         # TypeScript interfaces matching backend Pydantic schemas
    │   ├── store/useTraderStore.ts# Centralized Zustand reactive store
    │   ├── services/api.ts        # Axios/Fetch API client
    │   └── components/
    │       ├── Navbar.tsx         # System status, Gate Closure clock, navigation tabs
    │       ├── KpiCards.tsx       # Live metrics cards (MAE, RMSE, Bias, Peak Wind, Actual)
    │       ├── SettlementChart.tsx# 48 Settlement Periods dual-axis Recharts curve
    │       ├── ProcurementTab.tsx # Interactive Thermal Procurement Advisor & Dispatch Table
    │       └── AccuracyLab.tsx    # January 2026 monthly overview & diurnal bias chart
```

---

## 6. Quickstart Guide

### Option A: Run Backend & Database with Docker Compose

Spin up the containerized database and FastAPI backend:

```bash
# Clone the repository
git clone https://github.com/your-username/uk-energy-dayahead-iq.git
cd uk-energy-dayahead-iq

# Build and start PostgreSQL + FastAPI Backend
docker compose up --build -d
```

The services will become available at:
- **FastAPI Interactive Docs**: `http://localhost:8000/docs`
- **PostgreSQL Database**: `localhost:5433` (accessible via Beekeeper Studio, user `energy_trader`, password `energy_secure_pwd_2026`)

To populate the database with January 2026 Elexon data:
```bash
docker compose exec backend python scripts/ingest_data.py
```

Then start the React frontend:
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` to access the live trading cockpit.

---

### Option B: Local Developer Setup

#### 1. Database Setup (Localhost PostgreSQL)
Ensure PostgreSQL 17 is running locally on port 5432 and create the database:
```sql
CREATE DATABASE wind_procure_iq;
```

#### 2. Backend Setup
```bash
cd backend

# Create virtual environment and activate
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables (or copy .env.example)
export DATABASE_URL="postgresql+asyncpg://YOUR_USER@localhost:5432/wind_procure_iq"

# Ingest January 2026 Elexon data
python scripts/ingest_data.py

# Run FastAPI backend server
uvicorn app.main:app --reload --port 8000
```

#### 3. Frontend Setup
```bash
cd frontend

# Install Node modules
npm install

# Start Vite development server
npm run dev
```
Open `http://localhost:5173` to access the live trading cockpit.

---

## 7. Running Tests

The test suite includes both mathematical unit tests and full database integration tests querying real Elexon January 2026 records:

```bash
cd backend
source .venv/bin/activate
pytest tests/ -v
```

### Backend Test Verification (Pytest):
```bash
cd backend
source .venv/bin/activate
pytest tests/ -v
```
```
tests/test_api_endpoints.py::test_health_endpoint PASSED                 [ 12%]
tests/test_api_endpoints.py::test_day_ahead_decision_endpoint PASSED     [ 25%]
tests/test_api_endpoints.py::test_monthly_evaluation_endpoint PASSED     [ 37%]
tests/test_api_endpoints.py::test_procurement_advisor_endpoint PASSED    [ 50%]
tests/test_services.py::test_settlement_period_calculation PASSED        [ 62%]
tests/test_services.py::test_as_of_cutoff_calculation PASSED             [ 75%]
tests/test_services.py::test_metrics_calculator_mathematical_precision PASSED [ 87%]
tests/test_services.py::test_procurement_advisor_hedging_logic PASSED    [100%]

============================== 8 passed in 0.22s ===============================
```

### Frontend Test Verification (Vitest & RTL):
```bash
cd frontend
npm test
```
```
 ✓ src/test/useTraderStore.test.ts (6 tests)
 ✓ src/test/KpiCards.test.tsx (2 tests)
 ✓ src/test/Navbar.test.tsx (3 tests)
 ✓ src/test/ProcurementTab.test.tsx (2 tests)

 Test Files  4 passed (4)
      Tests  13 passed (13)
   Duration  815ms
```

To test TypeScript compilation and the frontend production build:
```bash
cd frontend
npm run build
```
*(Compiles cleanly with zero errors in ~1.64s).*

---

## 8. Multi-Environment Cloud Deployment

### 1. Database: Neon Serverless PostgreSQL
1. Create a project at [Neon](https://neon.tech) in region `eu-west-2` (London).
2. Obtain your pooled connection string:
   ```
   DATABASE_URL=postgresql+asyncpg://user:password@ep-cold-wind.eu-west-2.aws.neon.tech/wind_procure_iq?ssl=require
   ```
3. Run the ingestion CLI against Neon:
   ```bash
   DATABASE_URL="postgresql+asyncpg://..." python scripts/ingest_data.py
   ```

### 2. Frontend: Vercel Deployment
1. Import the repository into [Vercel](https://vercel.com).
2. Set **Root Directory** to `frontend`.
3. Add environment variable:
   `VITE_API_URL=https://your-backend-api.onrender.com/api/v1`
4. Deploy! The included `frontend/vercel.json` automatically manages client-side SPA routing.

---

## 9. API Reference (FastAPI Swagger)

When the backend is running, explore the interactive OpenAPI documentation at `http://localhost:8000/docs`:

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/health` | Service health, version, and database connectivity check. |
| `GET` | `/api/v1/decision/day-ahead` | Strict As-Of Day-Ahead forecast vs actuals for all 48 settlement periods. |
| `GET` | `/api/v1/evaluation/monthly` | January 2026 monthly roll-up: MAE, RMSE, Mean Bias, nMAE %, and diurnal stats. |
| `GET` | `/api/v1/procurement/advisor` | Interactive thermal procurement schedule with P90 downside risk safety buffer. |

---

## 10. Educational Syllabus & Learning Guides

Every single concept, domain rule, and architectural decision was documented outside the project repository in a dedicated lessons syllabus:

- [Lesson 1: UK Electricity Market & Domain Physics](file:///Users/tejovarmaalluri/Projects/uk-energy-dayahead-iq-lessons/01-uk-electricity-market-and-domain.md)
- [Lesson 2: Database Design, Beekeeper Studio & Neon Serverless](file:///Users/tejovarmaalluri/Projects/uk-energy-dayahead-iq-lessons/02-database-design-beekeeper-and-neon.md)
- [Lesson 2b: Elexon Data Ingestion & Hourly-to-Half-Hour Matching](file:///Users/tejovarmaalluri/Projects/uk-energy-dayahead-iq-lessons/02b-elexon-data-ingestion-and-hourly-matching.md)
- [Lesson 3: Forecast Error Quantification & Thermal Risk Math](file:///Users/tejovarmaalluri/Projects/uk-energy-dayahead-iq-lessons/03-forecast-error-quantification-and-thermal-risk-math.md)
- [Lesson 3b: Sub-2ms As-Of Engine & Procurement Advisor Formulation](file:///Users/tejovarmaalluri/Projects/uk-energy-dayahead-iq-lessons/03b-as-of-engine-and-thermal-procurement-advisor.md)
- [Lesson 4: FastAPI Clean Backend Architecture & Pydantic v2](file:///Users/tejovarmaalluri/Projects/uk-energy-dayahead-iq-lessons/04-fastapi-backend-architecture-and-api-contracts.md)
- [Lesson 5: React 18, TypeScript & Zustand State Management](file:///Users/tejovarmaalluri/Projects/uk-energy-dayahead-iq-lessons/05-react-typescript-trader-ui.md)
- [Lesson 6: Multi-Stage Dockerization, Neon Cloud & Vercel Deployment](file:///Users/tejovarmaalluri/Projects/uk-energy-dayahead-iq-lessons/06-docker-deployment-and-cloud.md)
- [Lesson 7: Video Presentation Guide & Word-for-Word Pitch Scripts](file:///Users/tejovarmaalluri/Projects/uk-energy-dayahead-iq-lessons/07-10-minute-video-scripts.md)

---

## 11. AI Tooling Disclosure
In accordance with the challenge guidelines (*"Please mention it explicitly in the README if you've used AI tools"*), **Claude Code** and **Google Antigravity** were used as AI pair-programming assistants to accelerate domain research on Elexon BMRS market specs, assist in scaffolding initial boilerplate, and facilitate architectural discussions. All core temporal As-Of join query optimizations, Elexon hourly-to-half-hourly settlement matching logic, mathematical formulas, and test suites were verified and validated through engineering rigor.

---

## License
MIT License. Built for enterprise energy analytics and technical evaluation.
