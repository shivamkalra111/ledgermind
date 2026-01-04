"""
Agent Workflow - Orchestrates the multi-agent system
Uses LangGraph for agent coordination
"""

from typing import Dict, Any, Optional, TypedDict, Annotated
from dataclasses import dataclass
from pathlib import Path
from enum import Enum

from agents.discovery import DiscoveryAgent
from agents.compliance import ComplianceAgent
from agents.strategist import StrategistAgent
from orchestration.router import IntentRouter, IntentType, ParsedIntent
from core.data_engine import DataEngine
from core.knowledge import KnowledgeBase
from llm.client import LLMClient
from config import SYSTEM_PROMPT


class WorkflowState(TypedDict):
    """State passed between workflow nodes."""
    user_input: str
    intent: Optional[ParsedIntent]
    data_loaded: bool
    discovery_result: Optional[Dict]
    compliance_result: Optional[Dict]
    strategist_result: Optional[Dict]
    knowledge_result: Optional[str]
    final_response: str
    error: Optional[str]


class AgentWorkflow:
    """
    Orchestrates the multi-agent workflow.
    
    Flow:
    1. User input → Intent Router
    2. Based on intent, route to appropriate agent(s)
    3. Aggregate results → Generate response
    """
    
    def __init__(self):
        # Initialize shared resources
        self.data_engine = DataEngine()
        self.knowledge_base = KnowledgeBase()
        self.llm = LLMClient()
        
        # Initialize agents
        self.discovery_agent = DiscoveryAgent(self.data_engine, self.llm)
        self.compliance_agent = ComplianceAgent(self.data_engine, self.knowledge_base, self.llm)
        self.strategist_agent = StrategistAgent(self.data_engine, self.llm)
        
        # Initialize router
        self.router = IntentRouter(self.llm)
        
        # Track state
        self._data_loaded = False
    
    def run(self, user_input: str) -> str:
        """
        Process user input through the workflow.
        
        Args:
            user_input: User's question or command
            
        Returns:
            Response string
        """
        
        # Step 1: Route intent
        intent = self.router.route(user_input)
        
        # Step 2: Execute based on intent
        try:
            if intent.intent_type == IntentType.FOLDER_ANALYSIS:
                return self._handle_folder_analysis(intent.extracted_path)
            
            elif intent.intent_type == IntentType.COMPLIANCE_CHECK:
                return self._handle_compliance_check()
            
            elif intent.intent_type == IntentType.STRATEGIC_ANALYSIS:
                return self._handle_strategic_analysis()
            
            elif intent.intent_type == IntentType.DATA_QUERY:
                return self._handle_data_query(intent.extracted_query)
            
            elif intent.intent_type == IntentType.KNOWLEDGE_QUERY:
                return self._handle_knowledge_query(intent.extracted_query)
            
            elif intent.intent_type == IntentType.HELP:
                return self._get_help_text()
            
            else:
                return self._handle_unknown(user_input)
                
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def _handle_folder_analysis(self, folder_path: Optional[str]) -> str:
        """Handle folder analysis request."""
        
        if not folder_path:
            return "Please provide a folder path to analyze. Example: `/path/to/your/excels/`"
        
        path = Path(folder_path).expanduser()
        
        if not path.exists():
            return f"❌ Folder not found: {path}"
        
        # Run discovery agent
        result = self.discovery_agent.discover(path)
        self._data_loaded = True
        
        # Format response
        response = f"""
## 📁 Folder Analysis Complete

**Path:** {result.folder_path}
**Files Found:** {result.files_discovered}
**Tables Created:** {len(result.tables_created)}

### Discovered Sheets:
"""
        
        for filename, mapping in result.mappings.items():
            response += f"\n**{filename}**\n"
            response += f"  - Type: {mapping.sheet_type.value}\n"
            response += f"  - Confidence: {mapping.confidence:.0%}\n"
            response += f"  - Mapped Fields: {len(mapping.header_mapping)}\n"
        
        if result.errors:
            response += f"\n### ⚠️ Errors:\n"
            for error in result.errors:
                response += f"  - {error}\n"
        
        response += "\n✅ Data loaded! You can now run compliance checks or ask questions about your data."
        
        return response
    
    def _handle_compliance_check(self) -> str:
        """Handle compliance check request."""
        
        if not self._data_loaded:
            return "⚠️ No data loaded. Please analyze a folder first.\n\nExample: `analyze folder /path/to/your/excels/`"
        
        # Run compliance agent
        report = self.compliance_agent.run_full_audit()
        
        # Format response
        response = report.summary
        
        if report.issues:
            response += "\n### Issues Found:\n"
            for issue in report.issues[:10]:  # Show top 10
                emoji = "🔴" if issue.severity == "critical" else "🟡" if issue.severity == "warning" else "🔵"
                response += f"\n{emoji} **{issue.issue_type}**\n"
                response += f"   {issue.description}\n"
                if issue.amount_impact:
                    response += f"   💰 Impact: ₹{issue.amount_impact:,.0f}\n"
                response += f"   📖 {issue.reference}\n"
        
        return response
    
    def _handle_strategic_analysis(self) -> str:
        """Handle strategic analysis request."""
        
        if not self._data_loaded:
            return "⚠️ No data loaded. Please analyze a folder first.\n\nExample: `analyze folder /path/to/your/excels/`"
        
        # Run strategist agent
        report = self.strategist_agent.run_full_analysis()
        
        # Format response
        response = "## 📊 Strategic Analysis Report\n\n"
        
        # Vendor rankings
        if report.vendor_rankings:
            response += "### 🏭 Top Vendors by Reliability\n"
            for i, vendor in enumerate(report.vendor_rankings[:5], 1):
                response += f"{i}. **{vendor.vendor_name}** - Score: {vendor.reliability_score:.0f}/100\n"
                response += f"   Transactions: {vendor.total_transactions}, Value: ₹{vendor.total_value:,.0f}\n"
        
        # Cash flow forecast
        if report.cash_flow_forecasts:
            response += "\n### 💰 Cash Flow Forecast\n"
            for forecast in report.cash_flow_forecasts:
                emoji = "✅" if forecast.net_cash_flow > 0 else "⚠️"
                response += f"{emoji} **{forecast.period}**: Net ₹{forecast.net_cash_flow:,.0f} "
                response += f"(Confidence: {forecast.confidence:.0%})\n"
        
        # Recommendations
        if report.recommendations:
            response += "\n### 💡 Recommendations\n"
            for rec in report.recommendations:
                response += f"- {rec}\n"
        
        return response
    
    def _handle_data_query(self, query: Optional[str]) -> str:
        """Handle query about user's data."""
        
        if not self._data_loaded:
            return "⚠️ No data loaded. Please analyze a folder first."
        
        if not query:
            # Show available data
            return self.discovery_agent.get_summary()
        
        # Try to convert natural language to SQL using LLM
        tables = self.data_engine.list_tables()
        
        prompt = f"""Convert this question to a SQL query.

Available tables: {', '.join(tables)}

Question: {query}

Rules:
1. Use only the tables listed above
2. Return ONLY the SQL query, nothing else
3. If unsure, return SELECT * FROM first_table LIMIT 10

SQL Query:"""

        try:
            sql = self.llm.generate(prompt, max_tokens=200)
            sql = sql.strip().strip('`').strip()
            
            if sql.upper().startswith("SELECT"):
                result = self.data_engine.query(sql)
                return f"**Query:** `{sql}`\n\n**Results:**\n```\n{result.to_string()}\n```"
            else:
                return f"Could not generate valid SQL for: {query}"
                
        except Exception as e:
            return f"❌ Query failed: {str(e)}"
    
    def _handle_knowledge_query(self, query: Optional[str]) -> str:
        """Handle query about GST rules/accounting concepts."""
        
        if not query:
            return "Please ask a specific question about GST rules or accounting concepts."
        
        # Search knowledge base
        relevant_rules = self.knowledge_base.get_relevant_rules(query)
        
        # Generate response using LLM with context
        prompt = f"""Answer this question using the provided context.

Question: {query}

Relevant Rules and Context:
{relevant_rules}

Instructions:
1. Base your answer ONLY on the provided context
2. Cite specific sections when applicable
3. If the context doesn't contain the answer, say so
4. Be concise but complete

Answer:"""

        response = self.llm.generate(prompt)
        
        return f"**Question:** {query}\n\n{response}"
    
    def _handle_unknown(self, user_input: str) -> str:
        """Handle unknown intent - try general conversation."""
        
        response = self.llm.generate(user_input)
        return response
    
    def _get_help_text(self) -> str:
        """Return help text."""
        
        return """
## 🤖 LedgerMind - AI CFO Assistant

### Available Commands:

**📁 Folder Analysis**
- `analyze folder /path/to/excels/` - Load and analyze your Excel/CSV files
- `scan ~/Documents/finances/` - Same as above

**✅ Compliance Check**
- `run compliance check` - Check for GST compliance issues
- `audit` - Same as above

**📊 Strategic Analysis**  
- `analyze vendors` - Get vendor reliability rankings
- `forecast cash flow` - Get cash flow predictions

**❓ Questions**
- Ask about your data: "What's my total sales this month?"
- Ask about GST rules: "What is the ITC time limit?"

### Tips:
1. First, load your data with `analyze folder /path/`
2. Then run `compliance check` or `strategic analysis`
3. Ask questions about your data or GST rules anytime

Type your question or command below!
"""

