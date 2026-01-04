"""
Data Engine - DuckDB Integration
Treats Excel/CSV files as SQL tables
"""

import duckdb
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Any
from config import DUCKDB_PATH, WORKSPACE_DIR, SDM_TABLES


class DataEngine:
    """DuckDB-based data engine for financial data analysis."""
    
    def __init__(self, db_path: Path = DUCKDB_PATH):
        self.db_path = db_path
        self.conn = duckdb.connect(str(db_path))
        self._init_extensions()
        
    def _init_extensions(self):
        """Initialize DuckDB extensions for Excel support."""
        # Install and load spatial extension for Excel support
        self.conn.execute("INSTALL spatial;")
        self.conn.execute("LOAD spatial;")
        
    def load_excel(
        self,
        file_path: Path,
        sheet_name: Optional[str] = None,
        table_name: Optional[str] = None
    ) -> str:
        """Load an Excel file into DuckDB as a table."""
        
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Default table name from filename
        if table_name is None:
            table_name = file_path.stem.lower().replace(" ", "_").replace("-", "_")
        
        # Read Excel with pandas (DuckDB can query pandas DataFrames)
        if sheet_name:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
        else:
            df = pd.read_excel(file_path)
        
        # Register as table
        self.conn.register(table_name, df)
        
        return table_name
    
    def load_csv(self, file_path: Path, table_name: Optional[str] = None) -> str:
        """Load a CSV file into DuckDB as a table."""
        
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if table_name is None:
            table_name = file_path.stem.lower().replace(" ", "_").replace("-", "_")
        
        # DuckDB can read CSV directly
        self.conn.execute(f"""
            CREATE OR REPLACE TABLE {table_name} AS 
            SELECT * FROM read_csv_auto('{file_path}')
        """)
        
        return table_name
    
    def load_folder(self, folder_path: Path) -> Dict[str, str]:
        """Load all Excel/CSV files from a folder."""
        
        folder_path = Path(folder_path)
        if not folder_path.exists():
            raise FileNotFoundError(f"Folder not found: {folder_path}")
        
        loaded_tables = {}
        
        # Load Excel files
        for excel_file in folder_path.glob("*.xlsx"):
            table_name = self.load_excel(excel_file)
            loaded_tables[excel_file.name] = table_name
            
        for excel_file in folder_path.glob("*.xls"):
            table_name = self.load_excel(excel_file)
            loaded_tables[excel_file.name] = table_name
        
        # Load CSV files
        for csv_file in folder_path.glob("*.csv"):
            table_name = self.load_csv(csv_file)
            loaded_tables[csv_file.name] = table_name
        
        return loaded_tables
    
    def query(self, sql: str) -> pd.DataFrame:
        """Execute a SQL query and return results as DataFrame."""
        return self.conn.execute(sql).fetchdf()
    
    def execute(self, sql: str) -> None:
        """Execute a SQL statement."""
        self.conn.execute(sql)
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """Get information about a table."""
        
        # Get columns
        columns = self.conn.execute(f"DESCRIBE {table_name}").fetchdf()
        
        # Get row count
        count = self.conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        
        # Get sample data
        sample = self.conn.execute(f"SELECT * FROM {table_name} LIMIT 5").fetchdf()
        
        return {
            "table_name": table_name,
            "columns": columns.to_dict("records"),
            "row_count": count,
            "sample_data": sample.to_dict("records")
        }
    
    def list_tables(self) -> List[str]:
        """List all tables in the database."""
        result = self.conn.execute("SHOW TABLES").fetchdf()
        return result["name"].tolist() if not result.empty else []
    
    def get_headers(self, table_name: str) -> List[str]:
        """Get column headers for a table."""
        result = self.conn.execute(f"DESCRIBE {table_name}").fetchdf()
        return result["column_name"].tolist()
    
    def get_sample_rows(self, table_name: str, n: int = 10) -> List[Dict]:
        """Get sample rows from a table."""
        df = self.conn.execute(f"SELECT * FROM {table_name} LIMIT {n}").fetchdf()
        return df.to_dict("records")
    
    def close(self):
        """Close the database connection."""
        self.conn.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Convenience function
def get_data_engine() -> DataEngine:
    """Get the default data engine."""
    return DataEngine()

