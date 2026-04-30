# Smart Travel Planner

An AI-powered travel planning agent that matches travelers to destinations using agents, tools, RAG, and ML classification.

---

## What It Does

A user sends a natural language request like:

> *"I have two weeks off in July and around $1,500. I want somewhere warm, not too touristy, and I like hiking. Where should I go, when should I book, and what should I expect?"*

The system answers them with a real, actionable trip plan — delivered in the chat interface and sent to their email via webhook.

---

## Architecture

```
React Frontend (Vite)
        ↓
FastAPI Backend (async, dependency injection, lifespan singletons)
        ↓
LangChain Agent (cheap model for tool extraction, strong model for synthesis)
    ├── RAG Tool → pgvector similarity search → Postgres
    ├── Classifier Tool → GradientBoosting ML model (joblib)
    └── Live Conditions Tool → wttr.in weather API (TTL cached)
        ↓
Postgres + pgvector (users, agent_runs, tool_call_logs, documents)
        ↓
Webhook → n8n → Gmail (trip plan delivered to user email)
```

---

## Stack

- **Backend:** FastAPI, SQLAlchemy 2.x async, asyncpg
- **Agent:** LangChain, Groq (llama-3.1-8b-instant + llama-3.3-70b-versatile)
- **ML:** scikit-learn GradientBoosting, joblib
- **RAG:** sentence-transformers (all-MiniLM-L6-v2), pgvector
- **Database:** Postgres 16 + pgvector
- **Auth:** JWT (python-jose), bcrypt
- **Webhook:** n8n + Gmail
- **Frontend:** React + Vite
- **Docker:** Postgres in Docker, backend runs locally
- **Tracing:** LangSmith

---

## Project Structure

```
smart-travel-planner/
├── backend/
│   ├── app/
│   │   ├── agent/          # LangChain agent + tool loop
│   │   ├── auth/           # JWT, bcrypt, dependencies
│   │   ├── ml/             # travel_classifier.joblib
│   │   ├── models/         # SQLAlchemy database models
│   │   ├── rag/            # ingest.py, retriever.py, dataset
│   │   ├── routes/         # auth.py, agent.py
│   │   ├── services/       # webhook.py
│   │   ├── tools/          # rag_tool, classifier_tool, live_conditions_tool
│   │   ├── config.py       # pydantic-settings Settings class
│   │   ├── db.py           # async engine + session factory
│   │   ├── main.py         # FastAPI app + lifespan
│   │   └── state.py        # singleton ml_model + embedder
│   ├── tests/
│   │   ├── test_agent.py
│   │   ├── test_schemas.py
│   │   └── test_tools.py
│   ├── ml_experiments/
│   │   ├── destinations_v2.csv
│   │   └── results.csv
│   ├── .env.example
│   └── pyproject.toml
├── frontend/               # Vite + React
├── docker-compose.yml
└── README.md
```

---

## ML Classifier

### Dataset

200 destinations labeled across 6 travel styles: Adventure, Relaxation, Culture, Budget, Luxury, Family.

**Labeling rules:**
- **Adventure** — hiking_score ≥ 4, low tourist density, varied cost
- **Relaxation** — beach_score ≥ 4, warm temperature, low museums
- **Culture** — museums_count high, UNESCO sites present, mid-range cost
- **Budget** — avg_cost_per_day < 60, avg_meal_cost < 8
- **Luxury** — avg_cost_per_day > 280, high safety score, low density
- **Family** — family_friendly_score = 5, high safety score

### Features

| Feature | Justification |
|---------|--------------|
| avg_cost_per_day_usd | Separates Budget from Luxury |
| avg_temp_july_celsius | Identifies warm/cold destinations |
| hiking_score (1-5) | Identifies Adventure |
| beach_score (1-5) | Identifies Relaxation |
| museums_count | Separates Culture from Budget |
| unesco_sites | Further separates Culture |
| tourist_density (1-5) | Cross-cutting signal |
| family_friendly_score (1-5) | Identifies Family |
| safety_score (1-5) | Cross-cutting signal |
| avg_meal_cost_usd | Key separator for Culture vs Budget |

### Why avg_meal_cost replaced cultural_sites_count

Initial model (v1) used a vague `cultural_sites_count` (1-5 scale) which caused Culture/Budget confusion — both had similar scores. Replaced with `museums_count` (real numbers: Paris=130, Bangkok=15), `unesco_sites`, and `avg_meal_cost_usd`. Culture F1 improved from 0.50 to 0.91.

### Model Comparison

