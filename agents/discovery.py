"""
Discovery Agent - Excel/CSV Structure Discovery and Mapping
Scans files, identifies sheet types, maps headers to Standard Data Model
"""

from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
import json

from core.data_engine import DataEngine
from core.mapper import HeaderMapper, MappingResult
from core.schema import SheetType
from llm.client import LLMClient
from config import DISCOVERY_SAMPLE_ROWS, WORKSPACE_DIR


@dataclass
class DiscoveryResult:
    """Result of folder discovery."""
    folder_path: Path
    files_discovered: int
    tables_created: List[str]
    mappings: Dict[str, MappingResult]
    errors: List[str]


class DiscoveryAgent:
    """
    Agent 1: Discovery & Mapping
    
    Responsibilities:
    - Scan a folder for Excel/CSV files
    - Identify sheet types (Sales, Purchase, Bank)
    - Map headers to Standard Data Model
    - Load data into DuckDB
    - Save mapping for future use
    """
    
    def __init__(
        self,
        data_engine: Optional[DataEngine] = None,
        llm_client: Optional[LLMClient] = None
    ):
        self.data_engine = data_engine or DataEngine()
        self.llm = llm_client
        self.mapper = HeaderMapper(llm_client)
        
    def discover(self, folder_path: Path) -> DiscoveryResult:
        """
        Discover and process all Excel/CSV files in a folder.
        
        Args:
            folder_path: Path to folder containing financial files
            
        Returns:
            DiscoveryResult with details of what was found and loaded
        """
        
        folder_path = Path(folder_path)
        if not folder_path.exists():
            raise FileNotFoundError(f"Folder not found: {folder_path}")
        
        tables_created = []
        mappings = {}
        errors = []
        
        # Find all Excel and CSV files
        files = list(folder_path.glob("*.xlsx")) + \
                list(folder_path.glob("*.xls")) + \
                list(folder_path.glob("*.csv"))
        
        for file_path in files:
            try:
                result = self._process_file(file_path)
                tables_created.append(result["table_name"])
                mappings[file_path.name] = result["mapping"]
            except Exception as e:
                errors.append(f"{file_path.name}: {str(e)}")
        
        # Save discovery metadata
        self._save_discovery_meta(folder_path, mappings)
        
        return DiscoveryResult(
            folder_path=folder_path,
            files_discovered=len(files),
            tables_created=tables_created,
            mappings=mappings,
            errors=errors
        )
    
    def _process_file(self, file_path: Path) -> Dict:
        """Process a single file: load, analyze, and map."""
        
        # Load file into DuckDB
        if file_path.suffix.lower() in ['.xlsx', '.xls']:
            table_name = self.data_engine.load_excel(file_path)
        else:
            table_name = self.data_engine.load_csv(file_path)
        
        # Get headers and sample data
        headers = self.data_engine.get_headers(table_name)
        sample_data = self.data_engine.get_sample_rows(table_name, DISCOVERY_SAMPLE_ROWS)
        
        # Map headers to SDM
        mapping_result = self.mapper.map_headers(headers, sample_data)
        
        # If we have a good mapping, create a standardized view
        if mapping_result.confidence >= 0.5 and mapping_result.header_mapping:
            view_name = f"sdm_{mapping_result.sheet_type.value}"
            view_sql = self.mapper.create_view_sql(
                table_name, 
                mapping_result.header_mapping,
                view_name
            )
            try:
                self.data_engine.execute(view_sql)
            except Exception as e:
                print(f"Could not create view {view_name}: {e}")
        
        return {
            "table_name": table_name,
            "mapping": mapping_result
        }
    
    def _save_discovery_meta(self, folder_path: Path, mappings: Dict[str, MappingResult]):
        """Save discovery metadata for future use."""
        
        meta_path = folder_path / "discovery_meta.json"
        
        # Convert to serializable format
        meta = {}
        for filename, mapping in mappings.items():
            meta[filename] = {
                "sheet_type": mapping.sheet_type.value,
                "confidence": mapping.confidence,
                "header_mapping": mapping.header_mapping,
                "unmapped_headers": mapping.unmapped_headers
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
        
        summary_lines = ["📊 **Discovered Data Summary**\n"]
        
        for table in tables:
            info = self.data_engine.get_table_info(table)
            summary_lines.append(f"**{table}**")
            summary_lines.append(f"  - Rows: {info['row_count']}")
            summary_lines.append(f"  - Columns: {len(info['columns'])}")
            summary_lines.append("")
        
        return "\n".join(summary_lines)

