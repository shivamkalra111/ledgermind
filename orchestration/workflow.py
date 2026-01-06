"""
Agent Workflow - Orchestrates the multi-agent system
Uses LangGraph for agent coordination

CUSTOMER ISOLATION:
Each workflow instance is bound to a specific customer.
All data operations are scoped to that customer's DuckDB.
"""

from typing import Dict, Any, Optional, TypedDict, Annotated, TYPE_CHECKING
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

if TYPE_CHECKING:
    from core.customer import CustomerContext


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
    
    CUSTOMER ISOLATION:
    - Each workflow instance is bound to a specific customer
    - data_engine connects to customer's DuckDB (not shared)
    - knowledge_base is shared (read-only reference data)
    
    Flow:
    1. User input → Intent Router
    2. Based on intent, route to appropriate agent(s)
    3. Aggregate results → Generate response
    """
    
    def __init__(self, customer: Optional["CustomerContext"] = None, auto_load: bool = True):
        """
        Initialize workflow with customer context.
        
        Args:
            customer: CustomerContext for data isolation.
                     If None, uses global DuckDB (legacy mode).
            auto_load: If True, automatically detect and load changed files.
        """
        self.customer = customer
        
        # Initialize shared resources (read-only, shared across customers)
        self.knowledge_base = KnowledgeBase()
        self.llm = LLMClient()
        
        # Initialize customer-specific data engine
        if customer:
            self.data_engine = customer.get_data_engine()
            self._data_dir = customer.data_dir
            self._data_state = customer.get_data_state_manager()
        else:
            # Legacy mode - global database
            self.data_engine = DataEngine()
            self._data_dir = None
            self._data_state = None
        
        # Initialize agents with customer-scoped data engine
        self.discovery_agent = DiscoveryAgent(self.data_engine, self.llm)
        self.compliance_agent = ComplianceAgent(self.data_engine, self.knowledge_base, self.llm)
        self.strategist_agent = StrategistAgent(self.data_engine, self.llm)
        
        # Initialize router
        self.router = IntentRouter(self.llm)
        
        # Track state
        self._data_loaded = False
        
        # Auto-load changed files on startup
        if auto_load and self._data_state:
            self._smart_load_data()
    
    @property
    def customer_id(self) -> Optional[str]:
        """Get current customer ID."""
        return self.customer.customer_id if self.customer else None
    
    def _smart_load_data(self) -> Optional[str]:
        """
        Smart data loading - only load new or changed files.
        
        Returns:
            Summary message if changes were made, None otherwise.
        """
        if not self._data_state:
            return None
        
        # Get existing tables to verify state matches DuckDB reality
        existing_tables = self.data_engine.list_tables()
        summary = self._data_state.get_summary(existing_tables=existing_tables)
        
        # Nothing to do
        if not summary["needs_reload"] and summary["loaded_files"] > 0:
            self._data_loaded = True
            return None
        
        # Get files that need loading (with verification)
        files_to_load = self._data_state.get_files_to_load(existing_tables=existing_tables)
        tables_to_delete = self._data_state.get_tables_to_delete()
        
        messages = []
        
        # Delete tables for removed files
        for table_name in tables_to_delete:
            try:
                self.data_engine.execute(f"DROP TABLE IF EXISTS {table_name}")
                messages.append(f"🗑️ Removed table: {table_name}")
            except Exception:
                pass
        
        # Load new/modified files
        for filename, file_path, change_type in files_to_load:
            try:
                # Load based on file type
                if file_path.suffix.lower() in [".xlsx", ".xls"]:
                    table_name = self.data_engine.load_excel(file_path)
                else:
                    table_name = self.data_engine.load_csv(file_path)
                
                # Get row count (convert to int for JSON serialization)
                try:
                    row_count = int(self.data_engine.query(f"SELECT COUNT(*) as cnt FROM {table_name}").iloc[0]["cnt"])
                except:
                    row_count = None
                
                # Mark as loaded
                self._data_state.mark_file_loaded(
                    filename=filename,
                    table_name=table_name,
                    row_count=row_count
                )
                
                icon = "🆕" if change_type.value == "new" else "🔄"
                messages.append(f"{icon} Loaded: {filename} → {table_name}")
                
            except Exception as e:
                messages.append(f"❌ Failed to load {filename}: {e}")
        
        # Clean up deleted files from state
        for change in self._data_state.detect_changes():
            if change.change_type.value == "deleted":
                self._data_state.mark_file_deleted(change.filename)
        
        # Save state
        self._data_state.save()
        
        if files_to_load or tables_to_delete:
            self._data_loaded = True
            return "\n".join(messages)
        
        return None
    
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
        """Handle folder analysis request with smart change detection."""
        
        # If no path provided and customer has data dir, use that
        if not folder_path:
            if self._data_dir and self._data_dir.exists():
                folder_path = str(self._data_dir)
            else:
                return "Please provide a folder path to analyze. Example: `analyze data` or `analyze folder /path/to/excels/`"
        
        # Handle "data" as shorthand for customer's data directory
        if folder_path.lower() == "data" and self._data_dir:
            folder_path = str(self._data_dir)
        
        path = Path(folder_path).expanduser()
        
        if not path.exists():
            return f"❌ Folder not found: {path}"
        
        # Check if this is the customer's data directory (use smart loading)
        if self._data_state and path == self._data_dir:
            return self._smart_folder_analysis()
        
        # Legacy: Run full discovery for arbitrary folders
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
    
    def _smart_folder_analysis(self) -> str:
        """
        Smart folder analysis with change detection.
        Only loads new/modified files.
        """
        if not self._data_state:
            return "❌ Data state manager not available."
        
        summary = self._data_state.get_summary()
        
        # Get changes
        from core.data_state import FileChangeType
        changes = self._data_state.detect_changes()
        
        # Build response header
        response = f"""
