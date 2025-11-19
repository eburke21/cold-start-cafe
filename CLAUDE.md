# ColdStart Cafe

Interactive web app exploring the cold-start problem in recommendation systems. Four algorithms compete with zero data, then progressively recover as users add signals.

## Project Structure

```
cold-start-cafe/
├── backend/          # FastAPI (Python 3.12, uv)
│   ├── app/
│   │   ├── config.py       # pydantic-settings (reads .env)
│   │   ├── main.py         # FastAPI app, CORS, lifespan
│   │   ├── data/            # Parquet data loading
│   │   ├── models/          # Pydantic models (enums, simulation, challenge, movies)
│   │   ├── routers/         # API route handlers
│   │   └── services/        # Business logic & algorithm implementations
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

## Code Style

### Backend (Python)
- Ruff enforces style: line-length 100, target py312
- Rule sets: E, F, I, N, W, UP
- Use `pydantic.BaseModel` for all request/response schemas
- Async endpoints by default
- pytest with `asyncio_mode = "auto"`

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
