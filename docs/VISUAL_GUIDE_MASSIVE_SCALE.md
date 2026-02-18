# Visual Guide: Massive Scale Table Selection

## The Problem Visualized

```
┌─────────────────────────────────────────────────────────────────┐
│ USER'S DATABASE: 500 TABLES                                     │
│                                                                  │
│ purchase_2015_01, purchase_2015_02, ..., purchase_2024_12      │
│ sales_2015_01, sales_2015_02, ..., sales_2024_12               │
│ inventory_2020_01, ..., bank_statement_q1_2015, ...            │
│ vendor_master, customer_master, product_master, ...            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ User Query:
                              │ "What are my total purchases for 2023?"
                              ▼
        ┌───────────────────────────────────────────┐
        │  ❌ OLD APPROACH: Show all to LLM         │
        └───────────────────────────────────────────┘
                              │
                              ▼
        ┌───────────────────────────────────────────┐
        │  500 tables × 100 chars = 50,000 chars   │
        │  = 12,500 tokens                          │
        │                                           │
        │  ⚠️  CONTEXT OVERFLOW!                    │
        │  32,768 token limit exceeded              │
        └───────────────────────────────────────────┘
```

---

## The Solution: Three-Stage Funnel

```
                    🔍 THREE-STAGE FUNNEL
                         
┌─────────────────────────────────────────────────────────────────┐
│                     500 TABLES                                   │
│  purchase_2015_01, purchase_2015_02, ..., sales_2024_12, ...   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ User Query:
                              │ "What are my total purchases for 2023?"
                              ▼
        ╔═══════════════════════════════════════════╗
        ║  STAGE 1: VECTOR SEARCH                  ║
        ║  Semantic Similarity (Cosine Distance)   ║
        ╚═══════════════════════════════════════════╝
                              │
                              │ • Embed query: "total purchases 2023"
                              │ • Compare with all 500 table embeddings
                              │ • Select top 20 most similar
                              │
                              │ ⚡ Token Cost: 0 (no LLM call!)
                              │ ⏱️  Time: ~50ms
                              ▼
        ┌───────────────────────────────────────────┐
        │  20 CANDIDATES                            │
        │  purchase_2023_01, purchase_2023_02, ... │
        │  purchase_2023_12, purchase_2022_12, ... │
        └───────────────────────────────────────────┘
                              │
                              ▼
        ╔═══════════════════════════════════════════╗
        ║  STAGE 2: FAMILY EXPANSION               ║
        ║  Pattern Matching                        ║
        ╚═══════════════════════════════════════════╝
                              │
                              │ • Detect: "purchase_2023_*" family
                              │ • Query wants "total" → include all
                              │ • Expand to full family (12 months)
                              │
                              │ ⚡ Token Cost: 0 (pattern matching)
                              │ ⏱️  Time: ~5ms
                              ▼
        ┌───────────────────────────────────────────┐
        │  12 TABLES (Family Expanded)              │
        │  purchase_2023_01, purchase_2023_02, ... │
        │  purchase_2023_12                         │
        └───────────────────────────────────────────┘
                              │
                              ▼
        ╔═══════════════════════════════════════════╗
        ║  STAGE 3: LLM REFINEMENT                 ║
        ║  Semantic Understanding                  ║
        ╚═══════════════════════════════════════════╝
                              │
                              │ • Build brief catalog (12 × 100 = 1,200 chars)
                              │ • Show to LLM: "Pick relevant tables"
                              │ • LLM confirms: All 12 needed for "total"
                              │
                              │ ⚡ Token Cost: ~500 tokens
                              │ ⏱️  Time: ~2s
                              ▼
        ┌───────────────────────────────────────────┐
        │  FINAL SELECTION: 12 TABLES               │
        │  purchase_2023_01, purchase_2023_02, ... │
        │  purchase_2023_12                         │
        └───────────────────────────────────────────┘
                              │
                              ▼
        ╔═══════════════════════════════════════════╗
        ║  SQL GENERATION                          ║
        ║  With Full Context                       ║
        ╚═══════════════════════════════════════════╝
                              │
                              │ • Get compressed schema (12 × 100 = 1,200 chars)
                              │ • Add few-shot examples (~1,000 chars)
                              │ • Total context: ~2,700 chars (~675 tokens)
                              │
                              ▼
        ┌───────────────────────────────────────────┐
        │  SQL QUERY                                │
        │  SELECT SUM(amount) FROM (                │
        │    SELECT amount FROM purchase_2023_01    │
        │    UNION ALL ...                          │
        │  )                                        │
        └───────────────────────────────────────────┘
```

