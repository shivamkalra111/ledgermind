# Testing & Evaluation Guide

## Files Created

### 1. `tests/test_questions.json` (50 test questions)
Ground truth test set covering:
- **Definitional** (15): "What is GST?", "What is ITC?"
- **Factual** (20): "What is the time limit?", "When is IGST applicable?"
- **Procedural** (10): "How to file GSTR-1?", "How to claim ITC?"
- **Analytical** (5): "Compare CGST vs SGST", "Difference between exempt and zero-rated"

**Difficulty levels:**
- Easy (18 questions): Basic definitions and facts
- Medium (24 questions): More complex rules and procedures
- Hard (8 questions): Complex concepts and comparisons

### 2. `tests/evaluate_assistant.py`
Automated evaluation script that:
- Runs all test questions through your RAG system
- Checks for expected keywords in answers
- Validates confidence, faithfulness, relevance
- Generates pass/fail report
- Provides actionable recommendations

---

## How to Run

### Quick Test (First 10 questions)
```bash
python tests/evaluate_assistant.py --limit 10
```

### Full Evaluation (All 50 questions)
```bash
python tests/evaluate_assistant.py
```

### Save Results to Custom File
```bash
python tests/evaluate_assistant.py --save my_results.json
```

---

## What to Expect

### First Run (Baseline)
```
🧪 EVALUATING LLM ASSISTANT
======================================================================

Initializing RAG pipeline...
✅ RAG Pipeline Ready!

📋 Running 50 test questions...
======================================================================

[1/50] What is GST?...
   ✅ PASS | Conf: 82% | Faith: 88% | Keywords: 100% | Time: 2.3s

[2/50] What is Input Tax Credit?...
   ✅ PASS | Conf: 76% | Faith: 92% | Keywords: 80% | Time: 2.1s

[3/50] What is the time limit to claim Input Tax Credit?...
   ❌ FAIL | Conf: 45% | Faith: 65% | Keywords: 33% | Time: 2.5s
      ⚠️  Missing keywords (33% coverage)
      ⚠️  Low faithfulness (65%)

...

======================================================================
📊 EVALUATION SUMMARY
======================================================================

⚠️ Overall Performance:
   Passed: 32/50 (64%)
   Failed: 18/50

📋 By Category:
   ✅ Definitional     12/15 (80%)
   ⚠️  Factual         14/20 (70%)
   ❌ Procedural       4/10 (40%)
   ❌ Analytical       2/5 (40%)

📊 By Difficulty:
   ✅ Easy             15/18 (83%)
   ⚠️  Medium          15/24 (63%)
   ❌ Hard             2/8 (25%)

⏱️  Performance Metrics:
   Avg Response Time: 2.34s
   Avg Confidence:    68%
   Avg Faithfulness:  73%
   Avg Relevance:     81%

❌ Failure Analysis (18 failures):
   📉 Low confidence: 8/18 (44%)
   📉 Low faithfulness: 10/18 (56%)
   📉 Missing keywords: 15/18 (83%)

💡 Recommendations:
   ⚠️  NEEDS IMPROVEMENT: Pass rate below 70%
   → Improve prompt: Add 'Answer ONLY from context' to system prompt
   → Improve answer quality: Add few-shot examples to system prompt
======================================================================

💾 Detailed results saved to: evaluation_results.json
```

---

## Success Targets

### Minimum Acceptable
- ✅ Overall pass rate: **>70%**
- ✅ Easy questions: **>80%**
- ✅ Avg faithfulness: **>75%**
- ✅ Avg response time: **<3s**

### Production Ready
- ✅ Overall pass rate: **>85%**
- ✅ Medium questions: **>75%**
- ✅ Hard questions: **>60%**
- ✅ Avg faithfulness: **>80%**
- ✅ Avg response time: **<2.5s**

### Excellent
- ✅ Overall pass rate: **>90%**
- ✅ All categories: **>80%**
- ✅ Avg faithfulness: **>85%**
- ✅ Avg response time: **<2s**

---

## Improving Your Scores

### If Overall Pass Rate < 50%
**Problem:** System fundamentally not working

**Check:**
```bash
# 1. Verify ChromaDB has data
python -c "import chromadb; c = chromadb.PersistentClient(path='./chroma_db'); print(c.get_collection('gst_rules').count())"
# Should show 800+

# 2. Verify Ollama is running
curl http://localhost:11434/api/tags

# 3. Test simple retrieval
python tests/test_search.py
```

