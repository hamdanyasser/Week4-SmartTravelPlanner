# Deployment Guide

This guide is for deploying the current AtlasBrief travel planner app:

- Backend: FastAPI container
- Frontend: Vite/React static build
- Database: PostgreSQL with pgvector support

The recommended first deployment is split-hosting:

- Put the backend on a Docker-capable host.
- Put the frontend on a static frontend host.
- Use a managed PostgreSQL database that supports the `vector` extension.

This keeps the deployment easy to explain: the browser calls the FastAPI API,
and FastAPI handles auth, trip briefs, ML, RAG, persistence, and optional LLM or
webhook integrations.

## Required Environment Variables

Set these on the backend host:

```text
APP_ENV=production
APP_DEBUG=false
CORS_ALLOW_ORIGINS=https://your-frontend-domain.example
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:PORT/DB_NAME
JWT_SECRET_KEY=replace-with-a-random-production-secret
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_MINUTES=120
EMBEDDING_PROVIDER=deterministic
EMBEDDING_DIMENSION=384
DATABASE_INIT_ON_STARTUP=true
RAG_INGEST_ON_STARTUP=true
WEATHER_LIVE_ENABLED=false
WEBHOOK_ENABLED=false
```

Optional backend variables:

```text
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
STRONG_MODEL_PROVIDER=auto
CHEAP_MODEL_PROVIDER=auto
DISCORD_WEBHOOK_URL=
LANGCHAIN_API_KEY=
LANGCHAIN_PROJECT=atlasbrief
```

Set this on the frontend build host:

```text
VITE_API_BASE_URL=https://your-backend-domain.example
```

Important: Vite reads `VITE_API_BASE_URL` at build time. If the backend URL
changes after deployment, rebuild the frontend.

## Backend Container

The backend image must be built from the repository root because it packages
both `backend/` and `data/`.

```powershell
docker build -f backend/Dockerfile -t atlasbrief-backend .
```

Run locally for a production-style smoke test:

```powershell
docker run --rm --env-file backend/.env -p 8000:8000 atlasbrief-backend
```

Health check:

```powershell
Invoke-RestMethod http://localhost:8000/health
```

The backend Dockerfile uses `${PORT:-8000}`, so hosts that inject a `PORT`
environment variable can control the listening port without code changes.

## Backend on Vercel

The repository includes a root `index.py` entrypoint plus `vercel.json` Python
runtime routing. The entrypoint imports the same FastAPI app used by Docker:

```powershell
vercel --prod
```

Before deploying, set the backend environment variables in Vercel. At minimum:

```text
APP_ENV=production
APP_DEBUG=false
CORS_ALLOW_ORIGINS=https://your-frontend-domain.example
JWT_SECRET_KEY=replace-with-a-random-production-secret
DATABASE_INIT_ON_STARTUP=false
RAG_INGEST_ON_STARTUP=false
WEATHER_LIVE_ENABLED=false
WEBHOOK_ENABLED=false
```

Why `DATABASE_INIT_ON_STARTUP=false` for Vercel: the app can run in local
fallback mode without Postgres, and serverless startup should stay lightweight.
Use a Docker-capable backend host when you want persistent Postgres/pgvector RAG
in production.

## Frontend Static Build

For static hosts, build from `frontend/`:

```powershell
cd frontend
npm install --no-package-lock
$env:VITE_API_BASE_URL="https://your-backend-domain.example"
npm run build
```

Deploy the generated `frontend/dist/` directory.

## Frontend on Vercel

Deploy the frontend from the `frontend/` directory after the backend URL exists:

```powershell
cd frontend
vercel --prod
```

Set this Vercel environment variable before the production frontend build:

```text
VITE_API_BASE_URL=https://your-backend-domain.example
```

## Frontend Container

If the frontend host expects a Docker image, build the production target from
the repository root:

```powershell
docker build `
  -f frontend/Dockerfile `
  --target production `
  --build-arg VITE_API_BASE_URL=https://your-backend-domain.example `
  -t atlasbrief-frontend .
```

Run locally:

```powershell
docker run --rm -p 8080:8080 atlasbrief-frontend
```

Open:

```text
http://localhost:8080
```

## Local Docker Stack

The local compose stack still uses development servers and bind mounts:

```powershell
Copy-Item backend\.env.example backend\.env
docker compose up --build
```

Local URLs:

```text
Backend:  http://localhost:8000
Frontend: http://localhost:5173
```

## Go-Live Checklist

1. Backend `/health` returns `{"status":"ok"}`.
2. Frontend `VITE_API_BASE_URL` points to the deployed backend.
3. Backend `CORS_ALLOW_ORIGINS` includes the deployed frontend domain.
4. `JWT_SECRET_KEY` is a real random production secret.
5. `DATABASE_URL` points to a production database, not the local Docker host.
6. The database supports `CREATE EXTENSION IF NOT EXISTS vector`.
7. Optional keys are only enabled when you want live LLM, LangSmith, weather, or webhook behavior.

## Design Choice

The frontend can deploy as static files instead of a long-running Node server.
That is simpler and cheaper, but it means `VITE_API_BASE_URL` is fixed at build
time. The backend stays as a container because it owns Python dependencies,
ML/RAG startup, auth, database access, and optional integrations.
