# Next Steps: Production Optimization (2-4 Weeks)

**Last Updated:** January 2, 2026  
**Current Status:** Phase 1 - 75% Complete  
**Focus:** Speed + Accuracy optimization for production readiness

---

## 📊 Current State

### Performance Metrics
| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Pass Rate | 40% | >85% | ❌ |
| Faithfulness | 57% | >65% | ⚠️ |
| Confidence | 61% | >45% | ✅ |
| Response Time | 38s | <5s | ❌ |
| Keyword Match | 50-100% | >50% | ✅ |

### What's Working
1. ✅ **Hybrid search** - 61% confidence (target: 45%+)
2. ✅ **Cross-page chunking** - Section 16(2) now intact
3. ✅ **NLI faithfulness** - Better than word-matching heuristic
4. ✅ **Document coverage** - 88% of questions answerable

### Critical Issues
1. ❌ **Response time: 38s** (target: <5s) - 7.6x too slow
2. ⚠️ **Faithfulness: 57%** (target: 65%+) - Needs 8%+ improvement
3. ⚠️ **Pass rate: 40%** (target: 85%+) - Need 45%+ improvement

---

## 🎯 Implementation Plan

### **Week 1: Quick Wins** (2-3 days)

#### 1. Async Processing Pipeline ⭐
**Expected:** 38s → 15-20s (50% faster)

**Current flow:**
```
Search (3s) → [wait] → LLM (25s) → [wait] → NLI (10s) = 38s
```

**New flow:**
```python
async def answer():
    # Parallel: Search + LLM prep
    chunks = await async_search(query)
    
    # Generate answer
    answer = await async_generate(chunks)
    
    # Background: Calculate metrics (don't block response)
    asyncio.create_task(calculate_metrics_background(answer))
    
    return answer  # ~15-20s
```

**Files to modify:**
- `rag/pipeline.py` - Convert to async
- `llm/assistant.py` - Add async methods
- `main.py` - Use async/await

**Testing:**
```bash
python tests/evaluate_assistant.py --limit 5
# Target: 15-20s avg response time
```

---

#### 2. Hybrid Search Boosting
**Expected:** +10-15% top-3 accuracy

**Implementation:**
```python
# In rag/hybrid_search.py
def adaptive_boost(query: str) -> float:
    if re.search(r'Section \d+', query):
        return 2.0  # Boost keyword for section references
    elif query.lower().startswith('what is'):
        return 1.5  # Boost semantic for definitions
    else:
        return 1.2  # Default
```

**Files to modify:**
- `rag/hybrid_search.py` - Add adaptive boosting

**Testing:**
```bash
python main.py "What are the conditions for Section 16?"
# Should retrieve Section 16(2) in top 3
```

---

### **Week 2-3: Core Improvements** (7-10 days)

#### 3. Re-Ranking Layer ⭐⭐ (HIGHEST IMPACT)
**Expected:** Faithfulness 57% → 70%+ (20%+ improvement)

**Why:**
- Bi-encoders (bge-large): ~80% accurate, fast
- Cross-encoders: ~95% accurate, slower
- **Solution:** Bi-encoder for initial search, cross-encoder for final selection

**Architecture:**
```
Query → Semantic Search (top 30, ~3s)
      → Re-rank with cross-encoder (~200ms)
      → Return top 5 to LLM (~12s vs 25s with 10 chunks)
      → Net: 15.2s vs 38s = 60% faster!
```

**Implementation:**
```python
# Create: rag/reranker.py
from sentence_transformers import CrossEncoder

class Reranker:
    def __init__(self):
        self.model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-12-v2')
    
    def rerank(self, query: str, chunks: List[Dict], top_k: int = 5):
        # Score each chunk
        pairs = [(query, chunk['text']) for chunk in chunks]
        scores = self.model.predict(pairs)
        
        # Sort and return top K
        ranked = sorted(zip(chunks, scores), key=lambda x: x[1], reverse=True)
        return [chunk for chunk, score in ranked[:top_k]]
```

