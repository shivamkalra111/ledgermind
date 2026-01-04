# LedgerMind - Technical Architecture

> Complete technical documentation for the Agentic AI CFO Platform

---

## 1. System Overview

LedgerMind is an **autonomous financial intelligence platform** built on a multi-agent architecture. It transforms unstructured financial data (Excel/CSV) into actionable insights through specialized AI agents.

### Core Principles

1. **Agents over Chatbots** — Autonomous task execution, not just Q&A
2. **SQL over Embeddings for Data** — DuckDB for financial data, ChromaDB for rules only
3. **Local-First** — All processing on user's machine, $0 cloud cost
4. **Math Safety** — LLM reasons, Python/SQL calculates

---

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER INTERFACE                                  │
│                         (CLI / Future: Web UI)                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ORCHESTRATION LAYER                                │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │  Intent Router  │───▶│ Agent Workflow  │───▶│  Response Gen   │         │
│  │  (Classify)     │    │  (Coordinate)   │    │  (Format)       │         │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘         │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AGENT LAYER                                     │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │   DISCOVERY     │    │   COMPLIANCE    │    │   STRATEGIST    │         │
│  │   AGENT         │    │   AGENT         │    │   AGENT         │         │
│  │                 │    │                 │    │                 │         │
│  │ • Structure     │    │ • Tax Rate      │    │ • Vendor        │         │
│  │   Detection     │    │   Verification  │    │   Ranking       │         │
│  │ • Header        │    │ • ITC Checks    │    │ • Cash Flow     │         │
│  │   Mapping       │    │ • 43B(h)        │    │   Forecast      │         │
│  │ • Schema        │    │   Compliance    │    │ • Profit        │         │
│  │   Creation      │    │ • Sec 17(5)     │    │   Analysis      │         │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘         │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CORE LAYER                                      │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │   DATA ENGINE   │    │  KNOWLEDGE BASE │    │   LLM CLIENT    │         │
│  │   (DuckDB)      │    │   (ChromaDB)    │    │   (Ollama)      │         │
│  │                 │    │                 │    │                 │         │
│  │ • Excel → SQL   │    │ • GST PDFs      │    │ • Qwen 7B       │         │
│  │ • Query Engine  │    │ • RAG Retrieval │    │ • Local LLM     │         │
│  │ • Aggregations  │    │ • Embeddings    │    │ • JSON Mode     │         │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘         │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATA LAYER                                      │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │    db/          │    │   knowledge/    │    │   workspace/    │         │
│  │                 │    │                 │    │                 │         │
│  │ • GST Rates     │    │ • GST Act PDFs  │    │ • User Excel    │         │
│  │ • MSME Limits   │    │ • Accounting    │    │ • User CSV      │         │
│  │ • State Codes   │    │   Standards     │    │ • Discovery     │         │
│  │ (Reference)     │    │ (RAG Source)    │    │   Metadata      │         │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘         │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Component Details

### 3.1 Orchestration Layer

#### Intent Router (`orchestration/router.py`)

Classifies user input into actionable intents:

| Intent | Trigger | Handler |
|--------|---------|---------|
| `FOLDER_ANALYSIS` | "analyze folder /path" | Discovery Agent |
| `COMPLIANCE_CHECK` | "run compliance", "audit" | Compliance Agent |
| `STRATEGIC_ANALYSIS` | "analyze vendors", "forecast" | Strategist Agent |
| `DATA_QUERY` | "what's my total sales" | DuckDB Query |
| `KNOWLEDGE_QUERY` | "what is ITC" | ChromaDB RAG |

```python
# Intent classification flow
user_input → pattern_match() → intent_type
           → llm_classify() (fallback)
           → ParsedIntent(type, confidence, extracted_data)
```

#### Agent Workflow (`orchestration/workflow.py`)

Coordinates multi-agent execution:

```python
class AgentWorkflow:
    def run(user_input):
        intent = router.route(user_input)
        
        if intent == FOLDER_ANALYSIS:
            return discovery_agent.discover(path)
        elif intent == COMPLIANCE_CHECK:
            return compliance_agent.run_full_audit()
        # ... etc
```

---

### 3.2 Agent Layer

#### Discovery Agent (`agents/discovery.py`)

**Purpose:** Transform raw Excel/CSV into structured, queryable data.

