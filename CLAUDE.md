# ColdStart Cafe

Interactive web app exploring the cold-start problem in recommendation systems. Four algorithms compete with zero data, then progressively recover as users add signals.

## Project Structure

```
cold-start-cafe/
├── backend/          # FastAPI (Python 3.12, uv)
│   ├── app/
│   │   ├── config.py       # pydantic-settings (reads .env)
│   │   ├── main.py         # FastAPI app, CORS, lifespan
│   │   ├── data/
│   │   │   └── loader.py   # DataStore: loads Parquet, O(1) movie lookups, search
│   │   ├── models/          # Pydantic models (enums, simulation, challenge, movies)
│   │   ├── routers/         # API route handlers
│   │   └── services/
│   │       ├── algorithms/
│   │       │   ├── base.py          # RecommenderResult model + Recommender Protocol
│   │       │   ├── popularity.py    # Bayesian average, cached rankings
│   │       │   ├── content_based.py # Genre vector cosine similarity
│   │       │   ├── collaborative.py # scikit-surprise SVD, demographic neighbors
│   │       │   └── hybrid.py        # Adaptive weighted ensemble of all three
│   │       ├── metrics.py           # precision@k, recall@k, NDCG@k
│   │       └── ground_truth.py      # Random eligible user + relevant set extraction
│   └── tests/
├── frontend/         # React 19, TypeScript, Vite, Chakra UI v3
│   └── src/
├── data/             # Bundled MovieLens 100K Parquet files (committed)
├── scripts/          # Data preparation scripts
└── docker-compose.yml
```

## Commands

### Backend
```bash
cd backend
uv sync                              # install deps
uv run uvicorn app.main:app --reload # dev server on :8000
uv run pytest -v                     # tests
uv run ruff check .                  # lint
uv run ruff format --check .         # format check
uv run ruff format .                 # auto-format
```

### Frontend
```bash
cd frontend
npm install          # install deps
npm run dev          # dev server on :5173
npm run lint         # eslint
npm run type-check   # tsc --noEmit
npm run build        # production build
```

### Docker
```bash
docker compose up --build   # runs both services
```

## API

- Base path: `/api/v1`
- Health check: `GET /api/v1/health`

## Architecture

### Algorithm Interface

All recommendation algorithms satisfy the `Recommender` Protocol (structural subtyping — no inheritance required):

```python
def recommend(state: SimulationState, data: DataStore) -> RecommenderResult
```

- `RecommenderResult` contains `movie_ids: list[int]` (ranked top-10) and `scores: list[float]` (normalized 0-1)
- Algorithms are **stateless module-level functions**, not classes
- Popularity and content-based cache expensive computations (genre matrix, rankings) at module level using `id(data)` as a cache-invalidation sentinel

### Algorithm Behavior at Cold Start

| Signal State | Popularity | Content-Based | Collaborative | Hybrid Weights |
|---|---|---|---|---|
| Zero signals | Returns 10 | Empty | Empty | 100% pop |
| Ratings only | Returns 10 | Genre-similar | SVD predictions | 20/40/40 |
| + demographics | Returns 10 | Unchanged | Neighbor-init'd | 20/30/50 |
| All signals | Returns 10 | Boosted by prefs | Full SVD | 15/25/50 |

### Key Dependencies

- `numpy>=1.26.0,<2.0.0` — pinned because scikit-surprise 1.1.4's Cython extensions are compiled against NumPy 1.x ABI
- `scikit-surprise` — collaborative filtering SVD (requires Python <3.13)
- `scikit-learn` — cosine similarity for content-based filtering

### Data Flow

1. `DataStore` loads Parquet files at startup → stored on `app.state.data`
2. `ground_truth.py` selects a random eligible user (≥3 genres, ≥20 ratings) → relevant set = movies rated ≥4.0
3. Each algorithm's `recommend()` receives `SimulationState` (user signals) + `DataStore` → returns ranked top-10
4. `metrics.py` compares recommendations against ground-truth relevant set → precision@k, recall@k, NDCG@k

## Code Style

### Backend (Python)
- Ruff enforces style: line-length 100, target py312
- Rule sets: E, F, I, N, W, UP
- Use `pydantic.BaseModel` for all request/response schemas
- Use `Protocol` for interfaces (not ABC) — algorithms are stateless functions
- Async endpoints by default
- pytest with `asyncio_mode = "auto"`
- Use `module`-scoped fixtures for expensive resources (DataStore, fixture datasets)
- Unit tests use small fixture datasets (`tmp_path_factory`); integration tests use real MovieLens data

### Frontend (TypeScript/React)
- ESLint + Prettier
- Chakra UI v3 for components and theming
- Recharts for data visualization
- React Router for navigation

## Environment

- Copy `.env.example` to `.env` at the project root
- `ANTHROPIC_API_KEY` — required for AI-powered features
- `DATA_DIR` — path to Parquet data files (default: `data`)
- `CORS_ORIGINS` — allowed origins (default: `["http://localhost:5173"]`)

## CI

GitHub Actions runs on push/PR to `main`:
- **Backend:** ruff check, ruff format --check, pytest
- **Frontend:** eslint, tsc type-check

## Tests

71 tests total across 6 test files:

| File | Count | Scope |
|---|---|---|
| `test_health.py` | 1 | Health endpoint smoke test |
| `test_data_loader.py` | 14 | DataStore loading, lookups, search, ground-truth eligibility |
| `test_metrics.py` | 19 | precision@k, recall@k, NDCG@k with hand-computed values |
| `test_algorithms.py` | 21 | Algorithm behavior contracts using 20-movie fixture dataset |
| `test_algorithm_pipeline.py` | 16 | Full pipeline on real MovieLens 100K (~10s, SVD-dominated) |

```bash
cd backend
uv run pytest -v                                 # all 71 tests
uv run pytest tests/test_algorithms.py -v         # fast algorithm unit tests only
uv run pytest tests/test_algorithm_pipeline.py -v # slow integration tests
```
