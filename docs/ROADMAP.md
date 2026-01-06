# LedgerMind - Development Roadmap

> The LLM is the product. Everything else is plumbing.

**Last Updated:** January 2026  
**Current Phase:** 1B Complete ✅

---

## Core Philosophy

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   USER ASKS QUESTION                                        │
│           │                                                 │
│           ▼                                                 │
│   ┌─────────────────────────────────────────────────────┐   │
│   │                    🧠 LLM                            │   │
│   │                                                      │   │
│   │   LLM decides EVERYTHING:                           │   │
│   │   • What type of question is this?                  │   │
│   │   • Where to find the answer?                       │   │
│   │   • How to respond?                                 │   │
│   │                                                      │   │
│   └─────────────────────────────────────────────────────┘   │
│           │                                                 │
│           ▼                                                 │
│   USER GETS ANSWER                                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘

API is just a delivery mechanism. Not the focus.
```

---

## Phase Overview

```
DONE ✅                DONE ✅                    NEXT
   │                      │                        │
   ▼                      ▼                        ▼
┌──────────┐       ┌──────────┐       ┌──────────┐       ┌──────────┐
│ Phase 1  │       │ Phase 1B │       │ Phase 2  │       │ Phase 3  │
│          │       │          │       │          │       │          │
│ LLM Core │──────▶│ API +    │──────▶│ Better   │──────▶│ Advanced │
│          │       │ Delivery │       │ LLM      │       │ Features │
│ DONE ✅  │       │ DONE ✅  │       │ NEXT     │       │ PLANNED  │
└──────────┘       └──────────┘       └──────────┘       └──────────┘
```

---

## Phase 1: LLM Foundation ✅ COMPLETE

**Goal:** Get the LLM brain working.

| Component | What | Status |
|-----------|------|--------|
| `llm/client.py` | Ollama connection | ✅ |
| `orchestration/workflow.py` | LLM routing logic | ✅ |
| `orchestration/router.py` | Intent classification | ✅ |
| `core/data_engine.py` | DuckDB for data | ✅ |
| `core/knowledge.py` | ChromaDB for rules | ✅ |
| `core/reference_data.py` | CSV lookups | ✅ |
| `core/customer.py` | Customer isolation | ✅ |
| `core/data_state.py` | Smart file detection | ✅ |
| 3 Agents | Discovery, Compliance, Strategist | ✅ |
| Tests | 166 passing | ✅ |

---

## Phase 1B: Delivery Layer ✅ COMPLETE

**Goal:** Wrap the LLM in an API so customers can use it.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  CUSTOMERS                           US (Internal)          │
│  ┌──────────────┐                   ┌──────────────┐       │
│  │ Their Apps   │                   │  Streamlit   │       │
│  │ Python/JS    │                   │  Admin UI    │       │
│  └──────┬───────┘                   └──────┬───────┘       │
│         │                                  │               │
│         ▼                                  ▼               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                  FASTAPI                             │   │
│  │                                                      │   │
│  │   POST /api/v1/upload  ─── Upload Excel/CSV         │   │
│  │   POST /api/v1/query   ─── Ask anything (LLM)       │   │
│  │                                                      │   │
│  └─────────────────────────────────────────────────────┘   │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    🧠 LLM                            │   │
│  │              (The actual product)                    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### What Was Built

| File | Purpose | Status |
|------|---------|--------|
| `api/app.py` | FastAPI application | ✅ |
| `api/auth.py` | API key authentication | ✅ |
| `api/models.py` | Request/Response schemas | ✅ |
| `api/routes/upload.py` | File upload endpoint | ✅ |
| `api/routes/query.py` | Single query endpoint | ✅ |
| `streamlit/app.py` | Streamlit UI (internal) | ✅ |
| `streamlit/api_keys.py` | API key management | ✅ |

### API Design (Minimal)

**Only 2 endpoints:**

```
POST /api/v1/upload
  - Upload Excel/CSV files
  - Returns: { tables_created: [...] }

POST /api/v1/query
  - Ask anything
  - LLM decides how to handle
  - Returns: { answer: "..." }
```

**Why so simple?**
- The LLM handles all routing internally
- No need for `/data/query` vs `/knowledge/query`
- One endpoint = simpler for customers

---

## Phase 2: Better LLM ◀── NEXT

**Goal:** Improve LLM accuracy, especially for SQL.

| Feature | Description | Priority |
|---------|-------------|----------|
| **SQL Model** | Use `sqlcoder` for data queries | P0 |
| **Query Templates** | Few-shot examples for common queries | P1 |
| **Error Recovery** | Auto-fix failed SQL queries | P1 |
| **Caching** | Cache frequent queries | P2 |

### SQL Accuracy Problem

Current: General LLM (qwen2.5) generates SQL
- Works ~70% of the time
- Fails on complex joins, date filtering

Phase 2: Specialized SQL model
- `sqlcoder` or `defog/sqlcoder-7b`
- Pre-trained on Text-to-SQL
- Expected: 90%+ accuracy

---

## Phase 3: Advanced Features

**Goal:** Add value beyond basic Q&A.

| Feature | Description |
|---------|-------------|
| **ITC Reconciliation** | Match with GSTR-2B |
| **43B(h) Alerts** | MSME payment warnings |
| **Cash Flow Forecast** | Predict upcoming needs |
| **Vendor Scoring** | Reliability rankings |
| **PDF Reports** | Export compliance reports |
| **Google Sheets Sync** | Auto-import data |

---

## Running The Project

### Start API (for customers)

```bash
# Start Ollama
ollama serve

# Start API
uvicorn api.app:app --port 8000

# Create API key
python -m admin.api_keys create company_name

# API ready at http://localhost:8000/docs
```

### Start Streamlit UI (for testing)

```bash
streamlit run streamlit/app.py
```

### Use the API

```bash
# Upload
curl -X POST -H "X-API-Key: YOUR_KEY" \
  -F "files=@sales.xlsx" \
  http://localhost:8000/api/v1/upload

# Query
curl -X POST -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is my total sales?"}' \
  http://localhost:8000/api/v1/query
```

---

## Key Decisions

### Why 2 Endpoints Only?

The LLM already routes queries internally via `IntentRouter`:
- Data question → DuckDB
- Knowledge question → ChromaDB
- Compliance → Agents

Exposing multiple endpoints just duplicates this logic. One endpoint = simpler API.

### Why No Customer UI?

We're API-only (like OpenAI, Stripe):
- Customers build their own UI
- Or integrate via code
- Less to maintain

Streamlit is internal for our testing.

### Why Local LLM?

- Customer data stays private
- No API costs
- Works offline
- Full control

---

## File Reference

```
api/
├── app.py           # FastAPI entry point
├── auth.py          # API key validation
├── models.py        # QueryRequest, QueryResponse
└── routes/
    ├── upload.py    # POST /upload
    └── query.py     # POST /query

streamlit/
├── app.py           # Streamlit UI
└── api_keys.py      # Key management CLI
```

---

**Remember: The LLM is the product. API is just plumbing.**
