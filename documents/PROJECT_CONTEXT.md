# LedgerMind Project Context

**For AI Assistants: This document provides complete context about the LedgerMind project. Read this to understand what we're building, current status, and help answer questions.**

---

## 🎯 Project Overview

**What:** LLM-powered accounting software (like Tally) with intelligent AI assistance  
**Current Stage:** Phase 1 - Building GST compliance Q&A assistant  
**Creator:** Solo developer learning LLM/RAG  
**Tech:** Python, Qwen2.5-7B, ChromaDB, RAG architecture

---

## 📊 Current Status (January 2026)

### **Phase 1: LLM Assistant Core** ✅ 95% Complete

**What Works:**
- RAG pipeline with ChromaDB (855 document chunks)
- Local LLM integration (Qwen2.5-7B-Instruct via Ollama)
- 294 pages of GST documents ingested (2 PDFs)
- Metrics tracking (confidence, faithfulness, relevance)
- 50-question automated test suite
- Document verification (88% coverage)

**Current Metrics:**
- Success rate: 100%
- Pass rate: 60-75% (target: >85%)
- Response time: 18s average (target: <5s)
- Confidence: 36% average (target: >45%)
- Verbose responses: 38% (need concise prompt)

**Active Work:**
- Optimizing response time (18s → <5s)
- Improving system prompt (reducing verbosity)
- Tuning retrieval parameters
- Reaching >85% pass rate

### **What's Next:**

**Phase 2** (Month 2-3): Add accounting database
- Design schema (customers, invoices, transactions, ledgers)
- Build CRUD API
- Connect LLM to user's accounting data
- Enable data-specific questions: "What's my ITC this month?"

**Phase 3** (Month 4-5): Function calling / tool use
- NOT building agentic system (too complex, unnecessary)
- Using function calling (simpler, sufficient for 80% of tasks)
- 10+ functions: `create_invoice()`, `get_itc_summary()`, etc.
- LLM can perform actions, not just Q&A

---

## 🏗️ Architecture Decisions

### **RAG System (Current):**
```
User Question 
  → Embedding (bge-large-en-v1.5, 1024-dim)
  → ChromaDB Vector Search (top-5 chunks, similarity >0.25)
  → LLM Generation (Qwen2.5-7B, temp=0.3, max_tokens=512)
  → Post-process (cite sources, calculate metrics)
  → Return answer + metadata
```

### **Why These Choices:**

**LLM: Qwen2.5-7B-Instruct**
- Best reasoning for legal/formal text
- Supports function calling (Phase 3)
- Runs locally via Ollama (privacy)
- Good balance of speed vs accuracy

**Embeddings: bge-large-en-v1.5 (1024-dim)**
- Optimized for formal/legal documents
- Better than bge-small (384-dim) for accuracy
- Consistent with ChromaDB for queries

**Vector DB: ChromaDB**
- Simple, lightweight, local
- Persistent storage
- Good enough for <1M documents

**Chunking: Semantic (structure-aware)**
- Splits by document structure (sections, rules)
- Preserves legal context
- Better than fixed-size chunking

### **Future Architecture (Phase 3):**
```
User Request
  → Intent Classification
  → Router: {Q&A, Data Query, Action}
       ↓
    ┌──────────────┬──────────────┬──────────────┐
    ↓              ↓              ↓              ↓
ChromaDB      AccountingDB    Functions     Actions
(Rules)        (User Data)    (Queries)     (CRUD)
    ↓              ↓              ↓              ↓
    └──────────────┴──────────────┴──────────────┘
                   ↓
           LLM Synthesizes Response
```

### **Why NOT Agentic System:**

**Function Calling vs Agents:**
- ✅ Function calling: LLM calls predefined functions (simpler, predictable)
- ❌ Agentic: Multiple AI agents communicate (complex, unpredictable)

**Decision:** Function calling is sufficient because:
1. Don't have accounting data yet (agents need data)
2. Accounting tasks are mostly deterministic (known steps)
3. Easier to debug and maintain
4. Covers 80% of use cases
5. Can add agents later if genuinely needed

**When Agents Make Sense:**
- Complex multi-step workflows (GST audit prep)
- Uncertain number of steps
- Exploratory analysis
- Multiple specialized domains

**Our Use Case:**
- Most tasks: Create invoice, calculate GST, validate ITC (deterministic)
- Function calling handles these perfectly

---

## 📁 Project Structure

