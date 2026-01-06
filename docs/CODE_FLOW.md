# LedgerMind Code Flow

A step-by-step walkthrough of how the code executes from start to finish.

---

## 1. Application Startup (`main.py`)

```
python main.py
```

### 1.1 Banner and System Check

| Function | What it does |
|----------|--------------|
| `print_banner()` | Shows the LedgerMind ASCII logo |
| `check_ollama()` | Verifies Ollama is running and model is available |

### 1.2 Customer Selection

| Function | What it does |
|----------|--------------|
| `CustomerManager()` | Initializes from `core/customer.py` - scans `workspace/` for existing customers |
| `show_customer_list()` | Displays table of existing companies |
| `select_customer()` | Prompts user to select, create new, or use demo |
| `create_new_customer()` | Creates new customer folder and profile |

**Files created per customer:**
```
workspace/{customer_id}/
├── profile.json          # Company metadata
├── data/                 # User's Excel/CSV files
├── {customer_id}.duckdb  # Customer's database
└── data_state.json       # File change tracking
```

### 1.3 Workflow Initialization

| Function | What it does |
|----------|--------------|
| `AgentWorkflow(customer=customer)` | Main orchestrator from `orchestration/workflow.py` |
| `customer.get_data_engine()` | Creates DuckDB connection for this customer |
| `customer.get_data_state_manager()` | Loads file tracking state |
| `workflow._smart_load_data()` | Detects new/modified files and loads them |

---

## 2. User Query Processing

When user types a question:

```
User types: "Show me the balance for November"
```

### 2.1 Intent Routing (`orchestration/router.py`)

| Function | What it does |
|----------|--------------|
| `IntentRouter.route(user_input)` | Pattern matches to determine intent type |

**Intent Types:**
```
FOLDER_ANALYSIS    → "analyze folder /path/"
DATA_QUERY         → "show my balance", "total sales"
KNOWLEDGE_QUERY    → "what is CGST?", "GST rate on milk?"
COMPLIANCE_CHECK   → "run compliance check"
STRATEGIC_ANALYSIS → "analyze vendors"
HELP               → "help"
```

### 2.2 Handler Dispatch (`orchestration/workflow.py`)

| Intent | Handler Function | Description |
|--------|------------------|-------------|
| DATA_QUERY | `_handle_data_query()` | Converts question to SQL, runs on DuckDB |
| KNOWLEDGE_QUERY | `_handle_knowledge_query()` | Routes to LLM/CSV/ChromaDB |
| COMPLIANCE_CHECK | `_handle_compliance_check()` | Runs `ComplianceAgent` |
| FOLDER_ANALYSIS | `_handle_folder_analysis()` | Runs `DiscoveryAgent` |
| STRATEGIC_ANALYSIS | `_handle_strategic_analysis()` | Runs `StrategistAgent` |

---

## 3. Data Query Flow (Example)

```
User: "Show me the balance for November"
```

### Step 1: Classification
```
_handle_data_query(query)
  └── _get_table_schemas(tables)    # Get column names from DuckDB
```

### Step 2: SQL Generation
```
LLMClient.generate(prompt)          # Ask LLM to write SQL
  └── prompt includes:
      - Table names and columns
      - Sample data
      - Rules for SQL generation
```

### Step 3: Execution
```
DataEngine.query(sql)               # Execute on DuckDB
  └── Returns pandas DataFrame
```

### Step 4: Response
```
Format results as markdown table
Return to user
```

---

## 4. Knowledge Query Flow (Example)

```
User: "What is the GST rate on laptops?"
```

### Step 1: Classification (`core/query_classifier.py`)

| Function | What it does |
|----------|--------------|
| `QueryClassifier.classify(query)` | Determines query type |

**Query Types:**
```
DEFINITION   → "What is CGST?"     → Use LLM knowledge
RATE_LOOKUP  → "rate on laptops"   → Search CSV files
LEGAL_RULE   → "Section 17(5)"     → Search ChromaDB
DATA_QUERY   → "my total sales"    → Query DuckDB
```

### Step 2: Route to Source

| Type | Source | Function |
|------|--------|----------|
| DEFINITION | LLM | `LLMClient.generate()` |
| RATE_LOOKUP | CSV | `core/reference_data.py` → `search_rate_by_name()` |
| LEGAL_RULE | ChromaDB | `core/knowledge.py` → `get_relevant_rules()` |

