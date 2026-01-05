"""
Guardrails - Safety checks and validation for LedgerMind
Ensures data quality, prevents hallucinations, and enforces business rules
"""

import re
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import date, datetime


class ValidationLevel(Enum):
    """Severity of validation issues."""
    ERROR = "error"      # Blocks processing
    WARNING = "warning"  # Proceeds with caution
    INFO = "info"        # Informational only


@dataclass
class ValidationResult:
    """Result of a validation check."""
    is_valid: bool
    level: ValidationLevel
    message: str
    field: Optional[str] = None
    value: Optional[Any] = None
    suggestion: Optional[str] = None


class Guardrails:
    """
    Safety guardrails for LedgerMind.
    
    Categories:
    1. Input Validation - Validate user inputs
    2. Data Quality - Check financial data integrity
    3. LLM Safety - Prevent hallucinations
    4. Business Rules - Enforce GST/compliance rules
    """
    
    # ==========================================================================
    # 1. INPUT VALIDATION
    # ==========================================================================
    
    @staticmethod
    def validate_gstin(gstin: str) -> ValidationResult:
        """
        Validate GSTIN format.
        Format: 2 digits state code + 10 char PAN + 1 entity code + 1 check digit + Z
        Example: 27AABCU9603R1ZM
        """
        if not gstin:
            return ValidationResult(
                is_valid=True,
                level=ValidationLevel.INFO,
                message="GSTIN not provided",
                field="gstin"
            )
        
        gstin = gstin.upper().strip()
        
        # Length check
        if len(gstin) != 15:
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message=f"GSTIN must be 15 characters, got {len(gstin)}",
                field="gstin",
                value=gstin,
                suggestion="Check GSTIN format: 27AABCU9603R1ZM"
            )
        
        # Format check
        pattern = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[A-Z0-9]{1}Z[A-Z0-9]{1}$'
        if not re.match(pattern, gstin):
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message="Invalid GSTIN format",
                field="gstin",
                value=gstin,
                suggestion="GSTIN format: 2 digits + 10 char PAN + entity + Z + check"
            )
        
        # State code check (01-37, 97, 99)
        state_code = int(gstin[:2])
        valid_states = list(range(1, 38)) + [97, 99]
        if state_code not in valid_states:
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message=f"Invalid state code: {state_code}",
                field="gstin",
                value=gstin
            )
        
        return ValidationResult(
            is_valid=True,
            level=ValidationLevel.INFO,
            message="Valid GSTIN",
            field="gstin",
            value=gstin
        )
    
    @staticmethod
    def validate_hsn_code(hsn: str) -> ValidationResult:
        """Validate HSN code format (4, 6, or 8 digits)."""
        if not hsn:
            return ValidationResult(
                is_valid=True,
                level=ValidationLevel.WARNING,
                message="HSN code not provided",
                field="hsn_code"
            )
        
        hsn = hsn.strip()
        
        # HSN should be numeric and 4, 6, or 8 digits
        if not hsn.isdigit():
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message="HSN code must be numeric",
                field="hsn_code",
                value=hsn
            )
        
        if len(hsn) not in [4, 6, 8]:
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.WARNING,
                message=f"HSN code should be 4, 6, or 8 digits, got {len(hsn)}",
                field="hsn_code",
                value=hsn
            )
        
        return ValidationResult(
            is_valid=True,
            level=ValidationLevel.INFO,
            message="Valid HSN code",
            field="hsn_code",
            value=hsn
        )
    
    @staticmethod
    def validate_invoice_number(invoice_no: str) -> ValidationResult:
        """Validate invoice number format."""
        if not invoice_no:
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message="Invoice number is required",
                field="invoice_number"
            )
        
        invoice_no = str(invoice_no).strip()
        
        # Max length check (16 chars as per GST)
        if len(invoice_no) > 16:
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.WARNING,
                message=f"Invoice number exceeds 16 characters",
                field="invoice_number",
                value=invoice_no
            )
        
        # Special characters check
        if not re.match(r'^[A-Za-z0-9/-]+$', invoice_no):
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.WARNING,
                message="Invoice number contains invalid characters",
                field="invoice_number",
                value=invoice_no,
                suggestion="Use only alphanumeric, /, -"
            )
        
        return ValidationResult(
            is_valid=True,
            level=ValidationLevel.INFO,
            message="Valid invoice number",
            field="invoice_number",
            value=invoice_no
        )
    
    @staticmethod
    def validate_amount(amount: Any, field_name: str = "amount") -> ValidationResult:
        """Validate monetary amount."""
        try:
            amount = float(amount)
        except (TypeError, ValueError):
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message=f"{field_name} must be a valid number",
                field=field_name,
                value=amount
            )
        
        if amount < 0:
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.WARNING,
                message=f"{field_name} is negative",
                field=field_name,
                value=amount,
                suggestion="Verify if this is correct"
            )
        
        # Suspiciously large amount
        if amount > 100_00_00_000:  # 100 crore
            return ValidationResult(
                is_valid=True,
                level=ValidationLevel.WARNING,
                message=f"{field_name} is very large: ₹{amount:,.0f}",
                field=field_name,
                value=amount,
                suggestion="Verify this amount"
            )
        
        return ValidationResult(
            is_valid=True,
            level=ValidationLevel.INFO,
            message=f"Valid {field_name}",
            field=field_name,
            value=amount
        )
    
    # ==========================================================================
    # 2. DATA QUALITY CHECKS
    # ==========================================================================
    
    @staticmethod
    def validate_tax_calculation(
        taxable_value: float,
        cgst: float,
        sgst: float,
        igst: float,
        total: float,
        tolerance: float = 1.0  # ₹1 tolerance for rounding
    ) -> ValidationResult:
        """Validate GST calculation consistency."""
        
        # Calculate expected total
        expected_total = taxable_value + cgst + sgst + igst
        difference = abs(total - expected_total)
        
        if difference > tolerance:
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message=f"Tax calculation mismatch. Expected ₹{expected_total:.2f}, got ₹{total:.2f}",
                field="total_value",
                value={"taxable": taxable_value, "cgst": cgst, "sgst": sgst, "igst": igst, "total": total},
                suggestion=f"Difference of ₹{difference:.2f}"
            )
        
        # CGST and SGST should be equal (intra-state)
        if cgst > 0 and sgst > 0 and abs(cgst - sgst) > tolerance:
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.WARNING,
                message=f"CGST (₹{cgst}) and SGST (₹{sgst}) should be equal",
                field="tax",
                suggestion="Check if this is an intra-state transaction"
            )
        
        # IGST should be exclusive (inter-state)
        if igst > 0 and (cgst > 0 or sgst > 0):
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message="IGST and CGST/SGST cannot both be applied",
                field="tax",
                suggestion="Use IGST for inter-state, CGST+SGST for intra-state"
            )
        
        return ValidationResult(
            is_valid=True,
            level=ValidationLevel.INFO,
            message="Tax calculation is correct"
        )
    
    @staticmethod
    def validate_date(
        date_value: Any,
        field_name: str = "date",
        min_date: Optional[date] = None,
        max_date: Optional[date] = None
    ) -> ValidationResult:
        """Validate date field."""
        
        if date_value is None:
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message=f"{field_name} is required",
                field=field_name
            )
        
        # Convert to date if needed
        if isinstance(date_value, datetime):
            date_value = date_value.date()
        elif isinstance(date_value, str):
            try:
                date_value = datetime.strptime(date_value, "%Y-%m-%d").date()
            except ValueError:
                return ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.ERROR,
                    message=f"Invalid date format: {date_value}",
                    field=field_name,
                    suggestion="Use YYYY-MM-DD format"
                )
        
        # Future date check
        if date_value > date.today():
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.WARNING,
                message=f"{field_name} is in the future",
                field=field_name,
                value=date_value
            )
        
        # Min/max bounds
        if min_date and date_value < min_date:
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.WARNING,
                message=f"{field_name} is before {min_date}",
                field=field_name,
                value=date_value
            )
        
        if max_date and date_value > max_date:
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.WARNING,
                message=f"{field_name} is after {max_date}",
                field=field_name,
                value=date_value
            )
        
        return ValidationResult(
            is_valid=True,
            level=ValidationLevel.INFO,
            message=f"Valid {field_name}",
            field=field_name,
            value=date_value
        )
    
    # ==========================================================================
    # 3. LLM SAFETY GUARDRAILS
    # ==========================================================================
    
    @staticmethod
    def validate_llm_response_no_math(response: str) -> ValidationResult:
        """
        Ensure LLM response doesn't contain arithmetic.
        LLM should use SQL/Python for calculations, not do math itself.
        """
        
        # Patterns that suggest LLM is doing math
        math_patterns = [
            r'\d+\s*[\+\-\*\/]\s*\d+\s*=',  # "100 + 200 ="
            r'=\s*₹?\s*[\d,]+',              # "= ₹300"
            r'total(?:s|ing)?\s*(?:to|=|is)\s*₹?\s*[\d,]+',  # "totals to ₹500"
            r'sum\s*(?:of|=|is)\s*₹?\s*[\d,]+',
        ]
        
        for pattern in math_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                return ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.WARNING,
                    message="LLM appears to be doing arithmetic",
                    field="llm_response",
                    suggestion="Use SQL or Python for calculations"
                )
        
        return ValidationResult(
            is_valid=True,
            level=ValidationLevel.INFO,
            message="LLM response does not contain arithmetic"
        )
    
    @staticmethod
    def validate_llm_response_has_citation(response: str) -> ValidationResult:
        """Check if LLM response cites sources when discussing rules."""
        
        # Keywords that suggest rules are being discussed
        rule_keywords = ["section", "rule", "act", "notification", "circular", "gst"]
        
        has_rule_discussion = any(kw in response.lower() for kw in rule_keywords)
        
        if not has_rule_discussion:
            return ValidationResult(
                is_valid=True,
                level=ValidationLevel.INFO,
                message="Response does not discuss rules"
            )
        
        # Check for citations
        citation_patterns = [
            r'section\s+\d+',           # Section 17
            r'rule\s+\d+',              # Rule 36
            r'notification\s+\d+',      # Notification 12/2017
            r'circular\s+\d+',          # Circular 123
        ]
        
        has_citation = any(re.search(p, response, re.IGNORECASE) for p in citation_patterns)
        
        if not has_citation:
            return ValidationResult(
                is_valid=True,
                level=ValidationLevel.WARNING,
                message="Response discusses rules but lacks specific citations",
                suggestion="Add section/rule numbers for verification"
            )
        
        return ValidationResult(
            is_valid=True,
            level=ValidationLevel.INFO,
            message="Response includes rule citations"
        )
    
    # ==========================================================================
    # 4. BUSINESS RULES
    # ==========================================================================
    
    @staticmethod
    def validate_itc_time_limit(invoice_date: date) -> ValidationResult:
        """
        Check if ITC can still be claimed.
        Time limit: 30th Nov of following FY or annual return date, whichever earlier.
        """
        
        today = date.today()
        
        # Determine FY of invoice
        if invoice_date.month <= 3:
            invoice_fy_end = date(invoice_date.year, 3, 31)
        else:
            invoice_fy_end = date(invoice_date.year + 1, 3, 31)
        
        # ITC deadline is 30th Nov of following FY
        itc_deadline = date(invoice_fy_end.year + 1, 11, 30)
        
        if today > itc_deadline:
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message=f"ITC time limit expired on {itc_deadline}",
                field="itc_eligibility",
                value=invoice_date,
                suggestion="ITC cannot be claimed for this invoice"
            )
        
        days_remaining = (itc_deadline - today).days
        if days_remaining < 30:
            return ValidationResult(
                is_valid=True,
                level=ValidationLevel.WARNING,
                message=f"ITC deadline approaching: {days_remaining} days remaining",
                field="itc_eligibility",
                value=invoice_date,
                suggestion=f"Claim ITC before {itc_deadline}"
            )
        
        return ValidationResult(
            is_valid=True,
            level=ValidationLevel.INFO,
            message=f"ITC can be claimed. Deadline: {itc_deadline}",
            field="itc_eligibility"
        )
    
    @staticmethod
    def validate_section_43b_h(
        invoice_date: date,
        payment_date: Optional[date],
        is_msme_vendor: bool
    ) -> ValidationResult:
        """
        Check Section 43B(h) compliance.
        Payment to MSMEs must be within 45 days.
        """
        
        if not is_msme_vendor:
            return ValidationResult(
                is_valid=True,
                level=ValidationLevel.INFO,
                message="Section 43B(h) not applicable (non-MSME vendor)"
            )
        
        today = date.today()
        days_since_invoice = (today - invoice_date).days
        
        if payment_date:
            payment_days = (payment_date - invoice_date).days
            if payment_days > 45:
                return ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.ERROR,
                    message=f"Payment made after 45 days ({payment_days} days)",
                    field="section_43b_h",
                    suggestion="Expense may be disallowed under Section 43B(h)"
                )
            return ValidationResult(
                is_valid=True,
                level=ValidationLevel.INFO,
                message=f"Payment made within time limit ({payment_days} days)"
            )
        
        # Not yet paid
        if days_since_invoice > 45:
            overdue_days = days_since_invoice - 45
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message=f"Payment overdue by {overdue_days} days",
                field="section_43b_h",
                suggestion="Pay immediately to avoid expense disallowance"
            )
        
        days_remaining = 45 - days_since_invoice
        if days_remaining < 7:
            return ValidationResult(
                is_valid=True,
                level=ValidationLevel.WARNING,
                message=f"Payment due in {days_remaining} days",
                field="section_43b_h",
                suggestion="Pay before 45-day limit"
            )
        
        return ValidationResult(
            is_valid=True,
            level=ValidationLevel.INFO,
            message=f"Payment due in {days_remaining} days"
        )