### If Pass Rate 50-70%
**Problem:** Need prompt tuning

**Fix:** Edit `config.py` - Add to `GST_SYSTEM_PROMPT`:
```python
GST_SYSTEM_PROMPT = """You are a GST compliance assistant for India.

CRITICAL RULES:
1. Answer ONLY from the provided context documents
2. If information is not in context, say "I cannot find this information in the provided documents"
3. Never use external knowledge or assumptions
4. Always cite [Source: filename, Page X] for every claim
5. Be precise with numbers, dates, and amounts

EXAMPLE OF GOOD ANSWER:
Question: What is the time limit for claiming ITC?
Answer: Input Tax Credit must be claimed within 6 months from the date of 
the invoice, as per Section 16(4) of the CGST Act [Source: CGST Act 2017, 
Section 16, Page 42].

Now answer user questions following this format.
"""
```

### If Confidence Too Low (<35%)
**Problem:** Can't find relevant documents

**Fix:** Edit `config.py`:
```python
# Retrieve more chunks
RAG_NUM_RESULTS = 7  # Was 5

# Lower similarity threshold
RAG_MIN_SIMILARITY = 0.2  # Was 0.25
```

### If Faithfulness Too Low (<70%)
**Problem:** LLM hallucinating or adding external knowledge

**Fix:** Edit `config.py`:
```python
# Make LLM more conservative
LLM_TEMPERATURE = 0.1  # Was 0.3

# Reduce max length (forces concise answers)
LLM_MAX_TOKENS = 400  # Was 512
```

---

## Iteration Process

### 1. Run Baseline
```bash
python tests/evaluate_assistant.py
# Note the pass rate and failure patterns
```

### 2. Make Changes
- Edit `config.py` (system prompt, parameters)
- Or edit chunking in `scripts/ingest_pdfs.py`

### 3. Re-test
```bash
# If changed config.py only:
python tests/evaluate_assistant.py

# If changed ingestion:
python scripts/ingest_pdfs.py  # Re-ingest
python tests/evaluate_assistant.py  # Re-test
```

### 4. Compare Results
```bash
# View detailed results
cat evaluation_results.json | python -m json.tool | less

# Compare pass rates
# Before: 64%, After: 78% → +14% improvement ✅
```

### 5. Repeat Until Target Met
- Target: >70% for MVP
- Target: >85% for production

---

## Understanding the Metrics

### Keyword Match
- **What:** % of expected keywords found in answer
- **Target:** >50%
- **Low score means:** Answer is off-topic or incomplete

### Confidence (Retrieval Quality)
- **What:** Average similarity of retrieved chunks
- **Target:** >30% (easy), >25% (hard)
- **Low score means:** Can't find relevant documents

### Faithfulness (Grounding)
- **What:** How much answer is supported by context
- **Target:** >65%
- **Low score means:** LLM is hallucinating

### Relevance (Answer Quality)
- **What:** How well answer addresses question
- **Target:** >70%
- **Low score means:** Answer doesn't match question type

---

## Next Steps After Testing

### If Pass Rate > 70%
✅ **You're ready for:**
1. Human validation (get real users to test)
2. Collect feedback on real questions
3. Monitor metrics in production

### If Pass Rate < 70%
⚠️ **You need to:**
1. Follow recommendations from evaluation output
2. Improve system prompt (see RAG_FINETUNING_GUIDE.md)
3. Tune retrieval parameters
4. Re-run evaluation

---

## Files Generated

- `evaluation_results.json` - Detailed test results
- `rag_metrics.jsonl` - Performance metrics from test run

**View detailed results:**
```bash
cat evaluation_results.json | python -m json.tool | less
```

**View individual failures:**
```bash
cat evaluation_results.json | python -c "
import json, sys
data = json.load(sys.stdin)
failures = [r for r in data['results'] if not r['passed']]
for f in failures:
    print(f\"Q: {f['question']}\")
    print(f\"A: {f['answer'][:200]}...\")
    print(f\"Score: {f['score']}\")
    print('-'*70)
"
```

---

## Quick Commands

```bash
# Run full evaluation
python tests/evaluate_assistant.py

# Quick test (10 questions)
python tests/evaluate_assistant.py --limit 10

# After making changes, compare
python tests/evaluate_assistant.py --save results_v2.json

# View metrics from evaluation
python view_metrics.py
```

---

**Start here:**
```bash
python tests/evaluate_assistant.py --limit 10
```

This will test your system with the first 10 questions (~3-5 minutes).

