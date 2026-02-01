# LedgerMind Architecture

> The LLM is the product. Everything else is plumbing.

---

## Core Principle

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   Question ──▶ LLM ──▶ Answer                              │
│                                                             │
│   That's it. Everything else supports this flow.           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         LEDGERMIND                                   │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    DELIVERY LAYER                            │    │
│  │                    (thin wrappers)                           │    │
│  │                                                              │    │
│  │   ┌──────────────┐              ┌──────────────┐            │    │
│  │   │   FastAPI    │              │  Streamlit   │            │    │
│  │   │  (customers) │              │  (internal)  │            │    │
│  │   └──────┬───────┘              └──────┬───────┘            │    │
│  │          │                             │                     │    │
│  └──────────┼─────────────────────────────┼─────────────────────┘    │
│             │                             │                          │
│             └──────────────┬──────────────┘                          │
│                            │                                         │
│                            ▼                                         │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                      LLM BRAIN                               │    │
│  │                                                              │    │
│  │   ┌──────────────────────────────────────────────────────┐  │    │
│  │   │              AgentWorkflow                            │  │    │
│  │   │              (orchestration/workflow.py)              │  │    │
│  │   │                                                       │  │    │
│  │   │   IntentRouter ──▶ Route to handler ──▶ Response     │  │    │
│  │   └──────────────────────────────────────────────────────┘  │    │
│  │                            │                                 │    │
│  └────────────────────────────┼─────────────────────────────────┘    │
│                               │                                      │
│             ┌─────────────────┼─────────────────┐                    │
│             │                 │                 │                    │
│             ▼                 ▼                 ▼                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │   DuckDB     │  │   ChromaDB   │  │   CSV Files  │               │
│  │  (customer   │  │  (GST rules) │  │  (rates)     │               │
│  │   data)      │  │              │  │              │               │
│  └──────────────┘  └──────────────┘  └──────────────┘               │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. Delivery Layer (Thin)

**FastAPI** (`api/`)
- 2 endpoints only: `/upload`, `/query`
- API key authentication
- Just calls `workflow.run()`

**Streamlit** (`streamlit/`)
- Internal testing tool
- Chat interface
- Customer selection

### 2. LLM Brain

**AgentWorkflow** (`orchestration/workflow.py`)
- The main orchestrator
- Routes all queries
- Calls appropriate handlers

**IntentRouter** (`orchestration/router.py`)
- Classifies user intent
- Pattern matching + LLM fallback

**LLMClient** (`llm/client.py`)
- Ollama connection
- Text generation
- **Few-shot SQL generation** with automatic fallback

### 3. Data Sources

**DuckDB** (`core/data_engine.py`)
- Customer's Excel/CSV as SQL tables
- Fast analytical queries
- Data-agnostic loading (works with ANY data)

**Table Catalog** (`core/table_catalog.py`)
- Schema stored at ingestion time
- Smart table selection (detects table families)
- Efficient query-time schema access

**ChromaDB** (`core/knowledge.py`)
- Vector database
- GST rules from PDFs
- RAG retrieval

**CSV Files** (`core/reference_data.py`)
- Tax rates
- HSN/SAC codes
- State codes

---

## Data Flow

### Query Flow

```
User: "What is my total sales?"
          │
          ▼
    ┌───────────┐
    │ API/CLI   │  Receives query
    └─────┬─────┘
          │
          ▼
    ┌───────────┐
    │ Workflow  │  workflow.run(query)
    └─────┬─────┘
          │
          ▼
    ┌───────────┐
    │ Router    │  Classifies: DATA_QUERY
    └─────┬─────┘
          │
          ▼
    ┌───────────┐
    │ Handler   │  _handle_data_query()
    └─────┬─────┘
          │
          ├──▶ TableCatalog: Select relevant tables
          │    (detects table families, includes all related)
          │
          ├──▶ Get schemas from catalog (stored at ingestion)
          │
          ├──▶ LLM generates SQL (with few-shot learning)
          │    Handles UNION ALL for table families
          │
          ├──▶ Execute SQL in DuckDB
          │
          ├──▶ Format response
          │
          ▼
    "Your total sales: ₹5,00,000"
```

