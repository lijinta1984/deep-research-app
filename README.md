# Deep Research Application

Production-grade deep research engine powered by **Kimi K2 (Moonshot)** + **Firecrawl**.

A multi-pass AI research system that automatically searches the web, scrapes content,
identifies knowledge gaps, and produces comprehensive research reports.

## Architecture

- **Frontend**: React 18 + TypeScript (strict) + Tailwind CSS + Shadcn/UI
- **Backend**: FastAPI (Python 3.11+), fully async
- **AI Model**: Moonshot Kimi K2 (`moonshot-v1-128k`) via OpenAI-compatible SDK
- **Scraping**: Firecrawl API (search + scrape)
- **Database**: PostgreSQL 15 (SQLAlchemy async + asyncpg)
- **Queue**: Redis 7 + Celery for async research jobs
- **Container**: Docker + docker-compose (5 services)

## Quick Start

### 1. Clone and configure

```bash
git clone <repo-url>
cd deep-research-app
cp .env.example .env
# Edit .env with your API keys
```

### 2. Start all services

```bash
make dev
```

This starts 5 services:
- **api** — FastAPI backend on port 8000
- **worker** — Celery worker for async research jobs
- **frontend** — React app on port 3000 (Nginx)
- **db** — PostgreSQL 15 on port 5432
- **redis** — Redis 7 on port 6379

### 3. Access the app

- Frontend: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Environment Variables

| Variable | Description |
|----------|-------------|
| `FIRECRAWL_API_KEY` | Firecrawl API key for web search/scraping |
| `MOONSHOT_API_KEY` | Moonshot API key for Kimi K2 LLM |
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |
| `MAX_CONCURRENT_JOBS` | Max parallel research jobs (default: 5) |

## Makefile Commands

```bash
make dev      # Start all services with docker-compose
make migrate  # Run Alembic migrations
make build    # Build production images
make logs     # Follow API + worker logs
make test     # Run pytest in API container
```

## Research Pipeline

The engine runs a 3-pass research pipeline:

1. **Pass 1 — Broad Search**: Generates 5-8 search queries, scrapes top results,
   synthesizes findings, and identifies knowledge gaps.
2. **Pass 2 — Gap Resolution**: Searches specifically for gap answers, updates
   the synthesis with new findings. (Runs if depth >= 2)
3. **Pass 3 — Final Synthesis**: Produces a publication-ready report with
   executive summary, sections, conclusions, and source citations.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/research/start` | Start a new research job |
| GET | `/api/research/status/{job_id}` | Poll job progress |
| GET | `/api/research/result/{job_id}` | Get full results |
| GET | `/api/research/history` | List recent jobs |
| DELETE | `/api/research/{job_id}` | Soft delete a job |
| POST | `/api/research/export/{job_id}` | Export as DOCX/Markdown |
| GET | `/api/research/tree/{job_id}` | Get search tree data |

## Project Structure

```
deep-research/
├── backend/
│   ├── api/
│   │   ├── routes.py            # FastAPI endpoints
│   │   └── dependencies.py      # Settings & config
│   ├── research/
│   │   ├── engine.py            # Core 3-pass research engine
│   │   ├── prompts.py           # Kimi K2 system prompts
│   │   └── schemas.py           # Pydantic V2 schemas
│   ├── db/
│   │   ├── models.py            # SQLAlchemy ORM models
│   │   └── session.py           # Async DB session
│   ├── tasks/
│   │   └── celery_tasks.py      # Celery task definitions
│   ├── export/
│   │   └── docx_builder.py      # DOCX report generation
│   ├── alembic/                 # Database migrations
│   ├── main.py                  # FastAPI app entry point
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/api.ts           # Typed API client
│   │   ├── components/ui/       # Shadcn/UI components
│   │   ├── pages/               # Home, Progress, Result, History
│   │   ├── types/research.ts    # TypeScript type mirrors
│   │   └── App.tsx
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
├── Makefile
├── .env.example
└── README.md
```
