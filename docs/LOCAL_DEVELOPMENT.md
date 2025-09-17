# Local Development Guide

## Prerequisites
- Node.js 20+ and pnpm
- Python 3.11+ and uv (preferred)
- Docker and Docker Compose

Install uv if needed:
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
# or via pipx
pipx install uv
```

## Services and Ports (local)
- Frontend: http://localhost:3000
- Backend (FastAPI): http://localhost:8082
- Document Processor (FastAPI): http://localhost:8081
- Firecrawl API: http://localhost:3002 (docker)
- Postgres: localhost:5432 (docker)
- Redis: localhost:6380 (docker, mapped to container 6379)
- QDrant HTTP API: http://localhost:6336 (docker)

## 1) Start local infrastructure
From repo root:
```bash
docker compose up -d
```

## 2) Create env files
Copy examples to local env files:
```bash
cp apps/backend/.env.example apps/backend/.env.local
cp apps/document-processor/.env.example apps/document-processor/.env.local
cp apps/frontend/.env.example apps/frontend/.env.local
```

Fill/verify values:
- apps/backend/.env.local
```bash
APP_ENV=local
HOST=0.0.0.0
PORT=8082
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/akamvp
REDIS_URL=redis://localhost:6380/0
QDRANT_URL=http://localhost:6336
QDRANT_API_KEY=
# Optional (for future auth integration):
# FRONTEGG_APP_URL=http://localhost:3000
# FRONTEGG_BASE_URL=<your_frontegg_base_url>
# FRONTEGG_CLIENT_ID=<your_client_id>
# FRONTEGG_APP_ID=<your_app_id>
# FRONTEGG_ENCRYPTION_PASSWORD=<64_char_hex>
# FRONTEGG_COOKIE_NAME=fe_session
# FRONTEGG_HOSTED_LOGIN=true
```

- apps/document-processor/.env.local
```bash
APP_ENV=local
HOST=0.0.0.0
PORT=8081
QDRANT_URL=http://localhost:6336
FIRECRAWL_API_URL=http://localhost:3002
# OPENAI_API_KEY=your_openai_key_here (required for embeddings)
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

- apps/frontend/.env.local
```bash
NEXT_PUBLIC_API_URL=http://localhost:8082
# Frontegg (fill when enabling auth)
# FRONTEGG_APP_URL=http://localhost:3000
# FRONTEGG_BASE_URL=<your_frontegg_base_url>
# FRONTEGG_CLIENT_ID=<your_client_id>
# FRONTEGG_APP_ID=<your_app_id>
# FRONTEGG_ENCRYPTION_PASSWORD=<64_char_hex>
# FRONTEGG_COOKIE_NAME=fe_session
# FRONTEGG_HOSTED_LOGIN=true
```

## 3) Install dependencies
- Node (from repo root):
```bash
pnpm install
```

- Python (backend):
```bash
cd apps/backend
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

- Python (document-processor):
```bash
cd apps/document-processor
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

Note: If `uv` isn’t installed, you can fallback to:
```bash
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
```

## 4) Run the apps
Use separate terminals:

- Backend:
```bash
cd apps/backend
source .venv/bin/activate
uvicorn src.main:app --host "$HOST" --port "$PORT"
```

- Document Processor:
```bash
cd apps/document-processor
source .venv/bin/activate
uvicorn src.main:app --host "$HOST" --port "$PORT"
```

- Frontend:
```bash
cd apps/frontend
pnpm dev
```

## 5) Smoke tests
- Backend health:
```bash
curl -s http://localhost:8082/health
```
- Document processor health:
```bash
curl -s http://localhost:8081/health
```
- Firecrawl health:
```bash
curl -s http://localhost:3002/test
```
- QDrant status:
```bash
curl -s http://localhost:6336/collections
```
- Test Firecrawl integration:
```bash
curl -X POST http://localhost:8081/test-firecrawl
```
- Open http://localhost:3000 in a browser

## 6) Testing Website Scraping and Qdrant Ingestion

Once all services are running, you can test the complete pipeline:

### Test scraping a website:
```bash
curl -X POST http://localhost:8081/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "collection_name": "test_collection",
    "metadata": {"source": "test"}
  }'
```

### Check collections in Qdrant:
```bash
curl -s http://localhost:8081/collections
```

### Get collection info:
```bash
curl -s http://localhost:8081/collections/test_collection/info
```

**Note**: You'll need an OpenAI API key in your `.env.local` file for the embedding generation to work. Without it, the scraping will fail at the embedding step.

## Troubleshooting
- Port conflicts: change `PORT` in `.env.local` for the conflicting service and update `NEXT_PUBLIC_API_URL` if backend port changes.
- Redis uses host port 6380; ensure your `.env.local` uses `redis://localhost:6380/0`.
- QDrant uses 6336 (HTTP) locally; set `QDRANT_URL=http://localhost:6336`.
- Restart infra:
```bash
docker compose down && docker compose up -d
```
- Check container status and logs:
```bash
docker compose ps
docker compose logs -f postgres redis qdrant
```
