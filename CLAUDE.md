# ColdStart Cafe

Interactive web app exploring the cold-start problem in recommendation systems. Four algorithms compete with zero data, then progressively recover as users add signals.

## Project Structure

```
cold-start-cafe/
├── backend/          # FastAPI (Python 3.12, uv)
│   ├── app/
│   │   ├── config.py       # pydantic-settings (reads .env)
│   │   ├── main.py         # FastAPI app, CORS, lifespan, error handlers
│   │   ├── data/
│   │   │   └── loader.py   # DataStore: loads Parquet, O(1) movie lookups, search
│   │   ├── models/          # Pydantic models (enums, simulation, challenge, movies)
│   │   ├── routers/
│   │   │   ├── simulation.py  # POST/GET /simulation, POST /simulation/{id}/signal
│   │   │   └── movies.py      # GET /movies/search
│   │   └── services/
│   │       ├── algorithms/
│   │       │   ├── base.py          # RecommenderResult model + Recommender Protocol
│   │       │   ├── popularity.py    # Bayesian average, cached rankings
│   │       │   ├── content_based.py # Genre vector cosine similarity
│   │       │   ├── collaborative.py # scikit-surprise SVD, demographic neighbors
│   │       │   └── hybrid.py        # Adaptive weighted ensemble of all three
│   │       ├── metrics.py           # precision@k, recall@k, NDCG@k
│   │       ├── ground_truth.py      # Random eligible user + relevant set extraction
│   │       ├── simulation_engine.py # Orchestrator: apply signal → run algos → compute metrics
│   │       ├── session_manager.py   # Thread-safe UUID → SimulationState store
│   │       └── validators.py        # Signal payload validation against dataset
│   └── tests/
├── frontend/         # React 19, TypeScript, Vite, Chakra UI v3
│   └── src/
│       ├── api/
│       │   └── client.ts       # Typed fetch wrapper with ApiError class
│       ├── components/
│       │   ├── Navbar.tsx          # Café-branded nav with active link state
│       │   ├── SignalPanel.tsx     # Four accordion sections for signal input
│       │   ├── MovieSearchModal.tsx # Debounced search, dual-mode (rating/viewHistory)
│       │   └── Toaster.tsx         # Chakra v3 toast renderer
│       ├── hooks/
│       │   └── useSimulation.ts    # Single source of truth for simulation state + actions
│       ├── pages/
│       │   ├── LandingPage.tsx     # Hero section + algorithm explainer grid
│       │   ├── SimulationDashboard.tsx  # Three-column layout (signals | data | narration)
│       │   └── ChallengePage.tsx   # Placeholder for Phase 6+
│       ├── types/
│       │   ├── simulation.ts   # TS interfaces mirroring backend Pydantic models
│       │   ├── movies.ts       # MovieSearchResult, MovieSearchResponse
│       │   └── challenge.ts    # Placeholder types for Phase 6+
│       ├── utils/
│       │   └── toaster.ts      # createToaster instance (separated for fast-refresh)
│       ├── theme/
│       │   └── index.ts        # Chakra v3 system: brand colors, algo colors, fonts
│       ├── App.tsx             # Routes + Navbar + Toaster
│       └── main.tsx            # StrictMode + BrowserRouter + ChakraProvider
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
- `POST /api/v1/simulation` → 201, creates session, selects ground-truth user, returns step 0
- `POST /api/v1/simulation/{session_id}/signal` → 200, adds signal (rating/demographic/genre_preference/view_history), re-runs algorithms
- `GET /api/v1/simulation/{session_id}` → 200, returns full state with all steps + current signal summary
- `GET /api/v1/movies/search?q={query}&limit={limit}` → 200, title substring search (default limit=10, max=50)
- Errors: 400 (invalid payload — bad movie ID, score out of range, unknown genre), 404 (session not found), 422 (Pydantic validation — wrong type or missing field)

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
2. `SessionManager` created at startup → injected into simulation router via `init_simulation_router()`
3. `POST /simulation` → `ground_truth.py` selects random eligible user → stored in server-side `_ground_truth_store` (never serialized to client)
4. `POST /simulation/{id}/signal` → `validators.py` checks payload → `simulation_engine.apply_signal()` mutates state → `simulation_engine.run_step()` runs all 4 algorithms → `metrics.py` computes precision@k, recall@k, NDCG@k → returns `SimulationStep`

### Backend Layers

```
Router (HTTP)              → Engine (Orchestration)         → Storage (State)
routers/simulation.py        services/simulation_engine.py    services/session_manager.py
routers/movies.py            services/validators.py
```

- **Routers** handle HTTP concerns: parse requests, map exceptions to status codes (ValueError→400, missing session→404)
- **Engine** handles business logic: apply signals, run algorithms, compute metrics, resolve movie metadata
- **Storage** handles state: thread-safe `dict[UUID, SimulationState]` with `threading.Lock`
- Ground truth stored separately from `SimulationState` to prevent data leakage through Pydantic serialization
- Global `@app.exception_handler(ValueError)` converts any `ValueError` to 400 JSON response

### Frontend Architecture

```
App.tsx (Routes + Navbar + Toaster)
├── LandingPage          → Hero + algorithm grid, CTA navigates to /simulate
├── SimulationDashboard  → Three-column layout, owns useSimulation hook
│   ├── SignalPanel      → Four accordion sections (rating, demographics, genres, view history)
│   ├── DebugStepView    → Center panel showing metrics per step (placeholder for Phase 5 charts)
│   ├── NarrationView    → Right panel showing narration per step
│   └── MovieSearchModal → Debounced search, dual-mode (rating stars / viewHistory checkboxes)
└── ChallengePage        → Placeholder for Phase 6+
```

- **`useSimulation` hook** is the single source of truth — components receive data and callbacks via props, never call `api/client.ts` directly
- **Exception:** `MovieSearchModal` calls `searchMovies()` directly since search results are ephemeral (not simulation state)
- **Auto-create on mount:** `useEffect` + `useRef` guard prevents duplicate sessions in StrictMode
- **Error handling:** API errors → `toaster.create()` toast notifications
- **Loading states:** `Skeleton` components in center panel during initial load

### Chakra UI v3 Patterns

- **Composable API:** `Dialog.Root`/`.Content`/`.Header` (not v2's `Modal`/`ModalContent`/`ModalHeader`)
- **Disabled propagation:** behavioral props (`disabled`, `readOnly`) go on `.Root`, not on `.Field`
- **Toast architecture:** `createToaster()` in `utils/toaster.ts` (imperative store), `<Toaster>` in `components/Toaster.tsx` (declarative renderer) — separated for ESLint `react-refresh/only-export-components`
- **Theme tokens:** `{ value: "#hex" }` syntax, `brand.*` for visual identity, `algo.*` for algorithm-specific colors
- **Fonts:** Playfair Display (headings) + Inter (body) via Google Fonts `<link>` in `index.html`, referenced in theme `fonts` tokens

### TypeScript Config

- `erasableSyntaxOnly: true` — no parameter properties, no enums, no namespaces (ensures compatibility with esbuild type stripping)
- `verbatimModuleSyntax: true` — must use `import type` for type-only imports
- Strict mode enabled

## Code Style

### Backend (Python)
- Ruff enforces style: line-length 100, target py312
- Rule sets: E, F, I, N, W, UP
- Use `pydantic.BaseModel` for all request/response schemas
- Use `Protocol` for interfaces (not ABC) — algorithms are stateless functions
- Async endpoints by default
- `threading.Lock` (not `asyncio.Lock`) for shared state — FastAPI dispatches sync code to thread pools
- `ValueError` for semantic validation errors (→400); Pydantic `ValidationError` for structural issues (→422)
- pytest with `asyncio_mode = "auto"`
- Use `module`-scoped fixtures for expensive resources (DataStore, fixture datasets)
- `TestClient(app)` must be used as context manager (`with TestClient(app) as c`) to trigger lifespan
- Unit tests use small fixture datasets (`tmp_path_factory`); integration tests use real MovieLens data

### Frontend (TypeScript/React)
- ESLint + Prettier
- Chakra UI v3 for components and theming (composable `.Root`/`.Content` API, not v2)
- `useCallback` on all hook actions to stabilize function references for child components
- Debounced search via `useEffect` + `setTimeout` cleanup (no external library)
- `import type` for all type-only imports (enforced by `verbatimModuleSyntax`)
- Recharts for data visualization (Phase 5)
- React Router v7 for navigation (`BrowserRouter` wrapping app in `main.tsx`)

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

109 backend tests across 8 test files:

| File | Count | Scope |
|---|---|---|
| `test_health.py` | 1 | Health endpoint smoke test |
| `test_data_loader.py` | 14 | DataStore loading, lookups, search, ground-truth eligibility |
| `test_metrics.py` | 19 | precision@k, recall@k, NDCG@k with hand-computed values |
| `test_algorithms.py` | 21 | Algorithm behavior contracts using 20-movie fixture dataset |
| `test_algorithm_pipeline.py` | 16 | Full pipeline on real MovieLens 100K (~10s, SVD-dominated) |
| `test_simulation_api.py` | 29 | Simulation endpoints: create, add signals (all 4 types), get state, error handling |
| `test_movies_api.py` | 9 | Movie search: queries, limits, case-insensitivity, edge cases |

```bash
cd backend
uv run pytest -v                                 # all 109 tests
uv run pytest tests/test_algorithms.py -v         # fast algorithm unit tests only
uv run pytest tests/test_algorithm_pipeline.py -v # slow integration tests
uv run pytest tests/test_simulation_api.py tests/test_movies_api.py -v  # API integration tests
```

Frontend checks (no test suite yet — manual testing via browser):

```bash
cd frontend
npm run type-check   # tsc --noEmit — strict TypeScript verification
npm run lint         # eslint — 0 errors, 0 warnings
npm run build        # production build — verifies full compilation
```