# Convenience functions
def validate_transaction(transaction: Dict) -> List[ValidationResult]:
    """Run all validations on a transaction."""
    results = []
    g = Guardrails()
    
    # Basic validations
    if "gstin" in transaction:
        results.append(g.validate_gstin(transaction["gstin"]))
    
    if "hsn_code" in transaction:
        results.append(g.validate_hsn_code(transaction["hsn_code"]))
    
    if "invoice_number" in transaction:
        results.append(g.validate_invoice_number(transaction["invoice_number"]))
    
    if "invoice_date" in transaction:
        results.append(g.validate_date(transaction["invoice_date"], "invoice_date"))
    
    # Amount validations
    for field in ["taxable_value", "total_value", "cgst_amount", "sgst_amount", "igst_amount"]:
        if field in transaction:
            results.append(g.validate_amount(transaction[field], field))
    
    # Tax calculation check
    if all(k in transaction for k in ["taxable_value", "total_value"]):
        results.append(g.validate_tax_calculation(
            transaction.get("taxable_value", 0),
            transaction.get("cgst_amount", 0),
            transaction.get("sgst_amount", 0),
            transaction.get("igst_amount", 0),
            transaction.get("total_value", 0)
        ))
    
    return results


def get_validation_summary(results: List[ValidationResult]) -> Dict:
    """Summarize validation results."""
    errors = [r for r in results if r.level == ValidationLevel.ERROR and not r.is_valid]
    warnings = [r for r in results if r.level == ValidationLevel.WARNING]
    
    return {
        "is_valid": len(errors) == 0,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": [{"field": r.field, "message": r.message} for r in errors],
        "warnings": [{"field": r.field, "message": r.message} for r in warnings]
    }

