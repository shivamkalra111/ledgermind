# LedgerMind

**Agentic AI CFO for MSMEs** — Transform messy financial data into actionable insights.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status: Phase 1](https://img.shields.io/badge/status-Phase%201-orange.svg)]()

---

## What is LedgerMind?

LedgerMind is an **autonomous AI platform** that analyzes your company's Excel/CSV financial data and provides:

- 🔍 **Tax Savings** — Find overpaid GST, wrong tax rates
- ⚠️ **Compliance Alerts** — Section 43B(h), blocked credits, ITC issues
- 📊 **Strategic Insights** — Vendor rankings, cash flow forecasts
- 💬 **Natural Language Queries** — Ask questions about your data or GST rules

**100% Local** — All processing happens on your machine. Your data never leaves.

---

## Current Status

### What's Built

| Component | Status | File |
|-----------|--------|------|
| **Data Engine** | ✅ Built | `core/data_engine.py` |
| **Guardrails** | ✅ Built | `core/guardrails.py` |
| **Metrics** | ✅ Built | `core/metrics.py` |
| **Schema (SDM)** | ✅ Built | `core/schema.py` |
| **Header Mapper** | ✅ Built | `core/mapper.py` |
| **Knowledge Base** | ✅ Built | `core/knowledge.py` |
| **LLM Client** | ✅ Built | `llm/client.py` |
| **Discovery Agent** | ✅ Built | `agents/discovery.py` |
| **Compliance Agent** | ✅ Built | `agents/compliance.py` |
| **Strategist Agent** | ✅ Built | `agents/strategist.py` |
| **Workflow Orchestrator** | ✅ Built | `orchestration/workflow.py` |
| **Intent Router** | ✅ Built | `orchestration/router.py` |
| **GST Rate Database** | ✅ Built | `db/gst_rates/*.csv` |
| **Sample Data** | ✅ Built | `workspace/sample_company/` |

### What's Needed to Run

| Requirement | Purpose |
|-------------|---------|
| **Python 3.10+** | Runtime |
| **Ollama** | Local LLM server |
| **qwen2.5:7b-instruct** | LLM model |

---

## Quick Start

### 1. Install Dependencies

```bash
cd ledgermind
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Start Ollama (Optional for full features)

```bash
# Install Ollama (if not installed)
curl -fsSL https://ollama.com/install.sh | sh

# Pull model
ollama pull qwen2.5:7b-instruct

# Start server
ollama serve
```

### 3. Run

```bash
python main.py
```

---

## Project Structure

```
ledgermind/
├── agents/                    # AI Agents
│   ├── discovery.py           # Scans Excel/CSV, maps headers
│   ├── compliance.py          # Tax checks, 43B(h), blocked credits
│   └── strategist.py          # Vendor ranking, cash flow
├── core/                      # Core Infrastructure
│   ├── data_engine.py         # DuckDB integration
│   ├── guardrails.py          # Input validation, safety
│   ├── metrics.py             # Performance tracking
│   ├── schema.py              # Standard Data Model
│   ├── mapper.py              # Header mapping
│   └── knowledge.py           # ChromaDB/RAG
├── orchestration/             # Agent Coordination
│   ├── router.py              # Intent classification
│   └── workflow.py            # Agent workflow
├── llm/                       # LLM Integration
│   └── client.py              # Ollama client
├── db/                        # Reference Data (CSV/JSON)
│   ├── gst_rates/             # HSN/SAC rates
│   ├── gst_rates_2025.json    # Master GST data
│   ├── msme_classification.csv
│   └── state_codes.csv
├── knowledge/                 # PDFs for RAG
│   ├── gst/                   # GST Act, Rules
│   └── accounting/            # Accounting books
├── workspace/                 # User Data
│   └── sample_company/        # Sample Excel/CSV files
├── docs/                      # Documentation
│   ├── ARCHITECTURE.md        # Technical design
│   └── ROADMAP.md             # Development plan
├── scripts/                   # Utilities
│   ├── create_sample_data.py  # Generate test data
│   └── ingest_knowledge.py    # Populate ChromaDB
├── main.py                    # Entry point
├── config.py                  # Configuration
└── requirements.txt           # Dependencies
```

---

## Verification Tests

Quick checks to verify the build:

```bash
# 1. Check dependencies install
pip install -r requirements.txt

# 2. Check config loads GST rates
python -c "from config import load_goods_rates; print(f'Goods rates: {len(load_goods_rates())} items')"

# 3. Check guardrails work
python -c "from core.guardrails import Guardrails; g = Guardrails(); print('GSTIN valid:', g.validate_gstin('27AAPFU0939F1ZV'))"

# 4. Check sample data exists
ls workspace/sample_company/

# 5. Run main (requires Ollama for full features)
python main.py
```

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| **LLM** | Qwen2.5-7B via Ollama |
| **Data Engine** | DuckDB |
| **Knowledge Base** | ChromaDB |
| **Embeddings** | bge-large-en-v1.5 |
| **Agent Framework** | LangGraph |

---

## GST 2025 Reference Data

Based on **56th GST Council Meeting (Sept 2025)**:

| Slab | Rate | Items |
|------|------|-------|
| Exempt | 0% | Fresh food, health insurance |
| Merit | 5% | FMCG, packaged food, medicines |
| Standard | 18% | Electronics, services |
| Luxury | 28%+ | Tobacco, luxury cars |

**Database:** 89 goods + 50 services in `db/gst_rates/`

---

## Development Roadmap

```
┌─────────────────────────────────────────────────────────────┐
│  Phase 1 (NOW)    Phase 2         Phase 3         Phase 4   │
│  FOUNDATION       COMPLIANCE      INTELLIGENCE    PRODUCTION│
│                                                             │
│  ■■■■■□□□        □□□□□□□□       □□□□□□□□       □□□□□□□□   │
│  ~70%             0%              0%              0%        │
└─────────────────────────────────────────────────────────────┘
```

### Phase 1 Progress

- [x] Project structure
- [x] DuckDB integration
- [x] ChromaDB setup
- [x] 3 Agent framework
- [x] GST rate database
- [x] Guardrails & Metrics
- [x] Sample data
- [ ] **Integration testing** ← Next
- [ ] Knowledge base population (PDFs)

### Upcoming Phases

| Phase | Key Deliverables |
|-------|------------------|
| **Phase 2** | Tax rate verification, ITC reconciliation, 43B(h) monitoring |
| **Phase 3** | Vendor scoring, MSME verification, cash flow ML |
| **Phase 4** | Web UI, PDF reports, REST API |

---

## Documentation

- [ARCHITECTURE.md](docs/ARCHITECTURE.md) — Technical design, data flows
- [ROADMAP.md](docs/ROADMAP.md) — Detailed milestones

---

**Built with ❤️ for Indian MSMEs**