### Knowledge Query Flow

```
User: "What is CGST?"
          │
          ▼
    ┌───────────┐
    │ Router    │  Classifies: KNOWLEDGE_QUERY
    └─────┬─────┘
          │
          ▼
    ┌───────────┐
    │ Classifier│  Sub-classifies: DEFINITION
    └─────┬─────┘
          │
          ▼
    ┌───────────┐
    │ LLM       │  General knowledge answer
    └─────┬─────┘
          │
          ▼
    "CGST is Central GST..."
```

---

## Customer Isolation

```
workspace/
├── customer_a/
│   ├── data/               # Their Excel files
│   ├── customer_a.duckdb   # Their database
│   ├── table_catalog.json  # Schema + metadata
│   ├── data_state.json     # File change tracking
│   └── profile.json        # Customer info
│
├── customer_b/
│   ├── data/               # Their Excel files
│   ├── customer_b.duckdb   # Their database
│   ├── table_catalog.json  # Schema + metadata
│   ├── data_state.json     # File change tracking
│   └── profile.json        # Customer info
```

**Each API request is scoped to one customer.** No cross-customer access.

---

## Security Model

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   API Request                                               │
│   X-API-Key: lm_live_xxxxx                                 │
│         │                                                   │
│         ▼                                                   │
│   ┌───────────────┐                                        │
│   │ auth.py       │  Validate key, get customer_id         │
│   └───────┬───────┘                                        │
│           │                                                 │
│           ▼                                                 │
│   ┌───────────────┐                                        │
│   │ CustomerCtx   │  Load only this customer's data        │
│   └───────┬───────┘                                        │
│           │                                                 │
│           ▼                                                 │
│   Customer sees only their data                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology | Why |
|-------|------------|-----|
| **LLM** | Ollama + Qwen2.5 | Local, free, good quality |
| **Data** | DuckDB | Fast SQL on files |
| **Knowledge** | ChromaDB | Vector search for RAG |
| **API** | FastAPI | Modern, fast, docs auto-gen |
| **Admin UI** | Streamlit | Quick internal tool |

---

## Key Design Decisions

### 1. LLM Handles Routing

No hardcoded "if query contains sales, do X". The LLM classifies intent and routes appropriately.

### 2. Single Query Endpoint

The LLM already routes internally. Multiple endpoints would just duplicate this.

### 3. Local First

All computation happens locally:
- LLM runs via Ollama
- Data stays in local DuckDB
- No cloud dependencies

### 4. Customer Isolation Built-In

Every query is scoped to a customer. Architecture prevents cross-customer access.

### 5. Thin API Layer

API just validates auth and calls `workflow.run()`. No business logic in routes.

### 6. Data-Agnostic Loading

The data loading layer makes NO assumptions about data:
- No hardcoded column names
- No assumed data types ("sales", "purchases", etc.)
- LLM understands columns from names + sample data
- Works with ANY Excel/CSV data

### 7. Schema Stored at Ingestion

Schema is extracted once when file is uploaded:
- Stored in `table_catalog.json`
- No need to query DuckDB schema at runtime
- Includes metadata for smart table selection

### 8. Few-Shot SQL Generation

SQL generation uses few-shot learning:
- Examples teach UNION ALL, GROUP BY, filtering patterns
- Automatic fallback if SQL model produces invalid output
- ~90% accuracy on complex queries

---

## Extension Points

### Add New Query Type

1. Add `IntentType` in `router.py`
2. Add handler in `workflow.py`
3. Done. `/query` endpoint automatically supports it.

### Add New Data Source

1. Create module in `core/`
2. Call from handler in `workflow.py`
3. No API changes needed.

### Improve SQL Accuracy

1. Add more few-shot examples in `llm/client.py`
2. Examples should cover new query patterns
3. System automatically uses them

### Support New File Types

1. Add loader in `core/data_engine.py`
2. Update `agents/discovery.py` to detect the type
3. Data-agnostic loading handles the rest

---

**Everything serves one purpose: get the LLM to answer questions.**
