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
┌─────────────────────────────────────────────────────────┐
│ AUTOMATIC SCALE DETECTION                               │
│                                                         │
│ IF num_tables > 100:                                    │
│   • Initialize vector search (one-time, 2-5 min)       │
│   • Use 3-stage massive scale selection                │
│ ELSE:                                                   │
│   • Use standard LLM-based selection                    │
└───────┬─────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────┐
│ THREE-STAGE SELECTION (For 100+ tables)                │
│                                                         │
│ Stage 1: Vector Search                                 │
│   • Semantic similarity (cosine distance)              │
│   • 500 tables → 20 candidates                         │
│   • Token cost: 0 (no LLM call!)                       │
│   • Time: ~50ms                                        │
│         │                                               │
│         ▼                                               │
│ Stage 2: Family Expansion                              │
│   • Pattern matching (purchase_2023_*)                 │
│   • For "total" queries: include all family            │
│   • Token cost: 0                                      │
│         │                                               │
│         ▼                                               │
│ Stage 3: LLM Refinement                                │
│   • LLM sees 20 candidates (~500 tokens)               │
│   • Selects final 3-5 tables                           │
│   • Token savings: 96% (vs 12,500 for full catalog)    │
└───────┬─────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────┐
│ Adaptive Schema │  Choose detail level based on count:
│ Detail Level    │  • 3-5 tables: FULL (750 chars/table)
└───────┬─────────┘  • 5-10 tables: MEDIUM (300 chars/table)
        │            • 10+ tables: COMPRESSED (100 chars/table)
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

### Massive Scale (100+ Tables)

For datasets with hundreds of tables:

