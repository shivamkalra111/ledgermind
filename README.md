# LedgerMind

**Agentic AI CFO for MSMEs** — Transform messy financial data into actionable insights.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status: Development](https://img.shields.io/badge/status-development-orange.svg)]()

---

## What is LedgerMind?

LedgerMind is an **autonomous AI platform** that analyzes your company's Excel/CSV financial data and provides:

- 🔍 **Tax Savings** — Find overpaid GST, wrong tax rates
- ⚠️ **Compliance Alerts** — Section 43B(h), blocked credits, ITC issues
- 📊 **Strategic Insights** — Vendor rankings, cash flow forecasts
- 💬 **Natural Language Queries** — Ask questions about your data or GST rules

**100% Local** — All processing happens on your machine. Your data never leaves.

---

## Quick Start

### Prerequisites

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull the model
ollama pull qwen2.5:7b-instruct

# Start Ollama (keep running)
ollama serve
```

### Installation

```bash
git clone <repo-url>
cd ledgermind

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### Run

```bash
# Interactive mode
python main.py

# Analyze a folder
python main.py "analyze folder /path/to/your/excels/"

# Ask a question
python main.py "What is the ITC time limit?"
```

---

## How It Works

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Your Excel/CSV │────▶│   AI Agents     │────▶│  Insights       │
│  Files          │     │                 │     │                 │
│                 │     │  • Discovery    │     │  • Tax Savings  │
│  • Sales        │     │  • Compliance   │     │  • Compliance   │
│  • Purchases    │     │  • Strategist   │     │  • Forecasts    │
│  • Bank         │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
     DuckDB               ChromaDB + LLM          Actionable
   (Your Data)            (GST Rules)             Reports
```

### Three AI Agents

| Agent | Purpose |
|-------|---------|
| **Discovery** | Scans your Excel/CSV files, maps headers, loads into queryable database |
| **Compliance** | Checks tax rates, ITC eligibility, Section 43B(h), blocked credits |
| **Strategist** | Ranks vendors, forecasts cash flow, analyzes profit margins |

---

## Example Usage

### 1. Analyze Your Data

```bash
python main.py
> analyze folder ~/Documents/MyCompany/

📁 Folder Analysis Complete
Files Found: 3
Tables Created: sales_2025, purchases, bank_statement

✅ Data loaded! You can now run compliance checks.
```

### 2. Run Compliance Check

```bash
> run compliance check

📋 Compliance Audit Summary

Issues Found: 5
🔴 Critical: 2
🟡 Warnings: 3

Financial Impact:
• Potential Tax Savings: ₹12,400
• Amount at Risk: ₹45,000

⚠️ Payment to ABC Traders overdue by 12 days — Section 43B(h) risk
```

### 3. Ask Questions

```bash
> What's my total sales this quarter?
Query: SELECT SUM(total_value) FROM sales WHERE ...
Results: ₹24,50,000

> What is Section 17(5)?
Section 17(5) of CGST Act lists items where ITC cannot be claimed...
```

---

## Project Structure

```
ledgermind/
├── agents/           # AI Agents (Discovery, Compliance, Strategist)
├── core/             # Data Engine (DuckDB), Knowledge Base (ChromaDB)
├── orchestration/    # Workflow coordination, Intent routing
├── llm/              # Ollama/Qwen integration
├── db/               # Reference data (GST rates, MSME limits)
├── knowledge/        # PDFs for RAG (GST Act, Accounting)
├── workspace/        # Your company data (Excel/CSV)
├── docs/             # Technical documentation
├── main.py           # Entry point
└── config.py         # Configuration
```

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| **LLM** | Qwen2.5-7B via Ollama (local) |
| **Data Engine** | DuckDB (Excel as SQL) |
| **Knowledge Base** | ChromaDB (RAG for rules) |
| **Embeddings** | bge-large-en-v1.5 |

---

## GST 2025 Ready

Based on **September 2025 GST reforms** (56th GST Council Meeting):

| Slab | Rate | Examples |
|------|------|----------|
| Exempt | 0% | Fresh food, health insurance, education |
| Merit | 5% | FMCG, packaged food, medicines |
| Standard | 18% | Electronics, services, construction |
| Luxury | 28%+ | Tobacco, aerated drinks, luxury cars |

---

## Documentation

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Technical architecture, data flows, component details |
| [ROADMAP.md](docs/ROADMAP.md) | Development phases, milestones, success criteria |

---

## Development Plan

### Phase Overview

```
Phase 1           Phase 2           Phase 3           Phase 4
FOUNDATION        COMPLIANCE        INTELLIGENCE      PRODUCTION
[2 weeks]         [3 weeks]         [3 weeks]         [2 weeks]

┌─────────┐       ┌─────────┐       ┌─────────┐       ┌─────────┐
│ DuckDB  │       │ Tax     │       │ Vendor  │       │ Web UI  │
│ ChromaDB│──────▶│ Checks  │──────▶│ Scoring │──────▶│ Reports │
│ Agents  │       │ ITC/43B │       │ Forecast│       │ API     │
└─────────┘       └─────────┘       └─────────┘       └─────────┘

◀─── WE ARE HERE
```

---

## Current Status: Phase 1 (Foundation)

### ✅ Completed

| Component | Status | Details |
|-----------|--------|---------|
| **Project Architecture** | ✅ Done | Multi-agent structure, orchestration layer |
| **DuckDB Integration** | ✅ Done | Excel/CSV → SQL tables |
| **ChromaDB Setup** | ✅ Done | Vector DB for RAG |
| **LLM Client** | ✅ Done | Ollama/Qwen integration |
| **Discovery Agent** | ✅ Done | Header mapping, sheet detection |
| **Compliance Agent** | ✅ Done | Tax checks, 43B(h), blocked credits |
| **Strategist Agent** | ✅ Done | Vendor ranking, cash flow |
| **GST Rate Database** | ✅ Done | 89 goods + 50 services (Sept 2025) |
| **Intent Router** | ✅ Done | Query classification |
| **CLI Interface** | ✅ Done | Interactive mode |

### 🔄 In Progress

| Task | Status | Notes |
|------|--------|-------|
| End-to-end testing | 🔄 | Test with real Excel files |
| PDF ingestion | 🔄 | Ingest GST PDFs to ChromaDB |
| Bug fixes | 🔄 | Runtime error handling |

### 📋 Upcoming (Phase 2-4)

| Phase | Key Features |
|-------|--------------|
| **Phase 2: Compliance** | Full tax rate verification, HSN/SAC lookup, ITC reconciliation, compliance reports |
| **Phase 3: Intelligence** | Vendor MSME verification, cash flow ML model, profit analysis, recommendations |
| **Phase 4: Production** | Web UI, PDF reports, API endpoints, multi-company support |

---

## Roadmap Summary

### Phase 1: Foundation ← **Current**
- [x] Project structure & architecture
- [x] DuckDB (Excel as SQL)
- [x] ChromaDB (GST rules RAG)
- [x] 3 Agent framework
- [x] GST 2025 rate database
- [ ] Integration testing
- [ ] Knowledge base population

### Phase 2: Compliance Engine
- [ ] Tax rate verification (HSN/SAC)
- [ ] ITC eligibility checker
- [ ] Section 17(5) detection
- [ ] Section 43B(h) monitoring
- [ ] Compliance report generation

### Phase 3: Strategic Intelligence
- [ ] Vendor reliability scoring
- [ ] MSME vendor identification
- [ ] Cash flow forecasting
- [ ] Profit margin analysis
- [ ] Actionable recommendations

### Phase 4: Production
- [ ] Web UI (FastAPI + Frontend)
- [ ] PDF/Excel report export
- [ ] REST API
- [ ] Multi-company support
- [ ] Deployment package

See [ROADMAP.md](docs/ROADMAP.md) for detailed technical milestones.

---

## Contributing

This is an active development project. Contributions welcome!

---

## License

MIT License — See LICENSE file.

---

**Built with ❤️ for Indian MSMEs**