```
Input: Folder with unorganized files
       ├── Sales_2025.xlsx
       ├── purchases.csv
       └── HDFC_bank.xlsx

Process:
1. Scan each file
2. Extract headers + sample rows
3. Use LLM to classify sheet type
4. Map headers → Standard Data Model
5. Load into DuckDB
6. Save mapping to discovery_meta.json

Output: DuckDB tables + mapping metadata
```

**Standard Data Model (SDM):**

```python
class StandardInvoice:
    invoice_number: str
    invoice_date: date
    party_name: str
    party_gstin: str
    taxable_value: float
    cgst_amount: float
    sgst_amount: float
    total_value: float
```

---

#### Compliance Agent (`agents/compliance.py`)

**Purpose:** Identify tax leakages, compliance issues, and risks.

```
Checks Performed:
├── Tax Rate Verification
│   └── Compare charged rate vs GST 2025 slabs
├── ITC Eligibility
│   └── Check Section 17(5) blocked credits
├── Section 43B(h) Compliance
│   └── Flag payments >45 days to MSMEs
└── Reconciliation
    └── Sales vs Bank Credits (future)
```

**Output:**

```python
@dataclass
class ComplianceReport:
    issues: List[ComplianceIssue]
    total_tax_savings: float
    total_risk_amount: float
    summary: str
```

---

#### Strategist Agent (`agents/strategist.py`)

**Purpose:** Provide strategic financial insights.

```
Analysis Performed:
├── Vendor Analysis
│   ├── Reliability scoring
│   ├── MSME status check
│   └── Payment history
├── Cash Flow Forecast
│   ├── Historical pattern analysis
│   └── Tax liability projection
└── Profit Analysis
    └── Margin by product/service
```

---

### 3.3 Core Layer

#### Data Engine (`core/data_engine.py`)

**Technology:** DuckDB (in-process SQL database)

**Why DuckDB?**
- Treats Excel/CSV as SQL tables
- No server required
- Extremely fast for analytics
- Supports complex aggregations

```python
class DataEngine:
    def load_excel(file_path) → table_name
    def load_csv(file_path) → table_name
    def query(sql) → DataFrame
    def get_table_info(table) → Dict
```

---

#### Knowledge Base (`core/knowledge.py`)

**Technology:** ChromaDB (vector database)

**Purpose:** Store and retrieve GST rules for RAG.

```python
class KnowledgeBase:
    def add_document(text, metadata)
    def search(query, n_results) → List[Dict]
    def get_relevant_rules(query) → str
    def ingest_pdf(pdf_path)
```

**Embedding Model:** `BAAI/bge-large-en-v1.5` (1024 dimensions)

---

#### LLM Client (`llm/client.py`)

**Technology:** Ollama + Qwen2.5-7B-Instruct

```python
class LLMClient:
    def generate(prompt, system_prompt) → str
    def generate_json(prompt) → dict
    def is_available() → bool
```

**Configuration:**
- Temperature: 0.1 (factual responses)
- Max Tokens: 1024
- JSON Mode: Supported

---

### 3.4 Data Layer

#### Reference Data (`db/`)

| File | Purpose | Format |
|------|---------|--------|
| `gst_rates_2025.json` | Master GST data | JSON |
| `gst_rates/goods_rates_2025.csv` | HSN-wise goods rates | CSV |
| `gst_rates/services_rates_2025.csv` | SAC-wise service rates | CSV |
| `msme_classification.csv` | MSME thresholds | CSV |
| `state_codes.csv` | GST state codes | CSV |

#### Knowledge PDFs (`knowledge/`)

| Folder | Contents |
|--------|----------|
| `gst/` | CGST Act, CGST Rules, Notifications |
| `accounting/` | Ind AS, Financial Accounting, etc. |

#### User Data (`workspace/`)

User's Excel/CSV files for analysis. Each company can have its own subfolder.

---

## 4. Data Flow Diagrams

### 4.1 Folder Analysis Flow

```
User: "analyze folder ~/Documents/company/"
                    │
                    ▼
┌─────────────────────────────────────┐
│         Intent Router               │
│    intent = FOLDER_ANALYSIS         │
│    path = ~/Documents/company/      │
└─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────┐
│         Discovery Agent             │
│                                     │
│  1. Scan folder for Excel/CSV       │
│  2. For each file:                  │
│     a. Load into DuckDB             │
│     b. Extract headers              │
│     c. LLM classifies sheet type    │
│     d. Map headers to SDM           │
│  3. Create standardized views       │
│  4. Save discovery_meta.json        │
└─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────┐
│           DuckDB                    │
│                                     │
│  Tables:                            │
│  • sales_2025 (raw)                 │
│  • purchases (raw)                  │
│  • sdm_sales_register (view)        │
│  • sdm_purchase_ledger (view)       │
└─────────────────────────────────────┘
```

