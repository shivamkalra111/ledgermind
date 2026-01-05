# LedgerMind - Development Roadmap

> End-to-end technical roadmap for building the Agentic AI CFO Platform

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
│  [2 weeks]        [3 weeks]        [3 weeks]        [2 weeks]              │
│                                                                             │
│  ┌─────────┐      ┌─────────┐      ┌─────────┐      ┌─────────┐           │
│  │ DuckDB  │      │ Tax     │      │ Cash    │      │ Web UI  │           │
│  │ Setup   │      │ Checks  │      │ Flow    │      │         │           │
│  │         │──────│         │──────│ Predict │──────│ Deploy  │           │
│  │ Discovery│     │ ITC     │      │         │      │         │           │
│  │ Agent   │      │ Verify  │      │ Vendor  │      │ API     │           │
│  │         │      │         │      │ Score   │      │         │           │
│  │ ChromaDB│      │ 43B(h)  │      │         │      │ Reports │           │
│  └─────────┘      └─────────┘      └─────────┘      └─────────┘           │
│                                                                             │
│  ◀─── WE ARE HERE                                                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Foundation (Weeks 1-2) ✅ COMPLETE

### Goals
- [x] Project structure and architecture
- [x] DuckDB integration for Excel/CSV
- [x] ChromaDB setup for GST rules (1,276 chunks)
- [x] Ollama/Qwen LLM integration
- [x] Basic Discovery Agent
- [x] GST rate database (89 goods + 50 services)
- [x] End-to-end CLI working
- [x] GST Basics knowledge (CGST, SGST, ITC, etc.)
- [x] Guardrails (GSTIN validation)
- [x] Query enhancement for better search

### Technical Milestones

#### 1.1 Data Engine (DuckDB)
```python
# Target capabilities
engine.load_excel("sales.xlsx")           # ✅ Done
engine.load_csv("purchases.csv")          # ✅ Done
engine.query("SELECT SUM(total) FROM sales")  # ✅ Done
engine.load_folder("/path/to/company/")   # ✅ Done
```

#### 1.2 Knowledge Base (ChromaDB)
```python
# Target capabilities
kb.ingest_pdf("gst_act.pdf")              # ✅ Done
kb.search("ITC eligibility")              # ✅ Done
kb.get_relevant_rules("blocked credits")  # ✅ Done
```

#### 1.3 Discovery Agent
```python
# Target capabilities
agent.discover("/path/to/folder")         # ✅ Done
# Returns: tables created, header mappings, sheet types
```

#### 1.4 Reference Data
```
db/
├── gst_rates_2025.json                   # ✅ Done (89 goods, 50 services)
├── gst_rates/goods_rates_2025.csv        # ✅ Done
├── gst_rates/services_rates_2025.csv     # ✅ Done
├── msme_classification.csv               # ✅ Done
└── state_codes.csv                       # ✅ Done
```

### Remaining Tasks (Phase 1)
- [x] Test Discovery Agent with real Excel files
- [x] Ingest GST PDFs into ChromaDB (1,276 chunks)
- [x] Fix any import/runtime errors
- [x] Basic CLI demo working
- [x] GST basics for common questions (CGST, SGST, ITC, etc.)

---

## Phase 2: Compliance Engine (Weeks 3-5)

### Goals
- [ ] Tax rate verification against GST 2025
- [ ] ITC eligibility checks
- [ ] Section 17(5) blocked credit detection
- [ ] Section 43B(h) payment monitoring
- [ ] Compliance report generation

### Technical Milestones

#### 2.1 Tax Rate Verification
```python
# Compare charged rate vs correct rate
def check_tax_rates(transactions: DataFrame) -> List[Issue]:
    for txn in transactions:
        hsn = txn.hsn_code
        charged_rate = txn.gst_rate
        correct_rate = get_rate_for_hsn(hsn)
        
        if charged_rate != correct_rate:
            yield TaxRateMismatch(
                item=txn.description,
                charged=charged_rate,
                correct=correct_rate,
                savings=(charged_rate - correct_rate) * txn.taxable_value
            )
```