**Integration:**
```python
# In rag/pipeline.py
retrieval_results = self.hybrid_searcher.search(query, n_results=30)  # More candidates
reranked_chunks = self.reranker.rerank(query, retrieval_results, top_k=5)  # Best 5
answer = self.llm.generate(reranked_chunks)  # Fewer, better chunks
```

**Files to create/modify:**
- `rag/reranker.py` - NEW: Re-ranking logic
- `rag/pipeline.py` - Integrate re-ranker
- `config.py` - Add `USE_RERANKER=True`, `RERANK_TOP_K=5`
- `requirements.txt` - Add `sentence-transformers`

**Testing:**
```bash
# Compare before/after
python tests/evaluate_assistant.py --limit 10

# Expected improvements:
# - Faithfulness: 57% → 70%+
# - Response time: 38s → 15-18s (fewer chunks to LLM)
# - Pass rate: 40% → 60-70%
```

---

#### 4. Hierarchical Chunking
**Expected:** +5-10% faithfulness, better multi-part questions

**Problem:**
- Small chunks: Good for matching, lack context
- Large chunks: Good context, poor matching

**Solution:**
```
Parent: Full Section 16 (all subsections)
Children: 16(1), 16(2)(a), 16(2)(b), etc.

Search: Match children → Return parents to LLM
```

**Implementation:**
```python
# In rag/enhanced_chunker.py
def create_hierarchical_chunks(text, metadata):
    # Create parent chunk (full section)
    parent = {
        'id': f"{metadata['section_id']}_parent",
        'text': full_section_text,
        'metadata': {..., 'chunk_type': 'parent'}
    }
    
    # Create child chunks (subsections)
    children = []
    for subsection in subsections:
        child = {
            'id': f"{metadata['section_id']}_{subsection_id}",
            'text': subsection_text,
            'metadata': {..., 'parent_id': parent['id'], 'chunk_type': 'child'}
        }
        children.append(child)
    
    return parent, children
```

**Retrieval:**
```python
# In rag/pipeline.py
child_chunks = self.search(query)  # Search in children (specific)

# Get parent IDs
parent_ids = [chunk['metadata']['parent_id'] for chunk in child_chunks]

# Retrieve parents for LLM context
parent_chunks = self.collection.get(ids=parent_ids)

# Use parents for generation
answer = self.llm.generate(parent_chunks)
```

**Files to modify:**
- `rag/enhanced_chunker.py` - Add hierarchical chunking
- `scripts/ingest_pdfs.py` - Store parents + children
- `rag/pipeline.py` - Retrieve children, use parents

**Testing:**
```bash
python main.py "What are the conditions for claiming ITC?"
# Should retrieve child (16(2)), use parent (full 16) for context
```

---

### **Week 3-4: Advanced Optimization** (5-7 days)

#### 5. Query Rewriting
**Expected:** +5-10% retrieval accuracy

**Implementation:**
```python
# Create: rag/query_rewriter.py
class QueryRewriter:
    def __init__(self):
        self.llm = FastLLM('qwen2.5:1.5b')  # Fast, small model
    
    def rewrite(self, query: str) -> str:
        prompt = f"""Rewrite this query for legal document search.
Add relevant section numbers, technical terms, and synonyms.

Query: {query}
Rewritten:"""
        return self.llm.generate(prompt, max_tokens=50)

# Example:
# User: "conditions for claiming ITC"
# Rewritten: "Section 16(2) eligibility conditions invoice goods tax paid return"
```

**Files to create/modify:**
- `rag/query_rewriter.py` - NEW: Query rewriting
- `rag/pipeline.py` - Rewrite before search
- `config.py` - Add `USE_QUERY_REWRITING=True`

---

#### 6. Metadata-Driven Retrieval
**Expected:** 3s → 1-2s (faster search), +5-10% accuracy

**Implementation:**
```python
# In rag/pipeline.py
def smart_filter(query: str):
    filters = {}
    
    # Section-specific
    if match := re.search(r'Section (\d+)', query):
        filters['section_id'] = {'$contains': match.group(1)}
    
    # Document type
    if any(word in query.lower() for word in ['rule', 'form', 'gstr']):
        filters['source'] = {'$contains': 'rules'}
    
    return filters

# Use in retrieval
results = self.collection.query(
    query_texts=[query],
    n_results=30,
    where=smart_filter(query)  # Filter before search
)
```

