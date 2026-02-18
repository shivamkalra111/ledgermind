"""
Table Catalog - Persistent metadata for loaded tables

Architecture:
1. When file is loaded → Extract schema + generate description → Save to catalog
2. When user queries → LLM reads catalog → Selects relevant tables → SQL model gets full schema

Benefits:
- Schema extracted ONCE during ingestion (not every query)
- Rich metadata (filename, description, keywords) for smart selection
- LLM-based table selection (understands context, not just keywords)
- Persisted across sessions
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
import numpy as np


@dataclass
class ColumnInfo:
    """Detailed column information."""
    name: str
    type: str
    description: str = ""  # What this column represents
    nullable: bool = True
    sample_values: List[Any] = field(default_factory=list)  # Example values
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "nullable": self.nullable,
            "sample_values": self.sample_values[:3]
        }


@dataclass
class DateRange:
    """Date range information for time-based tables."""
    date_column: str
    min_date: str
    max_date: str
    period_description: str = ""  # e.g., "FY 2021-22", "Q1 2022"


@dataclass
class TableStatistics:
    """Useful statistics about the table."""
    total_rows: int = 0
    unique_counts: Dict[str, int] = field(default_factory=dict)  # column -> unique count
    null_percentages: Dict[str, float] = field(default_factory=dict)  # column -> % nulls
    numeric_sums: Dict[str, float] = field(default_factory=dict)  # column -> sum
    
    def to_dict(self) -> Dict:
        return {
            "total_rows": self.total_rows,
            "unique_counts": self.unique_counts,
            "null_percentages": self.null_percentages,
            "numeric_sums": self.numeric_sums
        }


@dataclass
class TableMetadata:
    """Metadata for a single table."""
    
    # Core info
    table_name: str
    source_file: str  # Original filename
    
    # Schema - Enhanced with descriptions
    columns: List[Dict[str, str]]  # [{"name": "col", "type": "VARCHAR", "description": "..."}, ...]
    row_count: int
    
    # For table selection
    description: str  # Human-readable, e.g., "Purchase transactions for April 2022"
    keywords: List[str]  # ["purchase", "april", "2022", "vendor"]
    data_type: str  # "purchase", "sales", "bank", "unknown"
    
    # Sample data for SQL model
    sample_rows: List[Dict[str, Any]] = field(default_factory=list)
    
    # NEW: Enhanced metadata
    date_range: Optional[Dict] = None  # {"date_column": "date", "min": "...", "max": "..."}
    statistics: Optional[Dict] = None  # Useful stats
    example_queries: List[str] = field(default_factory=list)  # Pre-generated query examples
    related_tables: List[str] = field(default_factory=list)  # Tables this relates to
    
    # Timestamps
    created_at: str = ""
    updated_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "TableMetadata":
        return cls(**data)
    
    def get_column_names(self) -> List[str]:
        return [c["name"] for c in self.columns]
    
    def get_brief_description(self) -> str:
        """One-line description for catalog listing."""
        cols = len(self.columns)
        return f"{self.description} ({cols} columns, {self.row_count} rows)"
    
    def get_full_schema(self, include_samples: bool = True, include_stats: bool = True) -> str:
        """Full schema for SQL model - enhanced with column descriptions and stats."""
        lines = [f"TABLE: {self.table_name}"]
        lines.append(f"  Source: {self.source_file}")
        lines.append(f"  Description: {self.description}")
        
        # Date range if available
        if self.date_range:
            dr = self.date_range
            lines.append(f"  Date range: {dr.get('min_date', '?')} to {dr.get('max_date', '?')} ({dr.get('period_description', '')})")
        
        # Columns with descriptions
        lines.append("  Columns:")
        for c in self.columns:
            desc = f" - {c.get('description', '')}" if c.get('description') else ""
            lines.append(f"    \"{c['name']}\" ({c['type']}){desc}")
        
        # Statistics if available
        if include_stats and self.statistics:
            stats = self.statistics
            if stats.get('unique_counts'):
                top_uniques = list(stats['unique_counts'].items())[:3]
                uniq_str = ", ".join([f"{k}: {v} unique" for k, v in top_uniques])
                lines.append(f"  Key stats: {uniq_str}")
            if stats.get('numeric_sums'):
                top_sums = list(stats['numeric_sums'].items())[:2]
                sum_str = ", ".join([f"{k}: {v:,.2f}" for k, v in top_sums])
                lines.append(f"  Totals: {sum_str}")
        
        # Sample data
        if include_samples and self.sample_rows:
            lines.append("  Sample data:")
            for row in self.sample_rows[:2]:
                items = [f'{k}={repr(v)[:25]}' for k, v in list(row.items())[:6]]
                lines.append(f"    {', '.join(items)}")
        
        # Example queries if available
        if self.example_queries:
            lines.append(f"  Example queries: {', '.join(self.example_queries[:3])}")
        
        lines.append(f"  Total rows: {self.row_count}")
        return "\n".join(lines)
    
    def get_compressed_schema(self) -> str:
        """
        Ultra-brief schema for massive scale (20+ tables).
        
        Only column names and types, no descriptions or samples.
        Reduces from ~750 chars to ~100 chars per table!
        
        Example:
            purchase_2021_07(date DATE, vendor VARCHAR, amount DOUBLE, total DOUBLE)
        """
        columns_str = ", ".join([
            f"{col['name']} {col['type']}" 
            for col in self.columns
        ])
        
        return f"{self.table_name}({columns_str})"
    
    def get_medium_schema(self) -> str:
        """
        Medium detail schema: column names, types, and descriptions only.
        No samples or statistics. Reduces from ~750 to ~300 chars per table.
        """
        lines = [f"TABLE: {self.table_name}"]
        lines.append(f"  Description: {self.description}")
        lines.append("  Columns:")
        
        for col in self.columns:
            desc = col.get('description', '')
            if desc:
                lines.append(f"    - {col['name']} ({col['type']}): {desc}")
            else:
                lines.append(f"    - {col['name']} ({col['type']})")
        
        return "\n".join(lines)


class TableCatalog:
    """
    Persistent catalog of all loaded tables.
    
    Usage:
        catalog = TableCatalog(workspace_path)
        
        # During ingestion
        catalog.register_table(metadata)
        catalog.save()
        
        # During query
        catalog.load()
        relevant = catalog.get_tables_for_query("April purchases", llm_client)
        schema = catalog.get_schema_for_tables(relevant)
    """
    
    def __init__(self, workspace_path: Path = None):
        """
        Initialize catalog.
        
        Args:
            workspace_path: Path to customer workspace (contains catalog.json)
        """
        self.workspace_path = Path(workspace_path) if workspace_path else None
        self.tables: Dict[str, TableMetadata] = {}
        
        # Vector search components (initialized on demand)
        self.embeddings: Dict[str, np.ndarray] = {}
        self.embedding_model = None
        self._vector_search_enabled = False
        
        if self.workspace_path:
            self.catalog_path = self.workspace_path / "table_catalog.json"
            self.load()
    
    def load(self) -> bool:
        """Load catalog from disk."""
        if not self.catalog_path or not self.catalog_path.exists():
            return False
        
        try:
            with open(self.catalog_path) as f:
                data = json.load(f)
            
            self.tables = {
                name: TableMetadata.from_dict(meta)
                for name, meta in data.get("tables", {}).items()
            }
            return True
        except Exception as e:
            print(f"Warning: Could not load catalog: {e}")
            return False
    
    def save(self) -> bool:
        """Save catalog to disk."""
        if not self.catalog_path:
            return False
        
        try:
            data = {
                "version": "1.0",
                "updated_at": datetime.now().isoformat(),
                "tables": {name: meta.to_dict() for name, meta in self.tables.items()}
            }
            
            with open(self.catalog_path, "w") as f:
                json.dump(data, f, indent=2, default=str)
            return True
        except Exception as e:
            print(f"Warning: Could not save catalog: {e}")
            return False
    
    def register_table(self, metadata: TableMetadata):
        """Add or update table in catalog."""
        self.tables[metadata.table_name] = metadata
    
    def remove_table(self, table_name: str):
        """Remove table from catalog."""
        if table_name in self.tables:
            del self.tables[table_name]
    
    def get_table(self, table_name: str) -> Optional[TableMetadata]:
        """Get metadata for a specific table."""
        return self.tables.get(table_name)
    
    def list_tables(self) -> List[str]:
        """List all table names."""
        return list(self.tables.keys())
    
    def get_catalog_summary(self) -> str:
        """
        Get brief summary of all tables (for LLM to decide which to use).
        
        Returns something like:
        '''
        Available tables:
        1. april_2022_purchases - Purchase transactions for April 2022 (13 cols, 32 rows)
        2. may_2022_purchases - Purchase transactions for May 2022 (13 cols, 32 rows)
        3. sales_q1_2022 - Sales invoices Q1 2022 (10 cols, 150 rows)
        '''
        """
        if not self.tables:
            return "No tables loaded."
        
        lines = ["Available tables:"]
        for i, (name, meta) in enumerate(self.tables.items(), 1):
            lines.append(f"{i}. {name} - {meta.get_brief_description()}")
        
        return "\n".join(lines)
    
    def get_schema_for_tables(
        self, 
        table_names: List[str], 
        include_samples: bool = True,
        detail_level: str = "full"
    ) -> str:
        """
        Get schema for specific tables with configurable detail level.
        
        This is critical for handling large numbers of tables!
        
        Args:
            table_names: List of table names
            include_samples: Include sample data (only for "full" level)
            detail_level: One of "compressed", "medium", "full"
                - "compressed": Just column names/types (~100 chars/table)
                - "medium": + descriptions (~300 chars/table)  
                - "full": + samples + stats (~750 chars/table)
        
        Returns:
            Schema string for all tables
        """
        schemas = []
        
        for name in table_names:
            if name in self.tables:
                meta = self.tables[name]
                
                if detail_level == "compressed":
                    schemas.append(meta.get_compressed_schema())
                elif detail_level == "medium":
                    schemas.append(meta.get_medium_schema())
                else:  # "full"
                    schemas.append(meta.get_full_schema(include_samples))
        
        return "\n\n".join(schemas)
    
    def select_tables_with_llm(
        self, 
        query: str, 
        llm_client, 
        max_tables: int = 3
    ) -> List[str]:
        """
        Use LLM to select relevant tables based on user query.
        
        Smart selection:
        - Detects "table families" (e.g., purchase_2021_07, purchase_2021_08)
        - For "all/total" queries, includes ALL tables in the family
        - For specific queries, limits to max_tables
        
        Args:
            query: User's natural language question
            llm_client: LLM client for inference
            max_tables: Maximum tables to select (ignored for family queries)
            
        Returns:
            List of relevant table names
        """
        if not self.tables:
            return []
        
        if len(self.tables) == 1:
            return list(self.tables.keys())
        
        # Detect table families (tables with same prefix pattern)
        families = self._detect_table_families()
        
        # Check if query wants "all" data (total, all, entire, complete, etc.)
        query_lower = query.lower()
        wants_all = any(kw in query_lower for kw in [
            "all ", "total", "entire", "complete", "overall", "combined", 
            "across all", "sum of all", "everything"
        ])
        
        # If query wants all and we have a dominant family, return all tables in that family
        if wants_all and families:
            # Find which family matches the query
            for family_prefix, family_tables in families.items():
                # Check if query mentions the family (e.g., "purchases" matches "purchase_")
                family_base = family_prefix.rstrip('_').rstrip('0123456789')
                if family_base in query_lower or len(families) == 1:
                    # Return ALL tables in this family
                    return family_tables
        
        # Otherwise, use LLM to select specific tables
        catalog_summary = self.get_catalog_summary()
        
        # Inform LLM about table families
        family_info = ""
        if families:
            family_info = "\nNOTE: These tables appear to be related groups:\n"
            for prefix, tables in families.items():
                family_info += f"- {prefix}*: {len(tables)} tables ({', '.join(tables[:3])}{'...' if len(tables) > 3 else ''})\n"
        
        prompt = f"""Given this user question and available tables, select the most relevant table(s).

