# ColdStart Cafe

Interactive web app exploring the cold-start problem in recommendation systems. Two modes: **Simulation** — four algorithms compete with zero data, then progressively recover as users add signals; **Challenge** — users compete against the algorithms to recommend movies for a real user profile.

## Project Structure

```
cold-start-cafe/
├── backend/          # FastAPI (Python 3.12, uv)
│   ├── app/
│   │   ├── config.py       # pydantic-settings (reads .env)
│   │   ├── main.py         # FastAPI app, CORS, lifespan, background cleanup, rate limiting
│   │   ├── data/
│   │   │   ├── loader.py        # DataStore: loads Parquet, O(1) movie lookups, search
│   │   │   └── narrations.json  # 13 pre-generated café-themed narration templates
│   │   ├── middleware/
│   │   │   └── rate_limit.py    # Sliding window rate limiter (per-IP and per-session)
│   │   ├── models/          # Pydantic models (enums, simulation, challenge, movies)
│   │   ├── routers/
│   │   │   ├── simulation.py  # POST/GET /simulation, POST /simulation/{id}/signal
│   │   │   ├── movies.py      # GET /movies/search
│   │   │   ├── narration.py   # GET /simulation/{id}/narration/stream (SSE)
│   │   │   └── challenge.py   # POST /challenge, POST /challenge/{id}/submit
│   │   └── services/
│   │       ├── algorithms/
│   │       │   ├── base.py          # RecommenderResult model + Recommender Protocol
│   │       │   ├── popularity.py    # Bayesian average, cached rankings
│   │       │   ├── content_based.py # Genre vector cosine similarity
│   │       │   ├── collaborative.py # scikit-surprise SVD (10 epochs), demographic neighbors
│   │       │   └── hybrid.py        # Adaptive weighted ensemble of all three
│   │       ├── narration/
│   │       │   ├── templates.py           # Priority-ordered rule engine for template selection
│   │       │   ├── llm_narrator.py        # Claude API streaming fallback narration
│   │       │   └── challenge_narrator.py  # Claude API non-streaming challenge narration
│   │       ├── metrics.py           # precision@k, recall@k, NDCG@k
│   │       ├── ground_truth.py      # Random eligible user + relevant set extraction
│   │       ├── simulation_engine.py # Orchestrator: apply signal → run algos → narration → metrics
│   │       ├── challenge_engine.py  # Challenge scoring: user selection, seed ratings, algo comparison
│   │       ├── session_manager.py   # Thread-safe UUID → SimulationState store, TTL eviction
│   │       └── validators.py        # Signal payload validation against dataset
│   └── tests/
│       └── conftest.py   # Disables rate limiting for tests via env var
├── frontend/         # React 19, TypeScript, Vite, Chakra UI v3
│   └── src/
│       ├── api/
│       │   └── client.ts       # Typed fetch wrapper with ApiError class
│       ├── components/
│       │   ├── Navbar.tsx            # Café-branded nav with ☕ icon and active link state
│       │   ├── SignalPanel.tsx       # Four accordion sections for signal input
│       │   ├── MovieSearchModal.tsx  # Debounced search, dual-mode (rating/viewHistory)
│       │   ├── MetricsChart.tsx      # Recharts line chart (4 algos × 3 metrics) + srOnly data table
│       │   ├── AlgorithmTimeline.tsx # Animated race bars with sparkle bursts, ARIA labels
│       │   ├── SignalFilmstrip.tsx   # Horizontal scrollable signal chips with spring animations
│       │   ├── NarratorPanel.tsx     # Speech-bubble cards, dual animation (typing/SSE)
│       │   ├── RecommendationCards.tsx # Tabbed top-10 movie recommendations
│       │   ├── MoviePicker.tsx       # Challenge movie browser with search, keyboard nav, ARIA
│       │   ├── ScoreComparison.tsx   # Recharts bar chart with animated bars + scores table
│       │   ├── ErrorBoundary.tsx     # Class component error boundary with café-themed recovery UI
│       │   ├── PageTransition.tsx    # Framer Motion fade+slide route wrapper
│       │   └── Toaster.tsx           # Chakra v3 toast renderer
│       ├── hooks/
│       │   ├── useSimulation.ts      # Single source of truth for simulation state + actions
│       │   ├── useChallenge.ts       # Challenge state machine: setup → picking → results
│       │   ├── useTypingAnimation.ts # Character-by-character text reveal hook
│       │   └── useNarrationStream.ts # SSE streaming hook for LLM narrations
│       ├── pages/
│       │   ├── LandingPage.tsx     # Hero section + café SVG + algorithm grid with colored dots
│       │   ├── SimulationDashboard.tsx  # Three-column layout (signals | viz | narration)
│       │   └── ChallengePage.tsx   # Three-phase challenge: setup → picking → results
│       ├── types/
│       │   ├── simulation.ts   # TS interfaces mirroring backend Pydantic models
│       │   ├── movies.ts       # MovieSearchResult, MovieSearchResponse
│       │   └── challenge.ts    # Challenge types: target user, scores, create/submit responses
│       ├── utils/
│       │   └── toaster.ts      # createToaster instance (separated for fast-refresh)
│       ├── theme/
│       │   └── index.ts        # Chakra v3 system: brand colors, algo colors, fonts (+ mono)
│       ├── index.css           # Linen texture, .cafe-card shadows, keyframes (pulse, blink)
│       ├── App.tsx             # Routes + Navbar + AnimatePresence + Toaster
│       └── main.tsx            # StrictMode + BrowserRouter + ChakraProvider + ErrorBoundary
├── data/             # Bundled MovieLens 100K Parquet files (committed)
├── scripts/          # Data preparation scripts
├── docker-compose.yml  # Production config: nginx frontend (port 80), backend, health checks
└── .github/workflows/ci.yml  # CI: backend lint/test, frontend lint/typecheck/build, Docker builds
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
docker compose up --build   # production: nginx on :80, backend on :8000
docker compose down          # tear down
docker compose ps            # verify health status
```

