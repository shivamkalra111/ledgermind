# LedgerMind: LLM-Powered GST Compliance Assistant

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status: Phase 1 - 75%](https://img.shields.io/badge/status-Phase%201%20(75%25)-orange.svg)]()

> Building towards a Tally-like accounting software with intelligent LLM assistance. Currently: Optimizing production-ready GST compliance Q&A assistant using RAG with local LLMs.

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
- 🔄 Optimize for production (speed + accuracy)
- 📊 Validate with comprehensive testing

**Why This Order?** Master the AI/RAG layer first before adding accounting complexity. A bad LLM assistant on top of accounting data = bad product. A great LLM assistant = solid foundation for future features.

---

## 📊 Current Status (January 2, 2026)

### Performance Metrics
- **Pass Rate:** 40% (5-question sample)
- **Avg Faithfulness:** 57% (target: 65%+)
- **Avg Confidence:** 61% (target: 45%+) ✅
- **Avg Response Time:** 38s (target: <5s) ❌
- **Keyword Match:** 50-100%
- **Document Coverage:** 88%

### ✅ Recent Wins
1. **Fixed Cross-Page Chunking** - Major breakthrough!
   - **Problem:** Section 16(2) was split across pages 29-30
   - **Solution:** Process entire PDF as one document, chunk semantically
   - **Result:** 485 chunks (down from 1049), better coherence
   - **Impact:** Faithfulness improved 45% → 57%

2. **Hybrid Search** - Combining semantic + keyword (BM25)
   - Confidence: 36% → 61% (+69%)
   - Excellent precision on specific terms

3. **NLI-Based Faithfulness** - Replaced word-matching heuristic
   - Using `cross-encoder/nli-deberta-v3-base`
   - More accurate entailment detection
   - Still improving (57% avg)

### 🚧 Current Blockers

**Priority #1: Response Time (38s → Target: <5s)**
- Retrieval: ~3s (acceptable)
- LLM generation: ~25s (needs optimization)
- NLI faithfulness: ~10s (blocking user response)

**Priority #2: Faithfulness (57% → Target: 65%)**
- Some questions still get low scores (0-25%)
- LLM picking different aspects from chunks than expected
- Need better chunk precision

**Priority #3: Scalability**
- `RAG_NUM_RESULTS=10` is high (slow, expensive for LLM)
- Need better way to get top-3 accurate results
- Current retrieval sometimes misses best chunks

---

## 🚀 Technical Roadmap (Next 2-4 Weeks)

### **Phase 1A: Performance & Accuracy Optimization** (CURRENT)

#### Week 1: Quick Wins
**1. Async Processing Pipeline** ⭐ (Target: 38s → 15-20s)
```python
# Run retrieval, LLM, and metrics in parallel
- Search (3s) + LLM (25s) → Sequential: 28s
- Search → LLM | Calculate metrics async → Parallel: 15s
```

**2. Hybrid Search Boosting** (Better top-3 accuracy)
```python
# Dynamic boosting based on query type
if has_section_numbers: boost_keyword(2x)
elif is_definitional: boost_semantic(1.5x)
```

**Expected Impact:**
- Response time: 38s → 15-20s (✅ 50% faster)
- Top-3 accuracy: +10-15%
- No additional complexity

---

#### Week 2-3: Core Improvements
**3. Re-Ranking Layer** ⭐⭐ (HIGHEST IMPACT)
```
Current: Query → Semantic Search → Top 10 → LLM
Better:  Query → Semantic Search → Top 30 → Re-rank → Top 5 → LLM
```

**Why:**
- Bi-encoders (bge-large) give ~80% accuracy
- Cross-encoders give ~90-95% accuracy
- Standard in production RAG (LlamaIndex, LangChain)

**Implementation:**
- Model: `cross-encoder/ms-marco-MiniLM-L-12-v2`
- Retrieve 30 chunks (fast, approximate)
- Re-rank with cross-encoder (accurate)
- Return top 5 → LLM

**Expected Impact:**
- Faithfulness: 57% → 70%+ (✅ 20%+ improvement)
- Reduce `RAG_NUM_RESULTS` from 10 → 5 (faster LLM)
- Net latency: +200ms (re-ranking) -10s (fewer chunks) = **-9.8s faster**

**Trade-off:** Adds 200ms latency, but **much better precision** → fewer chunks → faster LLM → net win!

---

**4. Hierarchical Chunking** (Better context)
```
Parent Chunk: Full Section 16 (all subsections)
Child Chunks: 16(1), 16(2), 16(3), 16(4)

Retrieval: Search children → Return parents to LLM
```

**Why:**
- Child chunks are specific (good for matching)
- Parent chunks have full context (good for LLM)
- No information loss

**Expected Impact:**
- Faithfulness: +5-10%
- Better handling of multi-part questions

---

#### Week 3-4: Advanced Optimization
**5. Query Rewriting** (Generic, not question-specific)
```python
# Use fast LLM to enhance query before retrieval
User: "conditions for claiming ITC"
Rewritten: "Section 16(2) eligibility conditions invoice goods received"
```

**Implementation:**
- Use Qwen2.5:1.5B (fast, ~200ms)
- Generic templates (no hardcoded questions)

---

**6. Metadata-Driven Retrieval** (Faster, more accurate)
```python
# Filter chunks before search
if "Section 16" in query:
    filter = {"section_id": {"$contains": "16"}}
elif query_type == "definitional":
    filter = {"section_type": "definitions"}
```

**Expected Impact:**
- Speed: 3s → 1-2s (search fewer chunks)
- Accuracy: +5-10% (more relevant subset)

---

**7. Chunk Deduplication** (Reduce LLM cost)
```python
# Merge overlapping chunks, extract key sentences
10 verbose chunks (8k tokens) → 5 dense chunks (3k tokens)
```

**Expected Impact:**
- LLM time: 25s → 12-15s
- Quality: Same or better (less noise)

---

### Success Criteria (End of Phase 1A)
- **Response Time:** <5s average (currently 38s)
- **Faithfulness:** >70% average (currently 57%)
- **Pass Rate:** >85% (currently 40%)
- **Reduced `RAG_NUM_RESULTS`:** 10 → 5 (scalability)

---

## 🗺️ Full Development Roadmap

### ✅ **Phase 1: LLM Assistant Core** (IN PROGRESS - 75% Complete)

**Completed:**
- [x] RAG pipeline with ChromaDB
- [x] Local LLM (Qwen2.5-7B via Ollama)
- [x] 294 pages GST documents (485 chunks after optimization)
- [x] Hybrid search (semantic + keyword/BM25)
- [x] Enhanced chunking (context-enriched + sentence-aware)
- [x] **Cross-page chunking fix** (Section 16(2) now intact)
- [x] NLI-based faithfulness (cross-encoder/nli-deberta-v3-base)
- [x] Metrics system (confidence, faithfulness, relevance)
- [x] 50-question test suite
- [x] Document coverage verification (88%)

**In Progress (Next 2-4 weeks):**
- [ ] Async processing pipeline (38s → 15-20s)
- [ ] Re-ranking layer (faithfulness 57% → 70%+)
- [ ] Hierarchical chunking (better context)
- [ ] Query rewriting (better retrieval)
- [ ] Metadata filtering (faster search)
- [ ] Reach 85% pass rate

---

### 🔄 **Phase 2: Accounting Data Layer** (NEXT - Month 2-3)
**Goal:** Add accounting database so LLM can analyze YOUR data

**What We'll Build:**
```
Current:  User asks "What is ITC?" → LLM answers from rules
Next:     User asks "What's my ITC this month?" → LLM queries YOUR data + rules
```

**Components:**
1. Database Schema (Customers, Vendors, Invoices, Transactions)
2. API Layer (simple functions LLM can call)
3. LLM Integration (answer data-specific questions)

**Timeline:** 2-3 months

---

### 🎯 **Phase 3: Function Calling / Tool Use** (Month 4-5)
**Goal:** LLM can perform actions, not just answer questions

**Architecture:** **Function Calling (NOT Agentic System)**

**Why Function Calling?**
- ✅ Simpler, more predictable
- ✅ Sufficient for 80% of accounting tasks
- ✅ Natively supported by Qwen2.5

**Example:**
```python
User: "Create invoice for ABC Corp, 100k software, Maharashtra"

LLM calls: create_invoice({
    customer: "ABC Corp",
    items: [{name: "Software", hsn: "998314", amount: 100000}],
    cgst: 9000, sgst: 9000
})
```

**Timeline:** 1-2 months

---

### 🏗️ **Phase 4: Web UI & Polish** (Month 6-7)
- Web interface (FastAPI + React or Streamlit)
- Dashboard (revenue, GST liability, ITC)
- Forms & Reports (GSTR-1, P&L)

---

### 🚀 **Phase 5: Advanced Features** (Month 8+)
- Multi-company support
- Inventory management
- E-invoicing integration
- Banking integration
- **Agentic workflows** (only if genuinely needed)

---

## 🛠️ Tech Stack

| Component | Technology | Why? |
|-----------|-----------|------|
| **LLM** | Qwen2.5-7B-Instruct (Ollama) | Best reasoning, function calling |
| **Embeddings** | bge-large-en-v1.5 (1024-dim) | Optimized for legal text |
| **Vector DB** | ChromaDB (persistent) | Fast, local, simple |
| **Re-ranker** | cross-encoder/ms-marco-MiniLM | Production-grade accuracy |
| **Faithfulness** | cross-encoder/nli-deberta-v3-base | Accurate entailment detection |
| **Database** | PostgreSQL (future) | ACID, reliable |
| **Backend** | Python + FastAPI (future) | Fast, async |

**Principles:**
- ✅ Open-source first
- ✅ Privacy by default (local execution)
- ✅ No vendor lock-in
- ✅ Production-grade tools

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
# Quick test (5 questions, ~2-3 min)
python tests/evaluate_assistant.py --limit 5

# Full test (50 questions, ~15-20 min)
python tests/evaluate_assistant.py

# Verify documents
python tests/verify_documents.py
```

### Current Success Criteria
- **Pass Rate:** >85% (currently 40%)
- **Faithfulness:** >65% (currently 57%)
- **Confidence:** >45% (✅ currently 61%)
- **Response Time:** <5s (currently 38s)

---

## 📂 Project Structure

```
ledgermind/
├── data/gst/                  # GST PDFs (294 pages)
├── rag/
│   ├── pipeline.py            # RAG orchestration
│   ├── hybrid_search.py       # Semantic + keyword (BM25)
│   ├── enhanced_chunker.py    # Context-enriched chunking
│   └── metrics.py             # NLI-based faithfulness
├── llm/
│   └── assistant.py           # LLM interface (Ollama)
├── scripts/
│   ├── ingest_pdfs.py         # PDF → ChromaDB (cross-page aware)
│   └── clean.sh               # Clean database
├── tests/
│   ├── test_questions.json    # 50 test questions
│   ├── evaluate_assistant.py  # Automated evaluation
│   └── verify_documents.py    # Coverage check
├── config.py                  # All settings
├── main.py                    # Entry point
└── chroma_db/                 # Vector DB (485 chunks)
```

---

## 📚 Documentation

### Core Guides
- **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - How to test & improve
- **[FILE_FLOW_GUIDE.md](FILE_FLOW_GUIDE.md)** - Complete system flow
- **[HYBRID_SEARCH_GUIDE.md](HYBRID_SEARCH_GUIDE.md)** - Semantic + keyword search

### Quick Reference
- **[QUICKSTART.md](documents/QUICKSTART.md)** - Essential commands
- **[PROJECT_CONTEXT.md](documents/PROJECT_CONTEXT.md)** - Full context for LLMs

---

## 🔥 Key Technical Decisions

### Why Re-Ranking Layer?
- Bi-encoders (current): Fast but ~80% accurate
- Cross-encoders: Slower but ~95% accurate
- **Solution:** Use bi-encoder for initial search (30 chunks), cross-encoder for final selection (top 5)
- **Result:** Best of both worlds - speed + accuracy

### Why Async Processing?
- Current: Sequential (retrieval → LLM → metrics) = 38s
- Better: Parallel (retrieve + LLM, metrics in background) = 15-20s
- **Result:** 50% faster without sacrificing quality

### Why Hierarchical Chunking?
- Problem: Small chunks = good matches but lack context
- Solution: Search small chunks, return large parents to LLM
- **Result:** Precise retrieval + full context = better answers

### Why NOT Agentic System (Yet)?
- Don't have accounting data yet
- Function calling covers 80% of use cases
- Simpler to build, debug, and maintain
- Can add agents later if genuinely needed

---

## 🎯 Success Metrics

### Phase 1 Targets (2-4 weeks):
- ✅ Local execution
- ✅ 485 optimized chunks
- ✅ 88% document coverage
- ✅ Hybrid search implemented
- ✅ Cross-page chunking fixed
- 🔄 <5s response time (currently 38s)
- 🔄 >70% faithfulness (currently 57%)
- 🔄 >85% pass rate (currently 40%)

---

## 🤝 Contributing

**Current needs:**
- 🧪 Testing with real GST questions
- 📜 More GST documents (IGST Act, Circulars)
- 💼 Accounting domain expertise
- 🐛 Bug reports and feature requests

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

**Building the foundation, one optimization at a time. 🚀**

*Last Updated: January 2, 2026*  
*Phase 1: 75% Complete*  
*Next: Re-ranking layer + Async processing → Production-ready*