USER QUESTION: {query}

{catalog_summary}
{family_info}
RULES:
1. Select tables needed to answer the question
2. Return ONLY the table names, comma-separated
3. If asking about "all" or "total" of something, include ALL related tables
4. For date-specific queries, pick the matching period(s)

SELECTED TABLES:"""

        try:
            response = llm_client.generate(prompt, max_tokens=200)
            
            # Parse response - extract table names
            selected = []
            response_lower = response.lower().strip()
            
            for table_name in self.tables.keys():
                if table_name.lower() in response_lower:
                    selected.append(table_name)
            
            # If LLM response didn't match any tables, fallback to keyword matching
            if not selected:
                selected = self._fallback_selection(query, max_tables)
            
            # For "wants_all" queries, don't limit the results
            if wants_all:
                return selected
            
            return selected[:max_tables]
            
        except Exception as e:
            # Fallback to keyword matching
            return self._fallback_selection(query, max_tables)
    
    def initialize_vector_search(self, force: bool = False):
        """
        Initialize vector search for massive scale (100+ tables).
        
        This is optional and only needed for large datasets.
        Uses sentence-transformers (lightweight, CPU-friendly).
        
        Args:
            force: Force re-generation of embeddings even if already exist
        """
        if self._vector_search_enabled and not force:
            print("✓ Vector search already enabled")
            return
        
        if not self.tables:
            print("⚠ No tables to embed")
            return
        
        print(f"🔍 Initializing vector search for {len(self.tables)} tables...")
        
        try:
            from sentence_transformers import SentenceTransformer
            
            # Load lightweight embedding model (80MB, runs on CPU)
            if self.embedding_model is None:
                print("  Loading embedding model (all-MiniLM-L6-v2)...")
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Generate embeddings for each table
            print("  Generating embeddings...")
            for i, (table_name, metadata) in enumerate(self.tables.items(), 1):
                if table_name not in self.embeddings or force:
                    # Create rich text representation
                    text = self._create_embedding_text(metadata)
                    
                    # Generate embedding
                    embedding = self.embedding_model.encode(text, show_progress_bar=False)
                    self.embeddings[table_name] = embedding
                
                if i % 10 == 0:
                    print(f"    Progress: {i}/{len(self.tables)}")
            
            self._vector_search_enabled = True
            print(f"✓ Vector search ready ({len(self.embeddings)} tables embedded)")
            
        except ImportError:
            print("⚠ sentence-transformers not installed. Run: pip install sentence-transformers")
            print("  Falling back to standard LLM selection")
        except Exception as e:
            print(f"⚠ Failed to initialize vector search: {e}")
            print("  Falling back to standard LLM selection")
    
    def _create_embedding_text(self, metadata: TableMetadata) -> str:
        """
        Create rich text representation for embedding.
        
        Includes table name, description, column names, keywords, and sample values.
        This enables semantic matching (e.g., 'vendor' matches 'supplier').
        """
        parts = [
            f"Table: {metadata.table_name}",
            f"Description: {metadata.description}",
            f"Columns: {', '.join(metadata.get_column_names())}",
        ]
        
        # Add keywords
        if metadata.keywords:
            parts.append(f"Keywords: {', '.join(metadata.keywords)}")
        
        # Add date range if available
        if metadata.date_range:
            dr = metadata.date_range
            parts.append(f"Period: {dr.get('period_description', '')}")
        
        # Add sample values (helps with semantic matching)
        if metadata.sample_rows:
            first_row = metadata.sample_rows[0]
            sample_str = ", ".join([f"{k}={v}" for k, v in list(first_row.items())[:5]])
            parts.append(f"Sample: {sample_str[:100]}")
        
        return " | ".join(parts)
    
    def search_tables_by_vector(
        self, 
        query: str, 
        top_k: int = 20
    ) -> List[Tuple[str, float]]:
        """
        Vector search for relevant tables (massive scale optimization).
        
        Returns top K most semantically similar tables without using any tokens!
        
        Args:
            query: User's natural language question
            top_k: Number of candidate tables to return
            
        Returns:
            List of (table_name, similarity_score) tuples, sorted by relevance
        """
        if not self._vector_search_enabled:
            raise RuntimeError(
                "Vector search not initialized. Call initialize_vector_search() first."
            )
        
        if not self.embeddings:
            return []
        
        # Embed the query
        query_embedding = self.embedding_model.encode(query, show_progress_bar=False)
        
        # Compute cosine similarity with all tables
        similarities = []
        for table_name, table_embedding in self.embeddings.items():
            similarity = self._cosine_similarity(query_embedding, table_embedding)
            similarities.append((table_name, float(similarity)))
        
        # Sort by similarity (highest first)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
    
    def select_tables_for_massive_scale(
        self, 
        query: str, 
        llm_client, 
        max_final_tables: int = 5
    ) -> List[str]:
        """
        Three-stage selection for massive scale (100+ tables).
        
        This solves the context limit problem:
        - Stage 1: Vector search (500 tables → 20 candidates, 0 tokens!)
        - Stage 2: Family expansion (smart pattern detection)
        - Stage 3: LLM refinement (20 candidates → 5 final, ~500 tokens)
        
        Total token usage: ~500 tokens vs 12,500 for full catalog!
        
        Args:
            query: User's natural language question
            llm_client: LLM client for final refinement
            max_final_tables: Maximum tables in final selection
            
        Returns:
            List of selected table names
        """
        if not self._vector_search_enabled:
            # Fallback to standard selection
            print("⚠ Vector search not enabled, using standard selection")
            return self.select_tables_with_llm(query, llm_client, max_tables=max_final_tables)
        
        print(f"\n🔍 MASSIVE SCALE SELECTION (from {len(self.tables)} tables)")
        
        # ═══════════════════════════════════════════════════════════
        # STAGE 1: VECTOR SEARCH (semantic similarity, 0 tokens)
        # ═══════════════════════════════════════════════════════════
        
        print(f"  Stage 1: Vector search...")
        candidates = self.search_tables_by_vector(query, top_k=20)
        candidate_names = [name for name, score in candidates]
        
        print(f"    ✓ Found {len(candidate_names)} candidates")
        for name, score in candidates[:3]:
            print(f"      - {name} (similarity: {score:.3f})")
        
        # ═══════════════════════════════════════════════════════════
        # STAGE 2: FAMILY EXPANSION (pattern matching, 0 tokens)
        # ═══════════════════════════════════════════════════════════
        
        print(f"  Stage 2: Family detection...")
        
        query_lower = query.lower()
        wants_all = any(kw in query_lower for kw in [
            "all ", "total", "entire", "complete", "sum of all", "overall"
        ])
        
        if wants_all:
            # Expand to include full families
            expanded = self._expand_to_families(candidate_names)
            print(f"    ✓ Expanded to {len(expanded)} tables (families included)")
            candidate_names = expanded
        
        # ═══════════════════════════════════════════════════════════
        # STAGE 3: LLM REFINEMENT (20 candidates → final selection)
        # ═══════════════════════════════════════════════════════════
        
        print(f"  Stage 3: LLM refinement...")
        
        # Build catalog for ONLY the candidates (not all 500 tables!)
        candidate_catalog = self._build_candidate_catalog(candidate_names)
        
        # Token usage: 20 candidates × 100 chars = 2,000 chars (~500 tokens)
        # This fits easily in context!
        
        prompt = f"""Select the most relevant tables for this question.

