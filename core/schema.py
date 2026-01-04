"""
Standard Data Model (SDM) Definitions
Canonical schema for all financial data
"""

from dataclasses import dataclass
from typing import Optional, List
from datetime import date, datetime
from enum import Enum


class SheetType(Enum):
    """Types of financial sheets."""
    SALES_REGISTER = "sales_register"
    PURCHASE_LEDGER = "purchase_ledger"
    BANK_STATEMENT = "bank_statement"
    TAX_RETURNS = "tax_returns"
    VENDOR_MASTER = "vendor_master"
    UNKNOWN = "unknown"


class GSTRate(Enum):
    """GST 2026 tax rates."""
    EXEMPT = 0
    MERIT = 5
    STANDARD = 18
    LUXURY = 40


@dataclass
class StandardInvoice:
    """Standard invoice schema (Sales/Purchase)."""
    
    # Required fields
    invoice_number: str
    invoice_date: date
    party_name: str
    taxable_value: float
    total_value: float
    
    # Optional fields
    party_gstin: Optional[str] = None
    place_of_supply: Optional[str] = None
    hsn_code: Optional[str] = None
    description: Optional[str] = None
    quantity: Optional[float] = None
    rate: Optional[float] = None
    
    # Tax breakdown
    cgst_rate: Optional[float] = None
    cgst_amount: Optional[float] = None
    sgst_rate: Optional[float] = None
    sgst_amount: Optional[float] = None
    igst_rate: Optional[float] = None
    igst_amount: Optional[float] = None
    
    # Compliance
    is_reverse_charge: bool = False
    is_itc_eligible: bool = True


@dataclass
class StandardBankTransaction:
    """Standard bank transaction schema."""
    
    transaction_date: date
    description: str
    
    # One of these should be filled
    credit_amount: Optional[float] = None
    debit_amount: Optional[float] = None
    
    # Optional
    reference_number: Optional[str] = None
    balance: Optional[float] = None
    category: Optional[str] = None  # Mapped category


@dataclass
class VendorMaster:
    """Vendor/Supplier master data."""
    
    vendor_name: str
    
    # GST details
    gstin: Optional[str] = None
    pan: Optional[str] = None
    
    # MSME details (Section 43B(h))
    is_msme: bool = False
    msme_category: Optional[str] = None  # micro, small, medium
    msme_registration: Optional[str] = None
    
    # Payment terms
    payment_terms_days: int = 30
    
    # Contact
    address: Optional[str] = None
    state: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


# Header mapping suggestions for common variations
HEADER_ALIASES = {
    # Invoice fields
    "invoice_number": ["inv no", "invoice no", "bill no", "voucher no", "doc no"],
    "invoice_date": ["inv date", "date", "bill date", "doc date", "voucher date"],
    "party_name": ["customer", "vendor", "party", "name", "customer name", "vendor name", "supplier"],
    "party_gstin": ["gstin", "gst no", "gst number", "gstin/uin"],
    
    # Value fields
    "taxable_value": ["taxable", "taxable amt", "taxable amount", "base amount", "net amount"],
    "total_value": ["total", "total amt", "total amount", "gross amount", "invoice value", "bill amount"],
    
    # Tax fields
    "cgst_amount": ["cgst", "cgst amt", "central tax"],
    "sgst_amount": ["sgst", "sgst amt", "state tax"],
    "igst_amount": ["igst", "igst amt", "integrated tax"],
    
    # Bank fields
    "credit_amount": ["credit", "cr", "deposit", "receipt"],
    "debit_amount": ["debit", "dr", "withdrawal", "payment"],
    "balance": ["balance", "running balance", "closing balance"],
    
    # Common fields
    "description": ["desc", "particulars", "narration", "details", "item"],
    "hsn_code": ["hsn", "hsn code", "sac", "sac code"],
    "quantity": ["qty", "quantity", "units"],
    "rate": ["rate", "price", "unit price"],
}


def get_sdm_field(header: str) -> Optional[str]:
    """Try to match a header to a Standard Data Model field."""
    header_lower = header.lower().strip()
    
    for sdm_field, aliases in HEADER_ALIASES.items():
        if header_lower == sdm_field:
            return sdm_field
        if header_lower in aliases:
            return sdm_field
    
    return None

