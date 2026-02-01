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
        table_name: Optional[str] = None,
        header_row: Optional[int] = None,
        auto_detect_header: bool = False
    ) -> str:
        """
        Load an Excel file into DuckDB as a table.
        
        Args:
            file_path: Path to Excel file
            sheet_name: Specific sheet to load
            table_name: Name for the table (defaults to filename)
            header_row: Row number containing headers (0-indexed). If None, uses row 0.
            auto_detect_header: If True, try to detect header row (use for messy files)
        
        Note:
            Most files have headers in row 0. Only enable auto_detect_header for
            files with company letterhead/preamble at the top.
        """
        
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Default table name from filename
        if table_name is None:
            table_name = file_path.stem.lower().replace(" ", "_").replace("-", "_")
        
        # Determine header row
        if header_row is None and auto_detect_header:
            header_row = self._detect_header_row(file_path, sheet_name)
        
        # Read Excel with pandas
        read_kwargs = {'sheet_name': sheet_name or 0}
        if header_row is not None:
            read_kwargs['header'] = header_row
            
        df = pd.read_excel(file_path, **read_kwargs)
        
        # Clean column names
        df = self._clean_dataframe(df)
        
        # Register as table
        self.conn.register(table_name, df)
        
        return table_name
    
    def _detect_header_row(self, file_path: Path, sheet_name: Optional[str] = None) -> int:
        """
        Auto-detect which row contains the actual headers.
        
        Uses pattern-based detection (no hardcoded keywords):
        1. Row with many non-null values (headers are usually all filled)
        2. Mostly string values (not numbers)
        3. Short text (headers are brief, not sentences)
        4. All values are unique (headers don't repeat)
        5. Comes after sparse rows (title/company info tends to have few columns)
        """
        try:
            # Read first 30 rows without header
            df = pd.read_excel(file_path, sheet_name=sheet_name or 0, header=None, nrows=30)
            
            if df.empty:
                return 0
            
            total_cols = len(df.columns)
            best_row = 0
            best_score = -1
            
            # Track if we've seen sparse rows (potential title/company info section)
            seen_sparse = False
            
            for idx, row in df.iterrows():
                non_null_count = row.notna().sum()
                
                # Mark sparse rows
                if non_null_count <= 2:
                    seen_sparse = True
                    continue
                
                # Calculate header likelihood score
                score = self._calculate_header_score(row, total_cols, seen_sparse)
                
                if score > best_score:
                    best_score = score
                    best_row = idx
            
            return best_row
            
        except Exception as e:
            return 0  # Default to first row
    
    def _calculate_header_score(self, row: pd.Series, total_cols: int, after_sparse: bool) -> float:
        """
        Calculate how likely a row is to be a header row.
        
        Scoring factors (no hardcoded domain keywords):
        - High fill rate (headers usually have all columns filled)
        - Mostly strings (data rows often have more numbers)
        - Short values (headers are typically brief)
        - Unique values (headers shouldn't have duplicates)
        - Position after sparse rows (title sections are usually sparse)
        """
        score = 0.0
        
        values = row.dropna().tolist()
        non_null_count = len(values)
        
        if non_null_count < 3:
            return -1  # Too few values to be a header
        
        # 1. Fill rate: Higher is better for headers
        fill_rate = non_null_count / total_cols
        score += fill_rate * 20  # Max 20 points
        
        # 2. String ratio: Headers are usually text, not numbers
        string_count = sum(1 for v in values if isinstance(v, str))
        string_ratio = string_count / non_null_count if non_null_count > 0 else 0
        score += string_ratio * 25  # Max 25 points
        
        # 3. Short values: Headers are typically brief
        short_count = 0
        very_long_count = 0
        for v in values:
            if isinstance(v, str):
                length = len(v.strip())
                if length <= 30:
                    short_count += 1
                if length > 60:
                    very_long_count += 1
        
        if non_null_count > 0:
            short_ratio = short_count / non_null_count
            score += short_ratio * 20  # Max 20 points
            score -= very_long_count * 5  # Penalty for long text
        
        # 4. Uniqueness: Header values should be unique
        unique_count = len(set(str(v).lower().strip() for v in values if isinstance(v, str)))
        if string_count > 0:
            unique_ratio = unique_count / string_count
            score += unique_ratio * 15  # Max 15 points
        
        # 5. Position bonus: Headers often come after sparse title rows
        if after_sparse:
            score += 10
        
        # 6. No pure numeric strings in header (e.g., "123" is likely data)
        numeric_string_count = sum(
            1 for v in values 
            if isinstance(v, str) and v.strip().replace('.', '').replace(',', '').isdigit()
        )
        score -= numeric_string_count * 8  # Penalty
        
        # 7. Typical header patterns (language-agnostic)
        # Headers often have: underscores, camelCase, or Title Case
        pattern_matches = 0
        for v in values:
            if isinstance(v, str):
                v_str = v.strip()
                # Check for common header patterns
                if '_' in v_str:  # snake_case
                    pattern_matches += 1
                elif v_str != v_str.lower() and v_str != v_str.upper():  # Mixed case
                    pattern_matches += 1
                elif v_str.istitle():  # Title Case
                    pattern_matches += 1
        
        score += pattern_matches * 2  # Small bonus
        
        return score
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean DataFrame: standardize column names, remove empty rows/columns."""
        
        # Remove completely empty columns first
        df = df.dropna(axis=1, how='all')
        
        # Standardize column names
        new_columns = []
        for i, col in enumerate(df.columns):
            if isinstance(col, str):
                # Clean column name
                clean = col.strip().lower()
                clean = clean.replace(' ', '_').replace('-', '_')
                clean = ''.join(c if c.isalnum() or c == '_' else '_' for c in clean)
                clean = '_'.join(filter(None, clean.split('_')))  # Remove multiple underscores
                
                # Skip unnamed columns (these are usually empty or index columns)
                if clean.startswith('unnamed') or clean == '':
                    # Check if this column has any non-null values
                    if df.iloc[:, i].notna().sum() == 0:
                        clean = f"_drop_{i}"  # Mark for removal
                    else:
                        clean = f"col_{i}"
                
                new_columns.append(clean)
            else:
                new_columns.append(f"col_{len(new_columns)}")
        
        df.columns = new_columns
        
        # Drop columns marked for removal
        drop_cols = [c for c in df.columns if c.startswith('_drop_')]
        if drop_cols:
            df = df.drop(columns=drop_cols)
        
        # Remove completely empty rows
        df = df.dropna(how='all')
        
        # Remove rows where all values are NaN or the same as header (duplicate headers)
        if len(df) > 0:
            # Check for duplicate header rows
            first_row = df.iloc[0] if len(df) > 0 else None
            if first_row is not None:
                mask = df.apply(lambda row: not all(
                    str(row[col]).lower() == str(col).lower() 
                    for col in df.columns if pd.notna(row[col])
                ), axis=1)
                df = df[mask]
        
        return df.reset_index(drop=True)
    
    def load_csv(
        self, 
        file_path: Path, 
        table_name: Optional[str] = None,
        header_row: Optional[int] = None,
        auto_detect_header: bool = False
    ) -> str:
        """
        Load a CSV file into DuckDB as a table.
        
        Args:
            file_path: Path to CSV file
            table_name: Name for the table (defaults to filename)
            header_row: Row number containing headers (0-indexed). If None, uses row 0.
            auto_detect_header: If True, try to detect header row (use for messy files)
        
        Note:
            Most CSV files have headers in row 0. DuckDB's read_csv_auto handles
            this efficiently. Only enable auto_detect_header for files with preamble.
        """
        
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if table_name is None:
            table_name = file_path.stem.lower().replace(" ", "_").replace("-", "_")
        
        # Determine if we need to skip rows
        skip_rows = header_row or 0
        if header_row is None and auto_detect_header:
            skip_rows = self._detect_csv_header_row(file_path)
        
        if skip_rows > 0:
            # Read with pandas, skip preamble rows, then load to DuckDB
            df = pd.read_csv(file_path, skiprows=skip_rows)
            df = self._clean_dataframe(df)
            self.conn.register(table_name, df)
        else:
            # DuckDB can read CSV directly (faster for clean files)
            self.conn.execute(f"""
                CREATE OR REPLACE TABLE {table_name} AS 
                SELECT * FROM read_csv_auto('{file_path}')
            """)
        
        return table_name
    
    def _detect_csv_header_row(self, file_path: Path) -> int:
        """
        Detect header row in CSV files that may have preamble text.
        
        Returns the number of rows to skip (0 if header is first row).
        """
        try:
            # Read file as text first to handle inconsistent column counts
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = [f.readline() for _ in range(30)]
            
            # Find the row with the most consistent delimiter count
            delimiter = ','
            
            # Count delimiters in each line
            delimiter_counts = []
            for i, line in enumerate(lines):
                if line.strip():
                    count = line.count(delimiter)
                    delimiter_counts.append((i, count, line.strip()))
                else:
                    delimiter_counts.append((i, 0, ''))
            
            if not delimiter_counts:
                return 0
            
            # Find the most common high delimiter count (likely data rows)
            counts_only = [c for _, c, _ in delimiter_counts if c > 0]
            if not counts_only:
                return 0
            
            # Most common delimiter count among non-zero rows
            from collections import Counter
            most_common_count = Counter(counts_only).most_common(1)[0][0]
            
            # Find first row with this count (likely header)
            for i, count, line in delimiter_counts:
                if count == most_common_count:
                    return i
            
            return 0
            
        except Exception:
            return 0
    
    def load_file(
        self, 
        file_path: Path, 
        table_name: Optional[str] = None,
        auto_detect_header: bool = False
    ) -> str:
        """
        Load a single file (Excel or CSV) into DuckDB.
        
        Args:
            file_path: Path to file
            table_name: Optional table name (defaults to filename)
            auto_detect_header: If True, try to detect header row for messy files
            
        Returns:
            Name of the created table
        """
        file_path = Path(file_path)
        ext = file_path.suffix.lower()
        
        if ext in ['.xlsx', '.xls']:
            return self.load_excel(file_path, table_name=table_name, auto_detect_header=auto_detect_header)
        elif ext == '.csv':
            return self.load_csv(file_path, table_name=table_name, auto_detect_header=auto_detect_header)
        else:
            raise ValueError(f"Unsupported file type: {ext}. Supported: .xlsx, .xls, .csv")
    
    def load_folder(self, folder_path: Path, auto_detect_header: bool = False) -> Dict[str, str]:
        """Load all Excel/CSV files from a folder."""
        
        folder_path = Path(folder_path)
        if not folder_path.exists():
            raise FileNotFoundError(f"Folder not found: {folder_path}")
        
        loaded_tables = {}
        
        # Load Excel files
        for excel_file in folder_path.glob("*.xlsx"):
            table_name = self.load_excel(excel_file, auto_detect_header=auto_detect_header)
            loaded_tables[excel_file.name] = table_name
            
        for excel_file in folder_path.glob("*.xls"):
            table_name = self.load_excel(excel_file, auto_detect_header=auto_detect_header)
            loaded_tables[excel_file.name] = table_name
        
        # Load CSV files
        for csv_file in folder_path.glob("*.csv"):
            table_name = self.load_csv(csv_file, auto_detect_header=auto_detect_header)
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
    
    def validate_headers(self, table_name: str) -> Dict[str, Any]:
        """
        Check if table headers look valid.
        
        Returns:
            {
                "valid": True/False,
                "issues": ["list of potential problems"],
                "suggestion": "Possible fix suggestion"
            }
        """
        headers = self.get_headers(table_name)
        sample = self.get_sample_rows(table_name, 3)
        
        issues = []
        
        # Check 1: Too many "unnamed" or "col_" columns
        unnamed_count = sum(1 for h in headers if h.startswith(('unnamed', 'col_', 'column')))
        if unnamed_count > len(headers) * 0.3:
            issues.append(f"{unnamed_count} columns have generic names (unnamed/col_)")
        
        # Check 2: Headers look like data (numbers, dates, long text)
        numeric_headers = sum(1 for h in headers if h.replace('_', '').replace('.', '').isdigit())
        if numeric_headers > 0:
            issues.append(f"{numeric_headers} column names are numeric (may be data, not headers)")
        
        # Check 3: Very long column names (might be data)
        long_headers = [h for h in headers if len(h) > 50]
        if long_headers:
            issues.append(f"{len(long_headers)} column names are very long (>50 chars)")
        
        # Check 4: First row of data looks like headers (duplicate header detection)
        if sample:
            first_row_values = list(sample[0].values())
            string_values = [str(v) for v in first_row_values if v is not None]
            # Check if first row values look like headers (short, text, unique)
            if all(isinstance(v, str) and len(v) < 30 for v in first_row_values if v):
                all_unique = len(set(string_values)) == len(string_values)
                no_numbers = all(not str(v).replace('.', '').isdigit() for v in string_values)
                if all_unique and no_numbers and len(string_values) > 3:
                    issues.append("First data row looks like it might be headers")
        
        # Generate suggestion
        suggestion = None
        if issues:
            suggestion = "Try loading with header_row parameter or auto_detect_header=True"
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "suggestion": suggestion,
            "headers": headers[:10]  # First 10 for reference
        }
    
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