USER QUESTION: {query}

CANDIDATE TABLES (pre-filtered by semantic search):
{candidate_catalog}

RULES:
1. Select tables needed to answer the question
2. Return ONLY table names, comma-separated
3. Maximum {max_final_tables} tables (unless aggregate "all" query)

SELECTED TABLES:"""

        try:
            response = llm_client.generate(prompt, max_tokens=200)
            
            # Parse table names from response
            selected = []
            response_lower = response.lower().strip()
            
            for table_name in candidate_names:
                if table_name.lower() in response_lower:
                    selected.append(table_name)
            
            # Fallback: use top candidates from vector search
            if not selected:
                selected = candidate_names[:max_final_tables]
            
            # Limit to max tables (unless wants_all)
            if not wants_all:
                selected = selected[:max_final_tables]
            
            print(f"    ✓ Final selection: {len(selected)} tables")
            for name in selected:
                print(f"      - {name}")
            
            return selected
            
        except Exception as e:
            print(f"  ⚠ LLM refinement failed: {e}")
            # Fallback to top candidates from vector search
            return candidate_names[:max_final_tables]
    
    def _expand_to_families(self, candidate_names: List[str]) -> List[str]:
        """
        Expand candidate tables to include full families.
        
        Example:
            Input: ["purchase_2021_07", "purchase_2021_12"]
            Output: All 12 months of purchase_2021_*
        """
        families = self._detect_table_families()
        expanded = set(candidate_names)
        
        for candidate in candidate_names:
            # Find which family this belongs to
            for family_prefix, family_tables in families.items():
                if candidate in family_tables:
                    # Add all tables from this family
                    expanded.update(family_tables)
                    break
        
        return list(expanded)
    
    def _build_candidate_catalog(self, candidate_names: List[str]) -> str:
        """Build brief catalog for ONLY the candidate tables."""
        lines = []
        for i, name in enumerate(candidate_names, 1):
            if name in self.tables:
                meta = self.tables[name]
                lines.append(f"{i}. {name} - {meta.get_brief_description()}")
        
        return "\n".join(lines)
    
    def _detect_table_families(self) -> Dict[str, List[str]]:
        """
        Detect groups of related tables (e.g., purchase_2021_07, purchase_2021_08).
        
        Returns:
            Dict mapping family prefix to list of table names
        """
        import re
        
        families = {}
        
        for table_name in self.tables.keys():
            # Try to extract base name (before date/number suffix)
            # Pattern: word_word_YYYY_MM or word_word_NN
            match = re.match(r'^(.+?)_?(\d{4}[-_]?\d{2}|\d{2,4})$', table_name)
            if match:
                prefix = match.group(1) + "_"
            else:
                # Try simpler pattern: word_digits
                match = re.match(r'^(.+?)_\d+$', table_name)
                if match:
                    prefix = match.group(1) + "_"
                else:
                    prefix = table_name
            
            if prefix not in families:
                families[prefix] = []
            families[prefix].append(table_name)
        
        # Only keep families with more than 1 table
        return {k: v for k, v in families.items() if len(v) > 1}
    
    def _fallback_selection(self, query: str, max_tables: int) -> List[str]:
        """Fallback keyword-based selection if LLM fails."""
        query_lower = query.lower()
        scores = []
        
        for name, meta in self.tables.items():
            score = 0
            
            # Check keywords
            for kw in meta.keywords:
                if kw.lower() in query_lower:
                    score += 5
            
            # Check table name
            for part in name.lower().split("_"):
                if part in query_lower:
                    score += 3
            
            # Boost consolidated tables for general queries
            if "consolidated" in name.lower() or "all" in name.lower():
                score += 2
            
            # NEW: Check date range if query mentions dates
            if meta.date_range:
                period = meta.date_range.get("period_description", "").lower()
                if any(word in query_lower for word in period.split()):
                    score += 4
            
            scores.append((name, score))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        
        # Return top scoring or first table if no matches
        result = [name for name, score in scores if score > 0][:max_tables]
        return result if result else [scores[0][0]] if scores else []
    
    def find_related_tables(self) -> Dict[str, List[str]]:
        """
        Identify relationships between tables based on common columns.
        
        Returns:
            Dict mapping table name to list of related tables
        """
        relationships = {}
        
        # Find relationships based on common column names (any matching columns)
        table_cols = {}
        for name, meta in self.tables.items():
            # Get all column names for this table
            cols = set(c["name"].lower() for c in meta.columns)
            table_cols[name] = cols
        
        for name1, cols1 in table_cols.items():
            related = []
            for name2, cols2 in table_cols.items():
                if name1 != name2:
                    # Find common column names between tables
                    common = cols1.intersection(cols2)
                    # Only consider it a relationship if there's at least one common column
                    # that's not a generic column like 'id', 'date', 'created_at'
                    generic_cols = {'id', 'date', 'created_at', 'updated_at', 'month', 'year'}
                    meaningful_common = common - generic_cols
                    if meaningful_common:
                        related.append((name2, list(meaningful_common)))
            relationships[name1] = related
        
        return relationships
    
    def get_catalog_with_relationships(self) -> str:
        """Get catalog summary including table relationships."""
        base = self.get_catalog_summary()
        
        relationships = self.find_related_tables()
        
        rel_lines = ["\nTable relationships:"]
        has_relationships = False
        
        for table, related in relationships.items():
            if related:
                has_relationships = True
                for rel_table, common_cols in related:
                    rel_lines.append(f"  {table} ↔ {rel_table} (via {', '.join(common_cols)})")
        
        if has_relationships:
            return base + "\n".join(rel_lines)
        return base


def create_table_metadata(
    table_name: str,
    source_file: str,
    data_engine,
    llm_client=None,
    extract_stats: bool = True
) -> TableMetadata:
    """
    Create metadata for a newly loaded table.
    
    Args:
        table_name: Name of table in DuckDB
        source_file: Original filename
        data_engine: DuckDB engine
        llm_client: Optional LLM for generating description
        extract_stats: Whether to extract statistics (slower but more useful)
        
    Returns:
        TableMetadata object with enhanced metadata
    """
    # Get columns
    columns_df = data_engine.query(f"DESCRIBE {table_name}")
    columns = [
        {"name": row["column_name"], "type": row["column_type"]}
        for _, row in columns_df.iterrows()
    ]
    
    # Get row count
    row_count = int(data_engine.query(f"SELECT COUNT(*) as cnt FROM {table_name}").iloc[0]["cnt"])
    
    # Get sample rows
    sample_df = data_engine.query(f"SELECT * FROM {table_name} LIMIT 3")
    sample_rows = sample_df.to_dict("records")
    
    # Convert any non-serializable values in samples
    for row in sample_rows:
        for k, v in row.items():
            if hasattr(v, 'isoformat'):
                row[k] = v.isoformat()
            elif not isinstance(v, (str, int, float, bool, type(None))):
                row[k] = str(v)
    
    # Detect data type from table name and columns
    data_type = _detect_data_type(table_name, [c["name"] for c in columns])
    
    # Generate keywords from filename and columns
    keywords = _generate_keywords(source_file, table_name, [c["name"] for c in columns])
    
    # Generate description
    if llm_client:
        description = _generate_description_with_llm(
            table_name, source_file, columns, sample_rows, llm_client
        )
    else:
        description = _generate_description_simple(table_name, source_file, data_type)
    
    # NEW: Enhance columns with descriptions
    columns = _generate_column_descriptions(columns, data_type)
    
    # NEW: Extract date range
    date_range = _extract_date_range(table_name, columns, data_engine)
    
    # NEW: Extract statistics
    statistics = None
    if extract_stats:
        statistics = _extract_statistics(table_name, columns, data_engine)
    
    # NEW: Generate example queries
    example_queries = _generate_example_queries(table_name, columns, data_type)
    
    return TableMetadata(
        table_name=table_name,
        source_file=source_file,
        columns=columns,
        row_count=row_count,
        description=description,
        keywords=keywords,
        data_type=data_type,
        sample_rows=sample_rows,
        date_range=date_range,
        statistics=statistics,
        example_queries=example_queries
    )


def _detect_data_type(table_name: str, column_names: List[str]) -> str:
    """
    Return 'unknown' - we don't assume data types.
    The LLM will understand the data from column names and samples.
    """
    return "unknown"


def _generate_keywords(source_file: str, table_name: str, column_names: List[str]) -> List[str]:
    """Generate search keywords from file/table/column names only (no hardcoded terms)."""
    keywords = set()
    
    # From filename (split on common separators)
    file_parts = Path(source_file).stem.lower().replace("_", " ").replace("-", " ").split()
    keywords.update(p for p in file_parts if len(p) > 2)  # Skip short words
    
    # From table name
    table_parts = table_name.lower().replace("_", " ").split()
    keywords.update(p for p in table_parts if len(p) > 2)
    
    # From column names (just the column names, no assumed meanings)
    for col in column_names:
        col_parts = col.lower().replace("_", " ").split()
        keywords.update(p for p in col_parts if len(p) > 2)
    
    # Month names if present in filename/table (generic date detection)
    months = ["january", "february", "march", "april", "may", "june",
              "july", "august", "september", "october", "november", "december"]
    combined = f"{table_name} {source_file}".lower()
    for month in months:
        if month in combined or month[:3] in combined:
            keywords.add(month)
    
    return list(keywords)[:15]  # Limit keywords


def _generate_description_simple(table_name: str, source_file: str, data_type: str) -> str:
    """Generate simple description from filename only (no data type assumptions)."""
    import re
    
    # Clean up filename for description
    name = Path(source_file).stem
    name_clean = name.replace("_", " ").replace("-", " ")
    
    # Extract year if present
    year_match = re.search(r'20\d{2}', source_file)
    year = year_match.group() if year_match else ""
    
    # Extract month if present
    months = ["january", "february", "march", "april", "may", "june",
              "july", "august", "september", "october", "november", "december"]
    month = ""
    for m in months:
        if m in source_file.lower():
            month = m.capitalize()
            break
    
    # Build description
    if month and year:
        return f"Data for {month} {year}"
    elif year:
        return f"Data from {year}"
    else:
        return f"Data from {name_clean}"


def _generate_description_with_llm(
    table_name: str,
    source_file: str,
    columns: List[Dict],
    sample_rows: List[Dict],
    llm_client
) -> str:
    """Generate description using LLM."""
    col_names = [c["name"] for c in columns]
    
    sample_str = ""
    if sample_rows:
        sample_str = f"\nSample row: {sample_rows[0]}"
    
    prompt = f"""Generate a brief one-line description for this data table.

