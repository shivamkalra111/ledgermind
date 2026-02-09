# Code Flow - How LedgerMind Works

> The LLM is the product. This doc shows how questions flow through it.

---

## The Big Picture (LangGraph)

LedgerMind now uses **LangGraph** for agent orchestration. The workflow is defined as a directed graph where nodes are processing steps and edges define the flow.

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
│   AgentGraph   │  (orchestration/graph.py) - LangGraph-based
│   The brain    │
└───────┬────────┘
        │
        ▼
┌────────────────┐
│  route_intent  │  First node in graph
│  (IntentRouter)│
└───────┬────────┘
        │
        ├──── DATA_QUERY ────▶ handle_data_query node
        │
        ├──── KNOWLEDGE_QUERY ▶ handle_knowledge_query node
        │
        ├──── COMPLIANCE_CHECK ▶ handle_compliance_check node
        │
        ├──── MULTI_STEP_ANALYSIS ▶ 5-node chain (see below)
        │
        └──── FOLDER_ANALYSIS ─▶ handle_data_query node
                │
                ▼
        ┌────────────────┐
        │ format_response │  Final formatting node
        └───────┬────────┘
                │
                ▼
              END
```

### Legacy Flow (Still Supported)

The original `AgentWorkflow` in `orchestration/workflow.py` is still available for backward compatibility.

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
    MULTI_STEP_ANALYSIS = "multi_step"  # "full analysis" or "generate report"
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
│ TableCatalog    │  Get schema from catalog (stored at ingestion)
│ select_tables   │  Smart selection: detect table families
└───────┬─────────┘
        │
        ▼
┌─────────────────┐
│ LLM generates   │  Uses few-shot learning
│ SQL query       │  Handles UNION ALL for table families
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
│ Format response │
└───────┬─────────┘
        │
        ▼
    Answer
```

### Smart Table Selection

When user asks "total of all purchases" and you have:
- `purchase_2021_07`, `purchase_2021_08`, ..., `purchase_2022_01`

The system:
1. Detects these are a "table family" (same prefix)
2. Includes ALL tables in the query
3. Generates proper UNION ALL SQL

### Few-Shot SQL Generation

The LLM uses examples to learn patterns:
- Aggregations: `SUM(amount) AS total`
- Multi-table: `UNION ALL` for related tables
- Filtering: `WHERE name LIKE '%value%'`
- Grouping: `GROUP BY column ORDER BY total DESC`

### Key Files

| File | Purpose |
|------|---------|
| `core/data_engine.py` | DuckDB operations |
| `core/table_catalog.py` | Schema storage, table family detection |
| `llm/client.py` | SQL generation with few-shot learning |
| `orchestration/workflow.py` | Query handling |

---

## 5. Multi-Step Analysis

### Flow

```
"Generate full report" / "comprehensive analysis"
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│                 MULTI-STEP ANALYSIS                         │
│                                                             │
│  Step 1: Data Overview ─────────────────────────────────┐  │
│          Analyze tables, record counts, date ranges     │  │
│                        │                                 │  │
│                        ▼                                 │  │
│  Step 2: Compliance Check ──────────────────────────────│  │
│          Run full audit, identify issues                │  │
│                        │                                 │  │
│                        ▼                                 │  │
│  Step 3: Strategic Analysis ────────────────────────────│  │
│          Vendor rankings, cash flow forecasts           │  │
│                        │                                 │  │
│                        ▼                                 │  │
│  Step 4: Generate Recommendations ──────────────────────│  │
│          RecommendationAgent synthesizes findings       │  │
│                        │                                 │  │
│                        ▼                                 │  │
│  Step 5: Executive Summary ─────────────────────────────┘  │
│          LLM creates comprehensive report                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
    Full Report with all findings
```

### Key Features

- **Sequential orchestration**: Each step passes context to the next
- **State management**: `MultiStepAnalysisState` tracks progress and results
- **Error handling**: If a step fails, workflow marks it and continues
- **RecommendationAgent**: Dedicated agent for synthesizing findings into prioritized actions
- **LLM-powered synthesis**: Executive summary uses full context from all steps

### Recommendation Agent Features

The RecommendationAgent (`agents/recommendation.py`) provides:

1. **Template-based recommendations** for common scenarios:
   - Data quality issues (null values, missing data)
   - Critical compliance violations
   - Negative cash flow projections
   - Vendor risk concentration
   - MSME verification needs

2. **LLM-generated recommendations** for nuanced insights

3. **Prioritization**:
   - CRITICAL: Must do immediately
   - HIGH: Should do soon
   - MEDIUM: Plan to do
   - LOW: Nice to have

4. **Categories**: Compliance, Data Quality, Cash Flow, Vendor, Tax Savings, Operational, Risk

### Trigger Phrases

```
"full analysis"
"comprehensive review" 
"generate report"
"analyze everything"
"business health report"
"deep dive"
```

---

## 6. Knowledge Queries

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
├── table_catalog.json     # Schema + metadata (stored at ingestion)
├── profile.json           # Customer metadata
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
| `llm/client.py` | Ollama connection + few-shot SQL |

### Data Sources

| File | One-liner |
|------|-----------|
| `core/data_engine.py` | DuckDB for customer data |
| `core/table_catalog.py` | Schema storage, table selection |
| `core/knowledge.py` | ChromaDB for GST rules |
| `core/reference_data.py` | CSV lookups |

### Customer Management

| File | One-liner |
|------|-----------|
| `core/customer.py` | Customer isolation |
| `core/data_state.py` | File change detection |

### Data Loading (Data-Agnostic)

| File | One-liner |
|------|-----------|
| `agents/discovery.py` | File loading (any data type) |
| `core/schema.py` | Deprecated - generic schemas only |
| `core/mapper.py` | Deprecated - no longer used |

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
