# Quick Start Guide

## Prerequisites
- Python 3.8+
- Ollama installed

## Setup (One Time)

### 1. Start Ollama
```bash
# Terminal 1 - Keep this running
ollama serve
```

### 2. Download Model
```bash
# Terminal 2
ollama pull qwen2.5:7b-instruct
```

### 3. Install Dependencies (if not done)
```bash
cd /Users/shivam/Desktop/StartUp/ledgermind
pip install -r requirements.txt
```

### 4. Ingest PDFs (if not done)
```bash
python scripts/ingest_pdfs.py
```

---

## Running the System

### Interactive Mode
```bash
python main.py
```

### Single Question
```bash
python main.py "Your question here?"
```

---

## Commands (in Interactive Mode)

```
help      - Show help
stats     - System statistics
metrics   - Performance metrics
quit      - Exit
```

---

## View Metrics

```bash
python view_metrics.py
python view_metrics.py --last 10
```

---

## Testing

```bash
# Test retrieval
python tests/test_search.py

# Test full RAG
python tests/test_rag_system.py

# Verify embeddings
python tests/verify_embeddings.py
```

---

## Troubleshooting

**Ollama not running:**
```bash
ollama serve
```

**Model not found:**
```bash
ollama list
ollama pull qwen2.5:7b-instruct
```

**ChromaDB missing:**
```bash
python scripts/ingest_pdfs.py
```

