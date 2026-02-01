"""
Schema Definitions

NOTE: This module is DEPRECATED for data-specific schemas.
The system is now data-agnostic - it does not assume specific data types.
The LLM understands column meanings from names and sample values.

This module is kept for backward compatibility but should not be used
for new functionality that assumes specific data structures.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict
from datetime import date, datetime
from enum import Enum


# =============================================================================
# GENERIC COLUMN INFO (Data-agnostic)
# =============================================================================

@dataclass
class ColumnSchema:
    """Generic column schema information."""
    name: str
    data_type: str  # SQL type like VARCHAR, INTEGER, DATE
    nullable: bool = True
    description: str = ""  # LLM-generated or empty


@dataclass
class TableSchema:
    """Generic table schema information."""
    table_name: str
    columns: List[ColumnSchema]
    row_count: int = 0
    source_file: str = ""


# =============================================================================
# DEPRECATED: Domain-specific schemas (kept for reference only)
# =============================================================================
# 
# The following classes are DEPRECATED and should not be used in new code.
# They represent domain-specific assumptions that make the system less flexible.
#
# Instead, the system now:
# 1. Loads data as-is without schema mapping
# 2. Uses LLM to understand column meanings from names + samples
# 3. Generates SQL based on actual column names
#
# If you need domain-specific validation (e.g., GST compliance), 
# use the guardrails module or domain-specific features, not data ingestion.
# =============================================================================

