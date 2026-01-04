"""
Header Mapper - Maps Excel headers to Standard Data Model
Uses LLM for semantic understanding of ambiguous headers
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json

from config import DISCOVERY_PROMPT, DISCOVERY_CONFIDENCE_THRESHOLD
from core.schema import SheetType, get_sdm_field, HEADER_ALIASES


@dataclass
class MappingResult:
    """Result of header mapping."""
    sheet_type: SheetType
    confidence: float
    header_mapping: Dict[str, str]  # original -> sdm_field
    unmapped_headers: List[str]
    

class HeaderMapper:
    """Maps Excel/CSV headers to Standard Data Model using rules + LLM."""
    
    def __init__(self, llm_client=None):
        """
        Initialize mapper.
        
        Args:
            llm_client: Optional LLM client for semantic mapping.
                       If None, uses rule-based mapping only.
        """
        self.llm = llm_client
        
    def map_headers(
        self,
        headers: List[str],
        sample_data: Optional[List[Dict]] = None
    ) -> MappingResult:
        """
        Map headers to Standard Data Model.
        
        Args:
            headers: List of column headers
            sample_data: Optional sample rows for context
            
        Returns:
            MappingResult with sheet type and header mappings
        """
        
        # Step 1: Rule-based mapping
        rule_mapping = self._rule_based_mapping(headers)
        
        # Step 2: Determine sheet type from mapped fields
        sheet_type, confidence = self._infer_sheet_type(rule_mapping)
        
        # Step 3: If confidence is low and LLM available, use LLM
        unmapped = [h for h in headers if h not in rule_mapping]
        
        if confidence < DISCOVERY_CONFIDENCE_THRESHOLD and self.llm and sample_data:
            llm_result = self._llm_mapping(headers, sample_data)
            
            # Merge LLM results with rule-based
            for orig, sdm in llm_result.get("header_mapping", {}).items():
                if orig not in rule_mapping:
                    rule_mapping[orig] = sdm
            
            # Update sheet type if LLM is more confident
            if llm_result.get("confidence", 0) > confidence:
                sheet_type = SheetType(llm_result.get("sheet_type", "unknown"))
                confidence = llm_result.get("confidence", confidence)
            
            unmapped = llm_result.get("unmapped_headers", unmapped)
        
        return MappingResult(
            sheet_type=sheet_type,
            confidence=confidence,
            header_mapping=rule_mapping,
            unmapped_headers=unmapped
        )
    
    def _rule_based_mapping(self, headers: List[str]) -> Dict[str, str]:
        """Apply rule-based header mapping."""
        mapping = {}
        
        for header in headers:
            sdm_field = get_sdm_field(header)
            if sdm_field:
                mapping[header] = sdm_field
        
        return mapping
    
    def _infer_sheet_type(self, mapping: Dict[str, str]) -> Tuple[SheetType, float]:
        """Infer sheet type from mapped fields."""
        
        sdm_fields = set(mapping.values())
        
        # Sales indicators
        sales_fields = {"invoice_number", "invoice_date", "party_name", "taxable_value", "cgst_amount", "sgst_amount"}
        sales_score = len(sdm_fields & sales_fields) / len(sales_fields)
        
        # Bank indicators
        bank_fields = {"transaction_date", "description", "credit_amount", "debit_amount", "balance"}
        bank_score = len(sdm_fields & bank_fields) / len(bank_fields) if bank_fields else 0
        
        # Determine type
        if sales_score >= 0.5:
            # Could be sales or purchase - check for customer vs vendor hints
            return SheetType.SALES_REGISTER, sales_score
        elif bank_score >= 0.4:
            return SheetType.BANK_STATEMENT, bank_score
        else:
            return SheetType.UNKNOWN, 0.3
    
    def _llm_mapping(self, headers: List[str], sample_data: List[Dict]) -> Dict:
        """Use LLM for semantic header mapping."""
        
        prompt = DISCOVERY_PROMPT.format(
            headers=", ".join(headers),
            sample_data=json.dumps(sample_data[:3], default=str, indent=2)
        )
        
        try:
            result = self.llm.generate_json(prompt)
            return result
        except Exception as e:
            print(f"LLM mapping failed: {e}")
            return {}
    
    def create_view_sql(
        self,
        source_table: str,
        mapping: Dict[str, str],
        view_name: str
    ) -> str:
        """Generate SQL to create a standardized view."""
        
        # Build column selections with aliases
        columns = []
        for original, sdm_field in mapping.items():
            # Escape column names with spaces/special chars
            safe_original = f'"{original}"'
            columns.append(f"{safe_original} AS {sdm_field}")
        
        columns_sql = ",\n    ".join(columns)
        
        return f"""
CREATE OR REPLACE VIEW {view_name} AS
SELECT
    {columns_sql}
FROM {source_table}
"""

