# LedgerMind - Development Roadmap

> End-to-end technical roadmap for the Agentic AI CFO Platform

**Last Updated:** January 2026  
**Current Phase:** 1 Complete ✅ | Phase 2 Next

---

## Vision Statement

Build an **autonomous AI CFO** for MSMEs that:
- Transforms messy Excel/CSV data into structured insights
- Identifies tax savings and compliance risks automatically
- Provides strategic vendor and cash flow analysis
- Runs 100% locally with zero cloud dependency

---

## Phase Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DEVELOPMENT PHASES                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PHASE 1          PHASE 2          PHASE 3          PHASE 4                │
│  Foundation       Compliance       Intelligence     Production             │
│  ✅ COMPLETE      ◀── NEXT         Planned          Future                 │
│                                                                             │
│  ┌─────────┐      ┌─────────┐      ┌─────────┐      ┌─────────┐           │
│  │ DuckDB  │      │ Tax     │      │ Cash    │      │ Web UI  │           │
│  │ ChromaDB│      │ Rate    │      │ Flow    │      │ Reports │           │
│  │ 3 Agents│──────│ Verify  │──────│ Predict │──────│ API     │           │
│  │ Query   │      │ ITC     │      │ Vendor  │      │ Deploy  │           │
│  │ Classify│      │ 43B(h)  │      │ Score   │      │         │           │
│  │ Tests   │      │         │      │         │      │         │           │
│  └─────────┘      └─────────┘      └─────────┘      └─────────┘           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Foundation ✅ COMPLETE

### Summary

| Metric | Target | Achieved |
|--------|--------|----------|
| Core Modules | 14 | ✅ 15 |
| Reference Data Files | 3 | ✅ 6 |
| Knowledge Chunks | 500+ | ✅ 1,276 |
| Guardrails | 5 | ✅ 10 |
| Agents | 3 | ✅ 3 |
| Tests | 50+ | ✅ 121 |

### What Was Built

#### Core Infrastructure

| File | Purpose | Status |
|------|---------|--------|
| `core/data_engine.py` | DuckDB integration - Excel as SQL | ✅ |
| `core/knowledge.py` | ChromaDB RAG for legal documents | ✅ |
| `core/reference_data.py` | CSV data loading (clean separation) | ✅ |
| `core/query_classifier.py` | Routes queries to correct knowledge source | ✅ |
| `core/guardrails.py` | Input validation, safety checks | ✅ |
| `core/metrics.py` | Performance tracking | ✅ |
| `core/schema.py` | Standard Data Model definitions | ✅ |
| `core/mapper.py` | Header mapping logic | ✅ |

#### Agents

| File | Purpose | Status |
|------|---------|--------|
| `agents/discovery.py` | Scan files, map headers, create tables | ✅ |
| `agents/compliance.py` | Tax compliance checking framework | ✅ |
| `agents/strategist.py` | Strategic analysis framework | ✅ |

#### Reference Data (db/)

| Path | Contents | Records |
|------|----------|---------|
| `db/gst/slabs.csv` | Rate slab definitions | 4 |
| `db/gst/goods_hsn.csv` | HSN codes with rates | 89 |
| `db/gst/services_sac.csv` | SAC codes with rates | 50 |
| `db/gst/blocked_itc.csv` | Section 17(5) items | 15 |
| `db/msme/classification.csv` | MSME thresholds | 3 |
| `db/india/state_codes.csv` | GST state codes | 38 |

#### Test Suite

| File | Tests | Coverage |
|------|-------|----------|
| `test_config.py` | 10 | Config paths, settings |
| `test_reference_data.py` | 19 | CSV loading, lookups |
| `test_guardrails.py` | 17 | All validations |
| `test_query_classifier.py` | 20 | Query routing |
| `test_data_engine.py` | 8 | DuckDB ops |
| `test_knowledge.py` | 7 | ChromaDB search |
| `test_agents.py` | 10 | Agent init |
| `test_orchestration.py` | 10 | Router, workflow |
| `test_integration.py` | 20 | End-to-end |
| **Total** | **121** | |