---

## 5. File/Module Reference

### Core Files

| File | Purpose | Key Functions |
|------|---------|---------------|
| `main.py` | Entry point, CLI loop | `main()`, `select_customer()` |
| `config.py` | All configuration | Paths, model settings, prompts |
| `core/customer.py` | Customer isolation | `CustomerContext`, `CustomerManager` |
| `core/data_engine.py` | DuckDB operations | `load_excel()`, `load_csv()`, `query()` |
| `core/data_state.py` | File change detection | `detect_changes()`, `get_files_to_load()` |
| `core/reference_data.py` | GST rates, MSME data | `load_goods_rates()`, `get_rate_for_hsn()` |
| `core/knowledge.py` | ChromaDB RAG | `get_relevant_rules()` |
| `core/query_classifier.py` | Query routing | `QueryClassifier.classify()` |
| `core/guardrails.py` | Input validation | `validate_gstin()`, `validate_tax_calculation()` |

### Orchestration

| File | Purpose | Key Functions |
|------|---------|---------------|
| `orchestration/router.py` | Intent detection | `IntentRouter.route()` |
| `orchestration/workflow.py` | Main workflow | `AgentWorkflow.run()`, handlers |

### Agents

| File | Purpose | Key Functions |
|------|---------|---------------|
| `agents/discovery.py` | Data ingestion | `discover()`, `map_headers()` |
| `agents/compliance.py` | Compliance checking | `run_full_audit()` |
| `agents/strategist.py` | Strategic analysis | `run_full_analysis()` |

### LLM

| File | Purpose | Key Functions |
|------|---------|---------------|
| `llm/client.py` | Ollama integration | `generate()`, `generate_json()` |

---

## 6. Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         USER                                 │
│                    (types question)                          │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                      main.py                                 │
│                  (CLI input loop)                            │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│               orchestration/router.py                        │
│                 IntentRouter.route()                         │
│           Determines: DATA / KNOWLEDGE / etc.                │
└─────────────────────────┬───────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│ DATA_QUERY  │   │ KNOWLEDGE   │   │ COMPLIANCE  │
│             │   │   QUERY     │   │   CHECK     │
└──────┬──────┘   └──────┬──────┘   └──────┬──────┘
       │                 │                 │
       ▼                 ▼                 ▼
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│   DuckDB    │   │ LLM / CSV / │   │ Compliance  │
│   (User's   │   │  ChromaDB   │   │   Agent     │
│    data)    │   │  (Rules)    │   │             │
└─────────────┘   └─────────────┘   └─────────────┘
```

---

## 7. Startup Sequence Summary

```
1. main.py
   └── print_banner()
   └── check_ollama()
   └── CustomerManager()
   └── select_customer()
       └── CustomerContext(customer_id)
           └── ensure_exists()
               └── Creates workspace/{id}/
   └── AgentWorkflow(customer)
       └── KnowledgeBase()           # Shared ChromaDB
       └── LLMClient()               # Shared Ollama
       └── customer.get_data_engine() # Customer's DuckDB
       └── customer.get_data_state_manager()
       └── _smart_load_data()        # Load new/changed files
   └── Interactive loop
       └── workflow.run(user_input)
           └── router.route() → _handle_xxx()
```

---

## 8. Key Design Decisions

| Decision | Reason |
|----------|--------|
| **DuckDB per customer** | Data isolation, no cross-contamination |
| **Shared ChromaDB** | GST rules same for everyone, save memory |
| **Shared LLM** | Single Ollama instance, efficient |
| **Smart file loading** | Only reload changed files (by hash) |
| **Query classification** | Route to best knowledge source |
| **Fallback mechanisms** | Show helpful data when queries fail |

---

## 9. Adding New Features (Quick Guide)

### Add a new command:
1. Add pattern in `orchestration/router.py` → `patterns` dict
2. Add handler in `orchestration/workflow.py` → `run()` method

### Add new reference data:
1. Add CSV to `db/` folder
2. Add loader in `core/reference_data.py`
3. Add path in `config.py`

### Add new agent:
1. Create `agents/new_agent.py`
2. Initialize in `orchestration/workflow.py`
3. Add handler method

