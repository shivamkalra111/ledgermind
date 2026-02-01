"""
LedgerMind Core

Data-Agnostic Components:
- customer: Customer isolation and multi-tenancy
- data_engine: DuckDB integration for Excel/CSV as SQL tables
- data_state: Smart file change detection
- table_catalog: Persistent metadata for loaded tables
- metrics: Performance and usage tracking

Domain-Specific Features (GST/Accounting):
- knowledge: ChromaDB for GST rule lookups
- guardrails: Safety checks and validation (GST-specific)
- reference_data: GST rates, MSME limits
- query_classifier: Route queries to appropriate knowledge source

IMPORTANT: Data ingestion (data_engine, table_catalog) is DATA-AGNOSTIC.
It does not assume specific data types (sales, purchases, etc.).
Domain-specific features (knowledge, guardrails) are separate from data handling.
"""

from .customer import (
    CustomerContext,
    CustomerManager,
    CustomerProfile,
    get_customer,
    get_customer_manager,
    get_active_customer,
    set_active_customer,
    require_active_customer,
)
from .data_state import (
    DataStateManager,
    DataState,
    FileState,
    FileChange,
    FileChangeType,
    get_data_state_manager,
)
from .data_engine import DataEngine
from .table_catalog import TableCatalog, TableMetadata, create_table_metadata
from .knowledge import KnowledgeBase
from .guardrails import Guardrails, validate_transaction, get_validation_summary
from .metrics import MetricsCollector, get_metrics, timed, counted
from .reference_data import (
    load_goods_rates, 
    load_services_rates,
    load_blocked_credits,
    get_rate_for_hsn,
    get_rate_for_sac,
    get_gst_slabs,
    get_msme_classification,
)
from .query_classifier import QueryClassifier, QueryType

__all__ = [
    # Customer Isolation
    "CustomerContext",
    "CustomerManager",
    "CustomerProfile",
    "get_customer",
    "get_customer_manager",
    "get_active_customer",
    "set_active_customer",
    "require_active_customer",
    # Data State (Smart Loading)
    "DataStateManager",
    "DataState",
    "FileState",
    "FileChange",
    "FileChangeType",
    "get_data_state_manager",
    # Data (Data-Agnostic)
    "DataEngine",
    "TableCatalog",
    "TableMetadata",
    "create_table_metadata",
    "KnowledgeBase",
    # Guardrails (Domain-Specific)
    "Guardrails",
    "validate_transaction",
    "get_validation_summary",
    # Metrics
    "MetricsCollector",
    "get_metrics",
    "timed",
    "counted",
    # Reference Data (Domain-Specific)
    "load_goods_rates",
    "load_services_rates",
    "load_blocked_credits",
    "get_rate_for_hsn",
    "get_rate_for_sac",
    "get_gst_slabs",
    "get_msme_classification",
    # Query Classifier
    "QueryClassifier",
    "QueryType",
]