---

## Token Usage Comparison

```
┌─────────────────────────────────────────────────────────────────┐
│                    TOKEN USAGE BREAKDOWN                         │
└─────────────────────────────────────────────────────────────────┘

OLD APPROACH (Naive):
├─ Full Catalog: 500 × 100 chars = 50,000 chars = 12,500 tokens
├─ System Prompt: 500 tokens
├─ Few-Shot: 300 tokens
├─ Response Buffer: 500 tokens
└─ TOTAL: 13,800 tokens ❌ OVERFLOW (42% of context!)

NEW APPROACH (Vector Search):
├─ Stage 1 (Vector Search): 0 tokens ✅
├─ Stage 2 (Family Expansion): 0 tokens ✅
├─ Stage 3 (LLM Refinement): 
│   ├─ Candidate Catalog: 20 × 100 = 2,000 chars = 500 tokens
│   └─ System Prompt: 200 tokens
├─ SQL Generation:
│   ├─ Compressed Schema: 12 × 100 = 1,200 chars = 300 tokens
│   ├─ Few-Shot: 300 tokens
│   └─ System Prompt: 200 tokens
└─ TOTAL: 1,500 tokens ✅ (4.6% of context!)

SAVINGS: 12,300 tokens (89% reduction!)
```

---

## Scale Comparison

```
┌────────────────────────────────────────────────────────────────┐
│           HOW IT SCALES WITH TABLE COUNT                       │
└────────────────────────────────────────────────────────────────┘

Tables │ Old Approach      │ New Approach       │ Token Savings
───────┼───────────────────┼────────────────────┼──────────────
  10   │ ~2,500 tokens     │ ~2,000 tokens      │ 20% ✅
  50   │ ~6,250 tokens     │ ~1,800 tokens      │ 71% ✅
 100   │ ~12,500 tokens    │ ~1,500 tokens      │ 88% ✅
 500   │ ~62,500 tokens ❌ │ ~1,500 tokens ✅   │ 98% ✅
1000   │ ~125,000 tokens ❌│ ~1,500 tokens ✅   │ 99% ✅

Legend:
✅ = Fits in context (< 32,768 tokens)
❌ = Context overflow
```

---

## The Magic: Vector Search (Stage 1)

```
┌────────────────────────────────────────────────────────────────┐
│           HOW VECTOR SEARCH WORKS                              │
└────────────────────────────────────────────────────────────────┘

SETUP (One-Time):
┌───────────────────────────────────────────────────────────────┐
│ For each table, create rich text:                             │
│                                                                │
│ "Table: purchase_2023_07 |                                    │
│  Description: Purchase transactions for 07/2023 |             │
│  Columns: date, vendor, invoice_no, amount, cgst, sgst |      │
│  Keywords: purchase, vendor, 2023, 7 |                        │
│  Sample: date=2023-07-01, vendor=ABC Corp, amount=10000"      │
│                                                                │
│ ↓ Embedding Model (all-MiniLM-L6-v2)                          │
│                                                                │
│ [0.123, -0.456, 0.789, ..., 0.234]  (384 dimensions)         │
│                                                                │
│ Store in memory: {table_name: embedding_vector}               │
└───────────────────────────────────────────────────────────────┘

QUERY (Every Time):
┌───────────────────────────────────────────────────────────────┐
│ User Query: "What are my total purchases for 2023?"           │
│                                                                │
│ ↓ Embedding Model                                             │
│                                                                │
│ Query Vector: [0.234, -0.345, 0.567, ..., 0.123]             │
│                                                                │
│ ↓ Cosine Similarity with all 500 table vectors                │
│                                                                │
│ Similarity Scores:                                             │
│   purchase_2023_01: 0.923 ⭐                                   │
│   purchase_2023_02: 0.918 ⭐                                   │
│   purchase_2023_03: 0.915 ⭐                                   │
│   ...                                                          │
│   sales_2023_01: 0.512                                        │
│   vendor_master: 0.234                                        │
│                                                                │
│ ↓ Select Top 20                                               │
│                                                                │
│ Result: [purchase_2023_01, purchase_2023_02, ...]            │
│                                                                │
│ ⚡ Token Cost: 0 (pure math, no LLM!)                         │
│ ⏱️  Time: ~50ms for 500 tables                                │
└───────────────────────────────────────────────────────────────┘
```