### Key Technical Achievements

#### 1. Clean Separation of Concerns

```
config.py           → Paths, settings, prompts ONLY
core/reference_data.py → Data loading, rate lookups
```

#### 2. Query Classification System

```python
"What is CGST?"        → DEFINITION    → LLM general knowledge
"GST rate on milk?"    → RATE_LOOKUP   → CSV lookup
"Due date for GSTR-3B" → LEGAL_RULE    → ChromaDB RAG
"My total sales"       → DATA_QUERY    → DuckDB
```

#### 3. Production-Grade db/ Structure

```
db/
├── gst/              # All GST-related data
│   ├── slabs.csv
│   ├── goods_hsn.csv
│   ├── services_sac.csv
│   └── blocked_itc.csv
├── msme/             # MSME classification
│   └── classification.csv
└── india/            # India-specific
    └── state_codes.csv
```

#### 4. Guardrails (10 Methods)

```python
# Input validation
validate_gstin()           # GSTIN format check
validate_hsn_code()        # HSN format (4/6/8 digits)
validate_invoice_number()  # Invoice format
validate_date()            # Date validity
validate_amount()          # Amount bounds

# Business rules
validate_tax_calculation() # taxable + taxes = total
validate_itc_time_limit()  # Section 16(4)
validate_section_43b_h()   # 45-day MSME payment

# LLM safety
validate_llm_response_no_math()       # No arithmetic
validate_llm_response_has_citation()  # Sources required
```

---

## Phase 2: Compliance Engine (Next)

### Goals

Build the actual compliance checking logic that makes LedgerMind valuable.

| Feature | Description | Business Value |
|---------|-------------|----------------|
| Tax Rate Verification | Compare charged vs correct rate | Find overpaid GST |
| Section 43B(h) Monitoring | Track MSME payment deadlines | Avoid disallowed deductions |
| Section 17(5) Detection | Flag blocked ITC claims | Prevent reversals |
| ITC Reconciliation | Match with GSTR-2A/2B | Ensure claimable credits |
| Compliance Report | Actionable audit summary | One-click audit prep |

### Technical Milestones

#### 2.1 Tax Rate Verification

```python
def check_tax_rates(self) -> List[ComplianceIssue]:
    """Compare charged GST rate against correct rate from db/."""
    
    transactions = self.data_engine.query("""
        SELECT * FROM sdm_sales_register
        WHERE hsn_code IS NOT NULL
    """)
    
    issues = []
    for txn in transactions:
        correct_rate = get_rate_for_hsn(txn.hsn_code)
        if correct_rate and txn.gst_rate != correct_rate['rate']:
            issues.append(ComplianceIssue(
                issue_type="tax_rate_mismatch",
                severity="warning",
                description=f"HSN {txn.hsn_code}: Charged {txn.gst_rate}%, correct is {correct_rate['rate']}%",
                amount_impact=(txn.gst_rate - correct_rate['rate']) / 100 * txn.taxable_value
            ))
    
    return issues
```

#### 2.2 Section 43B(h) Monitoring

```python
def check_section_43b_h(self) -> List[ComplianceIssue]:
    """Flag payments to MSMEs overdue by >45 days."""
    
    purchases = self.data_engine.query("""
        SELECT vendor_name, vendor_gstin, invoice_date, total_value, payment_date
        FROM sdm_purchase_ledger
    """)
    
    issues = []
    for purchase in purchases:
        if is_msme_vendor(purchase.vendor_gstin):
            days_since = (date.today() - purchase.invoice_date).days
            if days_since > 45 and not purchase.payment_date:
                issues.append(ComplianceIssue(
                    issue_type="section_43b_h",
                    severity="critical",
                    description=f"Payment to {purchase.vendor_name} overdue by {days_since - 45} days",
                    amount_impact=purchase.total_value,
                    recommendation="Pay within 45 days to claim expense deduction"
                ))
    
    return issues
```