**Problem:** 500 tables × 100 chars = 50,000 chars = 12,500 tokens (can't fit in context!)

**Solution:** Three-stage hierarchical selection

1. **Vector Search (Stage 1)**
   - One-time embedding of all tables using sentence-transformers
   - User query → vector similarity → top 20 candidates
   - **0 tokens** - pure cosine distance math, no LLM!
   - Time: ~50ms for 500 tables

2. **Family Expansion (Stage 2)**
   - Pattern matching: detect `purchase_2023_*` families
   - For "total" queries: expand to include all family members
   - **0 tokens** - pattern matching only

3. **LLM Refinement (Stage 3)**
   - LLM sees only 20 candidates (~2,000 chars = 500 tokens)
   - Much better than 500 tables (50,000 chars = 12,500 tokens)
   - Selects final 3-5 tables with full understanding

**Result:** 96% token reduction, better accuracy, scales to unlimited tables!

### Compressed Schemas

For queries needing 20+ tables, the system uses compressed schema format:

```python
# Instead of full schema (750 chars):
TABLE: purchase_2023_01
  Source: purchase_jan_2023.xlsx
  Description: Purchase transactions for January 2023
  Columns:
    "date" (DATE) - Transaction date
    "vendor" (VARCHAR) - Vendor name
    ...

# Use compressed (100 chars):
purchase_2023_01(date DATE, vendor VARCHAR, amount DOUBLE, total DOUBLE)
```

**Compression ratio:** 7.5x - can fit 7.5x more tables in same context!

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
| `core/table_catalog.py` | Schema storage, table family detection, vector search for massive scale |
| `llm/client.py` | SQL generation with few-shot learning |
| `orchestration/workflow.py` | Query handling |
| `orchestration/graph.py` | LangGraph-based orchestration with automatic scale detection |

---

## 4.5. Massive Scale: Handling 500+ Tables

### The Challenge

When a dataset has 500+ tables:
- Brief catalog: 500 × 100 chars = 50,000 chars = **12,500 tokens**
- Context limit: 32,768 tokens
- **Problem:** Can't fit all table descriptions in context for LLM selection!

### The Solution: Three-Stage Hierarchical Selection

```
500 TABLES
    │
    │ AUTOMATIC DETECTION (num_tables > 100)
    ▼
┌─────────────────────────────────────────────────────────┐
│ STAGE 1: VECTOR SEARCH                                  │
│   Method: Semantic similarity (cosine distance)         │
│   Input: User query + 500 table embeddings              │
│   Output: Top 20 candidates                             │
│   Token Cost: 0 (no LLM call!)                          │
│   Time: ~50ms                                           │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ STAGE 2: FAMILY EXPANSION                               │
│   Method: Pattern matching (regex)                      │
│   Detects: purchase_2023_* families                     │
│   For "total" queries: Include all family members       │
│   Token Cost: 0 (pattern matching only)                 │
│   Time: ~5ms                                            │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ STAGE 3: LLM REFINEMENT                                 │
│   Input: 20 candidates (2,000 chars = ~500 tokens)      │
│   LLM: Selects final 3-5 tables with full context       │
│   Token Cost: ~500 tokens                               │
│   Time: ~2s                                             │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
              FINAL SELECTION
              (3-5 tables)

Total Token Usage: ~500 tokens (vs 12,500 without optimization!)
Savings: 96%
```

### Implementation Details

**Vector Search (Stage 1):**
```python
# One-time setup (2-5 min for 500 tables)
catalog.initialize_vector_search()

# For each table, embed rich text:
text = f"Table: {name} | Description: {desc} | Columns: {cols} | Keywords: {kw}"
embedding = model.encode(text)  # 384-dim vector

# Query time: cosine similarity
query_embedding = model.encode("What are my total purchases?")
similarities = [cosine_sim(query_embedding, table_embedding) for table in tables]
top_20 = sorted(similarities, reverse=True)[:20]  # 0 tokens!
```

**Family Expansion (Stage 2):**
```python
# Detect patterns like: purchase_2023_01, purchase_2023_02, ...
families = detect_families(top_20)  # {"purchase_2023_": [12 tables]}

# If query wants "total", expand to full family
if "total" in query.lower():
    selected = families["purchase_2023_"]  # All 12 months
```

**LLM Refinement (Stage 3):**
```python
# Build brief catalog for ONLY the candidates
candidate_catalog = "\n".join([
    f"{i}. {name} - {brief_desc}"
    for i, name in enumerate(top_20, 1)
])  # 20 × 100 chars = 2,000 chars (~500 tokens)

# LLM sees only 20 options, not 500!
prompt = f"""Select relevant tables:
{candidate_catalog}
USER QUESTION: {query}
"""
final_selection = llm.generate(prompt)  # ~500 tokens
```

### Adaptive Schema Detail

For large table sets, use compressed schema:

```python
# Automatic selection based on table count:
if len(selected) > 10:
    schema = catalog.get_schema(selected, detail_level="compressed")
    # Format: table(col1 TYPE, col2 TYPE, ...)
    # Size: ~100 chars/table (7.5x compression!)
elif len(selected) > 5:
    schema = catalog.get_schema(selected, detail_level="medium")
    # Format: columns + descriptions, no samples
    # Size: ~300 chars/table (2.5x compression)
else:
    schema = catalog.get_schema(selected, detail_level="full")
    # Format: full details + samples + stats
    # Size: ~750 chars/table
```

### Performance Characteristics

| Metric | Value |
|--------|-------|
| **Setup Time** | 2-5 min (one-time for 500 tables) |
| **Query Time (Stage 1)** | ~50ms (vector search) |
| **Query Time (Stage 2)** | ~5ms (pattern matching) |
| **Query Time (Stage 3)** | ~2s (LLM refinement) |
| **Total Query Time** | ~2-3s (same as before!) |
| **Token Savings** | 96% (12,500 → 500 tokens) |
| **Memory Overhead** | ~1MB for 500 embeddings |
| **Scale Limit** | Unlimited (tested with 500+) |

### Fallback Strategy

If vector search unavailable or fails:
1. **Fallback 1:** Standard LLM selection (works up to ~100 tables)
2. **Fallback 2:** Keyword matching (pattern-based)
3. **Fallback 3:** Use first N tables (last resort)

System is resilient with graceful degradation.

### Files

| File | Component |
|------|-----------|
| `core/table_catalog.py` | `initialize_vector_search()`, `search_tables_by_vector()`, `select_tables_for_massive_scale()` |
| `orchestration/graph.py` | Automatic scale detection in `_handle_data_query()` |
| `core/data_engine.py` | Catalog integration |
| `demo_massive_scale.py` | Demo script showing 96% token reduction |

### Demo

```bash
# Run demo with 500 simulated tables
python demo_massive_scale.py

# Shows:
# - Problem: 12,500 tokens for full catalog
# - Solution: 500 tokens with 3-stage selection
# - Result: 96% token savings
```

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

### 5. Security-First Design

Multi-layer protection against prompt injection and SQL injection:
- **Input Sanitization:** Pattern-based threat detection at API boundary
- **Defensive Prompt Engineering:** Secure prompt framing with XML tags
- **Secure System Prompts:** Immutable security rules, instruction hierarchy
- **Output Validation:** SQL validation (SELECT-only), artifact removal

### 6. Massive Scale Optimization

For datasets with 100+ tables, automatic three-stage selection prevents context overflow:
- **Stage 1:** Vector search (0 tokens) - semantic similarity
- **Stage 2:** Family expansion (0 tokens) - pattern matching
- **Stage 3:** LLM refinement (~500 tokens) - final selection

This provides 96% token savings (12,500 → 500 tokens) while improving accuracy.

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
