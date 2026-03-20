# ☕ ColdStart Cafe

![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=flat&logo=typescript&logoColor=white)
![React](https://img.shields.io/badge/React-61DAFB?style=flat&logo=react&logoColor=black)
![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)

<img width="307" height="171" alt="image 3" src="https://github.com/user-attachments/assets/3c4a4c4f-c9fb-4eb2-b8cf-08a08df2ca07" />



**An interactive exploration of the cold-start problem in recommendation systems.**

Watch four recommendation algorithms compete in real time — starting from zero knowledge — as you feed them signals like movie ratings, demographics, genre preferences, and viewing history. Then challenge the algorithms directly: can *you* recommend movies better than the machines?

## What is the Cold-Start Problem?

Every recommendation system faces a bootstrapping dilemma: how do you recommend things to a new user when you know nothing about them? This is the **cold-start problem**. ColdStart Cafe lets you experience it firsthand by watching algorithms struggle with zero data — then progressively recover as you provide signals.

## Features

### Simulation Mode
- **Four competing algorithms** — Popularity, Content-Based, Collaborative Filtering (SVD), and Hybrid — each starting from zero
- **Progressive signal feeding** — add ratings, demographics, genre preferences, and viewing history one at a time
- **Real-time visualization** — animated race bars, line charts tracking precision/recall/NDCG, and signal filmstrip
- **AI narration** — a cafe-themed narrator explains what's happening at each step (Claude API or templated fallback)
- **Top-10 recommendations** — see what each algorithm would recommend at every step

### Challenge Mode
- **Human vs. Machine** — study a target user's profile (demographics + 3 seed ratings), then pick 10 movies you think they'd love
- **Score comparison** — your precision@10 compared against all four algorithms in a horizontal bar chart
- **The Barista's Verdict** — AI-generated narration of your challenge results
- **Ground-truth reveal** — see the movies the target user actually loved

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.12, FastAPI, Pydantic, scikit-surprise (SVD), scikit-learn |
| **Frontend** | React 19, TypeScript, Vite, Chakra UI v3, Recharts, Framer Motion |
| **AI Narration** | Anthropic Claude API (streaming for simulation, non-streaming for challenge) |
| **Data** | MovieLens 100K (bundled as Parquet files) |
| **Infrastructure** | Docker Compose, GitHub Actions CI |

## Architecture

```
                    React Frontend                          FastAPI Backend
              ┌───────────────────────┐           ┌──────────────────────────────┐
              │  LandingPage          │           │  /api/v1/simulation          │
              │  SimulationDashboard ─┼──────────►│  /api/v1/challenge           │
              │  ChallengePage        │           │  /api/v1/movies/search       │
              │                       │    SSE    │  /api/v1/.../narration/stream │
              │  Recharts + Framer    │◄──────────┤                              │
              │  Motion visuals       │           │  ┌────────────────────┐      │
              │                       │           │  │  4 Algorithms      │      │
              │  useSimulation /      │           │  │  Popularity        │      │
              │  useChallenge hooks   │           │  │  Content-Based     │      │
              │                       │           │  │  Collaborative SVD │      │
              │  NarratorPanel        │           │  │  Hybrid            │      │
              └───────────────────────┘           │  └────────────────────┘      │
                                                  │                              │
                                                  │  ┌────────────────────┐      │
                                                  │  │  Narration Engine  │      │
                                                  │  │  Templates + LLM   │      │
                                                  │  └────────────────────┘      │
                                                  │              │               │
                                                  └──────────────┼───────────────┘
                                                                 │
                                                       MovieLens 100K Parquet
```

## How the Algorithms Work

| Algorithm | Strategy | Cold-Start Behavior |
|-----------|----------|-------------------|
| **Popularity** | Bayesian-average ranking of all movies | Always returns top-10 — no personalization |
| **Content-Based** | Cosine similarity on genre vectors | Empty until first rating (needs taste signal) |
| **Collaborative** | scikit-surprise SVD with demographic neighbors | Empty until demographics or ratings available |
| **Hybrid** | Adaptive weighted ensemble of all three | Falls back to 100% popularity at zero signals |

## Getting Started

### Prerequisites
- Python 3.12 (not 3.13 — scikit-surprise requires it)
- Node.js 20+
- [uv](https://github.com/astral-sh/uv) (Python package manager)

### Local Development

```bash
# Clone the repo
git clone https://github.com/yourusername/cold-start-cafe.git
cd cold-start-cafe

# Set up environment
cp .env.example .env
# Optionally add your ANTHROPIC_API_KEY for AI narration

# Backend
cd backend
uv sync
uv run uvicorn app.main:app --reload   # http://localhost:8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev                             # http://localhost:5173
```

### Docker Compose

```bash
docker compose up --build
# Frontend: http://localhost:5173
# Backend:  http://localhost:8000
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | *(empty)* | Claude API key for AI narration (optional — falls back to templates) |
| `DATA_DIR` | `data` | Path to MovieLens Parquet files |
| `CORS_ORIGINS` | `["http://localhost:5173"]` | Allowed CORS origins |
| `SIMULATION_TTL_SECONDS` | `3600` | Session expiry time (1 hour) |
| `MAX_CONCURRENT_SESSIONS` | `100` | Max simultaneous sessions |
| `RATE_LIMIT_ENABLED` | `true` | Enable/disable rate limiting |

## Running Tests

```bash
# Backend (146 tests)
cd backend
uv run pytest -v

# Frontend (type checking + linting)
cd frontend
npm run type-check
npm run lint
```

## Credits

- **[MovieLens 100K](https://grouplens.org/datasets/movielens/100k/)** — University of Minnesota GroupLens Research
- **[scikit-surprise](https://surpriselib.com/)** — SVD implementation for collaborative filtering
- **[Anthropic Claude](https://anthropic.com)** — AI-powered narration
- **[Recharts](https://recharts.org/)** — React charting library
- **[Chakra UI v3](https://chakra-ui.com/)** — Component library
- **[Framer Motion](https://www.framer.com/motion/)** — Animation library

## License

MIT
