# LedgerMind - Development Roadmap

> The LLM is the product. Everything else is plumbing.

**Last Updated:** February 2026  
**Current Phase:** Phase 2 Complete ✅

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
DONE ✅                DONE ✅               DONE ✅                 NEXT
   │                      │                     │                      │
   ▼                      ▼                     ▼                      ▼
┌──────────┐       ┌──────────┐       ┌──────────┐       ┌──────────┐
│ Phase 1  │       │ Phase 1B │       │ Phase 2  │       │ Phase 3  │
│          │       │          │       │          │       │          │
│ LLM Core │──────▶│ API +    │──────▶│ Better   │──────▶│ Advanced │
│          │       │ Delivery │       │ SQL      │       │ Features │
│ DONE ✅  │       │ DONE ✅  │       │ DONE ✅  │       │ PLANNED  │
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
| 4 Agents | Discovery, Compliance, Strategist, Recommendation | ✅ |
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

## Phase 2: Better SQL ✅ COMPLETE

**Goal:** Improve LLM accuracy for SQL generation.

| Feature | Description | Status |
|---------|-------------|--------|
| **Few-Shot Learning** | Examples for common SQL patterns | ✅ Implemented |
| **Smart Table Selection** | Detect table families, include all related | ✅ Implemented |
| **Data-Agnostic Loading** | Works with ANY data, not just financial | ✅ Implemented |
| **SQL Validation** | Auto-fallback if SQL model fails | ✅ Implemented |
| **Error Recovery** | Auto-fix failed SQL queries | ✅ Implemented |
| **Table Catalog** | Schema stored at ingestion time | ✅ Implemented |

### Few-Shot SQL Generation

The system now uses few-shot learning for SQL generation:

```python
# Few-shot examples teach the model patterns like:
# - UNION ALL for multiple related tables
# - GROUP BY with proper column selection
# - LIKE for text filtering
```

**Key improvements:**
1. When user asks "total of all purchases" → System finds ALL purchase_* tables
2. When tables are related (same prefix) → Automatically combines with UNION ALL
3. When SQL model (sqlcoder) produces invalid SQL → Falls back to qwen2.5

### Smart Table Selection

```python
# Table family detection:
# purchase_2021_07, purchase_2021_08, ... → family "purchase_"

# Query: "What is the total of all purchases?"
# Result: ALL tables in the "purchase_" family are queried
```

### Data-Agnostic Architecture

The data loading layer is now completely data-agnostic:
- No hardcoded column names (like "supplier_name", "total_amount")
- No assumed data types (like "sales", "purchases", "bank")
- LLM understands columns from names + sample data
- Works with ANY Excel/CSV data

**Files updated:**
- `core/table_catalog.py`: Generic metadata, no data-type assumptions
- `agents/discovery.py`: Data-agnostic file loading
- `core/schema.py`: Deprecated SDM mappings
- `core/mapper.py`: Deprecated header mapping
- `llm/client.py`: Few-shot SQL generation with validation

---

## Phase 2B: LangGraph Integration ✅ COMPLETE

**Goal:** Implement proper graph-based agent orchestration.

| Feature | Description | Status |
|---------|-------------|--------|
| **LangGraph Workflow** | Graph-based orchestration | ✅ Implemented |
| **State Management** | TypedDict state passing | ✅ Implemented |
| **Conditional Routing** | Intent-based branching | ✅ Implemented |
| **Recommendation Agent** | Dedicated agent for advice | ✅ Implemented |
| **Streaming Support** | Real-time step updates | ✅ Implemented |
| **Checkpointing** | Resume from failures | ✅ Optional |
| **Security Module** | Prompt injection protection | ✅ Implemented |

### Graph Structure

```
START → route_intent → [conditional routing]
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
    data_query    knowledge_query   multi_step_analysis
          │               │               │
          │               │         ┌─────┴─────┐
          │               │         ▼           │
          │               │    data_overview    │
          │               │         ▼           │
          │               │    compliance       │
          │               │         ▼           │
          │               │    strategic        │
          │               │         ▼           │
          │               │    recommendations  │
          │               │         ▼           │
          │               │    exec_summary     │
          └───────────────┴─────────┴───────────┘
                          │
                          ▼
                   format_response → END
```

### Why LangGraph?

| Before | After |
|--------|-------|
| Function-based handlers | Graph nodes with edges |
| Manual state passing | Built-in state management |
| No streaming | Real-time step updates |
| No checkpointing | Resumable workflows |

### Files Added/Updated

| File | Change |
|------|--------|
| `orchestration/graph.py` | NEW - LangGraph workflow |
| `agents/recommendation.py` | NEW - Recommendation agent |
| `orchestration/__init__.py` | Export AgentGraph |
| `requirements.txt` | Added langgraph>=1.0.0 |

### Security - Prompt Injection Protection

Comprehensive multi-layer security:

```
User Input → API Validation → LLM Sanitization → SQL Validation → Execute
```

| Protection | Layer | What It Does |
|------------|-------|--------------|
| **Input Sanitization** | API + LLM | Blocks system overrides, jailbreaks, delimiter injection |
| **SQL Validation** | LLM Client | Only SELECT allowed, blocks DROP/DELETE/INSERT |
| **Output Sanitization** | LLM Client | Removes leaked system artifacts |
| **Path Validation** | Workflow | Prevents path traversal attacks |

**Files added:**
- `core/security.py` - InputSanitizer, SQLValidator, PathValidator
- `api/routes/query.py` - API-level input validation
- `llm/client.py` - Integrated security checks

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