## API

- Base path: `/api/v1`
- Health check: `GET /api/v1/health`
- `POST /api/v1/simulation` → 201, creates session, selects ground-truth user, returns step 0
- `POST /api/v1/simulation/{session_id}/signal` → 200, adds signal (rating/demographic/genre_preference/view_history), re-runs algorithms
- `GET /api/v1/simulation/{session_id}` → 200, returns full state with all steps + current signal summary
- `GET /api/v1/movies/search?q={query}&limit={limit}` → 200, title substring search (default limit=10, max=50)
- `GET /api/v1/simulation/{session_id}/narration/stream?step={step_number}` → SSE stream (template: one `chunk` event + `done`; LLM: streamed `chunk` events + `done`)
- `POST /api/v1/challenge` → 201, selects ground-truth user (≥30 ratings), returns demographics, 3 seed ratings, 50 browseable movies
- `POST /api/v1/challenge/{session_id}/submit` → 200, scores user's 10 picks against ground truth, returns user scores, algorithm scores, LLM narration, ground-truth favorites
- Errors: 400 (invalid payload — bad movie ID, score out of range, unknown genre, duplicate picks), 404 (session not found), 422 (Pydantic validation — wrong type, missing field, pick count ≠ 10), 429 (rate limit exceeded — includes `Retry-After` header)
- Rate limits: `POST /simulation` 10/min/IP, `POST /challenge` 5/min/IP, `POST .../signal` 30/min/session

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

### Challenge Mode

Challenge mode is a one-shot evaluation: the user studies a target user profile, picks 10 movies, and gets scored against four algorithms. Unlike simulation's progressive state machine (N signals → N+1 steps), challenge has a simple two-step lifecycle: create → submit.

