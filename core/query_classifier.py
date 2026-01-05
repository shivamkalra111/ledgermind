"""
Query Classifier - Routes questions to appropriate knowledge source

This module classifies incoming queries and routes them to the correct
knowledge layer:
- Layer 1 (Reference Data): Rate lookups, code lookups → CSV/DB
- Layer 2 (Legal Knowledge): Rules, procedures, compliance → ChromaDB RAG  
- Layer 3 (Foundational): Definitions, concepts → LLM general knowledge
"""

import re
from enum import Enum
from dataclasses import dataclass
from typing import Optional, List, Tuple

from core.reference_data import (
    load_goods_rates,
    load_services_rates,
    get_rate_for_hsn,
    get_rate_for_sac,
    search_rate_by_name,
)


class QueryType(Enum):
    """Types of queries based on knowledge source needed."""
    
    # Layer 3: LLM already knows this (definitions, concepts)
    DEFINITION = "definition"
    
    # Layer 1: Lookup from our reference data (rates, codes)
    RATE_LOOKUP = "rate_lookup"
    HSN_SAC_LOOKUP = "hsn_sac_lookup"
    
    # Layer 2: RAG from legal documents (rules, procedures)
    LEGAL_RULE = "legal_rule"
    COMPLIANCE = "compliance"
    
    # Requires user's data (DuckDB)
    DATA_QUERY = "data_query"
    
    # General/mixed
    GENERAL = "general"


@dataclass
class ClassifiedQuery:
    """Result of query classification."""
    query_type: QueryType
    confidence: float
    extracted_entities: dict  # HSN codes, item names, etc.
    suggested_source: str  # "llm", "csv", "chromadb", "duckdb"
    reasoning: str


class QueryClassifier:
    """
    Classifies queries to route them to the appropriate knowledge source.
    
    This is NOT about understanding intent (that's the router).
    This is about WHERE to get the answer from.
    """
    
    def __init__(self):
        # Patterns for classification
        self.definition_patterns = [
            r"what (?:is|are|does)(?: a| an| the)? (.+?)(?:\?|$)",
            r"(?:explain|define|describe)(?: (?:what|the))? (.+?)(?:\?|$)",
            r"(?:tell me about|what do you mean by) (.+?)(?:\?|$)",
            r"how (?:does|do) (.+?) work",
            r"meaning of (.+?)(?:\?|$)",
        ]
        
        self.rate_lookup_patterns = [
            r"(?:gst|tax) (?:rate|%) (?:on|for|of) (.+?)(?:\?|$)",
            r"(?:what|how much) (?:is the )?(?:gst|tax) on (.+?)(?:\?|$)",
            r"(.+?) (?:gst|tax) rate",
            r"rate (?:for|of|on) (.+?)(?:\?|$)",
        ]
        
        self.hsn_sac_patterns = [
            r"hsn (?:code|number)? (?:for|of) (.+?)(?:\?|$)",
            r"sac (?:code|number)? (?:for|of) (.+?)(?:\?|$)",
            r"(.+?) hsn (?:code)?",
            r"(.+?) sac (?:code)?",
        ]
        
        self.legal_patterns = [
            r"section \d+",
            r"rule \d+",
            r"can i claim",
            r"(?:is|are) .+ (?:allowed|eligible|applicable)",
            r"(?:itc|input tax credit) (?:on|for|eligibility)",
            r"blocked credit",
            r"time limit",
            r"penalty",
            r"(?:gstr|return) filing",
            r"due date for (?:filing|gstr)",
        ]
        
        self.data_patterns = [
            r"(?:my|our) (?:total|sales|purchases|revenue|expenses)",
            r"(?:show|list|get) (?:my|our|all)",
            r"how (?:much|many) (?:did|do) (?:i|we)",
            r"(?:last|this) (?:month|quarter|year)",
        ]
        
        # GST concept keywords (LLM knows these)
        self.gst_concepts = {
            'cgst', 'sgst', 'igst', 'utgst', 'gst', 'cess',
            'input tax credit', 'itc', 'reverse charge', 'rcm',
            'composition scheme', 'e-way bill', 'e-invoice',
            'place of supply', 'time of supply', 'value of supply',
            'taxable person', 'exempt supply', 'nil rated',
            'zero rated', 'composite supply', 'mixed supply',
            'intra-state', 'inter-state', 'import', 'export',
        }
    
    def classify(self, query: str) -> ClassifiedQuery:
        """
        Classify a query to determine the best knowledge source.
        
        Returns:
            ClassifiedQuery with type, confidence, and routing info
        """
        query_lower = query.lower().strip()
        
        # Check for data queries first (needs user's data)
        if self._matches_patterns(query_lower, self.data_patterns):
            return ClassifiedQuery(
                query_type=QueryType.DATA_QUERY,
                confidence=0.9,
                extracted_entities={},
                suggested_source="duckdb",
                reasoning="Query refers to user's own data"
            )
        
        # Check for rate lookups (Layer 1 - CSV)
        rate_match = self._extract_from_patterns(query_lower, self.rate_lookup_patterns)
        if rate_match:
            return ClassifiedQuery(
                query_type=QueryType.RATE_LOOKUP,
                confidence=0.85,
                extracted_entities={"item": rate_match},
                suggested_source="csv",
                reasoning=f"Rate lookup for: {rate_match}"
            )
        
        # Check for HSN/SAC lookups (Layer 1 - CSV)
        hsn_sac_match = self._extract_from_patterns(query_lower, self.hsn_sac_patterns)
        if hsn_sac_match:
            return ClassifiedQuery(
                query_type=QueryType.HSN_SAC_LOOKUP,
                confidence=0.85,
                extracted_entities={"item": hsn_sac_match},
                suggested_source="csv",
                reasoning=f"HSN/SAC lookup for: {hsn_sac_match}"
            )
        
        # Check for legal/rule questions (Layer 2 - ChromaDB)
        if self._matches_patterns(query_lower, self.legal_patterns):
            return ClassifiedQuery(
                query_type=QueryType.LEGAL_RULE,
                confidence=0.8,
                extracted_entities={},
                suggested_source="chromadb",
                reasoning="Query about legal rules, sections, or procedures"
            )
        
        # Check for definition/concept questions (Layer 3 - LLM)
        definition_match = self._extract_from_patterns(query_lower, self.definition_patterns)
        if definition_match:
            # Check if it's a GST concept the LLM knows
            concept = definition_match.lower()
            is_gst_concept = any(c in concept for c in self.gst_concepts)
            
            return ClassifiedQuery(
                query_type=QueryType.DEFINITION,
                confidence=0.9 if is_gst_concept else 0.7,
                extracted_entities={"concept": definition_match},
                suggested_source="llm",
                reasoning=f"Definition question for: {definition_match}"
            )
        
        # Default: Check if it mentions GST concepts (likely definition)
        if any(concept in query_lower for concept in self.gst_concepts):
            return ClassifiedQuery(
                query_type=QueryType.DEFINITION,
                confidence=0.6,
                extracted_entities={},
                suggested_source="llm",
                reasoning="Query mentions GST concepts"
            )
        
        # Fallback to ChromaDB for anything else GST-related
        if any(kw in query_lower for kw in ['gst', 'tax', 'invoice', 'return', 'credit']):
            return ClassifiedQuery(
                query_type=QueryType.GENERAL,
                confidence=0.5,
                extracted_entities={},
                suggested_source="chromadb",
                reasoning="General GST question - trying RAG"
            )
        
        # True general question
        return ClassifiedQuery(
            query_type=QueryType.GENERAL,
            confidence=0.4,
            extracted_entities={},
            suggested_source="llm",
            reasoning="General question - using LLM knowledge"
        )
    
    def _matches_patterns(self, text: str, patterns: List[str]) -> bool:
        """Check if text matches any of the patterns."""
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def _extract_from_patterns(self, text: str, patterns: List[str]) -> Optional[str]:
        """Extract captured group from first matching pattern."""
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match and match.groups():
                return match.group(1).strip()
        return None


