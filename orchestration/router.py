"""
Intent Router - Classifies user input and routes to appropriate handler
"""

from enum import Enum
from typing import Optional, Tuple
from dataclasses import dataclass
import re

from llm.client import LLMClient


class IntentType(Enum):
    """Types of user intents."""
    FOLDER_ANALYSIS = "folder_analysis"      # Analyze a folder of files
    DATA_QUERY = "data_query"                # Query user's data
    KNOWLEDGE_QUERY = "knowledge_query"      # Ask about GST rules
    COMPLIANCE_CHECK = "compliance_check"    # Run compliance audit
    STRATEGIC_ANALYSIS = "strategic_analysis"  # Run strategic analysis
    HELP = "help"
    UNKNOWN = "unknown"


@dataclass
class ParsedIntent:
    """Parsed user intent with metadata."""
    intent_type: IntentType
    confidence: float
    extracted_path: Optional[str] = None
    extracted_query: Optional[str] = None


class IntentRouter:
    """Routes user input to appropriate agent or handler."""
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client
        
        # Pattern matchers for quick routing
        self.patterns = {
            IntentType.FOLDER_ANALYSIS: [
                r"analyze\s+(?:folder|directory|path|files?)\s*[:\s]*(.+)",
                r"load\s+(?:folder|directory|files?)\s*[:\s]*(.+)",
                r"scan\s+(.+)",
                r"process\s+(?:folder|directory)\s*[:\s]*(.+)",
            ],
            IntentType.DATA_QUERY: [
                r"(?:what(?:'s| is)|show|get|find|list)\s+(?:my|our|the)\s+(.+)",
                r"(?:total|sum|count|average)\s+(.+)",
                r"(?:how much|how many)\s+(.+)",
            ],
            IntentType.COMPLIANCE_CHECK: [
                r"(?:run|check|audit|verify)\s+compliance",
                r"(?:check|find)\s+(?:issues?|problems?|errors?)",
                r"compliance\s+(?:check|audit|report)",
                r"(?:check|verify)\s+(?:gst|tax|itc)",
            ],
            IntentType.STRATEGIC_ANALYSIS: [
                r"(?:analyze|rank|list)\s+vendors?",
                r"(?:forecast|predict)\s+(?:cash\s*flow|revenue|expenses?)",
                r"strategic\s+(?:analysis|report)",
                r"(?:profit|margin)\s+analysis",
            ],
            IntentType.KNOWLEDGE_QUERY: [
                r"(?:what|explain|describe|define)\s+(?:is|are|does)\s+(.+)",
                r"(?:section|rule|act)\s+\d+",
                r"(?:gst|cgst|sgst|igst|itc)\s+(?:rule|section|law)",
                r"(?:can i|is it allowed|eligible)",
            ],
            IntentType.HELP: [
                r"^help$",
                r"^what can you do",
                r"^commands?$",
            ],
        }
    
    def route(self, user_input: str) -> ParsedIntent:
        """
        Parse user input and determine intent.
        
        Args:
            user_input: Raw user input string
            
        Returns:
            ParsedIntent with type, confidence, and extracted data
        """
        
        user_input = user_input.strip()
        
        if not user_input:
            return ParsedIntent(IntentType.UNKNOWN, 0.0)
        
        # Check if it looks like a file path
        if self._looks_like_path(user_input):
            return ParsedIntent(
                IntentType.FOLDER_ANALYSIS,
                0.9,
                extracted_path=user_input
            )
        
        # Try pattern matching first (fast)
        for intent_type, patterns in self.patterns.items():
            for pattern in patterns:
                match = re.search(pattern, user_input, re.IGNORECASE)
                if match:
                    extracted = match.group(1) if match.groups() else None
                    
                    if intent_type == IntentType.FOLDER_ANALYSIS:
                        return ParsedIntent(intent_type, 0.85, extracted_path=extracted)
                    else:
                        return ParsedIntent(intent_type, 0.8, extracted_query=extracted or user_input)
        
        # If no pattern matched, use heuristics
        lower_input = user_input.lower()
        
        # Data query indicators
        if any(kw in lower_input for kw in ["my", "our", "total", "sum", "show", "list"]):
            return ParsedIntent(IntentType.DATA_QUERY, 0.6, extracted_query=user_input)
        
        # Knowledge query indicators  
        if any(kw in lower_input for kw in ["what is", "explain", "section", "rule", "gst", "tax"]):
            return ParsedIntent(IntentType.KNOWLEDGE_QUERY, 0.6, extracted_query=user_input)
        
        # Default to knowledge query for questions
        if user_input.endswith("?"):
            return ParsedIntent(IntentType.KNOWLEDGE_QUERY, 0.5, extracted_query=user_input)
        
        # Fall back to LLM classification if available
        if self.llm:
            return self._llm_classify(user_input)
        
        return ParsedIntent(IntentType.UNKNOWN, 0.3, extracted_query=user_input)
    
    def _looks_like_path(self, text: str) -> bool:
        """Check if text looks like a file/folder path."""
        path_indicators = [
            text.startswith("/"),
            text.startswith("~"),
            text.startswith("./"),
            text.startswith("../"),
            ":\\" in text,  # Windows
            "/" in text and not " " in text.split("/")[0],
        ]
        return any(path_indicators)
    
    def _llm_classify(self, user_input: str) -> ParsedIntent:
        """Use LLM to classify intent when patterns fail."""
        
        prompt = f"""Classify this user input into ONE category:

User Input: "{user_input}"

Categories:
- folder_analysis: User wants to analyze/load files from a folder
- data_query: User is asking about their own financial data
- knowledge_query: User is asking about GST rules, accounting concepts
- compliance_check: User wants to check for compliance issues
- strategic_analysis: User wants vendor/cash flow analysis
- help: User needs help with commands
- unknown: Cannot determine

Respond with just the category name."""

        try:
            response = self.llm.generate(prompt, max_tokens=20)
            category = response.strip().lower().replace("_", " ").replace(" ", "_")
            
            try:
                intent_type = IntentType(category)
                return ParsedIntent(intent_type, 0.7, extracted_query=user_input)
            except ValueError:
                pass
        except:
            pass
        
        return ParsedIntent(IntentType.UNKNOWN, 0.3, extracted_query=user_input)