### Deliverables

- [ ] `check_tax_rates()` fully implemented
- [ ] `check_section_43b_h()` with MSME verification
- [ ] `check_blocked_credits()` with 15 blocked categories
- [ ] Compliance report generation
- [ ] Integration tests with sample data

---

## Phase 3: Strategic Intelligence

### Goals

| Feature | Description |
|---------|-------------|
| Vendor Scoring | Reliability score based on payment history |
| MSME Verification | Check if vendor is MSME for 43B(h) |
| Cash Flow Forecast | Predict next 3 months |
| Profit Analysis | Margin by product/customer |

### Technical Details

```python
@dataclass
class VendorScore:
    vendor_name: str
    gstin: str
    total_transactions: int
    total_value: float
    avg_payment_days: float
    is_msme: bool
    reliability_score: float  # 0-100
```

---

## Phase 4: Production

### Goals

| Feature | Description |
|---------|-------------|
| Web UI | FastAPI + Modern frontend |
| Reports | PDF/Excel export |
| API | REST endpoints for integration |
| Multi-company | Separate workspaces |

---

## Success Criteria

### Phase 1 ✅ (Complete)

- [x] Can load any Excel/CSV folder
- [x] Can query data with SQL
- [x] Can answer GST questions (definitions, rates, rules)
- [x] Query classifier routes to correct source
- [x] Guardrails validate inputs
- [x] CLI works end-to-end
- [x] 121 tests passing
- [x] Clean code structure (config vs reference_data)
- [x] Production-grade db/ folder organization

### Phase 2 (Next)

- [ ] Identifies 90%+ of tax rate mismatches
- [ ] Catches all Section 17(5) blocked credits
- [ ] Tracks 43B(h) compliance accurately
- [ ] Generates actionable compliance report

### Phase 3 (Planned)

- [ ] Vendor scores correlate with behavior
- [ ] Cash flow forecast within 20% accuracy
- [ ] Profit analysis matches manual calculation

### Phase 4 (Future)

- [ ] Web UI loads in < 2s
- [ ] Reports generate in < 10s
- [ ] Zero data leaks (local only)

---

## Immediate Next Steps

### This Week (Phase 2 Start)

1. **Implement `check_tax_rates()`**
   - Load transactions from DuckDB
   - Look up correct rate from `db/gst/goods_hsn.csv`
   - Flag mismatches with amount impact

2. **Implement `check_section_43b_h()`**
   - Load purchases
   - Calculate days since invoice
   - Flag overdue MSME payments

3. **Test with sample data**
   - Run compliance check
   - Verify issues detected
   - Calculate savings/risk

### Commands to Test

```bash
# Run all tests (should pass 121)
pytest tests/ -v

# Analyze sample data
python main.py "analyze folder workspace/sample_company/"

# Run compliance check
python main.py "run compliance check"

# Ask about rules
python main.py "What is Section 43B(h)?"
```

---

## Project Statistics

| Metric | Value |
|--------|-------|
| **Python Files** | 25+ |
| **Lines of Code** | ~5,000 |
| **Tests** | 121 |
| **CSV Data Files** | 6 |
| **Reference Data Records** | 200+ |
| **ChromaDB Chunks** | 1,276 |

---

## Resources

### Documentation
- [ARCHITECTURE.md](./ARCHITECTURE.md) - Technical architecture
- [README.md](../README.md) - Project overview
- [db/README.md](../db/README.md) - Reference data documentation

### External References
- [CBIC GST Portal](https://cbic-gst.gov.in/)
- [GST Notifications](https://www.gst.gov.in/)
- [DuckDB Docs](https://duckdb.org/docs/)
- [ChromaDB Docs](https://docs.trychroma.com/)

---

*Last Updated: January 2026*