---

## Adaptive Schema Detail

```
┌────────────────────────────────────────────────────────────────┐
│           PROGRESSIVE SCHEMA DETAIL                            │
└────────────────────────────────────────────────────────────────┘

Selected Tables │ Detail Level  │ Chars/Table │ Total (10 tables)
────────────────┼───────────────┼─────────────┼──────────────────
    3-5         │ FULL          │ ~750        │ ~3,750 chars ✅
    5-10        │ MEDIUM        │ ~300        │ ~3,000 chars ✅
    10-20       │ COMPRESSED    │ ~100        │ ~2,000 chars ✅
    20+         │ COMPRESSED    │ ~100        │ ~2,000 chars ✅


FULL DETAIL (~750 chars):
┌───────────────────────────────────────────────────────────────┐
│ TABLE: purchase_2023_07                                        │
│   Source: purchase_july_2023.xlsx                             │
│   Description: Purchase transactions for July 2023            │
│   Date range: 2023-07-01 to 2023-07-31                        │
│   Columns:                                                     │
│     "date" (DATE) - Transaction date                          │
│     "vendor" (VARCHAR) - Vendor name                          │
│     "amount" (DOUBLE) - Amount before tax                     │
│     "cgst" (DOUBLE) - Central GST                             │
│     "sgst" (DOUBLE) - State GST                               │
│     "total" (DOUBLE) - Total with tax                         │
│   Key stats: vendor: 87 unique, invoice_no: 450 unique        │
│   Totals: amount: 2,250,000.00, total: 2,655,000.00          │
│   Sample data:                                                │
│     date='2023-07-01', vendor='ABC Corp', amount=10000, ...   │
│   Total rows: 450                                             │
└───────────────────────────────────────────────────────────────┘

MEDIUM DETAIL (~300 chars):
┌───────────────────────────────────────────────────────────────┐
│ TABLE: purchase_2023_07                                        │
│   Description: Purchase transactions for July 2023            │
│   Columns:                                                     │
│     - date (DATE): Transaction date                           │
│     - vendor (VARCHAR): Vendor name                           │
│     - amount (DOUBLE): Amount before tax                      │
│     - cgst (DOUBLE): Central GST                              │
│     - sgst (DOUBLE): State GST                                │
│     - total (DOUBLE): Total with tax                          │
└───────────────────────────────────────────────────────────────┘

COMPRESSED DETAIL (~100 chars):
┌───────────────────────────────────────────────────────────────┐
│ purchase_2023_07(date DATE, vendor VARCHAR, amount DOUBLE,    │
│                  cgst DOUBLE, sgst DOUBLE, total DOUBLE)      │
└───────────────────────────────────────────────────────────────┘

💡 LLM can generate correct SQL from just column names + types!
```

---

## End-to-End Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    COMPLETE QUERY FLOW                           │
└─────────────────────────────────────────────────────────────────┘

