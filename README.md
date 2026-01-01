# LedgerMind: LLM-Powered GST Compliance Assistant

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status: Phase 1 Complete](https://img.shields.io/badge/status-Phase%201%20Complete-green.svg)]()

> Building towards a Tally-like accounting software with intelligent LLM assistance. Currently: Production-ready GST compliance Q&A assistant using RAG with local LLMs.

---

## 🎯 Vision & Current Focus

**Long-term Vision:** Full accounting software (like Tally) with integrated AI that can:
- Answer compliance questions naturally
- Analyze your accounting data
- Validate transactions against rules
- Auto-fill forms and generate reports
- Provide intelligent recommendations

**Current Focus (Phase 1):** Build and perfect the **LLM Assistant foundation**
- ✅ RAG-powered GST Q&A system
- 🔄 Optimize to >85% accuracy
- 📊 Validate with comprehensive testing

**Why This Order?** Master the AI/RAG layer first before adding accounting complexity. A bad LLM assistant on top of accounting data = bad product. A great LLM assistant = solid foundation for future features.

---

## 🚀 What Works Right Now

```bash
$ python main.py "What is Input Tax Credit?"

Answer: Input Tax Credit (ITC) is the tax paid on purchases which can 
be set off against the tax payable on sales. To claim ITC, you must:
1. Possess a valid tax invoice
2. Have received the goods/services
3. Tax must be paid to the government
4. Returns must be filed [Source: CGST Act, Section 16, Page 42]

Confidence: 62% | Faithfulness: 88% | Time: 2.3s
```

**Features:**
- 🗣️ Natural language GST questions
- 🔍 Retrieves from official documents (294 pages, 855 chunks)
- ✅ Cites sources (document + page)
- 📊 Tracks performance metrics
- 🔒 100% local, no API costs
- 🧪 50-question automated test suite

---

## 🗺️ Development Roadmap

### ✅ **Phase 1: LLM Assistant Core** (COMPLETE)
**Goal:** Build reliable GST Q&A system  
**Status:** Functional, needs optimization (60-75% pass rate → target 85%)

**Completed:**
- [x] RAG pipeline with ChromaDB
- [x] Local LLM (Qwen2.5-7B via Ollama)
- [x] 294 pages GST documents ingested
- [x] Semantic chunking (structure-aware)
- [x] Metrics system (confidence, faithfulness, relevance)
- [x] 50-question test suite
- [x] Document coverage verification (88%)

**Current Work (Week 1-2):**
- [ ] Optimize response time (18s → <5s)
- [ ] Improve system prompt (reduce verbosity)
- [ ] Tune retrieval parameters
- [ ] Reach >85% pass rate
- [ ] Collect human feedback

---

### 🔄 **Phase 2: Accounting Data Layer** (NEXT - Month 2-3)
**Goal:** Add accounting database so LLM can analyze YOUR data

**What We'll Build:**
```
Current:  User asks "What is ITC?" → LLM answers from rules
Next:     User asks "What's my ITC this month?" → LLM queries YOUR data + rules
```

**Components:**
1. **Database Schema**
   - Customers, Vendors, Products
   - Invoices (sales/purchase)
   - Transactions, Ledgers
   - GST-specific fields (GSTIN, HSN, tax rates)

2. **API Layer**
   ```python
   # Simple functions LLM can use
   get_monthly_itc(month) → Returns ITC summary
   get_invoice(id) → Returns invoice details
   check_supplier_compliance(supplier_id) → Check if filed GSTR
   ```

3. **LLM Integration**
   ```python
   # LLM can now answer data-specific questions
   Q: "Why is my ITC only 50k this month?"
   → LLM calls get_monthly_itc()
   → Finds supplier ABC hasn't filed GSTR-1
   → Explains with rule: Section 16(2) - ITC blocked
   ```

**Timeline:** 2-3 months  
**Complexity:** Medium (standard CRUD + SQL)

---

### 🎯 **Phase 3: Function Calling / Tool Use** (Month 4-5)
**Goal:** LLM can perform actions, not just answer questions

**Architecture Decision:** **Function Calling (NOT Agentic System)**

**Why Function Calling?**
- ✅ Simpler to build and maintain
- ✅ More predictable and debuggable
- ✅ LLM stays in control
- ✅ Sufficient for 80% of accounting tasks
- ✅ Natively supported by Qwen2.5

**What We'll Build:**
```python
# Define tools LLM can use
tools = [
    "get_itc_summary(month)",
    "create_invoice(customer, items, amount)",
    "validate_transaction(transaction_id)",
    "check_gst_compliance(period)",
    "generate_gstr1(month)"
]

# Example interaction:
User: "Create invoice for ABC Corp, 100k software services, Maharashtra"

LLM thinks:
  1. Software services → HSN 998314
  2. Maharashtra (intrastate) → CGST 9% + SGST 9%
  3. Need: Customer ID, calculate tax
  
LLM calls: create_invoice({
    customer: "ABC Corp",
    items: [{name: "Software", hsn: "998314", amount: 100000}],
    cgst: 9000, sgst: 9000,
    place_of_supply: "Maharashtra"
})

Result: Invoice #INV-001 created ✅
```

**Timeline:** 1-2 months  
**Complexity:** Medium

---

### 🏗️ **Phase 4: Web UI & Polish** (Month 6-7)
**Goal:** Make it usable for end users

**Components:**
- Web interface (Streamlit or FastAPI + React)
- Dashboard (revenue, GST liability, ITC summary)
- Forms (invoice creation, transaction entry)
- Reports (GSTR-1, P&L, Balance Sheet)
- User feedback system

---

### 🚀 **Phase 5: Advanced Features** (Month 8+)
**Only if needed:**
- Multi-company support
- Inventory management
- E-invoicing integration
- Banking integration
- Mobile app
- **Agentic workflows** (for very complex multi-step tasks)

---

## 🤔 Why NOT Agentic System (Yet)?

**What are Agents?**
- Multiple AI "agents" that communicate
- Each has specialized role
- Autonomous decision-making
- Complex orchestration

**Why NOT now:**
1. **Don't have accounting data yet** - Agents need data to analyze
2. **Overkill for most tasks** - Accounting is mostly deterministic
3. **Harder to debug** - Multiple agents = complex interactions
4. **Function calling is enough** - Covers 80% of use cases

**When Agents Make Sense:**
- Complex multi-step workflows (GST audit preparation)
- Uncertain number of steps
- Multiple specialized domains
- Exploratory analysis

**Our Approach:** Start simple (functions), add agents only if genuinely needed.

---

## 🛠️ Tech Stack

| Component | Technology | Why? |
|-----------|-----------|------|
| **LLM** | Qwen2.5-7B-Instruct (Ollama) | Best reasoning, function calling support |
| **Embeddings** | bge-large-en-v1.5 (1024-dim) | Optimized for legal/formal text |
| **Vector DB** | ChromaDB (persistent) | Fast, local, simple |
| **Database** | PostgreSQL (future) | ACID, reliable for financial data |
| **Backend** | Python + FastAPI (future) | Fast, modern, async |
| **Frontend** | React/Streamlit (future) | TBD based on user needs |

**Principles:**
- ✅ Open-source first
- ✅ Privacy by default (local execution)
- ✅ No vendor lock-in
- ✅ Production-grade tools

---

## 📊 Current Performance

**Metrics (from real usage):**
- **Success Rate:** 100% (queries return answers)
- **Avg Response Time:** 18.2s (⚠️ needs optimization → target <5s)
- **Avg Confidence:** 36% (⚠️ needs improvement → target >45%)
- **Document Coverage:** 88% of test questions answerable
- **Pass Rate:** 60-75% (⚠️ optimizing to >85%)

**Known Issues:**
- Generation too slow (LLM taking 18s average)
- Responses too verbose (2000+ chars)
- Some queries have low confidence

**Active Optimizations:**
- Reduce `LLM_MAX_TOKENS` (512→256) for speed
- Improve system prompt for concise answers
- Tune retrieval parameters
- Add query expansion for GST terms

---

## 🚀 Quick Start

### Prerequisites
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull LLM model (~5GB)
ollama pull qwen2.5:7b-instruct
```

### Setup
```bash
# 1. Clone and install
git clone https://github.com/yourusername/ledgermind.git
cd ledgermind
pip install -r requirements.txt

# 2. Ingest documents (one-time, ~2-3 min)
python scripts/ingest_pdfs.py

# 3. Start Ollama (keep running in background)
ollama serve
```

### Run
```bash
# Interactive mode
python main.py

# Single question
python main.py "What is Input Tax Credit?"

# View performance metrics
python view_metrics.py
```

---

## 🧪 Testing & Validation

### Run Tests
```bash
# Quick test (10 questions, ~3-5 min)
python tests/evaluate_assistant.py --limit 10

# Full test (50 questions, ~10-15 min)
python tests/evaluate_assistant.py

# Verify documents
python tests/verify_documents.py

# View metrics
python view_metrics.py
```

### Success Criteria
- **Pass Rate:** >85% (currently 60-75%)
- **Response Time:** <5s average (currently 18s)
- **Faithfulness:** >80% (grounded in docs)
- **Confidence:** >45% average (currently 36%)

---

## 📂 Project Structure

```
ledgermind/
├── data/
│   └── gst/                    # GST PDF documents (294 pages)
├── rag/
│   ├── pipeline.py             # RAG orchestration
│   └── metrics.py              # Performance tracking
├── llm/
│   └── assistant.py            # LLM interface (Ollama)
├── scripts/
│   ├── ingest_pdfs.py          # PDF → ChromaDB
│   └── clean.sh                # Clean database
├── tests/
│   ├── test_questions.json     # 50 test questions
│   ├── evaluate_assistant.py   # Automated evaluation
│   ├── verify_documents.py     # Coverage check
│   └── test_search.py          # Retrieval tests
├── config.py                   # All settings
├── main.py                     # Entry point
├── chroma_db/                  # Vector database (855 chunks)
└── rag_metrics.jsonl           # Performance logs
```

---

## 📚 Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Essential commands
- **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - How to test & improve
- **[RAG_FINETUNING_GUIDE.md](RAG_FINETUNING_GUIDE.md)** - Optimization strategies
- **[PROJECT_CONTEXT.md](PROJECT_CONTEXT.md)** - Full project context for LLMs

---

## 🎯 Success Metrics

### Phase 1 (Current):
- ✅ 100% local execution (no APIs)
- ✅ 855 document chunks indexed
- ✅ 88% test coverage
- 🔄 Reaching 85% pass rate (in progress)

### Phase 2 (Goal):
- Accounting database operational
- LLM can query user's financial data
- Answers both rules AND data questions

### Phase 3 (Goal):
- 10+ functions available to LLM
- Can create invoices, validate transactions
- Complete GST workflow supported

---

## 🤝 Contributing

**Current needs:**
- 🧪 Testing with real GST questions
- 📜 More GST documents (IGST Act, Circulars)
- 💼 Accounting domain expertise
- 🐛 Bug reports and feature requests

**How to contribute:**
1. Test the assistant with your questions
2. Report incorrect answers
3. Suggest prompt improvements
4. Add test questions

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 📧 Contact

- **Issues:** [GitHub Issues](https://github.com/yourusername/ledgermind/issues)
- **Discussions:** [GitHub Discussions](https://github.com/yourusername/ledgermind/discussions)

---

**Building the foundation, one phase at a time. 🚀**

*Last Updated: January 1, 2026*  
*Phase 1 Complete | Optimizing for Production*