## 📁 Smart Data Analysis

**Data Folder:** {self._data_dir}
**Total Files:** {summary['total_files']}
**Previously Loaded:** {summary['loaded_files']}
"""
        
        # Show change summary
        new_count = summary['new_files']
        mod_count = summary['modified_files']
        del_count = summary['deleted_files']
        
        if new_count == 0 and mod_count == 0 and del_count == 0:
            # No changes
            response += "\n### ✅ No Changes Detected\n"
            response += "All files are up to date.\n"
            
            # Show loaded tables
            loaded = self._data_state.get_loaded_tables()
            if loaded:
                response += "\n**Loaded Tables:**\n"
                for filename, table_name in loaded.items():
                    state = self._data_state.state.files.get(filename)
                    rows = f" ({state.row_count} rows)" if state and state.row_count else ""
                    response += f"  - `{table_name}`{rows} ← {filename}\n"
            
            self._data_loaded = True
            return response
        
        # Process changes
        response += f"\n### 🔍 Changes Detected\n"
        response += f"  - 🆕 New files: {new_count}\n"
        response += f"  - 🔄 Modified files: {mod_count}\n"
        response += f"  - 🗑️ Deleted files: {del_count}\n"
        
        # Load changes
        load_result = self._smart_load_data()
        
        if load_result:
            response += f"\n### 📥 Loading Results\n"
            for line in load_result.split("\n"):
                response += f"  {line}\n"
        
        # Show all loaded tables
        loaded = self._data_state.get_loaded_tables()
        if loaded:
            response += "\n### 📊 Available Tables\n"
            for filename, table_name in loaded.items():
                state = self._data_state.state.files.get(filename)
                rows = f" ({state.row_count} rows)" if state and state.row_count else ""
                response += f"  - `{table_name}`{rows}\n"
        
        response += "\n✅ Data ready! Ask questions or run compliance check."
        
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
        
        tables = self.data_engine.list_tables()
        
        if not query:
            return self._show_available_data()
        
        # Handle special commands that should show data summary
        query_lower = query.lower().strip()
        if query_lower in ["data", "tables", "available", "available data", "what data"]:
            return self._show_available_data()
        
        # Get table schemas for better SQL generation
        schema_info = self._get_table_schemas(tables)
        
        prompt = f"""You are a SQL expert. Convert this natural language question to a DuckDB SQL query.

