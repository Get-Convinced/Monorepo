# Phase 1 – Foundation Setup

## Scope
Set up the monorepo skeleton, scaffold the three apps, add local infra (PostgreSQL, QDrant, Redis), and validate cross-service connectivity and basic auth.

## Assumptions (aligned with decisions)
- Package manager: pnpm
- Monorepo tool: Turborepo
- Node.js: 20.x LTS
- Python: 3.11
- Frontend: Next.js 14 App Router, TypeScript, ANT Design, Frontegg SDK
- Backend: FastAPI (Python)
- Document processor: FastAPI (Python)
- DB: PostgreSQL (local via Docker), ORM: SQLAlchemy
- Queue: Redis (RQ for Python workers initially)
- Vector DB: QDrant (local Docker for dev)
- CI: Skipped in Phase 1
- Env files: `.env.local` (local), `.env.dev` (dev server), `.env.prod` (production); maintain `.env.example` templates in each app

## Deliverables
- Monorepo initialized with base tooling and scripts
- Scaffolds for `apps/frontend`, `apps/backend`, `apps/document-processor`
- `packages/` for shared types, db, config
- Docker Compose for Postgres, QDrant, Redis
- `.env.example` files for each app; adopt `.env.local`, `.env.dev`, `.env.prod`
- Pre-commit hooks
- Local smoke test checklist documented

## Todo checklist
- [x] Decide monorepo tool and package manager (Decision: pnpm + Turborepo)
- [x] Confirm tech choices (FastAPI backend, SQLAlchemy, RQ, QDrant)
- [ ] Collect credentials and env vars (Frontegg, DB, QDrant, OpenAI/Anthropic)
- [x] Initialize monorepo workspace with root config and base tooling
- [x] Scaffold `apps/frontend` (Next.js 14, TS, ANT Design, Frontegg SDK)
- [x] Scaffold `apps/backend` (FastAPI + Python, SQLAlchemy)
- [x] Scaffold `apps/document-processor` (FastAPI, requirements, structure)
- [x] Create `packages/shared-types`, `packages/database`, `packages/config`
- [x] Add Docker Compose for Postgres, QDrant, Redis (local dev)
- [x] Add `.env.example` files for each app; support `.env.local`, `.env.dev`, `.env.prod`
- [x] Run local environment smoke tests across services

## Validation gates (Phase 1)
- 90% service availability locally
- Successful authentication roundtrip (Frontegg or fallback)
- Backend ↔ document-processor communication works
- DB and Qdrant connections verified

## Testing steps (local)
From repo root:
```bash
docker compose up -d
```
Create envs:
```bash
cp apps/backend/.env.example apps/backend/.env.local
cp apps/document-processor/.env.example apps/document-processor/.env.local
cp apps/frontend/.env.example apps/frontend/.env.local
```
Install deps:
```bash
pnpm install
cd apps/backend && uv venv && source .venv/bin/activate && uv pip install -r requirements.txt
cd ../../apps/document-processor && uv venv && source .venv/bin/activate && uv pip install -r requirements.txt
```
Run services (separate terminals):
```bash
# backend (PORT=8082)
cd apps/backend && source .venv/bin/activate && uvicorn src.main:app --host "$HOST" --port "$PORT"
# document-processor (PORT=8081)
cd apps/document-processor && source .venv/bin/activate && uvicorn src.main:app --host "$HOST" --port "$PORT"
# frontend (PORT=3000)
cd apps/frontend && pnpm dev
```
Smoke tests:
```bash
curl -s http://localhost:8082/health
curl -s http://localhost:8081/health
curl -s http://localhost:6336/collections
```
Open http://localhost:3000 in your browser.

## Open questions to unblock
1) Vector DB hosting: QDrant Cloud later; local Docker in Phase 1 – confirm
2) Auth: Frontegg credentials availability timeline; local fallback if delayed
3) Naming: Final Vercel project name for `frontend`
4) Secrets: Confirm using `.env.local` (local), `.env.dev` (dev), `.env.prod` (prod)

## Next steps (after decisions)
- Initialize monorepo (root configs, workspace, scripts)
- Scaffold apps and packages
- Add Docker Compose and env examples
- Validate local spin-up and smoke tests