| Model | CV Accuracy | CV F1 Macro | Val Accuracy | Val F1 Macro |
|-------|------------|-------------|--------------|--------------|
| RandomForest (default) | 0.821 ± 0.04 | 0.805 ± 0.05 | 0.792 | 0.794 |
| LogisticRegression (default) | 0.834 ± 0.03 | 0.820 ± 0.04 | 0.750 | 0.749 |
| GradientBoosting (default) | 0.807 ± 0.05 | 0.792 ± 0.06 | 0.833 | 0.841 |
| RandomForest (tuned) | — | 0.750 | — | 0.750 |
| **GradientBoosting (tuned)** | — | **0.967** | — | **0.966** |

**Winner: GradientBoosting tuned**

Best params: `n_estimators=100, max_depth=None, min_samples_split=2`

### Final Test Results

```
Test Accuracy: 0.967
Test F1 Macro: 0.966

              precision  recall  f1-score  support
   Adventure      1.00    1.00      1.00        5
      Budget      1.00    1.00      1.00        5
     Culture      0.83    1.00      0.91        5
      Family      1.00    0.80      0.89        5
      Luxury      1.00    1.00      1.00        5
  Relaxation      1.00    1.00      1.00        5
```

### Class Imbalance

All 6 classes were balanced at ~33 examples each. Per-class metrics reported above — no averaging that hides weak classes. Culture (F1=0.91) and Family (F1=0.89) are the weakest due to feature overlap with neighboring classes.

### No Data Leakage

Preprocessing (StandardScaler) is inside the scikit-learn Pipeline. It fits only on training folds during cross-validation, never on validation or test data.

---

## RAG System

### Documents

75 chunks across 15 destinations from Wikivoyage-style travel guides + destination feature profiles.

**4 chunk types per destination:**
- Overview / See / Do / Eat
- Best time to visit
- Budget and typical costs
- Getting there / Duration / Best for

**Plus 1 feature chunk per destination** containing exact numerical features (hiking_score, cost, museums_count etc.) so the LLM can extract real values for the classifier instead of guessing.

### Chunking Strategy

- **Chunk size:** One topic per chunk (overview, timing, budget, logistics) — roughly 80-150 words each
- **Overlap:** None — each chunk is self-contained by topic
- **Why:** Travel queries are topic-specific. A user asking about budget doesn't need hiking trail information in the same chunk — splitting by topic gives cleaner retrieval

### Embedding Model

`all-MiniLM-L6-v2` from sentence-transformers — 384 dimensions. Chosen for speed, small size, and strong semantic similarity performance on short texts.

### Retrieval Strategy

pgvector cosine similarity search, top-4 chunks. Tested manually before integration:

| Query | Top Result | Score |
|-------|-----------|-------|
| "hiking mountains Canada July" | Banff | 0.454 |
| "budget travel Asia temples" | Bangkok | 0.441 |
| "luxury beach resort warm" | Maldives | 0.438 |
| "off-topic: capital of France" | 0 results | — |

### RAG Edge Cases

| Query Type | Result | Explanation |
|------------|--------|-------------|
| Off-topic ("capital of France?") | 0 results | Correct — no travel documents match |
| Vague ("I want to travel") | 0 results | Too generic for semantic match |
| Contradicting ("luxury but $50/day") | 0 results | No document matches contradiction |
| Empty query | Graceful error | Does not crash |
| Specific ("hiking Canada July") | Banff found | Semantic match works correctly |

---

## Agent

### Tool Allowlist

Only 3 tools are permitted: `rag_tool`, `classifier_tool`, `live_conditions_tool`. Any other tool name is rejected with a structured error — the agent never crashes.

### Two-Model Routing

| Step | Model | Why |
|------|-------|-----|
| Tool argument extraction | llama-3.1-8b-instant (cheap) | Mechanical work — no creativity needed |
| Final trip plan synthesis | llama-3.3-70b-versatile (strong) | Needs reasoning, nuance, synthesis |

### Per-Query Cost (one full run)

| Model | Tokens | Cost (est.) |
|-------|--------|-------------|
| llama-3.1-8b-instant | ~895 | ~$0.0001 |
| llama-3.3-70b-versatile | ~1498 | ~$0.0012 |
| **Total** | **~2393** | **~$0.0013** |

Groq free tier — effectively $0 at current usage.

### Tool Synthesis

The strong model is explicitly prompted to synthesize across tools — not concatenate. If RAG recommends a destination but weather shows bad conditions for the activity, the answer reflects that tension:

> *"Banff is excellent for hiking in July — trails are open and weather is mild at 12°C. However note that the classifier suggests a Culture travel style based on your feature profile, which may indicate Banff's town and museum offerings are also worth including in your itinerary."*

