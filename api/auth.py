# LedgerMind API Authentication
"""
API Key authentication for customer access.

Security model:
- Each customer gets unique API keys (can have multiple)
- Keys are prefixed with "lm_live_" for production, "lm_test_" for testing
- Keys are hashed before storage
- Rate limiting per key (future)
"""

import os
import json
import hashlib
import secrets
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple
from fastapi import HTTPException, Security, Depends
from fastapi.security import APIKeyHeader

from config import WORKSPACE_DIR


# =============================================================================
# Constants
# =============================================================================

API_KEY_PREFIX_LIVE = "lm_live_"
API_KEY_PREFIX_TEST = "lm_test_"
API_KEYS_FILE = WORKSPACE_DIR / ".api_keys.json"

# API key header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


# =============================================================================
# Key Management Functions
# =============================================================================

def generate_api_key(is_test: bool = False) -> str:
    """Generate a new API key."""
    prefix = API_KEY_PREFIX_TEST if is_test else API_KEY_PREFIX_LIVE
    random_part = secrets.token_urlsafe(32)
    return f"{prefix}{random_part}"


def hash_api_key(api_key: str) -> str:
    """Hash an API key for storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()


def load_api_keys() -> dict:
    """Load API keys from storage."""
    if not API_KEYS_FILE.exists():
        return {"keys": {}}
    
    try:
        with open(API_KEYS_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"keys": {}}


def save_api_keys(data: dict) -> None:
    """Save API keys to storage."""
    API_KEYS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(API_KEYS_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)


def create_api_key(customer_id: str, name: str = "default", is_test: bool = False) -> str:
    """
    Create a new API key for a customer.
    
    Returns the plain API key (only shown once).
    """
    api_key = generate_api_key(is_test)
    key_hash = hash_api_key(api_key)
    
    data = load_api_keys()
    
    # Store by hash
    data["keys"][key_hash] = {
        "customer_id": customer_id,
        "name": name,
        "created_at": datetime.now().isoformat(),
        "last_used": None,
        "is_active": True,
        "is_test": is_test,
        # Store prefix for display (first 12 chars)
        "key_prefix": api_key[:12] + "..."
    }
    
    save_api_keys(data)
    
    return api_key


def validate_api_key(api_key: str) -> Optional[dict]:
    """
    Validate an API key and return customer info if valid.
    
    Returns None if invalid.
    """
    if not api_key:
        return None
    
    # Check prefix
    if not (api_key.startswith(API_KEY_PREFIX_LIVE) or 
            api_key.startswith(API_KEY_PREFIX_TEST)):
        return None
    
    key_hash = hash_api_key(api_key)
    data = load_api_keys()
    
    key_info = data["keys"].get(key_hash)
    if not key_info:
        return None
    
    if not key_info.get("is_active", True):
        return None
    
    # Update last used
    key_info["last_used"] = datetime.now().isoformat()
    save_api_keys(data)
    
    return key_info


def revoke_api_key(api_key: str) -> bool:
    """Revoke an API key."""
    key_hash = hash_api_key(api_key)
    data = load_api_keys()
    
    if key_hash in data["keys"]:
        data["keys"][key_hash]["is_active"] = False
        save_api_keys(data)
        return True
    
    return False


def list_customer_keys(customer_id: str) -> list:
    """List all API keys for a customer (shows prefixes only)."""
    data = load_api_keys()
    
    keys = []
    for key_hash, info in data["keys"].items():
        if info.get("customer_id") == customer_id:
            keys.append({
                "key_prefix": info.get("key_prefix", "lm_..."),
                "name": info.get("name", "default"),
                "created_at": info.get("created_at"),
                "last_used": info.get("last_used"),
                "is_active": info.get("is_active", True),
                "is_test": info.get("is_test", False)
            })
    
    return keys


# =============================================================================
# FastAPI Dependency
# =============================================================================

async def get_current_customer(
    api_key: Optional[str] = Security(api_key_header)
) -> Tuple[str, dict]:
    """
    FastAPI dependency to authenticate and get current customer.
    
    Returns (customer_id, key_info) tuple.
    
    Raises HTTPException if authentication fails.
    """
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Include X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    key_info = validate_api_key(api_key)
    
    if not key_info:
        raise HTTPException(
            status_code=401,
            detail="Invalid or revoked API key.",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    customer_id = key_info["customer_id"]
    
    # Verify customer workspace exists
    customer_path = WORKSPACE_DIR / customer_id
    if not customer_path.exists():
        raise HTTPException(
            status_code=403,
            detail=f"Customer workspace not found. Contact support."
        )
    
    return customer_id, key_info