DATABASE SCHEMA:
{schema_info}

USER QUESTION: {query}

RULES:
1. Use ONLY the tables and columns listed above - look at the actual column names
2. Return ONLY the raw SQL query - no explanations, no markdown, no backticks
3. Column names with spaces MUST be quoted with double quotes
4. Look at the sample data to understand date formats and use appropriate filtering
5. For date columns that are VARCHAR, use LIKE patterns based on the format you see in sample data
6. For date columns that are DATE type, use strftime() for filtering
7. Query ONE table at a time - don't try to UNION different table structures
8. For aggregations (SUM, COUNT, AVG), always give alias names
9. Limit results to reasonable amounts (LIMIT 20) unless user asks for all
10. Use the exact column names as shown in the schema

SQL:"""

        try:
            sql = self.llm.generate(prompt, max_tokens=300)
            sql = self._clean_sql_response(sql)
            
            # Validate and execute
            if sql.upper().startswith("SELECT"):
                try:
                    result = self.data_engine.query(sql)
                    
                    if len(result) == 0:
                        return f"**Query:** `{sql}`\n\n**Results:** No data found matching your criteria."
                    
                    return f"**Query:** `{sql}`\n\n**Results ({len(result)} rows):**\n```\n{result.to_string(index=False)}\n```"
                except Exception as db_error:
                    # Try to fix common SQL issues and retry
                    fixed_result = self._try_fix_and_execute(sql, query, tables, str(db_error))
                    if fixed_result:
                        return fixed_result
                    # Show helpful error with available data
                    return f"❌ Couldn't run that query. Error: {str(db_error)[:100]}\n\n" + self._show_available_data()
            else:
                return self._show_available_data()
                
        except Exception as e:
            return f"❌ Query failed: {str(e)}"
    
    def _clean_sql_response(self, sql: str) -> str:
        """Clean up LLM SQL response."""
        sql = sql.strip()
        
        # Remove markdown code blocks
        if sql.startswith("```"):
            lines = sql.split("\n")
            sql = "\n".join(line for line in lines if not line.startswith("```"))
            sql = sql.strip()
        
        # Remove language hints
        if sql.lower().startswith("sql"):
            sql = sql[3:].strip()
        
        # Remove backticks
        sql = sql.strip('`').strip()
        
        # Take only first statement
        if ";" in sql:
            sql = sql.split(";")[0].strip()
        
        return sql
    
    def _get_table_schemas(self, tables: list) -> str:
        """Get schema information for all tables."""
        schema_parts = []
        
        for table in tables:
            try:
                # Get column info
                columns_df = self.data_engine.query(f"DESCRIBE {table}")
                columns = columns_df['column_name'].tolist()
                types = columns_df['column_type'].tolist()
                
                # Get sample rows
                sample = self.data_engine.query(f"SELECT * FROM {table} LIMIT 3")
                
                schema_parts.append(f"TABLE: {table}")
                schema_parts.append(f"  Columns: {', '.join(f'\"{c}\" ({t})' for c, t in zip(columns, types))}")
                
                # Show sample data for context
                if len(sample) > 0:
                    schema_parts.append(f"  Sample data:")
                    for idx, row in sample.head(2).iterrows():
                        row_str = ", ".join(f'{k}={repr(v)[:30]}' for k, v in row.items())
                        schema_parts.append(f"    {row_str}")
                
                # Get row count
                count = self.data_engine.query(f"SELECT COUNT(*) as cnt FROM {table}").iloc[0]['cnt']
                schema_parts.append(f"  Total rows: {count}")
                schema_parts.append("")
            except Exception:
                schema_parts.append(f"TABLE: {table} (schema unavailable)")
                schema_parts.append("")
        
        return "\n".join(schema_parts)
    
    def _try_fix_and_execute(self, original_sql: str, query: str, tables: list, error: str) -> Optional[str]:
        """Try to fix common SQL issues and re-execute."""
        
        # Ask LLM to fix the SQL based on the error
        fix_prompt = f"""The following SQL query failed with an error. Fix it.