```
ledgermind/
├── data/gst/                          # Input PDFs (2 files, 294 pages)
│   ├── a2017-12.pdf                   # CGST Act 2017
│   └── 01062021-cgst-rules-2017.pdf   # CGST Rules
│
├── chroma_db/                         # Vector database (855 chunks)
│   └── [auto-generated]
│
├── rag/
│   ├── pipeline.py                    # Main RAG orchestration
│   └── metrics.py                     # Performance tracking
│
├── llm/
│   └── assistant.py                   # LLM interface (Ollama API)
│
├── scripts/
│   ├── ingest_pdfs.py                 # PDF → ChromaDB ingestion
│   └── clean.sh                       # Clean/reset database
│
├── tests/
│   ├── test_questions.json            # 50 ground truth questions
│   ├── evaluate_assistant.py          # Automated evaluation
│   ├── verify_documents.py            # Document coverage check
│   ├── test_search.py                 # Retrieval-only tests
│   └── verify_embeddings.py           # Embedding consistency
│
├── config.py                          # All configurable settings
├── main.py                            # Entry point (CLI + interactive)
├── view_metrics.py                    # View performance logs
│
├── rag_metrics.jsonl                  # Performance logs (gitignored)
│
└── Documentation/
    ├── README.md                      # Main project README
    ├── QUICKSTART.md                  # Quick commands
    ├── TESTING_GUIDE.md               # Testing & improvement
    ├── RAG_FINETUNING_GUIDE.md        # Optimization strategies
    └── PROJECT_CONTEXT.md             # This file
```

---

## 🔧 Configuration (config.py)

```python
# LLM Settings
LLM_MODEL_NAME = "qwen2.5:7b-instruct"
LLM_TEMPERATURE = 0.3         # Conservative for accuracy
LLM_MAX_TOKENS = 512          # Need to reduce to 256 (optimization)
LLM_TOP_P = 0.9

# RAG Settings
RAG_NUM_RESULTS = 7           # Need to reduce to 5 (optimization)
RAG_MIN_SIMILARITY = 0.25     # May increase to 0.30

# Embedding
EMBEDDING_MODEL = "BAAI/bge-large-en-v1.5"  # 1024 dimensions

# ChromaDB
CHROMA_DB_PATH = "./chroma_db"
CHROMA_COLLECTION_NAME = "gst_rules"

# System Prompt (needs improvement for conciseness)
GST_SYSTEM_PROMPT = """You are a GST compliance assistant..."""
```

---

## 🐛 Known Issues & Fixes

### **Issue 1: Slow Response Time (18s avg)**
**Cause:** LLM generating too much text  
**Fix (in progress):**
- Reduce `LLM_MAX_TOKENS` from 512 to 256
- Add conciseness rules to system prompt
- Increase temperature slightly (0.3 → 0.5)
**Expected:** 18s → 4-6s (70% improvement)

### **Issue 2: Verbose Responses (38%)**
**Cause:** System prompt not strict enough  
**Fix:** Add explicit length limits and examples
**Expected:** Verbose rate 38% → 15%

### **Issue 3: Low Confidence (36% avg)**
**Cause:** Not expanding GST abbreviations  
**Fix:** Add query expansion (ITC → Input Tax Credit)
**Expected:** 36% → 45% confidence

### **Issue 4: ChromaDB Corruption**
**Occurred:** When passing both `documents` and `embeddings` to `collection.add()`  
**Fixed:** Only pass `documents`, let ChromaDB handle embedding  
**Solution:** Re-ingest with `python scripts/ingest_pdfs.py`

---

## 🧪 Testing

### **Test Suite:**
- 50 questions covering: Definitions, Facts, Procedures, Analysis
- Difficulty: Easy (18), Medium (24), Hard (8)
- Categories: Definitional, Factual, Procedural, Analytical
- Document coverage: 88% (44/50 answerable)

### **Evaluation Metrics:**
1. **Keyword Match:** % of expected keywords in answer
2. **Confidence:** Average similarity of retrieved chunks
3. **Faithfulness:** How grounded in context (0-100%)
4. **Relevance:** How well answer addresses question (0-100%)
5. **Response Quality:** good / verbose / too_short

### **Commands:**
```bash
# Quick test (10 questions)
python tests/evaluate_assistant.py --limit 10

# Full test (50 questions)
python tests/evaluate_assistant.py

# Check document coverage
python tests/verify_documents.py

# View metrics
python view_metrics.py
```

---

## 🎯 Success Criteria

### **Phase 1 (Current):**
- ✅ 100% local execution
- ✅ 855 chunks indexed
- ✅ 88% document coverage
- 🔄 >85% pass rate (currently 60-75%)
- 🔄 <5s response time (currently 18s)
- 🔄 >75% faithfulness (not tracked yet)

### **Phase 2 (Goal):**
- Accounting database operational
- LLM answers data-specific questions
- Can query: "What's my ITC this month?"

### **Phase 3 (Goal):**
- 10+ functions available
- Can create invoices via LLM
- Complete GST workflow

---

## 💡 Key Learnings

### **What Worked Well:**
1. **Semantic chunking** - Better than fixed-size for legal docs
2. **bge-large-en-v1.5** - Worth the 1024-dim for accuracy
3. **Persistent ChromaDB** - Simple, reliable
4. **Test suite first** - Caught issues early
5. **Document verification** - Validated test coverage

