# LedgerMind - Technical Architecture

> Complete technical documentation for the Agentic AI CFO Platform

**Last Updated:** January 2026  
**Phase:** 1 (Foundation) ✅ Complete

---

## 1. System Overview

LedgerMind is an **autonomous financial intelligence platform** built on a multi-agent architecture. It transforms unstructured financial data (Excel/CSV) into actionable insights through specialized AI agents.

### Core Principles

1. **Agents over Chatbots** — Autonomous task execution, not just Q&A
2. **SQL over Embeddings for Data** — DuckDB for financial data, ChromaDB for rules only
3. **Local-First** — All processing on user's machine, $0 cloud cost
4. **Math Safety** — LLM reasons, Python/SQL calculates
5. **Proper Knowledge Routing** — Each knowledge layer serves its purpose

---

## 2. Knowledge Architecture

### The Three Knowledge Layers

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     KNOWLEDGE ARCHITECTURE                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  LAYER 1: REFERENCE DATA (Facts that change with policy)               │
│  ─────────────────────────────────────────────────────                 │
│  Source: db/*.csv, db/*.json                                           │
│  Purpose: Rate lookups, code validation, thresholds                    │
│  Examples: GST rates, MSME limits, state codes                         │
│                                                                         │
│  → Queried via: Direct CSV/JSON lookup                                 │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  LAYER 2: LEGAL KNOWLEDGE (Rules, procedures, sections)                │
│  ───────────────────────────────────────────────────────               │
│  Source: ChromaDB (from PDFs in knowledge/)                            │
│  Purpose: RAG for specific legal questions                             │
│  Examples: CGST Act, Rules, Notifications                              │
│                                                                         │
│  → Queried via: ChromaDB semantic search                               │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  LAYER 3: FOUNDATIONAL KNOWLEDGE (What the LLM already knows)          │
│  ────────────────────────────────────────────────────────              │
│  Source: LLM training data                                              │
│  Purpose: Definitions, concepts, explanations                          │
│  Examples: "What is CGST?", "How does ITC work?"                       │
│                                                                         │
│  → Queried via: LLM without context restriction                        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Query Classification & Routing

```
User Question
     │
     ▼
┌────────────────────────────────────────────────────────────┐
│              QUERY CLASSIFIER                              │
│              (core/query_classifier.py)                    │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  "What is CGST?"        → DEFINITION    → LLM (Layer 3)   │
│  "GST rate on milk?"    → RATE_LOOKUP   → CSV (Layer 1)   │
│  "Due date for GSTR-3B" → LEGAL_RULE    → ChromaDB (L2)   │
│  "My total sales?"      → DATA_QUERY    → DuckDB          │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## 3. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER INTERFACE                                  │
│                         (CLI / Future: Web UI)                              │
│                              main.py                                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ORCHESTRATION LAYER                                │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │  Intent Router  │───▶│ Query Classifier│───▶│  Agent Workflow │         │
│  │   (router.py)   │    │  (classifier.py)│    │  (workflow.py)  │         │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘         │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AGENT LAYER                                     │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │   DISCOVERY     │    │   COMPLIANCE    │    │   STRATEGIST    │         │
│  │   (discovery.py)│    │  (compliance.py)│    │  (strategist.py)│         │
│  │                 │    │                 │    │                 │         │
│  │ • File scanning │    │ • Tax rate      │    │ • Vendor        │         │
│  │ • Header map    │    │   verification  │    │   analysis      │         │
│  │ • Schema create │    │ • ITC checks    │    │ • Cash flow     │         │
│  │ • Type detect   │    │ • 43B(h) check  │    │ • Forecasting   │         │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘         │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CORE LAYER                                      │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │   DATA ENGINE   │    │  KNOWLEDGE BASE │    │   LLM CLIENT    │         │
│  │  (data_engine)  │    │  (knowledge.py) │    │   (client.py)   │         │
│  │                 │    │                 │    │                 │         │
│  │ • DuckDB        │    │ • ChromaDB      │    │ • Ollama        │         │
│  │ • Excel → SQL   │    │ • RAG retrieval │    │ • Qwen 7B       │         │
│  │ • Query engine  │    │ • PDF ingestion │    │ • JSON mode     │         │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘         │
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │   GUARDRAILS    │    │    METRICS      │    │ QUERY CLASSIFIER│         │
│  │ (guardrails.py) │    │  (metrics.py)   │    │ (classifier.py) │         │
│  │                 │    │                 │    │                 │         │
│  │ • GSTIN check   │    │ • Performance   │    │ • Route queries │         │
│  │ • Tax math      │    │ • Compliance    │    │ • Detect type   │         │
│  │ • LLM safety    │    │ • Tracking      │    │ • Extract info  │         │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘         │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATA LAYER                                      │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │    db/          │    │   knowledge/    │    │   workspace/    │         │
│  │ (Reference Data)│    │ (PDFs for RAG)  │    │ (User's Data)   │         │
│  │                 │    │                 │    │                 │         │
│  │ • GST rates CSV │    │ • CGST Act PDF  │    │ • Excel files   │         │
│  │ • MSME limits   │    │ • CGST Rules    │    │ • CSV files     │         │
│  │ • State codes   │    │ • Accounting    │    │ • Discovery     │         │
│  │ • Blocked ITC   │    │   standards     │    │   metadata      │         │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘         │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Complete File Structure

### Directory Overview

```
ledgermind/
├── 🎯 main.py                      # Entry point - CLI interface
├── ⚙️  config.py                    # Configuration and settings
├── 📋 requirements.txt             # Python dependencies
│
├── 🤖 agents/                      # AI Agents (business logic)
│   ├── __init__.py
│   ├── discovery.py                # File discovery & schema mapping
│   ├── compliance.py               # Tax compliance checks
│   └── strategist.py               # Strategic analysis
│
├── ⚙️  core/                        # Core infrastructure
│   ├── __init__.py
│   ├── data_engine.py              # DuckDB integration
│   ├── knowledge.py                # ChromaDB RAG
│   ├── query_classifier.py         # Query routing (NEW)
│   ├── guardrails.py               # Safety validations
│   ├── metrics.py                  # Performance tracking
│   ├── schema.py                   # Data models (SDM)
│   └── mapper.py                   # Header mapping logic
│
├── 🔀 orchestration/               # Workflow control
│   ├── __init__.py
│   ├── router.py                   # Intent classification
│   └── workflow.py                 # Agent coordination
│
├── 🧠 llm/                         # LLM integration
│   ├── __init__.py
│   └── client.py                   # Ollama client
│
├── 📊 db/                          # Reference data (Layer 1)
│   ├── gst_rates_2025.json         # Master GST data
│   ├── gst_rates/
│   │   ├── goods_rates_2025.csv    # HSN → rate mapping
│   │   ├── services_rates_2025.csv # SAC → rate mapping
│   │   └── blocked_credits_17_5.csv# Section 17(5) items
│   ├── msme_classification.csv     # MSME thresholds
│   └── state_codes.csv             # GST state codes
│
├── 📚 knowledge/                   # PDFs for RAG (Layer 2)
│   ├── gst/
│   │   ├── a2017-12.pdf            # CGST Act 2017
│   │   └── 01062021-cgst-rules...  # CGST Rules
│   └── accounting/                 # Accounting standards
│
├── 📂 workspace/                   # User data
│   └── sample_company/             # Sample test data
│
├── 🔧 scripts/                     # Utility scripts
│   ├── create_sample_data.py       # Generate test data
│   ├── ingest_knowledge.py         # Populate ChromaDB
│   └── scrape_gst_rates.py         # Update GST rates
│
├── 📖 docs/                        # Documentation
│   ├── ARCHITECTURE.md             # This file
│   └── ROADMAP.md                  # Development plan
│
├── 🗄️  chroma_db/                   # ChromaDB storage
└── 🦆 ledgermind.duckdb            # DuckDB database
```

---

## 5. File Descriptions (What & Why)

### Entry Points

| File | Purpose | Why It Exists |
|------|---------|---------------|
| `main.py` | CLI entry point | User interacts with system here |
| `config.py` | Central configuration | Single source for all settings |

### Agents (`agents/`)

| File | Purpose | Why It Exists |
|------|---------|---------------|
| `discovery.py` | Reads Excel/CSV, maps to standard schema | MSMEs have messy, inconsistent files |
| `compliance.py` | Checks tax compliance issues | Core value - find savings/risks |
| `strategist.py` | Vendor analysis, cash flow forecasting | Strategic business insights |

### Core Infrastructure (`core/`)

| File | Purpose | Why It Exists |
|------|---------|---------------|
| `data_engine.py` | DuckDB wrapper - Excel as SQL | Fast analytics on user's financial data |
| `knowledge.py` | ChromaDB wrapper - RAG for rules | Legal questions need document search |
| `query_classifier.py` | Routes queries to correct source | **Each knowledge layer serves its purpose** |
| `guardrails.py` | Validation & safety checks | Prevent bad data, LLM hallucinations |
| `metrics.py` | Performance & compliance tracking | Monitor system health |
| `schema.py` | Standard Data Model definitions | Normalize different Excel formats |
| `mapper.py` | Header mapping logic | Map "Inv. No." → "invoice_number" |

### Orchestration (`orchestration/`)

| File | Purpose | Why It Exists |
|------|---------|---------------|
| `router.py` | Classify user intent | "analyze folder" vs "what is GST" |
| `workflow.py` | Coordinate agents | Right agent for right task |

### LLM (`llm/`)

| File | Purpose | Why It Exists |
|------|---------|---------------|
| `client.py` | Ollama/Qwen wrapper | Local LLM, no cloud dependency |

### Reference Data (`db/`)

| File | Purpose | Why It Exists |
|------|---------|---------------|
| `gst_rates_2025.json` | Master GST data | Central source for rates |
| `goods_rates_2025.csv` | HSN codes → rates | Look up rate by product |
| `services_rates_2025.csv` | SAC codes → rates | Look up rate by service |
| `blocked_credits_17_5.csv` | Section 17(5) list | ITC eligibility check |
| `msme_classification.csv` | MSME thresholds | Section 43B(h) checks |
| `state_codes.csv` | GST state codes | GSTIN validation |

### Scripts (`scripts/`)

| File | Purpose | Why It Exists |
|------|---------|---------------|
| `create_sample_data.py` | Generate test Excel/CSV | Testing without real data |
| `ingest_knowledge.py` | Populate ChromaDB | Load PDFs for RAG |
| `scrape_gst_rates.py` | Update rates from official source | Keep rates current |

---

## 6. Guardrails System

### Current Guardrails (10 Methods)

| Guardrail | What It Does | When Used |
|-----------|--------------|-----------|
| `validate_gstin` | Check GSTIN format & checksum | All transactions |
| `validate_hsn_code` | Check HSN code format (4/6/8 digits) | Rate lookups |
| `validate_invoice_number` | Check invoice format | Data ingestion |
| `validate_date` | Check date validity | All date fields |
| `validate_amount` | Check amount is positive, reasonable | All amounts |
| `validate_tax_calculation` | Verify CGST+SGST=Total | Tax fields |
| `validate_itc_time_limit` | Check ITC not expired | ITC claims |
| `validate_section_43b_h` | Check MSME payment deadline | Vendor payments |
| `validate_llm_response_no_math` | Ensure LLM doesn't do arithmetic | LLM outputs |
| `validate_llm_response_has_citation` | Check LLM cites sources | Legal answers |

### Guardrail Categories

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         GUARDRAILS SYSTEM                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. INPUT VALIDATION                                                    │
│     • GSTIN format check                                                │
│     • HSN/SAC code validation                                           │
│     • Invoice number format                                             │
│     • Date validity                                                     │
│                                                                         │
│  2. DATA QUALITY                                                        │
│     • Amount bounds checking                                            │
│     • Tax calculation consistency                                       │
│     • Missing field detection                                           │
│                                                                         │
│  3. LLM SAFETY                                                          │
│     • No arithmetic in responses (math safety)                          │
│     • Citation required for rules                                       │
│     • Confidence scoring                                                │
│                                                                         │
│  4. BUSINESS RULES                                                      │
│     • ITC time limits (Section 16(4))                                   │
│     • Section 43B(h) - 45 day payment                                   │
│     • Section 17(5) - blocked credits                                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Data Flow Diagrams

### Knowledge Query Flow

```
User: "What is CGST?"
         │
         ▼
┌────────────────────────────┐
│ Intent Router              │
│ → KNOWLEDGE_QUERY          │
└────────────────────────────┘
         │
         ▼
┌────────────────────────────┐
│ Query Classifier           │
│ → Type: DEFINITION         │
│ → Source: LLM (Layer 3)    │
└────────────────────────────┘
         │
         ▼
┌────────────────────────────┐
│ LLM (No context restrict)  │
│ Use general knowledge      │
└────────────────────────────┘
         │
         ▼
┌────────────────────────────┐
│ Response: "CGST is the     │
│ Central Goods and Services │
│ Tax collected by..."       │
└────────────────────────────┘
```

### Rate Lookup Flow

```
User: "GST rate on milk?"
         │
         ▼
┌────────────────────────────┐
│ Query Classifier           │
│ → Type: RATE_LOOKUP        │
│ → Source: CSV (Layer 1)    │
│ → Item: "milk"             │
└────────────────────────────┘
         │
         ▼
┌────────────────────────────┐
│ CSV Lookup                 │
│ goods_rates_2025.csv       │
│ → HSN: 0401                │
│ → Rate: 0%                 │
└────────────────────────────┘
         │
         ▼
┌────────────────────────────┐
│ LLM formats response       │
│ with context               │
└────────────────────────────┘
         │
         ▼
┌────────────────────────────┐
│ Response: "Fresh milk is   │
│ GST exempt (0%)..."        │
└────────────────────────────┘
```

---

## 8. Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **LLM** | Qwen2.5-7B-Instruct | Reasoning, classification |
| **LLM Host** | Ollama | Local inference, no cloud |
| **Data Engine** | DuckDB | Excel/CSV as SQL, analytics |
| **Vector DB** | ChromaDB | RAG for legal documents |
| **Embeddings** | Default (ChromaDB) | Semantic search |
| **Framework** | Python 3.10+ | Core language |
| **CLI** | Rich | Beautiful terminal UI |

---

## 9. Security & Privacy

### Data Locality
- **100% local processing** — No data leaves the machine
- Ollama runs locally
- DuckDB is file-based
- ChromaDB persists to local disk

### Data Separation
- `workspace/` — User data (transient, per-company)
- `db/` — Reference data (versioned, shared)
- `knowledge/` — Legal PDFs (static, shared)
- `chroma_db/` — Indexed knowledge (regeneratable)

---

## 10. Current Status

### Phase 1 Complete ✅

| Component | Status | Test Result |
|-----------|--------|-------------|
| DuckDB Data Engine | ✅ | Connected, 3 tables |
| ChromaDB Knowledge | ✅ | 1,276 chunks |
| Query Classifier | ✅ | 4 types classified correctly |
| Guardrails | ✅ | 10 validation methods |
| 3 Agents | ✅ | All import successfully |
| LLM Client | ✅ | Ollama connected |
| Reference Data | ✅ | 89 goods, 50 services |

### Test Command

```bash
python -c "
from core.query_classifier import QueryClassifier
c = QueryClassifier()
print(c.classify('What is CGST?'))  # → definition, llm
print(c.classify('GST rate on milk?'))  # → rate_lookup, csv
"
```

---

*Last Updated: January 2026*