**Key design decisions:**
- **Algorithm reuse via structural compatibility:** `challenge_engine.py` constructs a minimal `SimulationState(ratings=seed_ratings, demographics=demographics)` and passes it to the same algorithm functions used by simulation — no new interfaces needed
- **Pre-computed algorithm scores:** Algorithms run at creation time (scores stored server-side); submit endpoint only scores user picks — reducing submit latency
- **Module-level dict stores:** Three plain dicts (`_challenge_store`, `_challenge_ground_truth`, `_challenge_algo_scores`) instead of SessionManager — challenges don't need progressive state management
- **Non-streaming narration:** `client.messages.create()` returns complete text (vs. simulation's `.stream()` → SSE) because challenge results are a one-shot reveal
- **Layered validation:** Pydantic `Field(min_length=10, max_length=10)` for pick count (→422), explicit code for duplicates/movie existence (→400)
- **User selection threshold:** ≥30 ratings (vs. simulation's ≥20) to ensure enough high-rated movies for a meaningful relevant set

### Narration System (Two-Tier Architecture + Challenge Narrator)

```
Template matcher (instant)          LLM fallback (streaming)
templates.py                        llm_narrator.py
├── 13 café-themed templates        ├── Claude API (claude-sonnet-4-20250514)
├── Priority-ordered rules          ├── Async streaming via messages.stream()
├── One-time deduplication          ├── Context: state + results + prev narrations
└── Returns str | None              └── Yields text chunks → SSE → frontend
         │                                     │
         ▼                                     ▼
    narration_source="template"           narration_source="llm"
         │                                     │
         └──────── SimulationStep ─────────────┘
                        │
                   narration.py (SSE router)
                   ├── event: chunk → text fragment
                   ├── event: done  → stream complete
                   └── event: error → error message
```

- **Template path:** `match_template(state, step)` → returns full narration or `None`
- **LLM path:** `generate_narration(state, step, prev_narrations)` → async generator of text chunks
- **Challenge path:** `generate_challenge_narration(demographics, seed_ratings, user_picks, user_score, algo_scores, data)` → complete string (non-streaming)
- **Graceful degradation:** Template → LLM streaming → static fallback (no API key / API error); challenge uses `_fallback_narration()` with win-count branching (4 contextual variants)
- **Temp-step pattern:** `run_step()` builds a temporary `SimulationStep` with empty narration so the template matcher can inspect algorithm results before constructing the final step
- **Cross-router state sharing:** `get_ground_truth_store()` exposes the ground-truth dict from the simulation router; injected into narration router during `init_narration_router()` at startup

### Key Dependencies

- `numpy>=1.26.0,<2.0.0` — pinned because scikit-surprise 1.1.4's Cython extensions are compiled against NumPy 1.x ABI
- `scikit-surprise` — collaborative filtering SVD (requires Python <3.13)
- `scikit-learn` — cosine similarity for content-based filtering
- `sse-starlette` — Server-Sent Events support for FastAPI (narration streaming)
- `anthropic` — Claude API client for LLM narration fallback

### Session Management & Rate Limiting

- **Session TTL eviction:** Background `asyncio` task runs every 60 seconds, evicts sessions older than `SIMULATION_TTL_SECONDS` (default: 1 hour). Evicts both simulation sessions (`SessionManager.evict_expired()`) and challenge sessions (`evict_expired_challenges()`). Task started via `asyncio.create_task()` in lifespan, cancelled cleanly on shutdown.
- **Rate limiting:** `RateLimitMiddleware` (Starlette `BaseHTTPMiddleware`) uses sliding window counter — `dict[str, list[float]]` keyed by IP or session, prunes expired timestamps on each check. Only applies to POST requests. Returns 429 with `Retry-After` header. Disabled via `RATE_LIMIT_ENABLED=false` in tests (set in `conftest.py` before app imports).
- **Max concurrent sessions:** `SessionManager` enforces `MAX_CONCURRENT_SESSIONS` (default: 100), raising `RuntimeError` → 400 when exceeded.

### Data Flow

1. `DataStore` loads Parquet files at startup → stored on `app.state.data`
2. `SessionManager` created at startup → injected into simulation router via `init_simulation_router()`
3. Background cleanup task started → runs every 60s, evicts expired simulation and challenge sessions
4. `POST /simulation` → rate limiter checks IP → `ground_truth.py` selects random eligible user → stored in server-side `_ground_truth_store` (never serialized to client)
5. `POST /simulation/{id}/signal` → rate limiter checks session → `validators.py` checks payload → `simulation_engine.apply_signal()` mutates state → `simulation_engine.run_step()` runs all 4 algorithms → `metrics.py` computes precision@k, recall@k, NDCG@k → template matcher selects narration (or marks for LLM) → returns `SimulationStep`
6. `GET /simulation/{id}/narration/stream?step=N` → SSE endpoint streams narration: template narrations yield one chunk; LLM narrations stream tokens from Claude API, then update the step's narration text on completion

### Backend Layers

```
Middleware (Cross-cutting)   → Router (HTTP)              → Engine (Orchestration)              → Storage (State)
middleware/rate_limit.py       routers/simulation.py        services/simulation_engine.py         services/session_manager.py
                               routers/movies.py            services/validators.py
                               routers/narration.py (SSE)   services/narration/templates.py
                               routers/challenge.py         services/narration/llm_narrator.py
                                                            services/narration/challenge_narrator.py
                                                            services/challenge_engine.py          module-level dicts in challenge.py
```

- **Middleware** handles cross-cutting concerns: rate limiting (sliding window), registered after CORS (so OPTIONS preflight isn't limited)
- **Routers** handle HTTP concerns: parse requests, map exceptions to status codes (ValueError→400, missing session→404)
- **Engine** handles business logic: apply signals, run algorithms, compute metrics, resolve movie metadata
- **Storage** handles state: thread-safe `dict[UUID, SimulationState]` with `threading.Lock`, TTL eviction via background task
- Ground truth stored separately from `SimulationState` to prevent data leakage through Pydantic serialization
- Global `@app.exception_handler(ValueError)` converts any `ValueError` to 400 JSON response

### Frontend Architecture

```
ErrorBoundary (class component, catches render errors → café-themed recovery UI)
└── App.tsx (Routes + Navbar + AnimatePresence + Toaster)
    ├── LandingPage              → Café SVG + hero + algorithm grid with colored dots + dual CTA
    ├── SimulationDashboard      → Three-column layout, owns useSimulation hook
    │   ├── SignalPanel          → Four accordion sections (rating, demographics, genres, view history)
    │   │   └── MovieSearchModal → Debounced search, dual-mode (rating stars / viewHistory checkboxes)
    │   ├── Center panel (visualization)
    │   │   ├── AlgorithmTimeline   → Race bars with spring animations, sparkle ✨ on big jumps
    │   │   ├── SignalFilmstrip     → Scrollable chips with spring entrance (stiffness:300, damping:20)
    │   │   ├── MetricsChart        → Recharts line chart + hidden srOnly data table for a11y
    │   │   └── RecommendationCards → Tabbed top-10 recommendations per algorithm
    │   └── NarratorPanel        → Speech-bubble cards with dual animation support
    │       ├── useTypingAnimation  → Template narrations: local character-by-character reveal
    │       └── useNarrationStream  → LLM narrations: SSE streaming from Claude API
    └── ChallengePage            → Three-phase state machine, owns useChallenge hook
        ├── SetupPhase            → Target user card (demographics + 3 seed ratings) + Start button
        ├── MoviePicker           → 2-column grid with search, keyboard nav, ARIA roles
        └── ResultsPhase          → ScoreComparison + narration + GroundTruthReveal + Try Again
            ├── ScoreComparison   → Recharts bar chart with animated bars + scores table
            └── GroundTruthReveal → User's actual top-rated movies grid
```

- **`useSimulation` / `useChallenge` hooks** are the single source of truth — components receive data and callbacks via props, never call `api/client.ts` directly
- **Exception:** `MovieSearchModal` and `MoviePicker` call `searchMovies()` directly since search results are ephemeral (not simulation/challenge state)
- **Auto-create on mount:** `useEffect` + `useRef` guard prevents duplicate sessions in StrictMode
- **Error handling:** `ErrorBoundary` (class component) at app root catches render crashes → café-themed recovery UI; API errors → `toaster.create()` toast notifications
- **Loading states:** Skeleton matching timeline + chart shape during initial load
- **Empty state:** "The kitchen is empty" at step 0 with arrow pointing to signal panel
- **Session expired state:** "Your table's been cleared!" with error detail and recovery CTA
- **Page transitions:** `PageTransition` wrapper with Framer Motion `AnimatePresence` (fade + slide on route changes)
- **Dual narration animation:** Both `useTypingAnimation` and `useNarrationStream` always called (React Rules of Hooks), with `skip`/`enabled` flags controlling which is active — template narrations use local typing effect, LLM narrations stream via SSE
- **Accessibility:** ARIA labels on chart containers (`role="img"`), hidden `srOnly` data tables for screen readers, `role="button"` + `tabIndex` + `onKeyDown` (Enter/Space) on interactive `<Box>` elements, `aria-pressed` for toggle/selection state

### Chakra UI v3 Patterns

- **Composable API:** `Dialog.Root`/`.Content`/`.Header` (not v2's `Modal`/`ModalContent`/`ModalHeader`)
- **Disabled propagation:** behavioral props (`disabled`, `readOnly`) go on `.Root`, not on `.Field`
- **Toast architecture:** `createToaster()` in `utils/toaster.ts` (imperative store), `<Toaster>` in `components/Toaster.tsx` (declarative renderer) — separated for ESLint `react-refresh/only-export-components`
- **Theme tokens:** `{ value: "#hex" }` syntax, `brand.*` for visual identity, `algo.*` for algorithm-specific colors
- **Fonts:** Playfair Display (headings) + Inter (body) + Fira Code (mono/metrics) via Google Fonts `<link>` in `index.html`, referenced in theme `fonts` tokens (`heading`, `body`, `mono`)
- **Café visual polish:** `.cafe-card` CSS class for warm terracotta-tinted shadows (`rgba(200, 85, 61, 0.08)`), inline SVG `feTurbulence` noise for linen texture background, algorithm colored dots (8px circles) for consistent color coding

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
- `asyncio.create_task()` in lifespan for recurring background tasks (session cleanup); cancelled on shutdown via `task.cancel()` + `await`
- `ValueError` for semantic validation errors (→400); Pydantic `ValidationError` for structural issues (→422)
- pytest with `asyncio_mode = "auto"`
- Use `module`-scoped fixtures for expensive resources (DataStore, fixture datasets)
- `TestClient(app)` must be used as context manager (`with TestClient(app) as c`) to trigger lifespan
- Unit tests use small fixture datasets (`tmp_path_factory`); integration tests use real MovieLens data
- `tests/conftest.py` sets `RATE_LIMIT_ENABLED=false` via `os.environ` before app imports — prevents rate limiter from blocking rapid test requests

### Frontend (TypeScript/React)
- ESLint + Prettier
- Chakra UI v3 for components and theming (composable `.Root`/`.Content` API, not v2)
- `useCallback` on all hook actions to stabilize function references for child components
- Debounced search via `useEffect` + `setTimeout` cleanup (no external library)
- `import type` for all type-only imports (enforced by `verbatimModuleSyntax`)
- Recharts for data visualization (line charts, bar charts with `Cell` for per-bar colors, tooltips, responsive containers)
- Framer Motion for animations — spring physics (`type: "spring"`, stiffness/damping/mass) for organic entrance; keyframe arrays for burst effects (sparkle ✨); `AnimatePresence` for exit animations
- React Router v7 for navigation (`BrowserRouter` wrapping app in `main.tsx`)
- `useRef` + `hasStartedRef` pattern to prevent duplicate EventSource connections in StrictMode
- `null`-as-sentinel pattern: `useState<string | null>(null)` — `null` = not started, `""` = started, no data yet

## Environment

- Copy `.env.example` to `.env` at the project root
- `ANTHROPIC_API_KEY` — required for AI-powered narration (falls back to templates without it)
- `DATA_DIR` — path to Parquet data files (default: `data`)
- `CORS_ORIGINS` — allowed origins (default: `["http://localhost:5173"]`)
- `SIMULATION_TTL_SECONDS` — session expiry time (default: `3600` / 1 hour)
- `MAX_CONCURRENT_SESSIONS` — max simultaneous sessions (default: `100`)
- `RATE_LIMIT_ENABLED` — enable/disable rate limiting (default: `true`, set to `false` in tests)

## CI

GitHub Actions runs on push/PR to `main` (3 jobs):
- **Backend:** ruff check, ruff format --check, pytest (146 tests)
- **Frontend:** eslint, tsc type-check, vite build
- **Docker:** builds both images (`needs: [backend, frontend]` — skips if code quality fails)

## Tests

146 backend tests across 9 test files:

| File | Count | Scope |
|---|---|---|
| `test_health.py` | 1 | Health endpoint smoke test |
| `test_data_loader.py` | 14 | DataStore loading, lookups, search, ground-truth eligibility |
| `test_metrics.py` | 19 | precision@k, recall@k, NDCG@k with hand-computed values |
| `test_algorithms.py` | 21 | Algorithm behavior contracts using 20-movie fixture dataset |
| `test_algorithm_pipeline.py` | 16 | Full pipeline on real MovieLens 100K (~10s, SVD-dominated) |
| `test_simulation_api.py` | 29 | Simulation endpoints: create, add signals (all 4 types), get state, error handling |
| `test_movies_api.py` | 9 | Movie search: queries, limits, case-insensitivity, edge cases |
| `test_narration.py` | 19 | Template loading, template matcher (step 0, ratings 1-5, signal types, dedup, hybrid leads), LLM fallback, narration_source field |
| `test_challenge_api.py` | 18 | Challenge create/submit flow, user scores, algorithm scores, narration, ground-truth reveal, error handling (pick count, duplicates, invalid movie/session) |

```bash
cd backend
uv run pytest -v                                 # all 146 tests
uv run pytest tests/test_algorithms.py -v         # fast algorithm unit tests only
uv run pytest tests/test_algorithm_pipeline.py -v # slow integration tests
uv run pytest tests/test_simulation_api.py tests/test_movies_api.py -v  # API integration tests
uv run pytest tests/test_narration.py -v          # narration system tests
uv run pytest tests/test_challenge_api.py -v      # challenge mode tests
```

Frontend checks (no test suite yet — manual testing via browser):

```bash
cd frontend
npm run type-check   # tsc --noEmit — strict TypeScript verification
npm run lint         # eslint — 0 errors, 0 warnings
npm run build        # production build — verifies full compilation
```

## Docker Production Architecture

Multi-stage builds minimize image size and improve security:

- **Backend:** `python:3.12-slim` → builder installs deps via uv → production stage copies `.venv` + app code, runs as non-root `appuser`, 2 uvicorn workers. Health check uses `python -c "urllib.request.urlopen(...)"` (no curl in slim image).
- **Frontend:** `node:20-slim` → builder runs `npm ci && npm run build` → production stage copies `dist/` into `nginx:alpine` (~25MB). Nginx serves SPA with `try_files $uri $uri/ /index.html`, proxies `/api/` to backend with SSE support (`proxy_buffering off`), caches hashed `/assets/` for 1 year.
- **Compose:** Restart policies (`unless-stopped`), memory limits (backend: 1GB, frontend: 128MB), health checks with `start_period` for initialization grace.
- **`.dockerignore`** files exclude `node_modules`, `.venv`, `tests`, `__pycache__` from build context.

### Performance

- SVD collaborative filtering: 10 epochs (tuned down from 20 for 37% latency improvement)
- Average step latency: ~616ms (well under 2s target)
- Popularity rankings + content-based genre matrix cached at module level
- Bundle size: ~1.1MB (single chunk; Recharts dominates)