### **What Didn't Work:**
1. **Manual embeddings** - Caused ChromaDB corruption
2. **High temperature** - Too creative for legal text
3. **No token limits** - Generated 2000+ char responses
4. **Vague system prompt** - LLM too verbose

### **Developer's Learning Journey:**
- New to LLM/RAG/ChromaDB when started
- Learned importance of:
  - Embedding consistency (same model for ingest & query)
  - Metrics-driven optimization
  - Testing before scaling
  - Prompt engineering > model fine-tuning

---

## 🔮 Future Considerations

### **Phase 2 Planning (Accounting Database):**

**Schema (Preliminary):**
```sql
customers (id, name, gstin, email, state)
products (id, name, hsn_code, gst_rate, unit)
invoices (id, customer_id, date, amount, cgst, sgst, igst)
transactions (id, date, type, amount, category, gst_applicable)
ledgers (id, name, type, balance)
```

**API Functions (Planned):**
```python
get_monthly_itc(month) → ITC summary
get_invoice(id) → Invoice details
check_supplier_compliance(supplier_id) → GSTR filing status
create_invoice(data) → New invoice
validate_transaction(tx_id) → Rule validation
```

### **Phase 3 Planning (Function Calling):**

**Function Examples:**
1. `get_itc_summary(month)` - ITC data
2. `create_invoice(customer, items, amount)` - Create invoice
3. `validate_transaction(tx_id)` - Check against rules
4. `check_gst_compliance(period)` - Compliance status
5. `generate_gstr1(month)` - Generate report

**Implementation:** Qwen2.5 native function calling

---

## 📊 Metrics Tracking

**Automatic Logging:** Every query logs to `rag_metrics.jsonl`

**Tracked Metrics:**
- Question, timestamp
- Chunks retrieved, chunks used
- Avg similarity, top similarity
- Retrieval time, generation time, total time
- Answer length, words
- Confidence score
- Response quality flag (good/verbose/too_short)
- Efficiency score (confidence/time)

**Analysis:**
```bash
python view_metrics.py --last 10
```

---

## 🤝 How to Help This Project

**As an AI Assistant, you can help by:**

1. **Answering Questions:**
   - Architecture decisions
   - Optimization strategies
   - Code reviews
   - Debugging issues

2. **Providing Guidance:**
   - RAG best practices
   - Prompt engineering
   - Database design (Phase 2)
   - Function calling implementation (Phase 3)

3. **Being Aware Of:**
   - Developer is learning (new to LLM/RAG)
   - Solo project (no team)
   - Local execution only (no cloud)
   - Open-source, no budget

4. **Not Doing:**
   - Over-engineering (keep it simple)
   - Suggesting paid services
   - Complex architectures too early
   - Agents before necessary

---

## 📞 Common Questions You Might Get Asked

### **Q: Should I build agentic system?**
**A:** Not yet. Function calling is sufficient for Phase 3. Agents only if complex multi-step workflows needed later.

### **Q: What's the fastest way to improve pass rate?**
**A:** 
1. Reduce `LLM_MAX_TOKENS` to 256
2. Improve system prompt (add conciseness rules)
3. Reduce `RAG_NUM_RESULTS` to 5
Expected: +20% pass rate improvement

### **Q: Why is my response time 18s?**
**A:** LLM generation is 98% of time (17.9s). Fix: Reduce max tokens, improve prompt.

### **Q: Should I fine-tune the model?**
**A:** No. Prompt engineering achieves 80% of fine-tuning benefits. Fine-tune only after 6+ months of data collection.

### **Q: Why bge-large instead of bge-small?**
**A:** Legal documents need higher dimensions for accuracy. 1024-dim > 384-dim for formal text.

### **Q: How to add more documents?**
**A:** Drop PDFs in `data/gst/`, run `python scripts/ingest_pdfs.py`. Verify with `python tests/verify_documents.py`.

### **Q: ChromaDB is corrupted, what to do?**
**A:** `rm -rf chroma_db/`, then `python scripts/ingest_pdfs.py` to re-ingest.

---

## 🎯 Summary for Quick Context

**TL;DR:**
- Building Tally-like software with LLM
- Currently: GST Q&A assistant (Phase 1, 95% done)
- Next: Add accounting database (Phase 2)
- Then: Function calling for actions (Phase 3)
- NOT building agents (function calling is enough)
- Tech: Python, Qwen2.5-7B, ChromaDB, RAG
- Status: Works, needs optimization (18s→5s, 65%→85% pass rate)

**Current Need:** Optimize Phase 1 before moving to Phase 2

---

*This document should give you complete context to answer questions about LedgerMind intelligently.*

**Last Updated:** January 1, 2026

