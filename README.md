# ColdStart Cafe

An interactive web application that makes the cold-start problem in recommendation systems tangible and explorable. Watch four algorithms struggle with zero data, then progressively add signals and observe how each recovers in real-time.

## Quick Start

```bash
# Backend
cd backend
cp ../.env.example ../.env  # add your ANTHROPIC_API_KEY
uv sync
uv run uvicorn app.main:app --reload

# Frontend (in a separate terminal)
cd frontend
npm install
npm run dev
```

Or with Docker:

```bash
docker compose up --build
```

## Tech Stack

- **Backend:** Python 3.12, FastAPI, pandas, scikit-surprise, scikit-learn
- **Frontend:** React, TypeScript, Vite, Chakra UI v3, Recharts
- **Data:** MovieLens 100K (bundled as Parquet)