**Files to modify:**
- `rag/pipeline.py` - Add metadata filtering

---

#### 7. Chunk Deduplication
**Expected:** 25s → 12-15s LLM time (fewer tokens)

**Implementation:**
```python
# In rag/pipeline.py
def deduplicate_chunks(chunks: List[Dict]) -> List[Dict]:
    # Remove overlapping chunks
    # Extract key sentences from each
    # Return 5 dense chunks instead of 10 verbose ones
    pass
```

---

## ✅ Success Criteria (End of Week 4)

| Metric | Before | Target | How |
|--------|--------|--------|-----|
| Response Time | 38s | <5s | Async + Re-ranker + Fewer chunks |
| Faithfulness | 57% | >70% | Re-ranker + Hierarchical chunks |
| Pass Rate | 40% | >85% | All improvements combined |
| Chunks to LLM | 10 | 5 | Re-ranker precision |

---

## 📝 Daily Checklist

### Day 1-2: Async Processing
- [ ] Convert `rag/pipeline.py` to async
- [ ] Add async methods to `llm/assistant.py`
- [ ] Update `main.py` for async
- [ ] Test with `--limit 5`
- [ ] Verify: 38s → 15-20s

### Day 3: Hybrid Search Boosting
- [ ] Add adaptive boosting to `rag/hybrid_search.py`
- [ ] Test section-specific queries
- [ ] Verify: Top-3 accuracy improved

### Day 4-7: Re-Ranking Layer
- [ ] Create `rag/reranker.py`
- [ ] Integrate into pipeline
- [ ] Update requirements.txt
- [ ] Test with `--limit 10`
- [ ] Verify: Faithfulness 57% → 70%+

### Day 8-10: Hierarchical Chunking
- [ ] Add hierarchical chunking to `rag/enhanced_chunker.py`
- [ ] Update ingestion script
- [ ] Re-ingest PDFs
- [ ] Update retrieval logic
- [ ] Test multi-part questions

### Day 11-14: Query Rewriting
- [ ] Create `rag/query_rewriter.py`
- [ ] Integrate into pipeline
- [ ] Test various query types

### Day 15-17: Metadata Filtering
- [ ] Add smart filtering to pipeline
- [ ] Test section-specific queries
- [ ] Measure speed improvement

### Day 18-20: Final Testing & Optimization
- [ ] Run full 50-question evaluation
- [ ] Verify all metrics meet targets
- [ ] Document learnings
- [ ] Update README

---

## 🚀 Commands Reference

```bash
# Quick test (5 questions)
python tests/evaluate_assistant.py --limit 5

# Full evaluation (50 questions)
python tests/evaluate_assistant.py

# Single question test
python main.py "What is Input Tax Credit?"

# View metrics
python view_metrics.py

# Clean and re-ingest (after chunking changes)
rm -rf chroma_db && python scripts/ingest_pdfs.py
```

---

## 📊 Tracking Progress

Create a spreadsheet or doc to track:

| Date | Change | Response Time | Faithfulness | Pass Rate | Notes |
|------|--------|---------------|--------------|-----------|-------|
| Jan 2 | Baseline (cross-page fix) | 38s | 57% | 40% | After chunking fix |
| Jan 3 | Async processing | TBD | TBD | TBD | Target: 15-20s |
| Jan 5 | Re-ranker | TBD | TBD | TBD | Target: 70%+ faith |
| Jan 8 | Hierarchical chunks | TBD | TBD | TBD | Target: 75%+ faith |
| ... | ... | ... | ... | ... | ... |
| Jan 20 | All improvements | <5s | >70% | >85% | **GOAL** |

---

## 🎯 After Phase 1 Complete

Once we hit targets (>85% pass rate, <5s response time):

1. **Document everything** - Write production deployment guide
2. **Prepare for Phase 2** - Design accounting database schema
3. **User testing** - Get real GST professionals to test
4. **Optimization round 2** - Fine-tune based on real usage

---

**Let's build! 🚀**