Filename: {source_file}
Table name: {table_name}
Columns: {', '.join(col_names)}{sample_str}

Description (one line, be specific about what data this contains):"""

    try:
        response = llm_client.generate(prompt, max_tokens=50)
        # Clean up response
        desc = response.strip().split("\n")[0]
        desc = desc.strip('"').strip("'")
        if len(desc) > 100:
            desc = desc[:97] + "..."
        return desc
    except:
        return _generate_description_simple(table_name, source_file, 
                                            _detect_data_type(table_name, col_names))


def _extract_date_range(table_name: str, columns: List[Dict], data_engine) -> Optional[Dict]:
    """Extract date range from date columns."""
    # Find date columns - prefer actual DATE type columns
    actual_date_cols = [c["name"] for c in columns if "DATE" in c["type"].upper()]
    date_like_cols = [c["name"] for c in columns if 
                      any(kw in c["name"].lower() for kw in ["date", "period"]) 
                      and c["name"] not in actual_date_cols]
    
    date_cols = actual_date_cols + date_like_cols
    
    if not date_cols:
        return None
    
    date_col = date_cols[0]
    
    try:
        result = data_engine.query(f"""
            SELECT 
                MIN("{date_col}") as min_date,
                MAX("{date_col}") as max_date
            FROM {table_name}
            WHERE "{date_col}" IS NOT NULL
        """)
        
        if result.empty:
            return None
        
        min_date = result.iloc[0]["min_date"]
        max_date = result.iloc[0]["max_date"]
        
        # Convert to string if datetime
        if hasattr(min_date, 'strftime'):
            min_date = min_date.strftime("%Y-%m-%d")
            max_date = max_date.strftime("%Y-%m-%d")
        
        # Generate period description
        period_desc = _generate_period_description(str(min_date), str(max_date))
        
        return {
            "date_column": date_col,
            "min_date": str(min_date),
            "max_date": str(max_date),
            "period_description": period_desc
        }
    except Exception as e:
        return None


def _generate_period_description(min_date: str, max_date: str) -> str:
    """Generate human-readable period description."""
    try:
        from datetime import datetime
        min_dt = datetime.fromisoformat(min_date.split("T")[0])
        max_dt = datetime.fromisoformat(max_date.split("T")[0])
        
        # Same month
        if min_dt.year == max_dt.year and min_dt.month == max_dt.month:
            return min_dt.strftime("%B %Y")
        
        # Same year
        if min_dt.year == max_dt.year:
            return f"{min_dt.strftime('%b')} - {max_dt.strftime('%b %Y')}"
        
        # Financial year (Apr-Mar)
        if min_dt.month >= 4:
            fy_start = min_dt.year
        else:
            fy_start = min_dt.year - 1
        
        if max_dt.month >= 4:
            fy_end = max_dt.year + 1
        else:
            fy_end = max_dt.year
        
        if fy_start == fy_end - 1:
            return f"FY {fy_start}-{str(fy_end)[-2:]}"
        else:
            return f"FY {fy_start}-{str(fy_end)[-2:]}"
    except:
        return ""


def _extract_statistics(table_name: str, columns: List[Dict], data_engine) -> Dict:
    """
    Extract basic statistics about the table (generic, no column name assumptions).
    """
    stats = {
        "unique_counts": {},
        "null_percentages": {},
        "numeric_sums": {}
    }
    
    # Identify column types for analysis (by SQL type, not column name)
    text_cols = [c["name"] for c in columns if "VARCHAR" in c["type"].upper() or "TEXT" in c["type"].upper()]
    numeric_cols = [c["name"] for c in columns if any(t in c["type"].upper() for t in ["INT", "DOUBLE", "FLOAT", "DECIMAL", "NUMERIC"])]
    
    try:
        # Get unique counts for first 2 text columns (likely identifiers)
        for col in text_cols[:2]:
            result = data_engine.query(f'SELECT COUNT(DISTINCT "{col}") as cnt FROM {table_name}')
            stats["unique_counts"][col] = int(result.iloc[0]["cnt"])
        
        # Get sums for first 2 numeric columns
        for col in numeric_cols[:2]:
            result = data_engine.query(f'SELECT SUM("{col}") as total FROM {table_name}')
            total = result.iloc[0]["total"]
            if total is not None:
                stats["numeric_sums"][col] = float(total)
                
    except Exception:
        pass
    
    return stats


def _generate_column_descriptions(columns: List[Dict], data_type: str) -> List[Dict]:
    """
    Return columns as-is without adding hardcoded descriptions.
    Column meanings should be inferred by the LLM from column names and sample data.
    """
    return [
        {
            "name": col["name"],
            "type": col["type"],
            "description": ""  # LLM will infer from column name
        }
        for col in columns
    ]


def _generate_example_queries(table_name: str, columns: List[Dict], data_type: str) -> List[str]:
    """
    Generate generic example queries based on column types (not hardcoded data patterns).
    """
    col_names = [c["name"].lower() for c in columns]
    col_types = {c["name"].lower(): c["type"].upper() for c in columns}
    examples = []
    
    # Find numeric columns (for aggregations)
    numeric_cols = [name for name, typ in col_types.items() 
                    if any(t in typ for t in ["INT", "DOUBLE", "FLOAT", "DECIMAL", "NUMERIC"])]
    
    # Find text columns (for grouping)
    text_cols = [name for name, typ in col_types.items() 
                 if any(t in typ for t in ["VARCHAR", "TEXT", "CHAR"])]
    
    # Find date columns
    date_cols = [name for name, typ in col_types.items() 
                 if "DATE" in typ or "TIME" in typ]
    
    # Generate generic examples based on column types
    if numeric_cols:
        examples.append(f"Total of {numeric_cols[0]}")
        if text_cols:
            examples.append(f"Sum of {numeric_cols[0]} by {text_cols[0]}")
    
    if text_cols:
        examples.append(f"Count by {text_cols[0]}")
    
    if date_cols and numeric_cols:
        examples.append(f"Trend of {numeric_cols[0]} over time")
    
    examples.append(f"Show all data from {table_name}")
    
    return examples[:5]
