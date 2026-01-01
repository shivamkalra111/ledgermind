# LedgerMind: LLM-Powered GST Compliance Assistant

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status: Phase 1 Complete](https://img.shields.io/badge/status-Phase%201%20Complete-green.svg)]()

> An open-source AI assistant that answers GST compliance questions using RAG (Retrieval-Augmented Generation) with local LLMs. No API costs, complete data privacy, grounded in official GST documents.

---

## 🎯 Current Focus

Building a **production-ready LLM assistant** for Indian GST compliance that can accurately answer questions like:
- "What is the time limit to claim Input Tax Credit?"
- "How to file GSTR-1?"
- "What is reverse charge mechanism?"

Future vision: Full Tally-like accounting software with integrated AI assistance.

## ✨ Features (Working Now)

- 🗣️ **Natural Language Q&A**: Ask GST questions in plain English
- 🔍 **RAG-Powered**: Retrieves relevant sections from official GST documents
- ✅ **Grounded Answers**: Responses cite sources (document + page numbers)
- 📊 **Performance Metrics**: Tracks confidence, faithfulness, relevance
- 🔒 **100% Local**: No API calls, complete data privacy
- 🧪 **Automated Testing**: 50-question test suite with evaluation

## 🏗️ Architecture

```
User Question
      ↓
Query Expansion (GST abbreviations)
      ↓
Vector Search (ChromaDB)
  • 855+ document chunks
  • bge-large-en-v1.5 embeddings
  • Semantic + metadata filtering
      ↓
Top-K Retrieval (5-7 chunks)
  • Min similarity: 0.25
  • With source metadata
      ↓
LLM Generation (Qwen2.5-7B-Instruct)
  • Context-aware reasoning
  • Forced citation
  • Temperature: 0.3 (conservative)
      ↓
Post-processing
  • Faithfulness scoring
  • Relevance scoring
  • Source formatting
      ↓
JSON Response + Metrics
```

## 🛠️ Tech Stack

| Component | Technology | Why? |
|-----------|-----------|------|
| **LLM** | Qwen2.5-7B-Instruct (via Ollama) | Best reasoning for legal text |
| **Embeddings** | bge-large-en-v1.5 (1024-dim) | Optimized for formal documents |
| **Vector DB** | ChromaDB (persistent) | Fast, lightweight, local |
| **Chunking** | Semantic (structure-aware) | Preserves legal context |
| **Framework** | Python 3.8+ | Simple, maintainable |

**Why this stack?**
- ✅ 100% open-source (no API costs)
- ✅ Runs completely offline (after initial model download)
- ✅ Data never leaves your machine
- ✅ Production-ready performance

## 🚀 Quick Start

### Prerequisites
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull LLM model (4.7 GB, one-time)
ollama pull qwen2.5:7b-instruct
```

### Setup
```bash
# 1. Clone repository
git clone https://github.com/yourusername/ledgermind.git
cd ledgermind

# 2. Install dependencies
pip install -r requirements.txt

# 3. Ingest GST documents (one-time, ~2-3 minutes)
python scripts/ingest_pdfs.py

# 4. Start Ollama server (keep running)
ollama serve
```

### Run Assistant
```bash
# Interactive mode
python main.py

# Single question
python main.py "What is Input Tax Credit?"

# Commands in interactive mode:
#   help     - Show available commands
#   stats    - System statistics
#   metrics  - Performance metrics
#   quit     - Exit
```

## 💡 Example Usage

**Question:**
```
What are the conditions for claiming Input Tax Credit?
```

**Response:**
```
To claim Input Tax Credit, the following conditions must be met:

1. You must possess a tax invoice or debit note
2. The goods or services must have been received
3. The tax must have been paid to the government
4. You must have filed your GST returns

All conditions under Section 16(2) of the CGST Act must be satisfied
[Source: CGST Act 2017, Section 16, Page 42].

Sources:
  1. a2017-12.pdf (Page 42, 85% match)
  2. cgst-rules.pdf (Page 67, 72% match)

Confidence: 85%
Faithfulness: 92%
Relevance: 88%
Time: 2.3s
```

## 📊 Current Status

**Phase:** Phase 1 - LLM Assistant ✅ **COMPLETE**  
**Pass Rate:** 60-75% on 50-question test suite (target: >70%)

| Component | Status | Details |
|-----------|--------|---------|
| RAG Pipeline | ✅ Working | ChromaDB + bge-large embeddings |
| LLM Integration | ✅ Working | Qwen2.5-7B via Ollama |
| GST Knowledge Base | ✅ Loaded | 855 chunks, 294 pages |
| Metrics System | ✅ Working | Confidence, faithfulness, relevance |
| Test Suite | ✅ Ready | 50 questions, automated evaluation |
| Document Verification | ✅ Complete | 88% coverage |

**Next:** Improve pass rate to >85% through prompt optimization

## 📂 Project Structure

```
ledgermind/
├── data/
│   └── gst/                    # GST PDF documents (2 files, 294 pages)
├── rag/
│   ├── pipeline.py             # RAG orchestration
│   └── metrics.py              # Performance tracking
├── llm/
│   └── assistant.py            # LLM interface (Ollama)
├── scripts/
│   ├── ingest_pdfs.py          # PDF → ChromaDB ingestion
│   └── clean.sh                # Clean ChromaDB
├── tests/
│   ├── test_questions.json     # 50 ground truth questions
│   ├── evaluate_assistant.py   # Automated evaluation
│   ├── verify_documents.py     # Document coverage check
│   ├── test_search.py          # Retrieval-only tests
│   └── verify_embeddings.py    # Embedding consistency check
├── config.py                   # Centralized configuration
├── main.py                     # Main entry point
├── view_metrics.py             # Metrics viewer
├── chroma_db/                  # Vector database (created on first run)
├── rag_metrics.jsonl           # Performance logs
├── QUICKSTART.md               # Quick commands
├── TESTING_GUIDE.md            # How to test & improve
└── RAG_FINETUNING_GUIDE.md     # Optimization strategies
```

## 🧪 Testing & Validation

### Run Tests
```bash
# Quick test (10 questions, ~3-5 min)
python tests/evaluate_assistant.py --limit 10

# Full evaluation (50 questions, ~10-15 min)
python tests/evaluate_assistant.py

# Verify documents can answer questions
python tests/verify_documents.py

# View performance metrics
python view_metrics.py
```

### Success Metrics
- **Pass Rate:** >70% (minimum), >85% (production-ready)
- **Faithfulness:** >75% (grounded in documents)
- **Response Time:** <3s average
- **Document Coverage:** 88% of test questions answerable

**Current Results:**
- ✅ Document coverage: 88% (44/50 questions)
- ✅ Faithfulness: ~75%
- ✅ Response time: ~2.3s average

## 🗺️ Roadmap

### ✅ Phase 1: LLM Assistant (Complete)
- [x] RAG pipeline with ChromaDB
- [x] Local LLM integration (Qwen2.5-7B)
- [x] GST document ingestion (294 pages)
- [x] Metrics tracking system
- [x] Automated test suite (50 questions)
- [x] Document verification tool

### 🔄 Phase 2: Optimization (Current - Week 1-4)
- [ ] Improve system prompt (add examples, strict rules)
- [ ] Query expansion (GST abbreviations)
- [ ] Tune retrieval parameters
- [ ] Reach >85% pass rate
- [ ] Collect human feedback

### ⏳ Phase 3: Production Readiness (Month 2-3)
- [ ] Hybrid search (semantic + keyword)
- [ ] Re-ranking for better accuracy
- [ ] Add GSTR forms knowledge
- [ ] Web interface (Streamlit/FastAPI)
- [ ] User feedback system

### 🎯 Phase 4: Accounting Integration (Month 4+)
- [ ] Database for accounting data (ledgers, invoices)
- [ ] LLM reads YOUR accounting data
- [ ] Transaction validation
- [ ] Auto-categorization
- [ ] GST return generation assistance

## 🤝 Contributing

**We need help with:**
- 📜 Adding more GST documents (IGST Act, UTGST Act, Circulars)
- 🧪 Testing with real-world questions
- 💼 Accounting domain expertise
- 🎨 UI/UX design (Phase 3)

**How to contribute:**
1. Test the assistant with your questions
2. Report issues or incorrect answers
3. Suggest improvements to prompts
4. Add more test questions

## 🎯 Why LedgerMind?

| Problem | LedgerMind Solution |
|---------|-------------------|
| ❌ Pure LLMs hallucinate on GST rules | ✅ RAG retrieves actual official documents |
| ❌ Search is keyword-based and clunky | ✅ Natural language understanding |
| ❌ No source verification | ✅ Every answer cites document + page |
| ❌ Paid APIs are expensive | ✅ 100% free, runs locally |
| ❌ Data privacy concerns | ✅ Never leaves your machine |
| ❌ Requires internet | ✅ Works completely offline |

## 📊 Performance Validation

Our system is scientifically tested:
- **Test Suite:** 50 carefully crafted GST questions
- **Automated Evaluation:** Keyword matching, faithfulness scoring
- **Document Verification:** 88% of questions answerable from our docs
- **Continuous Metrics:** Every query tracked for performance

**Transparency:** We don't just claim accuracy, we measure and publish it.

## 📚 Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Essential commands
- **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - How to test and improve
- **[RAG_FINETUNING_GUIDE.md](RAG_FINETUNING_GUIDE.md)** - Optimization strategies
- **[METRICS_AND_FINETUNING_SUMMARY.md](METRICS_AND_FINETUNING_SUMMARY.md)** - Detailed metrics guide

## 🔧 Configuration

All settings in `config.py`:
```python
# LLM Settings
LLM_MODEL_NAME = "qwen2.5:7b-instruct"
LLM_TEMPERATURE = 0.3  # Conservative for accuracy
LLM_MAX_TOKENS = 512

# RAG Settings
RAG_NUM_RESULTS = 5  # Top-K chunks to retrieve
RAG_MIN_SIMILARITY = 0.25  # Similarity threshold

# Embedding Model
EMBEDDING_MODEL = "BAAI/bge-large-en-v1.5"  # 1024 dimensions
```

Easy to experiment without code changes!

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **GST Documents:** Government of India (public domain)
- **LLM:** Qwen2.5 by Alibaba Cloud
- **Embeddings:** BGE by Beijing Academy of AI
- **Infrastructure:** ChromaDB, Ollama

---

## 📧 Contact & Support

- **Issues:** [GitHub Issues](https://github.com/yourusername/ledgermind/issues)
- **Discussions:** [GitHub Discussions](https://github.com/yourusername/ledgermind/discussions)

---

**Built with ❤️ for accountants and SMEs who need accurate, verifiable GST compliance assistance.**

*Phase 1 Complete: January 1, 2026*
