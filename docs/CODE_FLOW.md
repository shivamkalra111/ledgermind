# Code Flow - How LedgerMind Works

> The LLM is the product. This doc shows how questions flow through it.

---

## The Big Picture

```
User Question
     │
     ▼
┌────────────────┐
│  API Endpoint  │  (POST /api/v1/query)
│  Thin wrapper  │
└───────┬────────┘
        │
        ▼
┌────────────────┐
│  AgentWorkflow │  (orchestration/workflow.py)
│  The brain     │
└───────┬────────┘
        │
        ▼
┌────────────────┐
│  IntentRouter  │  (orchestration/router.py)
│  Classifies    │
└───────┬────────┘
        │
        ├──── DATA_QUERY ────▶ DuckDB (core/data_engine.py)
        │
        ├──── KNOWLEDGE_QUERY ▶ ChromaDB + LLM (core/knowledge.py)
        │
        ├──── COMPLIANCE_CHECK ▶ Agents (agents/compliance.py)
        │
        └──── FOLDER_ANALYSIS ─▶ Agents (agents/discovery.py)
                │
                ▼
            Response
```

---

## 1. API Layer (Thin)

### `api/app.py`
- FastAPI application
- 2 routes: `/upload` and `/query`
- Just passes request to workflow

### `api/routes/query.py`
```python
@router.post("/query")
async def query(request: QueryRequest, customer: ...):
    workflow = AgentWorkflow(customer=ctx)
    answer = workflow.run(request.query)  # <-- ALL logic here
    return QueryResponse(answer=answer)
```

**Key point:** API does nothing smart. Just calls `workflow.run()`.

---

## 2. The Brain - AgentWorkflow

### `orchestration/workflow.py`

This is where everything happens:

```python
def run(self, user_input: str) -> str:
    # Step 1: Classify intent
    intent = self.router.route(user_input)
    
    # Step 2: Route to handler
    if intent.intent_type == IntentType.DATA_QUERY:
        return self._handle_data_query(intent.extracted_query)
    
    elif intent.intent_type == IntentType.KNOWLEDGE_QUERY:
        return self._handle_knowledge_query(intent.extracted_query)
    
    elif intent.intent_type == IntentType.COMPLIANCE_CHECK:
        return self._handle_compliance_check()
    
    # ... etc
```

---

## 3. Intent Classification

### `orchestration/router.py`

Pattern-based + LLM classification:

```python
class IntentType(Enum):
    DATA_QUERY = "data_query"           # "show my sales"
    KNOWLEDGE_QUERY = "knowledge_query" # "what is CGST"
    COMPLIANCE_CHECK = "compliance"     # "check compliance"
    FOLDER_ANALYSIS = "folder"          # "analyze my data"
    HELP = "help"
    UNKNOWN = "unknown"
```

The router checks patterns first, then uses LLM if unclear.

---

## 4. Data Queries

### Flow

```
"What is my total sales?"
        │
        ▼
┌─────────────────┐
│ _handle_data_   │
│ query()         │
└───────┬─────────┘
        │
        ▼
┌─────────────────┐
│ Get table       │
│ schemas from    │
│ DuckDB          │
└───────┬─────────┘
        │
        ▼
┌─────────────────┐
│ LLM generates   │
│ SQL query       │
└───────┬─────────┘
        │
        ▼
┌─────────────────┐
│ Execute SQL     │
│ in DuckDB       │
└───────┬─────────┘
        │
        ▼
┌─────────────────┐
│ LLM formats     │
│ response        │
└───────┬─────────┘
        │
        ▼
    Answer
```

### Key Files

| File | Purpose |
|------|---------|
| `core/data_engine.py` | DuckDB operations |
| `orchestration/workflow.py` | SQL generation via LLM |

---

## 5. Knowledge Queries

### Flow

```
"What is CGST?"
        │
        ▼
┌─────────────────┐
│ QueryClassifier │  Determines: DEFINITION / RATE_LOOKUP / LEGAL_RULE
└───────┬─────────┘
        │
        ├── DEFINITION ──▶ LLM general knowledge
        │
        ├── RATE_LOOKUP ─▶ CSV files (db/gst/goods_hsn.csv)
        │
        └── LEGAL_RULE ──▶ ChromaDB RAG
                │
                ▼
            Answer
```

### Key Files

| File | Purpose |
|------|---------|
| `core/query_classifier.py` | Sub-classifies knowledge queries |
| `core/knowledge.py` | ChromaDB search |
| `core/reference_data.py` | CSV lookups |

---

## 6. Customer Isolation

### `core/customer.py`

Each customer gets:
```
workspace/{customer_id}/
├── data/                  # Their Excel/CSV files
├── {customer_id}.duckdb   # Their database
├── profile.json           # Metadata
└── data_state.json        # File change tracking
```

### Flow

```
API Request with X-API-Key
        │
        ▼
┌─────────────────┐
│ api/auth.py     │  Validates key, gets customer_id
└───────┬─────────┘
        │
        ▼
┌─────────────────┐
│ CustomerContext │  Loads customer's DuckDB, workspace
└───────┬─────────┘
        │
        ▼
    Workflow uses customer's data only
```

---

## 7. Smart Data Loading

### `core/data_state.py`

Tracks file changes automatically:

```python
# On startup or query
data_state = DataStateManager(customer.root_dir)
changes = data_state.get_changes()

if changes["new"] or changes["modified"]:
    # Load only changed files
    for file in changes["new"]:
        engine.load_file(file)
```

No manual "refresh data" needed.

---

## 8. File Summary

### Core (The Brain)

| File | One-liner |
|------|-----------|
| `orchestration/workflow.py` | **THE MAIN FILE** - LLM routing |
| `orchestration/router.py` | Intent classification |
| `llm/client.py` | Ollama connection |

### Data Sources

| File | One-liner |
|------|-----------|
| `core/data_engine.py` | DuckDB for customer data |
| `core/knowledge.py` | ChromaDB for GST rules |
| `core/reference_data.py` | CSV lookups |

### Customer Management

| File | One-liner |
|------|-----------|
| `core/customer.py` | Customer isolation |
| `core/data_state.py` | File change detection |

### API (Thin Wrapper)

| File | One-liner |
|------|-----------|
| `api/app.py` | FastAPI entry |
| `api/auth.py` | API key validation |
| `api/routes/query.py` | POST /query |
| `api/routes/upload.py` | POST /upload |

### Streamlit (Internal)

| File | One-liner |
|------|-----------|
| `streamlit/app.py` | Streamlit UI |
| `streamlit/api_keys.py` | Key management |

---

## Key Design Decisions

### 1. Single Query Endpoint

**Why not `/data/query` and `/knowledge/query`?**

The LLM already routes internally. Exposing multiple endpoints just duplicates logic.

### 2. LLM Decides Everything

The `IntentRouter` classifies intent, then the appropriate handler runs. No hardcoded rules about "if query contains X, do Y".

### 3. API is Thin

API routes just call `workflow.run()`. All intelligence is in the workflow.

### 4. Customer Isolation by Default

Every API request is tied to a customer. No cross-customer data access.

---

## Adding New Features

### Add a new query type

1. Add to `IntentType` enum in `router.py`
2. Add pattern in `_classify()` method
3. Add handler in `workflow.py`

### Add a new data source

1. Create loader in `core/`
2. Call from appropriate handler in `workflow.py`

### Add a new API endpoint

Don't. Just handle it in `workflow.py` and let `/query` route to it.

---

**Remember: All roads lead to `workflow.run()`**
