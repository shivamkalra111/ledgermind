"""
Header Mapper - DEPRECATED

NOTE: This module is DEPRECATED. The system is now data-agnostic.
Instead of mapping headers to a predefined schema, the LLM understands
column meanings from names and sample values at query time.

This file is kept for backward compatibility but should not be used
for new functionality.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class ColumnInfo:
    """Generic column information (data-agnostic)."""
    name: str
    data_type: str
    sample_values: List[str] = None


def get_column_info(headers: List[str], types: List[str]) -> List[ColumnInfo]:
    """
    Get generic column information without assuming specific data types.
    
    Args:
        headers: List of column names
        types: List of SQL types
        
    Returns:
        List of ColumnInfo objects
    """
    return [
        ColumnInfo(name=h, data_type=t)
        for h, t in zip(headers, types)
    ]