ORIGINAL SQL: {original_sql}

ERROR: {error}

RULES:
1. Return ONLY the fixed SQL - no explanations
2. If the error is about column names, check for typos or missing quotes
3. If the error is about date functions, try using LIKE patterns instead
4. If the error is about missing tables, use an available table

FIXED SQL:"""
        
        try:
            fixed_sql = self.llm.generate(fix_prompt, max_tokens=300)
            fixed_sql = self._clean_sql_response(fixed_sql)
            
            if fixed_sql.upper().startswith("SELECT") and fixed_sql != original_sql:
                result = self.data_engine.query(fixed_sql)
                if len(result) > 0:
                    return f"**Query:** `{fixed_sql}`\n\n**Results ({len(result)} rows):**\n```\n{result.to_string(index=False)}\n```"
        except:
            pass
        
        return None
    
    def _show_available_data(self) -> str:
        """Show what data is available to query."""
        tables = self.data_engine.list_tables()
        
        summary = "## 📊 Available Data\n\n"
        
        for table in tables:
            try:
                count = self.data_engine.query(f"SELECT COUNT(*) as cnt FROM {table}").iloc[0]['cnt']
                columns_df = self.data_engine.query(f"DESCRIBE {table}")
                columns = columns_df['column_name'].tolist()
                
                summary += f"### {table}\n"
                summary += f"- **Rows:** {count}\n"
                summary += f"- **Columns:** {', '.join(columns)}\n\n"
            except:
                summary += f"### {table}\n\n"
        
        summary += "---\n\n"
        summary += "💡 **Example questions you can ask:**\n"
        summary += "- Show me all data from [table name]\n"
        summary += "- What is the total of [column name]?\n"
        summary += "- List records where [column] contains [value]\n"
        summary += "- Show the latest [number] records\n"
        
        return summary
    
    def _handle_knowledge_query(self, query: Optional[str]) -> str:
        """
        Handle query about GST rules/accounting concepts.
        
        Routes to appropriate knowledge source:
        - Definitions/Concepts → LLM general knowledge
        - Rate lookups → CSV data
        - Legal rules → ChromaDB RAG
        """
        
        if not query:
            return "Please ask a specific question about GST rules or accounting concepts."
        
        # Import query classifier
        from core.query_classifier import (
            QueryClassifier, QueryType, 
            lookup_gst_rate, format_rate_response
        )
        
        classifier = QueryClassifier()
        classified = classifier.classify(query)
        
        # Route based on classification
        if classified.query_type == QueryType.RATE_LOOKUP:
            # Layer 1: CSV lookup for rates
            item = classified.extracted_entities.get("item", query)
            rate_info = lookup_gst_rate(item)
            
            if rate_info:
                csv_context = format_rate_response(rate_info, item)
                prompt = f"""The user asked: "{query}"

Here is the rate information from our database:
{csv_context}

Provide a helpful response using this data. You can add context about how GST works 
(CGST/SGST for intra-state, IGST for inter-state) but use the exact rates from above."""
                
                response = self.llm.generate(prompt)
                return f"**Question:** {query}\n\n{response}"
            else:
                # Rate not found in CSV - use LLM knowledge + ChromaDB
                relevant_rules = self.knowledge_base.get_relevant_rules(query)
                prompt = f"""You are a GST expert. Answer this question about GST rates:

Question: {query}

Context from CGST Rules (if relevant):
{relevant_rules}

If you know the rate, provide it. Include:
- The applicable GST rate
- Whether it's 0%, 5%, 12%, 18%, or 28%
- Any cess if applicable (like on cigarettes, tobacco, luxury items)
- Mention CGST/SGST for intra-state or IGST for inter-state"""

                response = self.llm.generate(prompt)
                return f"**Question:** {query}\n\n{response}"
        
        elif classified.query_type == QueryType.DEFINITION:
            # Layer 3: LLM general knowledge for definitions
            # Don't restrict to context - LLM knows GST basics
            prompt = f"""You are a GST expert. Answer this question clearly and accurately:

Question: {query}

Provide a comprehensive but concise answer. Include:
- Clear definition
- How it works (if applicable)
- A simple example (if helpful)

Use your knowledge of Indian GST system. Be accurate and professional."""
            
            response = self.llm.generate(prompt)
            if response:
                return f"**Question:** {query}\n\n{response}"
            else:
                return f"**Question:** {query}\n\nI couldn't generate a response. Please try again."
        
        elif classified.query_type in [QueryType.LEGAL_RULE, QueryType.COMPLIANCE]:
            # Layer 2: ChromaDB RAG for legal/procedural questions
            relevant_rules = self.knowledge_base.get_relevant_rules(query)
            
            prompt = f"""Answer this question using the provided legal context.

Question: {query}

Relevant Rules and Context from CGST Act/Rules:
{relevant_rules}

Instructions:
1. Base your answer on the provided context
2. Cite specific sections when applicable
3. If context is insufficient, say what you know and suggest checking official sources
4. Be accurate - this is legal/tax advice

Answer:"""
            
            response = self.llm.generate(prompt)
            if response:
                return f"**Question:** {query}\n\n{response}"
            else:
                return f"**Question:** {query}\n\nI couldn't find relevant information. Please check official CBIC sources."
        
        else:
            # General or uncertain - try ChromaDB first, then LLM
            relevant_rules = self.knowledge_base.get_relevant_rules(query)
            
            # Check if we got useful context
            if relevant_rules and "No relevant rules found" not in relevant_rules:
                prompt = f"""Answer this question using the provided context.

Question: {query}

Context:
{relevant_rules}

If the context is helpful, use it. If not, use your general knowledge of GST.
Be accurate and helpful."""
            else:
                prompt = f"""You are a GST expert. Answer this question:

Question: {query}

Provide an accurate, helpful answer based on your knowledge of Indian GST system."""
            
            response = self.llm.generate(prompt)
            if response:
                return f"**Question:** {query}\n\n{response}"
            else:
                return f"**Question:** {query}\n\nI apologize, I couldn't generate a response. Please try rephrasing your question."
    
    def _handle_unknown(self, user_input: str) -> str:
        """Handle unknown intent - try general conversation."""
        
        try:
            response = self.llm.generate(user_input)
            if response:
                return response
            return "I couldn't understand that. Try asking about GST, tax rates, or run a compliance check."
        except Exception as e:
            return f"❌ Error generating response: {str(e)}"
    
    def _get_help_text(self) -> str:
        """Return help text."""
        
        # Customer-aware help
        if self.customer:
            data_path = self.customer.data_dir
            company_name = self.customer.profile.company_name
            customer_info = f"""
### 🏢 Current Company: {company_name}
Data folder: `{data_path}`
"""
        else:
            customer_info = ""
        
        return f"""
## 🤖 LedgerMind - AI CFO Assistant
{customer_info}
### Available Commands:

**📁 Folder Analysis**
- `analyze data` - Analyze your company's data folder
- `analyze folder /path/to/excels/` - Analyze a specific folder

**✅ Compliance Check**
- `run compliance check` - Check for GST compliance issues
- `audit` - Same as above

**📊 Strategic Analysis**  
- `analyze vendors` - Get vendor reliability rankings
- `forecast cash flow` - Get cash flow predictions

**🔄 Company Management**
- `switch company` - Change to a different company
- `company` - Show current company info

**❓ Questions**
- Ask about your data: "What's my total sales this month?"
- Ask about GST rules: "What is the ITC time limit?"

### Tips:
1. Place your Excel/CSV files in your company's data folder
2. Run `analyze data` to load them
3. Then run `compliance check` or ask questions

Type your question or command below!
"""