def lookup_gst_rate(item_description: str) -> Optional[dict]:
    """
    Look up GST rate from CSV data for an item.
    
    Returns dict with rate info or None if not found.
    """
    item_lower = item_description.lower()
    
    # Search goods rates
    goods = load_goods_rates()
    for rate in goods:
        if item_lower in rate.get('item_name', '').lower():
            return {
                "type": "goods",
                "hsn_code": rate.get('hsn_code'),
                "item_name": rate.get('item_name'),
                "gst_rate": rate.get('gst_rate'),
                "cess_rate": rate.get('cess_rate', '0'),
                "category": rate.get('category'),
            }
    
    # Search services rates
    services = load_services_rates()
    for rate in services:
        if item_lower in rate.get('service_name', '').lower():
            return {
                "type": "services",
                "sac_code": rate.get('sac_code'),
                "service_name": rate.get('service_name'),
                "gst_rate": rate.get('gst_rate'),
                "category": rate.get('category'),
                "condition": rate.get('condition', ''),
            }
    
    return None


def format_rate_response(rate_info: dict, item: str) -> str:
    """Format rate lookup result as readable text."""
    if not rate_info:
        return f"Could not find GST rate for '{item}' in our database. Please check the HSN/SAC code."
    
    if rate_info["type"] == "goods":
        return f"""**GST Rate for {rate_info['item_name']}**

- **HSN Code:** {rate_info['hsn_code']}
- **GST Rate:** {rate_info['gst_rate']}%
- **Cess:** {rate_info['cess_rate']}%
- **Category:** {rate_info['category']}

For intra-state supply: CGST = {float(rate_info['gst_rate'])/2}% + SGST = {float(rate_info['gst_rate'])/2}%
For inter-state supply: IGST = {rate_info['gst_rate']}%"""
    
    else:  # services
        response = f"""**GST Rate for {rate_info['service_name']}**

- **SAC Code:** {rate_info['sac_code']}
- **GST Rate:** {rate_info['gst_rate']}%
- **Category:** {rate_info['category']}"""
        
        if rate_info.get('condition'):
            response += f"\n- **Condition:** {rate_info['condition']}"
        
        return response