User: "What are my total purchases for 2023?"
                              │
                              ▼
        ┌───────────────────────────────────────┐
        │  API Layer (query.py)                 │
        │  • Input sanitization                 │
        │  • Prompt injection check             │
        └───────────────────────────────────────┘
                              │
                              ▼
        ┌───────────────────────────────────────┐
        │  Router (router.py)                   │
        │  • Intent: DATA_QUERY                 │
        └───────────────────────────────────────┘
                              │
                              ▼
        ┌───────────────────────────────────────┐
        │  Orchestrator (graph.py)              │
        │  • Check table count: 500 tables      │
        │  • Trigger: Massive scale mode        │
        └───────────────────────────────────────┘
                              │
                              ▼
        ┌───────────────────────────────────────┐
        │  Scale Detection                      │
        │  • num_tables > 100? YES              │
        │  • Initialize vector search           │
        └───────────────────────────────────────┘
                              │
                              ▼
        ╔═══════════════════════════════════════╗
        ║  STAGE 1: Vector Search               ║
        ║  500 → 20 candidates                  ║
        ║  Token cost: 0, Time: 50ms            ║
        ╚═══════════════════════════════════════╝
                              │
                              ▼
        ╔═══════════════════════════════════════╗
        ║  STAGE 2: Family Expansion            ║
        ║  20 → 12 (purchase_2023_* family)     ║
        ║  Token cost: 0, Time: 5ms             ║
        ╚═══════════════════════════════════════╝
                              │
                              ▼
        ╔═══════════════════════════════════════╗
        ║  STAGE 3: LLM Refinement              ║
        ║  12 → 12 confirmed                    ║
        ║  Token cost: 500, Time: 2s            ║
        ╚═══════════════════════════════════════╝
                              │
                              ▼
        ┌───────────────────────────────────────┐
        │  Schema Builder                       │
        │  • 12 tables selected                 │
        │  • Use: COMPRESSED (12 × 100 chars)   │
        └───────────────────────────────────────┘
                              │
                              ▼
        ┌───────────────────────────────────────┐
        │  SQL Generator (client.py)            │
        │  • Context: ~2,700 chars (~675 tokens)│
        │  • Generate: UNION ALL query          │
        └───────────────────────────────────────┘
                              │
                              ▼
        ┌───────────────────────────────────────┐
        │  SQL Validator (security.py)          │
        │  • Check: SELECT only                 │
        │  • Block: DELETE/DROP/INSERT          │
        └───────────────────────────────────────┘
                              │
                              ▼
        ┌───────────────────────────────────────┐
        │  DuckDB Execution (data_engine.py)    │
        │  • Execute validated SQL              │
        │  • Return results                     │
        └───────────────────────────────────────┘
                              │
                              ▼
        ┌───────────────────────────────────────┐
        │  Response Formatter                   │
        │  • Format as markdown table           │
        │  • Add metadata                       │
        └───────────────────────────────────────┘
                              │
                              ▼
                      User sees result!

Total Time: ~2-3 seconds
Total Tokens: ~1,500 (vs 12,500 for old approach!)
```

---

## Interview Diagram: The Funnel

```
Show this on whiteboard:


    500 TABLES
    ███████████████████
    ███████████████████
    ███████████████████
          │
          │ Vector Search (0 tokens)
          ▼
    20 CANDIDATES
    ████████
          │
          │ Family Expansion (0 tokens)
          ▼
    12 RELATED
    █████
          │
          │ LLM Refinement (~500 tokens)
          ▼
    5 FINAL
    ██
          │
          │ SQL Generation
          ▼
    ⚡ RESULT


Key Points to Say:
1. "Stage 1 uses vector similarity - no LLM, no tokens"
2. "Stage 2 detects patterns like purchase_2023_*"
3. "Stage 3 is smart - LLM only sees 20, not 500"
4. "Total: 96% token reduction, same query time"
```

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────────┐
│              MASSIVE SCALE QUICK REFERENCE                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ TRIGGER: num_tables > 100                                       │
│                                                                  │
│ STAGE 1: Vector Search                                          │
│   • Method: Cosine similarity                                   │
│   • Input: 500 tables                                           │
│   • Output: Top 20 candidates                                   │
│   • Cost: 0 tokens, ~50ms                                       │
│                                                                  │
│ STAGE 2: Family Expansion                                       │
│   • Method: Pattern matching (regex)                            │
│   • Detects: table_YYYY_MM patterns                             │
│   • For "total" queries: Include all family                     │
│   • Cost: 0 tokens, ~5ms                                        │
│                                                                  │
│ STAGE 3: LLM Refinement                                         │
│   • Input: 20 candidates (2,000 chars)                          │
│   • Output: 3-5 final tables                                    │
│   • Cost: ~500 tokens, ~2s                                      │
│                                                                  │
│ SCHEMA DETAIL:                                                  │
│   • 3-5 tables   → FULL (750 chars/table)                       │
│   • 5-10 tables  → MEDIUM (300 chars/table)                     │
│   • 10+ tables   → COMPRESSED (100 chars/table)                 │
│                                                                  │
│ TOTAL TOKEN SAVINGS: 96%                                        │
│   • Old: 12,500 tokens (overflow!)                              │
│   • New: 500 tokens (fits easily)                               │
│                                                                  │
│ FALLBACKS:                                                      │
│   • No sentence-transformers → Standard LLM selection           │
│   • LLM fails → Use vector search top-K                         │
│   • Vector search fails → Keyword matching                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

Use these visuals in interviews to quickly explain the system! 🎨
