"""
Customer Context Manager

Handles customer-specific data isolation.
Each customer has their own:
- workspace folder
- DuckDB database
- data files

Shared resources (read-only for all customers):
- Reference data (db/)
- Legal knowledge (knowledge/)
- ChromaDB (chroma_db/)
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime

from config import WORKSPACE_DIR


# =============================================================================
# CUSTOMER DATA MODEL
# =============================================================================

@dataclass
class CustomerProfile:
    """Customer profile information."""
    
    customer_id: str                    # Unique identifier (folder name)
    company_name: str                   # Display name
    gstin: Optional[str] = None         # Company GSTIN (if registered)
    email: Optional[str] = None         # Contact email
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_accessed: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Business details
    business_type: str = "trading"      # trading, services, manufacturing
    turnover_category: str = "micro"    # micro, small, medium
    state_code: str = "27"              # Default: Maharashtra
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "CustomerProfile":
        return cls(**data)


# =============================================================================
# CUSTOMER CONTEXT
# =============================================================================

class CustomerContext:
    """
    Manages customer-specific data isolation.
    
    Each customer gets:
    - workspace/{customer_id}/           # Root folder
    - workspace/{customer_id}/data/      # Excel/CSV files
    - workspace/{customer_id}/{id}.duckdb # Customer's database
    - workspace/{customer_id}/profile.json # Customer metadata
    
    Usage:
        customer = CustomerContext("acme_corp")
        customer.ensure_exists()
        
        # Load customer's data
        engine = customer.get_data_engine()
        engine.load_folder(customer.data_dir)
        
        # Query is now scoped to this customer only
        results = engine.query("SELECT * FROM sales")
    """
    
    def __init__(self, customer_id: str):
        """
        Initialize customer context.
        
        Args:
            customer_id: Unique identifier (used as folder name)
                        Must be lowercase, alphanumeric with underscores
        """
        self.customer_id = self._validate_customer_id(customer_id)
        
        # Paths (all scoped to this customer)
        self.root_dir = WORKSPACE_DIR / self.customer_id
        self.data_dir = self.root_dir / "data"
        self.duckdb_path = self.root_dir / f"{self.customer_id}.duckdb"
        self.profile_path = self.root_dir / "profile.json"
        
        # Profile (loaded lazily)
        self._profile: Optional[CustomerProfile] = None
        self._data_engine = None
    
    @staticmethod
    def _validate_customer_id(customer_id: str) -> str:
        """Validate and normalize customer ID."""
        # Normalize
        customer_id = customer_id.lower().strip()
        customer_id = customer_id.replace(" ", "_").replace("-", "_")
        
        # Validate
        if not customer_id:
            raise ValueError("Customer ID cannot be empty")
        
        if not customer_id.replace("_", "").isalnum():
            raise ValueError(
                f"Customer ID must be alphanumeric with underscores only: {customer_id}"
            )
        
        if len(customer_id) > 50:
            raise ValueError(f"Customer ID too long (max 50 chars): {customer_id}")
        
        # Reserved names
        reserved = {"sample_company", "test", "admin", "system", "default"}
        if customer_id in reserved:
            raise ValueError(f"Reserved customer ID: {customer_id}")
        
        return customer_id
    
    # =========================================================================
    # LIFECYCLE
    # =========================================================================
    
    def exists(self) -> bool:
        """Check if customer workspace exists."""
        return self.root_dir.exists() and self.profile_path.exists()
    
    def ensure_exists(self) -> None:
        """Create customer workspace if it doesn't exist."""
        self.root_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(exist_ok=True)
        
        # Create profile if doesn't exist
        if not self.profile_path.exists():
            self._profile = CustomerProfile(
                customer_id=self.customer_id,
                company_name=self.customer_id.replace("_", " ").title()
            )
            self._save_profile()
    
    def delete(self) -> None:
        """Delete customer workspace (use with caution!)."""
        import shutil
        if self.root_dir.exists():
            shutil.rmtree(self.root_dir)
        self._profile = None
        self._data_engine = None
    
    # =========================================================================
    # PROFILE
    # =========================================================================
    
    @property
    def profile(self) -> CustomerProfile:
        """Get customer profile (lazy loaded)."""
        if self._profile is None:
            self._load_profile()
        return self._profile
    
    def _load_profile(self) -> None:
        """Load profile from disk."""
        if self.profile_path.exists():
            with open(self.profile_path, "r") as f:
                data = json.load(f)
            self._profile = CustomerProfile.from_dict(data)
        else:
            # Create default profile
            self._profile = CustomerProfile(
                customer_id=self.customer_id,
                company_name=self.customer_id.replace("_", " ").title()
            )
    
    def _save_profile(self) -> None:
        """Save profile to disk."""
        if self._profile:
            with open(self.profile_path, "w") as f:
                json.dump(self._profile.to_dict(), f, indent=2)
    
    def update_profile(self, **kwargs) -> None:
        """Update profile fields."""
        profile = self.profile  # Load if needed
        
        for key, value in kwargs.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        
        profile.last_accessed = datetime.now().isoformat()
        self._save_profile()
    
    # =========================================================================
    # DATA ENGINE
    # =========================================================================
    
    def get_data_engine(self):
        """
        Get customer-specific data engine.
        
        Returns a DataEngine connected to this customer's DuckDB file.
        """
        # Import here to avoid circular imports
        from core.data_engine import DataEngine
        
        if self._data_engine is None:
            self._data_engine = DataEngine(self.duckdb_path)
        
        return self._data_engine
    
    def close(self) -> None:
        """Close data engine connection."""
        if self._data_engine:
            self._data_engine.close()
            self._data_engine = None
    
    # =========================================================================
    # DATA FILES
    # =========================================================================
    
    def list_data_files(self) -> List[Dict[str, Any]]:
        """List all data files in customer's data directory."""
        files = []
        
        if not self.data_dir.exists():
            return files
        
        for file_path in self.data_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in [".xlsx", ".xls", ".csv"]:
                stat = file_path.stat()
                files.append({
                    "name": file_path.name,
                    "path": str(file_path),
                    "type": file_path.suffix.lower(),
                    "size_bytes": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
        
        return sorted(files, key=lambda x: x["name"])
    
    def get_data_file_path(self, filename: str) -> Path:
        """Get full path for a data file."""
        return self.data_dir / filename
    
    # =========================================================================
    # CONTEXT MANAGER
    # =========================================================================
    
    def __enter__(self):
        """Enter context - ensure workspace exists."""
        self.ensure_exists()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context - close connections."""
        self.close()
    
    def __repr__(self):
        return f"CustomerContext('{self.customer_id}')"


# =============================================================================
# CUSTOMER MANAGER
# =============================================================================

class CustomerManager:
    """
    Manages all customers.
    
    Usage:
        manager = CustomerManager()
        
        # List all customers
        customers = manager.list_customers()
        
        # Create new customer
        customer = manager.create_customer("acme_corp", company_name="Acme Corporation")
        
        # Get existing customer
        customer = manager.get_customer("acme_corp")
    """
    
    def __init__(self, workspace_dir: Path = WORKSPACE_DIR):
        self.workspace_dir = workspace_dir
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
    
    def list_customers(self) -> List[Dict[str, Any]]:
        """List all customers with basic info."""
        customers = []
        
        for item in self.workspace_dir.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                profile_path = item / "profile.json"
                
                if profile_path.exists():
                    try:
                        with open(profile_path, "r") as f:
                            profile_data = json.load(f)
                        customers.append({
                            "customer_id": item.name,
                            "company_name": profile_data.get("company_name", item.name),
                            "gstin": profile_data.get("gstin"),
                            "last_accessed": profile_data.get("last_accessed"),
                            "path": str(item)
                        })
                    except (json.JSONDecodeError, KeyError):
                        # Invalid profile, skip
                        pass
                elif item.name == "sample_company":
                    # Legacy sample company (no profile)
                    customers.append({
                        "customer_id": "sample_company",
                        "company_name": "Sample Company (Demo)",
                        "gstin": None,
                        "last_accessed": None,
                        "path": str(item)
                    })
        
        return sorted(customers, key=lambda x: x["company_name"])
    
    def get_customer(self, customer_id: str) -> CustomerContext:
        """Get customer context by ID."""
        return CustomerContext(customer_id)
    
    def create_customer(
        self,
        customer_id: str,
        company_name: Optional[str] = None,
        gstin: Optional[str] = None,
        email: Optional[str] = None,
        business_type: str = "trading",
        turnover_category: str = "micro",
        state_code: str = "27"
    ) -> CustomerContext:
        """Create a new customer."""
        customer = CustomerContext(customer_id)
        
        if customer.exists():
            raise ValueError(f"Customer already exists: {customer_id}")
        
        customer.ensure_exists()
        customer.update_profile(
            company_name=company_name or customer_id.replace("_", " ").title(),
            gstin=gstin,
            email=email,
            business_type=business_type,
            turnover_category=turnover_category,
            state_code=state_code
        )
        
        return customer
    
    def delete_customer(self, customer_id: str, confirm: bool = False) -> bool:
        """Delete a customer (requires confirmation)."""
        if not confirm:
            raise ValueError("Must confirm=True to delete customer data")
        
        customer = CustomerContext(customer_id)
        if customer.exists():
            customer.delete()
            return True
        return False
    
    def customer_exists(self, customer_id: str) -> bool:
        """Check if customer exists."""
        return CustomerContext(customer_id).exists()


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def get_customer_manager() -> CustomerManager:
    """Get the customer manager instance."""
    return CustomerManager()


def get_customer(customer_id: str) -> CustomerContext:
    """Get a customer context by ID."""
    return CustomerContext(customer_id)


# Active customer (set by main.py)
_active_customer: Optional[CustomerContext] = None


def set_active_customer(customer: CustomerContext) -> None:
    """Set the active customer for the current session."""
    global _active_customer
    _active_customer = customer


def get_active_customer() -> Optional[CustomerContext]:
    """Get the active customer for the current session."""
    return _active_customer


def require_active_customer() -> CustomerContext:
    """Get active customer or raise error if not set."""
    if _active_customer is None:
        raise RuntimeError("No active customer. Select a customer first.")
    return _active_customer