### 4.2 Compliance Check Flow

```
User: "run compliance check"
                    │
                    ▼
┌─────────────────────────────────────┐
│         Compliance Agent            │
│                                     │
│  1. Query DuckDB for transactions   │
│  2. For each transaction:           │
│     a. Check tax rate vs GST slabs  │
│     b. Check blocked credits        │
│     c. Check payment age (43B)      │
│  3. Query ChromaDB for rules        │
│  4. Aggregate issues                │
│  5. Calculate impact                │
└─────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
┌───────────────┐       ┌───────────────┐
│    DuckDB     │       │   ChromaDB    │
│  (User Data)  │       │  (GST Rules)  │
└───────────────┘       └───────────────┘
                    │
                    ▼
┌─────────────────────────────────────┐
│         Compliance Report           │
│                                     │
│  Issues: [...]                      │
│  Tax Savings: ₹X                    │
│  Risk Amount: ₹Y                    │
└─────────────────────────────────────┘
```

---

## 5. Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **LLM** | Qwen2.5-7B-Instruct | Reasoning, classification |
| **LLM Host** | Ollama | Local inference |
| **Data Engine** | DuckDB | Excel/CSV as SQL |
| **Vector DB** | ChromaDB | RAG for rules |
| **Embeddings** | bge-large-en-v1.5 | Semantic search |
| **Framework** | Python 3.10+ | Core language |
| **CLI** | Rich + Typer | Beautiful terminal UI |

---

## 6. Security & Privacy

### Data Locality
- **All processing happens locally**
- No data sent to external APIs
- Ollama runs on user's machine
- DuckDB is file-based

### Data Separation
- User data in `workspace/` (transient)
- Reference data in `db/` (versioned)
- Knowledge in `knowledge/` (static)

---

## 7. Extension Points

### Adding New Agents

```python
# agents/new_agent.py
class NewAgent:
    def __init__(self, data_engine, knowledge_base, llm_client):
        ...
    
    def run_analysis(self) -> Report:
        ...

# Register in orchestration/workflow.py
self.new_agent = NewAgent(...)
```

### Adding New Data Sources

```python
# core/data_engine.py
def load_google_sheets(url) -> str:
    ...

def load_tally_export(file_path) -> str:
    ...
```

### Adding New Compliance Rules

```python
# db/gst_rates/new_rules.csv
# Add CSV file with rule data

# agents/compliance.py
def check_new_rule(self) -> List[ComplianceIssue]:
    rules = load_new_rules()
    ...
```

---

## 8. File Structure Reference

```
ledgermind/
├── agents/                 # AI Agents
│   ├── __init__.py
│   ├── discovery.py        # Excel/CSV discovery
│   ├── compliance.py       # Tax compliance
│   └── strategist.py       # Strategic analysis
│
├── core/                   # Core infrastructure
│   ├── __init__.py
│   ├── data_engine.py      # DuckDB integration
│   ├── knowledge.py        # ChromaDB integration
│   ├── mapper.py           # Header mapping
│   └── schema.py           # Data models
│
├── orchestration/          # Workflow control
│   ├── __init__.py
│   ├── router.py           # Intent classification
│   └── workflow.py         # Agent coordination
│
├── llm/                    # LLM integration
│   ├── __init__.py
│   └── client.py           # Ollama client
│
├── db/                     # Reference data
│   ├── gst_rates_2025.json
│   ├── gst_rates/
│   ├── msme_classification.csv
│   └── state_codes.csv
│
├── knowledge/              # PDFs for RAG
│   ├── gst/
│   └── accounting/
│
├── workspace/              # User data
│   └── sample_company/
│
├── scripts/                # Utility scripts
│   └── scrape_gst_rates.py
│
├── docs/                   # Documentation
│   ├── ARCHITECTURE.md
│   └── ROADMAP.md
│
├── config.py               # Configuration
├── main.py                 # Entry point
├── requirements.txt        # Dependencies
└── README.md               # Overview
```

---

*Last Updated: January 2026*