---

## Engineering Standards

### Async All the Way Down

All FastAPI routes, tool functions, database calls, and HTTP requests are async. No `time.sleep` or `requests.get` in any request path.

### Dependency Injection

LLM client, database session, and current user are all injected via FastAPI `Depends()`. No globals in route handlers.

### Singletons via Lifespan

The database engine, ML model, and sentence-transformers embedder are loaded once at startup via FastAPI's lifespan handler and stored in `state.py`. Loading the joblib model per request is explicitly avoided.

### TTL Cache

Weather responses are cached for 10 minutes per city using `cachetools.TTLCache`. Same city within 10 minutes returns instantly without hitting the API again.

### Pydantic at Every Boundary

Every tool input is a Pydantic model. Invalid LLM outputs are caught at the boundary and returned as structured errors — never raised as exceptions that crash the agent loop.

### Structured Logging

`structlog` used for webhook delivery logging. Every success and failure is logged with structured fields (`user`, `error`) — no print statements.

### Error Handling

All external calls (LLM, weather API, webhook) wrapped with `tenacity` retries (3 attempts, exponential backoff). Webhook failure is fully isolated from user response via `BackgroundTasks`.

---

## Tests

17 tests passing across 3 files.

```
tests/test_schemas.py   — 8 tests  — Pydantic validation (valid + invalid inputs)
tests/test_tools.py     — 11 tests — Tool isolation + RAG edge cases
tests/test_agent.py     — 3 tests  — Agent loop with mocked LLM
```

Run:
```bash
cd backend
uv run pytest tests/ -v
```

---

## Setup

### Requirements

- Python 3.12
- Node.js 18+
- Docker Desktop
- uv

### Environment Variables

Copy `.env.example` to `.env` and fill in:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/travelplanner
GROQ_API_KEY=your_groq_key
SECRET_KEY=your_secret_key
WEBHOOK_URL=http://localhost:5678/webhook/trip-plan
ML_MODEL_PATH=app/ml/travel_classifier.joblib
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_key
LANGCHAIN_PROJECT=smart-travel-planner
```

### Running the Project

```bash
# 1. Start Postgres
docker compose up db

# 2. Start backend
cd backend
uv run uvicorn app.main:app --reload

# 3. Ingest RAG documents (first time only)
uv run python -m app.rag.ingest

# 4. Start frontend
cd frontend
npm run dev

# 5. Start n8n (webhook)
docker run -it --name n8n -p 5678:5678 -v n8n_data:/home/node/.n8n n8nio/n8n
```

---

## Webhook Delivery

When the agent finishes, a webhook fires in the background delivering the trip plan to n8n. n8n sends it via Gmail to the user's email.

- Timeout: 30 seconds
- Retries: 3 attempts with exponential backoff (1s, 2s, 4s)
- Failure isolation: webhook failure never breaks the user-facing response
- Structured logging on every success and failure

---

## LangSmith Trace

Every agent run is traced end-to-end in LangSmith showing:
- Cheap model tool call decisions
- Each tool input and output
- Strong model synthesis
- Token usage per step

---

## Docker Note

The backend runs locally due to `sentence-transformers` pulling PyTorch + CUDA dependencies (~4GB). In production this would be managed via a pre-built Docker image with model weights cached. Postgres runs in Docker with a named volume (`pgdata`) so embeddings and user data survive container restarts.

---

## Defend Your Choices

**Why GradientBoosting over RandomForest?**
GradientBoosting had better validation F1 (0.841 vs 0.794) before tuning. After tuning both, GradientBoosting reached 0.967 test F1 vs 0.750 for RandomForest.

**Why chunk by topic instead of fixed size?**
Travel queries are topic-specific. A user asking about budget retrieves the budget chunk directly rather than getting a mixed chunk that includes hiking info. Topic-based chunking gives cleaner, more relevant retrieval.

**Why TTL cache on weather?**
Weather for the same city doesn't change in 10 minutes. Caching avoids paying the API latency and rate limits twice for the same data within a session.

**Why two models?**
Tool argument extraction is mechanical — it just needs to parse the user query and produce JSON. A cheap fast model does this perfectly. The final synthesis requires reasoning across conflicting tool outputs — that needs a stronger model. Cost per query drops from ~$0.005 to ~$0.0013.

**Why `state.py` for singletons?**
`main.py` must be at the top of the import tree — nothing imports from it. Putting shared state in `main.py` caused circular imports (`classifier_tool → main → classifier_tool`). `state.py` has zero imports, breaking the cycle cleanly.