#### 2.2 ITC Verification
```python
# Check ITC eligibility
def verify_itc(purchase: Dict) -> ITCStatus:
    # Check vendor GSTIN validity
    # Check if blocked under Section 17(5)
    # Check time limit (Section 16(4))
    # Return: eligible / blocked / expired
```

#### 2.3 Section 43B(h) Monitoring
```python
# Flag overdue payments to MSMEs
def check_43b_h(purchases: DataFrame, payments: DataFrame) -> List[Issue]:
    for purchase in purchases:
        if is_msme_vendor(purchase.vendor):
            days_since_invoice = (today - purchase.date).days
            if days_since_invoice > 45 and not is_paid(purchase):
                yield OverduePayment(
                    vendor=purchase.vendor,
                    amount=purchase.total,
                    days_overdue=days_since_invoice - 45,
                    consequence="Expense disallowed under Section 43B(h)"
                )
```

#### 2.4 Compliance Report
```python
@dataclass
class ComplianceReport:
    issues: List[ComplianceIssue]
    tax_savings_found: float
    risk_amount: float
    
    by_category: Dict[str, List[Issue]]
    # - tax_rate_mismatch
    # - blocked_credit
    # - overdue_payment
    # - invalid_gstin
    
    recommendations: List[str]
    summary: str
```

### Deliverables
- [ ] `agents/compliance.py` fully implemented
- [ ] Tax rate checker with HSN/SAC lookup
- [ ] Section 17(5) blocked credit detector
- [ ] Section 43B(h) payment tracker
- [ ] PDF compliance report generator

---

## Phase 3: Strategic Intelligence (Weeks 6-8)

### Goals
- [ ] Vendor reliability scoring
- [ ] MSME vendor identification
- [ ] Cash flow forecasting
- [ ] Profit margin analysis
- [ ] Tax liability projection

### Technical Milestones

#### 3.1 Vendor Analysis
```python
@dataclass
class VendorScore:
    vendor_name: str
    gstin: str
    
    # Reliability metrics
    total_transactions: int
    total_value: float
    avg_payment_days: float
    on_time_delivery_rate: float
    
    # Compliance metrics
    is_msme: bool
    msme_category: str  # micro/small/medium
    gstin_status: str   # active/cancelled/suspended
    
    # Risk score
    reliability_score: float  # 0-100
    risk_factors: List[str]
```

#### 3.2 Cash Flow Forecasting
```python
def forecast_cash_flow(
    sales_history: DataFrame,
    purchase_history: DataFrame,
    months: int = 3
) -> List[CashFlowForecast]:
    
    # Analyze historical patterns
    monthly_sales = aggregate_monthly(sales_history)
    monthly_purchases = aggregate_monthly(purchase_history)
    
    # Apply seasonality
    # Project forward
    # Estimate tax liability
    
    return forecasts
```

#### 3.3 Profit Analysis
```python
def analyze_profit_margins(
    sales: DataFrame,
    purchases: DataFrame
) -> ProfitAnalysis:
    
    # By product/service
    # By customer segment
    # By time period
    # After GST adjustment
```

### Deliverables
- [ ] `agents/strategist.py` fully implemented
- [ ] Vendor scoring algorithm
- [ ] MSME status checker (via API or manual input)
- [ ] Cash flow projection model
- [ ] Profit margin dashboard data

---

## Phase 4: Production (Weeks 9-10)

### Goals
- [ ] Web UI (FastAPI + React/HTMX)
- [ ] Report generation (PDF/Excel)
- [ ] Multi-company support
- [ ] API for integrations
- [ ] Deployment package

### Technical Milestones

#### 4.1 Web UI
```
Frontend:
├── Dashboard (summary cards)
├── Upload (drag-drop Excel/CSV)
├── Compliance (issues list)
├── Vendors (ranking table)
├── Forecast (charts)
└── Settings (company profile)
```

