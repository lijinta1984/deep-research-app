# Deep Research App
Autonomous deep research agent — powered by Firecrawl + Kimi K2 (Moonshot API)

## Prerequisites
- Python 3.11+
- Node.js 20+
- Firecrawl API key → https://firecrawl.dev
- Moonshot API key → https://platform.moonshot.cn
  Recommended model: moonshot-v1-128k

## Setup

### 1. Clone and configure environment
```bash
git clone <repo-url>
cd deep-research-app
cp .env.example .env
# Edit .env and fill in MOONSHOT_API_KEY and FIRECRAWL_API_KEY
```

### 2. Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```

### 3. Frontend (new terminal)
```bash
cd frontend
npm install
npm run dev
```

App runs at: http://localhost:5173
API runs at: http://localhost:8000
