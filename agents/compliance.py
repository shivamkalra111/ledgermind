"""
Compliance Agent - ITC Checks, Reconciliation, Section 43B(h) Monitoring
Cross-references user data against GST rules from ChromaDB
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import date, timedelta

from core.data_engine import DataEngine
from core.knowledge import KnowledgeBase
from llm.client import LLMClient
from config import (
    COMPLIANCE_OVERDUE_DAYS,
    GST_SLABS_2026,
    COMPLIANCE_PROMPT
)


@dataclass
class ComplianceIssue:
    """A compliance issue found in the data."""
    issue_type: str
    severity: str  # "critical", "warning", "info"
    description: str
    amount_impact: Optional[float] = None
    recommendation: str = ""
    reference: str = ""  # GST section reference


@dataclass 
class ComplianceReport:
    """Complete compliance report."""
    issues: List[ComplianceIssue]
    total_tax_savings: float
    total_risk_amount: float
    summary: str


class ComplianceAgent:
    """
    Agent 2: Compliance (Auditor)
    
    Responsibilities:
    - Check tax rates against 2026 GST slabs
    - Verify ITC eligibility
    - Detect Section 17(5) blocked credits
    - Monitor Section 43B(h) compliance (45-day payment rule)
    - Reconcile sales vs bank credits
    """
    
    def __init__(
        self,
        data_engine: Optional[DataEngine] = None,
        knowledge_base: Optional[KnowledgeBase] = None,
        llm_client: Optional[LLMClient] = None
    ):
        self.data_engine = data_engine or DataEngine()
        self.knowledge = knowledge_base or KnowledgeBase()
        self.llm = llm_client
        
    def run_full_audit(self) -> ComplianceReport:
        """Run a complete compliance audit on loaded data."""
        
        all_issues = []
        
        # Run individual checks
        all_issues.extend(self.check_tax_rates())
        all_issues.extend(self.check_blocked_credits())
        all_issues.extend(self.check_section_43b_h())
        
        # Calculate totals
        total_savings = sum(
            i.amount_impact for i in all_issues 
            if i.amount_impact and i.issue_type == "tax_rate_mismatch"
        )
        
        total_risk = sum(
            i.amount_impact for i in all_issues
            if i.amount_impact and i.severity == "critical"
        )
        
        # Generate summary
        summary = self._generate_summary(all_issues, total_savings, total_risk)
        
        return ComplianceReport(
            issues=all_issues,
            total_tax_savings=total_savings,
            total_risk_amount=total_risk,
            summary=summary
        )
    
    def check_tax_rates(self) -> List[ComplianceIssue]:
        """Check if correct GST rates are being applied."""
        
        issues = []
        
        # Check if purchase data exists
        tables = self.data_engine.list_tables()
        purchase_tables = [t for t in tables if 'purchase' in t.lower()]
        
        if not purchase_tables:
            return issues
        
        # Query purchase data (simplified - actual implementation would be more robust)
        try:
            for table in purchase_tables:
                # Get sample transactions to check
                df = self.data_engine.query(f"""
                    SELECT * FROM {table} LIMIT 100
                """)
                
                # Check each row for rate issues
                for _, row in df.iterrows():
                    issue = self._check_single_rate(row.to_dict())
                    if issue:
                        issues.append(issue)
                        
        except Exception as e:
            print(f"Error checking tax rates: {e}")
        
        return issues
    
    def _check_single_rate(self, transaction: Dict) -> Optional[ComplianceIssue]:
        """Check a single transaction for rate issues."""
        
        # Look for description/item field
        description = ""
        for key in ["description", "item", "particulars", "narration"]:
            if key in transaction:
                description = str(transaction[key]).lower()
                break
        
        if not description:
            return None
        
        # Look for tax rate in transaction
        tax_rate = None
        taxable_value = 0
        
        for key in ["cgst_rate", "tax_rate", "gst_rate"]:
            if key in transaction and transaction[key]:
                tax_rate = float(transaction[key]) * 2  # CGST is half
                break
        
        for key in ["taxable_value", "taxable_amount", "base_amount"]:
            if key in transaction and transaction[key]:
                taxable_value = float(transaction[key])
                break
        
        if tax_rate is None:
            return None
        
        # Check against 2026 slabs
        correct_rate = self._get_correct_rate(description)
        
        if correct_rate is not None and abs(tax_rate - correct_rate) > 0.5:
            # Rate mismatch found
            tax_diff = (tax_rate - correct_rate) / 100 * taxable_value
            
            return ComplianceIssue(
                issue_type="tax_rate_mismatch",
                severity="warning" if tax_diff > 0 else "info",
                description=f"Item '{description[:50]}' charged at {tax_rate}% but 2026 rate is {correct_rate}%",
                amount_impact=abs(tax_diff) if tax_diff > 0 else None,
                recommendation=f"Verify GST rate. Potential {'overpayment' if tax_diff > 0 else 'underpayment'}.",
                reference="GST 2026 Rate Notification"
            )
        
        return None
    
    def _get_correct_rate(self, description: str) -> Optional[float]:
        """Get correct GST rate for an item based on 2026 slabs."""
        
        description_lower = description.lower()
        
        for slab_name, slab_info in GST_SLABS_2026.items():
            for item in slab_info["items"]:
                if item in description_lower:
                    return slab_info["rate"]
        
        return None
    
    def check_blocked_credits(self) -> List[ComplianceIssue]:
        """Check for Section 17(5) blocked credits."""
        
        issues = []
        
        # Blocked credit categories
        blocked_keywords = [
            ("food", "beverages", "catering"),
            ("club", "membership"),
            ("personal vehicle", "motor vehicle"),
            ("beauty", "health services"),
            ("travel benefits", "leave travel"),
        ]
        
        # Check purchase tables
        tables = self.data_engine.list_tables()
        purchase_tables = [t for t in tables if 'purchase' in t.lower()]
        
        for table in purchase_tables:
            try:
                df = self.data_engine.query(f"SELECT * FROM {table}")
                
                for _, row in df.iterrows():
                    description = ""
                    for key in ["description", "item", "particulars"]:
                        if key in row and row[key]:
                            description = str(row[key]).lower()
                            break
                    
                    for keywords in blocked_keywords:
                        if any(kw in description for kw in keywords):
                            # Get tax amount
                            tax_amount = 0
                            for key in ["cgst_amount", "tax_amount", "gst_amount"]:
                                if key in row and row[key]:
                                    tax_amount = float(row[key]) * 2
                                    break
                            
                            issues.append(ComplianceIssue(
                                issue_type="blocked_credit",
                                severity="warning",
                                description=f"ITC blocked under Section 17(5): {description[:50]}",
                                amount_impact=tax_amount if tax_amount > 0 else None,
                                recommendation="Reverse this ITC as it's not eligible under Section 17(5)",
                                reference="Section 17(5) CGST Act"
                            ))
                            break
                            
            except Exception as e:
                print(f"Error checking blocked credits in {table}: {e}")
        
        return issues
    
    def check_section_43b_h(self) -> List[ComplianceIssue]:
        """Check for Section 43B(h) compliance - 45 day payment to MSEs."""
        
        issues = []
        
        # This would require vendor master data with MSME status
        # and payment tracking. Simplified implementation:
        
        tables = self.data_engine.list_tables()
        purchase_tables = [t for t in tables if 'purchase' in t.lower()]
        
        for table in purchase_tables:
            try:
                # Check for invoices without payment info that might be overdue
                df = self.data_engine.query(f"""
                    SELECT * FROM {table}
                    WHERE 1=1
                    LIMIT 100
                """)
                
                # Look for date fields and check if >45 days old
                for _, row in df.iterrows():
                    invoice_date = None
                    for key in ["invoice_date", "bill_date", "date"]:
                        if key in row and row[key]:
                            try:
                                invoice_date = row[key]
                                if hasattr(invoice_date, 'date'):
                                    invoice_date = invoice_date.date()
                                break
                            except:
                                pass
                    
                    if invoice_date:
                        days_old = (date.today() - invoice_date).days if isinstance(invoice_date, date) else 0
                        
                        if days_old > COMPLIANCE_OVERDUE_DAYS:
                            amount = 0
                            for key in ["total_value", "total_amount", "bill_amount"]:
                                if key in row and row[key]:
                                    amount = float(row[key])
                                    break
                            
                            vendor = ""
                            for key in ["vendor", "party_name", "supplier"]:
                                if key in row and row[key]:
                                    vendor = str(row[key])
                                    break
                            
                            issues.append(ComplianceIssue(
                                issue_type="section_43b_h",
                                severity="critical",
                                description=f"Payment to '{vendor[:30]}' overdue by {days_old - COMPLIANCE_OVERDUE_DAYS} days (45-day limit)",
                                amount_impact=amount,
                                recommendation="If vendor is MSME, this expense may be disallowed as tax deduction",
                                reference="Section 43B(h) Income Tax Act"
                            ))
                            
            except Exception as e:
                print(f"Error checking 43B(h) in {table}: {e}")
        
        return issues
    
    def _generate_summary(
        self,
        issues: List[ComplianceIssue],
        total_savings: float,
        total_risk: float
    ) -> str:
        """Generate a human-readable compliance summary."""
        
        critical = len([i for i in issues if i.severity == "critical"])
        warnings = len([i for i in issues if i.severity == "warning"])
        info = len([i for i in issues if i.severity == "info"])
        
        summary = f"""
## 📋 Compliance Audit Summary

**Issues Found:** {len(issues)}
- 🔴 Critical: {critical}
- 🟡 Warnings: {warnings}  
- 🔵 Info: {info}

**Financial Impact:**
- Potential Tax Savings: ₹{total_savings:,.0f}
- Amount at Risk: ₹{total_risk:,.0f}
"""
        
        if critical > 0:
            summary += "\n⚠️ **Immediate attention required for critical issues!**"
        
        return summary