#### 4.2 API Design
```python
# FastAPI endpoints
POST /api/analyze          # Upload and analyze folder
GET  /api/compliance       # Get compliance report
GET  /api/vendors          # Get vendor rankings
GET  /api/forecast         # Get cash flow forecast
POST /api/query            # Natural language query
GET  /api/reports/{type}   # Download report
```

#### 4.3 Report Generation
```python
def generate_report(report_type: str, data: Dict) -> bytes:
    # Types: compliance_pdf, vendor_excel, forecast_pdf
    # Use reportlab for PDF
    # Use openpyxl for Excel
```

### Deliverables
- [ ] Web UI with all features
- [ ] PDF report generation
- [ ] Excel export
- [ ] Docker deployment
- [ ] User documentation

---

## Technical Specifications

### Performance Targets

| Operation | Target Time | Current |
|-----------|-------------|---------|
| Load 10 Excel files | < 5s | TBD |
| Compliance scan (1000 txns) | < 10s | TBD |
| Knowledge query | < 3s | TBD |
| Cash flow forecast | < 5s | TBD |

### Accuracy Targets

| Check | Target | Notes |
|-------|--------|-------|
| Tax rate matching | 95% | HSN/SAC coverage |
| Sheet type detection | 90% | LLM classification |
| Header mapping | 85% | SDM field mapping |
| ITC eligibility | 98% | Section 17(5) rules |

### Scale Targets

| Metric | Target |
|--------|--------|
| Files per folder | 50+ |
| Rows per file | 100,000+ |
| Concurrent queries | 10+ |
| Knowledge base size | 1000+ chunks |

---

## Risk Mitigation

### Technical Risks

| Risk | Mitigation |
|------|------------|
| LLM hallucination | JSON mode, validation, SQL for math |
| Slow DuckDB on large files | Indexing, chunked loading |
| ChromaDB memory usage | Persistent storage, lazy loading |
| Header mapping errors | User confirmation, learning |

### Business Risks

| Risk | Mitigation |
|------|------------|
| GST rate changes | Versioned db/, update scripts |
| MSME definition changes | Configurable thresholds |
| New compliance rules | Pluggable rule system |

---

## Success Criteria

### Phase 1 (Foundation)
- [ ] Can load any Excel/CSV folder
- [ ] Can query data with SQL
- [ ] Can answer GST questions via RAG
- [ ] CLI works end-to-end

### Phase 2 (Compliance)
- [ ] Identifies 90% of tax rate mismatches
- [ ] Catches all Section 17(5) blocked credits
- [ ] Tracks 43B(h) compliance accurately
- [ ] Generates actionable compliance report

### Phase 3 (Intelligence)
- [ ] Vendor scores correlate with payment behavior
- [ ] Cash flow forecast within 20% accuracy
- [ ] Profit analysis matches manual calculation
- [ ] Recommendations are actionable

### Phase 4 (Production)
- [ ] Web UI loads in < 2s
- [ ] Reports generate in < 10s
- [ ] System handles 10 concurrent users
- [ ] Zero data leaks (local only)

---

## Next Steps (Immediate)

### This Week
1. **Test Discovery Agent** with sample Excel files
2. **Ingest GST PDFs** into ChromaDB
3. **Fix runtime errors** in workflow
4. **Create sample data** for testing

### Next Week
1. **Implement tax rate checker** with full HSN lookup
2. **Add Section 17(5) detection**
3. **Build compliance report generator**
4. **Test with real company data**

---

## Resources

### Documentation
- [ARCHITECTURE.md](./ARCHITECTURE.md) - Technical architecture
- [README.md](../README.md) - Project overview

### External References
- [CBIC GST Portal](https://cbic-gst.gov.in/)
- [GST Notifications](https://www.gst.gov.in/)
- [DuckDB Docs](https://duckdb.org/docs/)
- [ChromaDB Docs](https://docs.trychroma.com/)
- [Ollama Docs](https://ollama.ai/)

---

*Last Updated: January 2026*

