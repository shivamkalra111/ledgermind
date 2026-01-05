"""
Reference Data Module

Handles loading and accessing structured reference data from CSV files:
- GST rates (goods, services)
- GST slabs (0%, 5%, 18%, 28%)
- MSME classification thresholds
- Blocked credits (Section 17(5))
- State codes

ALL data comes from CSV files in the db/ folder.
This is the SINGLE SOURCE OF TRUTH for reference data.
"""

import csv
from pathlib import Path
from typing import Dict, List, Optional, Any


# =============================================================================
# PATHS (from config.py)
# =============================================================================

from config import (
    GST_SLABS_FILE,
    GOODS_RATES_FILE,
    SERVICES_RATES_FILE,
    BLOCKED_CREDITS_FILE,
    MSME_FILE,
    STATE_CODES_FILE,
)


# =============================================================================
# CACHES (for performance)
# =============================================================================

_goods_cache: Optional[List[Dict]] = None
_services_cache: Optional[List[Dict]] = None
_blocked_cache: Optional[List[Dict]] = None
_msme_cache: Optional[List[Dict]] = None
_state_codes_cache: Optional[List[Dict]] = None
_slabs_cache: Optional[List[Dict]] = None


def _load_csv(filepath: Path) -> List[Dict]:
    """Generic CSV loader."""
    if not filepath.exists():
        return []
    with open(filepath, "r") as f:
        reader = csv.DictReader(f)
        return list(reader)


# =============================================================================
# GST SLABS
# =============================================================================

def load_gst_slabs() -> List[Dict]:
    """
    Load GST slab definitions from CSV.
    
    Returns:
        List of dicts with: slab_name, rate, description, examples
    """
    global _slabs_cache
    if _slabs_cache is None:
        _slabs_cache = _load_csv(GST_SLABS_FILE)
    return _slabs_cache


def get_gst_slabs() -> Dict[str, Dict]:
    """
    Get GST slabs as a dictionary.
    
    Returns:
        Dict like: {"exempt": {"rate": 0, "description": "..."}, ...}
    """
    slabs = load_gst_slabs()
    return {
        s["slab_name"]: {
            "rate": int(s["rate"]),
            "description": s["description"],
            "examples": s.get("examples", "")
        }
        for s in slabs
    }


# =============================================================================
# GOODS RATES (HSN codes)
# =============================================================================

def load_goods_rates() -> List[Dict]:
    """
    Load goods GST rates from CSV.
    
    Returns:
        List of dicts with keys: hsn_code, item_name, gst_rate, cess_rate, category
    """
    global _goods_cache
    if _goods_cache is None:
        _goods_cache = _load_csv(GOODS_RATES_FILE)
    return _goods_cache


def get_rate_for_hsn(hsn_code: str) -> Optional[Dict]:
    """
    Get GST rate for a given HSN code (goods).
    
    Args:
        hsn_code: 4, 6, or 8 digit HSN code
        
    Returns:
        Dict with rate, cess, item, category or None if not found
    """
    rates = load_goods_rates()
    
    for rate in rates:
        if rate["hsn_code"] == hsn_code:
            return {
                "rate": int(rate["gst_rate"]),
                "cess": rate.get("cess_rate", "0"),
                "item": rate["item_name"],
                "category": rate["category"]
            }
        # Check for chapter/range matches (e.g., "01-05" for chapters 01 to 05)
        if "-" in rate["hsn_code"]:
            start, end = rate["hsn_code"].split("-")
            if hsn_code.startswith(start[:2]):
                return {
                    "rate": int(rate["gst_rate"]),
                    "cess": rate.get("cess_rate", "0"),
                    "item": rate["item_name"],
                    "category": rate["category"]
                }
    
    return None


# =============================================================================
# SERVICES RATES (SAC codes)
# =============================================================================

def load_services_rates() -> List[Dict]:
    """
    Load services GST rates from CSV.
    
    Returns:
        List of dicts with keys: sac_code, service_name, gst_rate, category
    """
    global _services_cache
    if _services_cache is None:
        _services_cache = _load_csv(SERVICES_RATES_FILE)
    return _services_cache


def get_rate_for_sac(sac_code: str) -> Optional[Dict]:
    """
    Get GST rate for a given SAC code (services).
    
    Args:
        sac_code: 4 or 6 digit SAC code
        
    Returns:
        Dict with rate, service, category, condition or None if not found
    """
    rates = load_services_rates()
    
    for rate in rates:
        if rate["sac_code"] == sac_code:
            return {
                "rate": int(rate["gst_rate"]),
                "service": rate["service_name"],
                "category": rate["category"],
                "condition": rate.get("condition", "")
            }
    
    return None


# =============================================================================
# BLOCKED CREDITS (Section 17(5))
# =============================================================================

