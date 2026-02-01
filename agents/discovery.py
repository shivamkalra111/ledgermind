"""
Discovery Agent - Excel/CSV Structure Discovery

Architecture:
1. Load file into DuckDB (with auto header detection)
2. Extract schema + generate description using LLM
3. Save metadata to TableCatalog (persisted)
4. At query time: LLM reads catalog → selects tables → SQL model generates query

NOTE: This agent is DATA-AGNOSTIC - it does not assume any specific data type
(e.g., sales, purchases, invoices). The LLM understands the data from column
names and sample values.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import json

from core.data_engine import DataEngine
from core.table_catalog import TableCatalog, create_table_metadata
from llm.client import LLMClient
from config import DISCOVERY_SAMPLE_ROWS, WORKSPACE_DIR


@dataclass
class FileMetadata:
    """Metadata for a discovered file (generic, no data-type assumptions)."""
    filename: str
    table_name: str
    columns: List[str]
    row_count: int
    column_types: Dict[str, str] = field(default_factory=dict)


@dataclass
class DiscoveryResult:
    """Result of folder discovery."""
    folder_path: Path
    files_discovered: int
    tables_created: List[str]
    file_metadata: Dict[str, FileMetadata]  # filename -> metadata
    errors: List[str]
    catalog_updated: bool = False


class DiscoveryAgent:
    """
    Agent 1: Discovery
    
    Responsibilities:
    - Scan a folder for Excel/CSV files
    - Load data into DuckDB (with automatic header detection)
    - Save metadata to TableCatalog (for smart table selection)
    
    NOTE: This agent is DATA-AGNOSTIC. It does not:
    - Assume specific data types (sales, purchases, bank, etc.)
    - Map columns to a predefined schema
    - Require specific column names
    
    The LLM will understand the data from column names and samples.
    """
    
    def __init__(
        self,
        data_engine: Optional[DataEngine] = None,
        llm_client: Optional[LLMClient] = None,
        workspace_path: Optional[Path] = None
    ):
        self.data_engine = data_engine or DataEngine()
        self.llm = llm_client
        
        # Initialize table catalog for metadata persistence
        self.workspace_path = workspace_path
        self.catalog = TableCatalog(workspace_path) if workspace_path else None
        
    def discover(self, folder_path: Path) -> DiscoveryResult:
        """
        Discover and process all Excel/CSV files in a folder.
        
        Args:
            folder_path: Path to folder containing data files
            
        Returns:
            DiscoveryResult with details of what was found and loaded
        """
        
        folder_path = Path(folder_path)
        if not folder_path.exists():
            raise FileNotFoundError(f"Folder not found: {folder_path}")
        
        tables_created = []
        file_metadata = {}
        errors = []
        
        # Find all Excel and CSV files
        files = list(folder_path.glob("*.xlsx")) + \
                list(folder_path.glob("*.xls")) + \
                list(folder_path.glob("*.csv"))
        
        for file_path in files:
            try:
                result = self._process_file(file_path)
                tables_created.append(result["table_name"])
                file_metadata[file_path.name] = result["metadata"]
            except Exception as e:
                errors.append(f"{file_path.name}: {str(e)}")
        
        # Save discovery metadata
        self._save_discovery_meta(folder_path, file_metadata)
        
        # Save table catalog
        catalog_saved = False
        if self.catalog:
            catalog_saved = self.catalog.save()
        
        return DiscoveryResult(
            folder_path=folder_path,
            files_discovered=len(files),
            tables_created=tables_created,
            file_metadata=file_metadata,
            errors=errors,
            catalog_updated=catalog_saved
        )
    
    def _process_file(self, file_path: Path) -> Dict:
        """Process a single file: load and register in catalog."""
        
        # Load file into DuckDB (auto-detects headers)
        if file_path.suffix.lower() in ['.xlsx', '.xls']:
            table_name = self.data_engine.load_excel(file_path, auto_detect_header=True)
        else:
            table_name = self.data_engine.load_csv(file_path, auto_detect_header=True)
        
        # Get table info
        table_info = self.data_engine.get_table_info(table_name)
        headers = self.data_engine.get_headers(table_name)
        
        # Create file metadata (generic)
        metadata = FileMetadata(
            filename=file_path.name,
            table_name=table_name,
            columns=headers,
            row_count=table_info.get("row_count", 0),
            column_types={col: typ for col, typ in zip(
                table_info.get("columns", []), 
                table_info.get("types", [])
            )}
        )
        
        # Register table in catalog with rich metadata
        if self.catalog:
            try:
                catalog_metadata = create_table_metadata(
                    table_name=table_name,
                    source_file=file_path.name,
                    data_engine=self.data_engine,
                    llm_client=self.llm  # Use LLM to generate description
                )
                self.catalog.register_table(catalog_metadata)
            except Exception as e:
                print(f"Warning: Could not register {table_name} in catalog: {e}")
        
        return {
            "table_name": table_name,
            "metadata": metadata
        }
    
    def _save_discovery_meta(self, folder_path: Path, file_metadata: Dict[str, FileMetadata]):
        """Save discovery metadata for future use."""
        
        meta_path = folder_path / "discovery_meta.json"
        
        # Convert to serializable format
        meta = {}
        for filename, metadata in file_metadata.items():
            meta[filename] = {
                "table_name": metadata.table_name,
                "columns": metadata.columns,
                "row_count": metadata.row_count,
                "column_types": metadata.column_types
            }
        
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)
    
    def load_existing_meta(self, folder_path: Path) -> Optional[Dict]:
        """Load existing discovery metadata if available."""
        
        meta_path = Path(folder_path) / "discovery_meta.json"
        
        if meta_path.exists():
            with open(meta_path) as f:
                return json.load(f)
        
        return None
    
    def get_summary(self) -> str:
        """Get a summary of discovered data."""
        
        tables = self.data_engine.list_tables()
        
        if not tables:
            return "No data loaded yet."
        
        summary_lines = ["**Discovered Data Summary**\n"]
        
        for table in tables:
            info = self.data_engine.get_table_info(table)
            summary_lines.append(f"**{table}**")
            summary_lines.append(f"  - Rows: {info['row_count']}")
            summary_lines.append(f"  - Columns: {len(info['columns'])}")
            summary_lines.append("")
        
        return "\n".join(summary_lines)