def load_blocked_credits() -> List[Dict]:
    """
    Load Section 17(5) blocked credits from CSV.
    Items where ITC cannot be claimed.
    
    Returns:
        List of dicts with keys: item, section, description
    """
    global _blocked_cache
    if _blocked_cache is None:
        _blocked_cache = _load_csv(BLOCKED_CREDITS_FILE)
    return _blocked_cache


def is_blocked_credit(item_description: str) -> bool:
    """Check if an item is under Section 17(5) blocked credits."""
    blocked = load_blocked_credits()
    desc_lower = item_description.lower()
    
    for blocked_item in blocked:
        if blocked_item["item"].lower() in desc_lower:
            return True
    return False


# =============================================================================
# MSME CLASSIFICATION
# =============================================================================

def load_msme_classification() -> List[Dict]:
    """
    Load MSME classification limits from CSV.
    
    Returns:
        List of dicts with: category, turnover_limit_inr, investment_limit_inr
    """
    global _msme_cache
    if _msme_cache is None:
        _msme_cache = _load_csv(MSME_FILE)
    return _msme_cache


def get_msme_classification() -> Dict[str, Dict]:
    """
    Get MSME classification as a dictionary.
    
    Returns:
        Dict like: {"micro": {"turnover_limit": 50000000, ...}, ...}
    """
    msme = load_msme_classification()
    return {
        m["category"]: {
            "turnover_limit": int(m["turnover_limit_inr"]),
            "investment_limit": int(m["investment_limit_inr"]),
            "description": m.get("description", "")
        }
        for m in msme
    }


def get_msme_category(turnover: float) -> str:
    """
    Determine MSME category based on turnover.
    
    Args:
        turnover: Annual turnover in rupees
        
    Returns:
        'micro', 'small', 'medium', or 'large'
    """
    classification = get_msme_classification()
    
    if turnover <= classification.get("micro", {}).get("turnover_limit", 50000000):
        return "micro"
    elif turnover <= classification.get("small", {}).get("turnover_limit", 500000000):
        return "small"
    elif turnover <= classification.get("medium", {}).get("turnover_limit", 2500000000):
        return "medium"
    else:
        return "large"


# =============================================================================
# STATE CODES
# =============================================================================

def load_state_codes() -> List[Dict]:
    """
    Load GST state codes from CSV.
    
    Returns:
        List of dicts with: code, state_name, state_type, region
    """
    global _state_codes_cache
    if _state_codes_cache is None:
        _state_codes_cache = _load_csv(STATE_CODES_FILE)
    return _state_codes_cache


def get_state_codes() -> Dict[str, str]:
    """
    Get state codes as a dictionary.
    
    Returns:
        Dict like: {"27": "Maharashtra", "29": "Karnataka", ...}
    """
    states = load_state_codes()
    return {s["code"]: s["state_name"] for s in states}


def get_state_name(code: str) -> Optional[str]:
    """Get state name from code."""
    states = get_state_codes()
    return states.get(code)


# =============================================================================
# COMPLIANCE RULES
# =============================================================================

def get_compliance_rules() -> Dict:
    """
    Get compliance rules.
    Currently returns hardcoded rules - can be moved to CSV later.
    """
    return {
        "section_43b_h": {
            "description": "Payment to MSMEs within 45 days",
            "days_limit": 45,
            "penalty": "Disallowance of expense deduction"
        },
        "section_17_5": {
            "description": "Blocked Input Tax Credit",
            "items": [item["item"] for item in load_blocked_credits()]
        },
        "itc_time_limit": {
            "description": "ITC claim deadline",
            "deadline": "30th November of following FY or annual return, whichever earlier"
        }
    }


# =============================================================================
# SEARCH FUNCTIONS
# =============================================================================

def search_rate_by_name(item_name: str) -> Optional[Dict]:
    """
    Search for GST rate by item/service name (fuzzy match).
    
    Args:
        item_name: Name to search for
        
    Returns:
        Dict with rate info or None if not found
    """
    item_lower = item_name.lower()
    
    # Search goods first
    for rate in load_goods_rates():
        if item_lower in rate["item_name"].lower():
            return {
                "type": "goods",
                "hsn_code": rate["hsn_code"],
                "item": rate["item_name"],
                "rate": int(rate["gst_rate"]),
                "cess": rate.get("cess_rate", "0"),
                "category": rate["category"]
            }
    
    # Then search services
    for rate in load_services_rates():
        if item_lower in rate["service_name"].lower():
            return {
                "type": "services",
                "sac_code": rate["sac_code"],
                "service": rate["service_name"],
                "rate": int(rate["gst_rate"]),
                "category": rate["category"]
            }
    
    return None


# =============================================================================
# VALIDATION HELPERS
# =============================================================================

def is_valid_gst_rate(rate: int) -> bool:
    """Check if a rate is a valid GST slab."""
    valid_rates = {0, 5, 12, 18, 28}  # Current slabs
    return rate in valid_rates


def is_valid_state_code(code: str) -> bool:
    """Check if a state code is valid."""
    return code in get_state_codes()
