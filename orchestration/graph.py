"""
LangGraph-based Agent Orchestration

This module implements the multi-step analysis workflow using LangGraph
for better state management, conditional routing, and potential parallelization.

Graph Structure:
    START
      │
      ▼
    route_intent ─────────────────────────┐
      │                                    │
      ├─► data_query ──────────────────────┤
      ├─► knowledge_query ─────────────────┤
      ├─► compliance_check ────────────────┤
      ├─► strategic_analysis ──────────────┤
      │                                    │
      └─► multi_step_analysis              │
            │                              │
            ▼                              │
          data_overview                    │
            │                              │
            ▼                              │
          compliance_analysis              │
            │                              │
            ▼                              │
          strategic_insights               │
            │                              │
            ▼                              │
          generate_recommendations         │
            │                              │
            ▼                              │
          executive_summary                │
            │                              │
            ▼                              │
          format_response ◄────────────────┘
            │
            ▼
           END
"""

from typing import Dict, Any, Optional, List, TypedDict, Annotated, Literal
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import operator

from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver

from agents.discovery import DiscoveryAgent
from agents.compliance import ComplianceAgent
from agents.strategist import StrategistAgent
from agents.recommendation import RecommendationAgent, AnalysisContext
from orchestration.router import IntentRouter, IntentType, ParsedIntent
from core.data_engine import DataEngine
from core.knowledge import KnowledgeBase
from llm.client import LLMClient


# ============================================================================
# State Definition
# ============================================================================

class AnalysisState(TypedDict):
    """
    State that flows through the LangGraph workflow.
    
    Using TypedDict for LangGraph compatibility.
    The state is passed to each node and can be updated.
    """
    # Input
    user_input: str
    customer_id: Optional[str]
    
    # Routing
    intent: Optional[str]  # IntentType value
    intent_confidence: float
    extracted_query: Optional[str]
    
    # Analysis Results
    data_overview: Optional[Dict[str, Any]]
    compliance_result: Optional[Dict[str, Any]]
    strategic_result: Optional[Dict[str, Any]]
    recommendations: Optional[List[Dict[str, Any]]]
    executive_summary: Optional[str]
    
    # For simple queries
    simple_result: Optional[str]
    
    # Workflow tracking
    current_step: str
    steps_completed: List[str]
    errors: List[str]
    
    # Final output
    final_response: str
    
    # Metadata
    started_at: Optional[str]
    completed_at: Optional[str]


def create_initial_state(user_input: str, customer_id: Optional[str] = None) -> AnalysisState:
    """Create initial state for the graph."""
    return AnalysisState(
        user_input=user_input,
        customer_id=customer_id,
        intent=None,
        intent_confidence=0.0,
        extracted_query=None,
        data_overview=None,
        compliance_result=None,
        strategic_result=None,
        recommendations=None,
        executive_summary=None,
        simple_result=None,
        current_step="start",
        steps_completed=[],
        errors=[],
        final_response="",
        started_at=datetime.now().isoformat(),
        completed_at=None
    )


# ============================================================================
# Graph Builder
# ============================================================================

class AgentGraph:
    """
    LangGraph-based agent orchestration.
    
    This class builds and manages the workflow graph for processing
    user queries through various agents.
    """
    
    def __init__(
        self,
        data_engine: DataEngine,
        knowledge_base: KnowledgeBase,
        llm_client: LLMClient,
        enable_checkpointing: bool = False
    ):
        self.data_engine = data_engine
        self.knowledge_base = knowledge_base
        self.llm = llm_client
        
        # Initialize agents
        self.discovery_agent = DiscoveryAgent(data_engine, llm_client)
        self.compliance_agent = ComplianceAgent(data_engine, knowledge_base, llm_client)
        self.strategist_agent = StrategistAgent(data_engine, llm_client)
        self.recommendation_agent = RecommendationAgent(data_engine, llm_client)
        
        # Initialize router
        self.router = IntentRouter(llm_client)
        
        # Build the graph
        self.graph = self._build_graph()
        
        # Optional checkpointing for resumable workflows
        if enable_checkpointing:
            self.checkpointer = MemorySaver()
            self.app = self.graph.compile(checkpointer=self.checkpointer)
        else:
            self.app = self.graph.compile()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        
        # Create the graph with our state schema
        graph = StateGraph(AnalysisState)
        
        # ====================================================================
        # Add Nodes
        # ====================================================================
        
        # Intent routing node
        graph.add_node("route_intent", self._route_intent)
        
        # Simple query handlers
        graph.add_node("handle_data_query", self._handle_data_query)
        graph.add_node("handle_knowledge_query", self._handle_knowledge_query)
        graph.add_node("handle_compliance_check", self._handle_compliance_check)
        graph.add_node("handle_strategic_analysis", self._handle_strategic_analysis)
        graph.add_node("handle_help", self._handle_help)
        
        # Multi-step analysis nodes
        graph.add_node("analyze_data_overview", self._analyze_data_overview)
        graph.add_node("analyze_compliance", self._analyze_compliance)
        graph.add_node("analyze_strategic", self._analyze_strategic)
        graph.add_node("generate_recommendations", self._generate_recommendations)
        graph.add_node("create_executive_summary", self._create_executive_summary)
        
        # Final formatting
        graph.add_node("format_response", self._format_response)
        
        # ====================================================================
        # Add Edges
        # ====================================================================
        
        # Start -> Route intent
        graph.add_edge(START, "route_intent")
        
        # Conditional routing based on intent
        graph.add_conditional_edges(
            "route_intent",
            self._decide_route,
            {
                "data_query": "handle_data_query",
                "knowledge_query": "handle_knowledge_query",
                "compliance_check": "handle_compliance_check",
                "strategic_analysis": "handle_strategic_analysis",
                "multi_step_analysis": "analyze_data_overview",
                "help": "handle_help",
                "unknown": "format_response"
            }
        )
        
        # Simple handlers -> Format response
        graph.add_edge("handle_data_query", "format_response")
        graph.add_edge("handle_knowledge_query", "format_response")
        graph.add_edge("handle_compliance_check", "format_response")
        graph.add_edge("handle_strategic_analysis", "format_response")
        graph.add_edge("handle_help", "format_response")
        
        # Multi-step analysis chain
        graph.add_edge("analyze_data_overview", "analyze_compliance")
        graph.add_edge("analyze_compliance", "analyze_strategic")
        graph.add_edge("analyze_strategic", "generate_recommendations")
        graph.add_edge("generate_recommendations", "create_executive_summary")
        graph.add_edge("create_executive_summary", "format_response")
        
        # Format response -> End
        graph.add_edge("format_response", END)
        
        return graph
    
    # ========================================================================
    # Node Implementations
    # ========================================================================
    
    def _route_intent(self, state: AnalysisState) -> Dict[str, Any]:
        """Route the user input to the appropriate handler."""
        
        parsed = self.router.route(state["user_input"])
        
        return {
            "intent": parsed.intent_type.value,
            "intent_confidence": parsed.confidence,
            "extracted_query": parsed.extracted_query,
            "current_step": "route_intent",
            "steps_completed": state["steps_completed"] + ["route_intent"]
        }
    
    def _decide_route(self, state: AnalysisState) -> str:
        """Decide which path to take based on intent."""
        
        intent = state.get("intent", "unknown")
        
        # Map intent to route
        route_map = {
            "data_query": "data_query",
            "knowledge_query": "knowledge_query",
            "compliance_check": "compliance_check",
            "strategic_analysis": "strategic_analysis",
            "multi_step_analysis": "multi_step_analysis",
            "folder_analysis": "data_query",  # Treat as data query for now
            "help": "help"
        }
        
        return route_map.get(intent, "unknown")
    
    def _handle_data_query(self, state: AnalysisState) -> Dict[str, Any]:
        """Handle a data query."""
        
        query = state.get("extracted_query") or state["user_input"]
        
        try:
            # Get tables
            tables = self.data_engine.list_tables()
            
            if not tables:
                return {
                    "simple_result": "⚠️ No data loaded. Please upload files first.",
                    "current_step": "handle_data_query",
                    "steps_completed": state["steps_completed"] + ["handle_data_query"]
                }
            
            # Build schema
            schema_parts = []
            for table in tables[:5]:
                try:
                    cols = self.data_engine.query(f"DESCRIBE {table}")
                    col_list = cols['column_name'].tolist()
                    schema_parts.append(f"TABLE: {table}\n  Columns: {', '.join(col_list)}")
                except:
                    pass
            
            schema = "\n".join(schema_parts)
            
            # Generate SQL (returns tuple: sql_string, is_valid)
            sql_result = self.llm.generate_sql(query, schema)
            
            # Handle both old (string) and new (tuple) return formats
            if isinstance(sql_result, tuple):
                sql, is_valid = sql_result
                if not is_valid:
                    response = "❌ Could not generate a safe query. Please rephrase your question."
                    return {
                        "simple_result": response,
                        "current_step": "handle_data_query",
                        "steps_completed": state["steps_completed"] + ["handle_data_query"]
                    }
            else:
                sql = sql_result  # Legacy compatibility
            
            if sql and sql.upper().startswith("SELECT"):
                result = self.data_engine.query(sql)
                response = f"**Query:** `{sql}`\n\n**Results ({len(result)} rows):**\n```\n{result.to_string(index=False)}\n```"
            else:
                response = "I couldn't generate a valid query for that. Try being more specific."
            
        except Exception as e:
            response = f"❌ Query failed: {str(e)}"
        
        return {
            "simple_result": response,
            "current_step": "handle_data_query",
            "steps_completed": state["steps_completed"] + ["handle_data_query"]
        }
    
    def _handle_knowledge_query(self, state: AnalysisState) -> Dict[str, Any]:
        """Handle a knowledge query about GST rules."""
        
        query = state.get("extracted_query") or state["user_input"]
        
        try:
            # Get relevant rules from ChromaDB
            rules = self.knowledge_base.get_relevant_rules(query)
            
            prompt = f"""Answer this question about GST/tax:

Question: {query}

Context:
{rules}

Provide a clear, accurate answer."""

            response = self.llm.generate(prompt)
            result = f"**Question:** {query}\n\n{response}"
            
        except Exception as e:
            result = f"❌ Error: {str(e)}"
        
        return {
            "simple_result": result,
            "current_step": "handle_knowledge_query",
            "steps_completed": state["steps_completed"] + ["handle_knowledge_query"]
        }
    
    def _handle_compliance_check(self, state: AnalysisState) -> Dict[str, Any]:
        """Handle a compliance check request."""
        
        try:
            report = self.compliance_agent.run_full_audit()
            
            response = report.summary
            if report.issues:
                response += "\n\n### Issues Found:\n"
                for issue in report.issues[:10]:
                    emoji = "🔴" if issue.severity == "critical" else "🟡"
                    response += f"\n{emoji} **{issue.issue_type}**: {issue.description}\n"
            
        except Exception as e:
            response = f"❌ Compliance check failed: {str(e)}"
        
        return {
            "simple_result": response,
            "current_step": "handle_compliance_check",
            "steps_completed": state["steps_completed"] + ["handle_compliance_check"]
        }
    
    def _handle_strategic_analysis(self, state: AnalysisState) -> Dict[str, Any]:
        """Handle a strategic analysis request."""
        
        try:
            report = self.strategist_agent.run_full_analysis()
            
            response = "## 📊 Strategic Analysis\n\n"
            
            if report.vendor_rankings:
                response += "### Top Vendors\n"
                for i, v in enumerate(report.vendor_rankings[:5], 1):
                    response += f"{i}. {v.vendor_name} - Score: {v.reliability_score:.0f}\n"
            
            if report.recommendations:
                response += "\n### Recommendations\n"
                for rec in report.recommendations:
                    response += f"- {rec}\n"
            
        except Exception as e:
            response = f"❌ Strategic analysis failed: {str(e)}"
        
        return {
            "simple_result": response,
            "current_step": "handle_strategic_analysis",
            "steps_completed": state["steps_completed"] + ["handle_strategic_analysis"]
        }
    
    def _handle_help(self, state: AnalysisState) -> Dict[str, Any]:
        """Handle help request."""
        
        response = """## 🤖 LedgerMind Help

### Commands:
- **full analysis** - Run comprehensive multi-step analysis
- **check compliance** - Run compliance audit
- **analyze vendors** - Get vendor rankings
- Ask questions about your data or GST rules

### Examples:
- "What is my total sales?"
- "What is CGST?"
- "Generate full report"
"""
        
        return {
            "simple_result": response,
            "current_step": "handle_help",
            "steps_completed": state["steps_completed"] + ["handle_help"]
        }
    
    # ========================================================================
    # Multi-Step Analysis Nodes
    # ========================================================================
    
    def _analyze_data_overview(self, state: AnalysisState) -> Dict[str, Any]:
        """Step 1: Analyze data structure."""
        
        tables = self.data_engine.list_tables()
        
        overview = {
            "total_tables": len(tables),
            "tables": {},
            "total_records": 0
        }
        
        for table in tables:
            try:
                count = int(self.data_engine.query(f"SELECT COUNT(*) as cnt FROM {table}").iloc[0]['cnt'])
                cols = self.data_engine.query(f"DESCRIBE {table}")
                
                overview["tables"][table] = {
                    "row_count": count,
                    "columns": cols['column_name'].tolist(),
                    "column_count": len(cols)
                }
                overview["total_records"] += count
            except:
                overview["tables"][table] = {"error": "Could not analyze"}
        
        return {
            "data_overview": overview,
            "current_step": "analyze_data_overview",
            "steps_completed": state["steps_completed"] + ["analyze_data_overview"]
        }
    
    def _analyze_compliance(self, state: AnalysisState) -> Dict[str, Any]:
        """Step 2: Run compliance checks."""
        
        try:
            report = self.compliance_agent.run_full_audit()
            
            result = {
                "summary": report.summary,
                "issues": [
                    {
                        "type": i.issue_type,
                        "severity": i.severity,
                        "description": i.description,
                        "amount_impact": i.amount_impact
                    }
                    for i in (report.issues or [])
                ],
                "critical_count": sum(1 for i in (report.issues or []) if i.severity == "critical"),
                "warning_count": sum(1 for i in (report.issues or []) if i.severity == "warning")
            }
        except Exception as e:
            result = {"error": str(e), "issues": []}
        
        return {
            "compliance_result": result,
            "current_step": "analyze_compliance",
            "steps_completed": state["steps_completed"] + ["analyze_compliance"]
        }
    
    def _analyze_strategic(self, state: AnalysisState) -> Dict[str, Any]:
        """Step 3: Run strategic analysis."""
        
        try:
            report = self.strategist_agent.run_full_analysis()
            
            result = {
                "vendor_rankings": [
                    {
                        "name": v.vendor_name,
                        "score": v.reliability_score,
                        "transactions": v.total_transactions,
                        "value": v.total_value
                    }
                    for v in (report.vendor_rankings or [])[:5]
                ],
                "cash_flow_forecasts": [
                    {
                        "period": f.period,
                        "net_cash_flow": f.net_cash_flow,
                        "confidence": f.confidence
                    }
                    for f in (report.cash_flow_forecasts or [])
                ],
                "recommendations": report.recommendations or []
            }
        except Exception as e:
            result = {"error": str(e)}
        
        return {
            "strategic_result": result,
            "current_step": "analyze_strategic",
            "steps_completed": state["steps_completed"] + ["analyze_strategic"]
        }
    
    def _generate_recommendations(self, state: AnalysisState) -> Dict[str, Any]:
        """Step 4: Generate recommendations using RecommendationAgent."""
        
        # Build context from previous steps
        context = AnalysisContext(
            data_summary=state.get("data_overview"),
            compliance_issues=state.get("compliance_result", {}).get("issues"),
            strategic_insights=state.get("strategic_result")
        )
        
        try:
            report = self.recommendation_agent.generate_recommendations(context, max_recommendations=7)
            
            recommendations = [
                {
                    "id": rec.id,
                    "title": rec.title,
                    "description": rec.description,
                    "priority": rec.priority.value,
                    "category": rec.category.value,
                    "impact_score": rec.impact_score,
                    "action_items": rec.action_items
                }
                for rec in report.recommendations
            ]
        except Exception as e:
            recommendations = [{"error": str(e)}]
        
        return {
            "recommendations": recommendations,
            "current_step": "generate_recommendations",
            "steps_completed": state["steps_completed"] + ["generate_recommendations"]
        }
    
    def _create_executive_summary(self, state: AnalysisState) -> Dict[str, Any]:
        """Step 5: Create executive summary."""
        
        # Build context for LLM
        data = state.get("data_overview", {})
        compliance = state.get("compliance_result", {})
        recs = state.get("recommendations", [])
        
        context = f"""Create an executive summary:

DATA: {data.get('total_tables', 0)} tables, {data.get('total_records', 0)} records
COMPLIANCE: {compliance.get('critical_count', 0)} critical, {compliance.get('warning_count', 0)} warnings
RECOMMENDATIONS: {len(recs)} action items

Write 2-3 paragraphs summarizing business health and priorities."""
        
        try:
            summary = self.llm.generate(context, max_tokens=300)
        except:
            summary = "Executive summary could not be generated."
        
        return {
            "executive_summary": summary,
            "current_step": "create_executive_summary",
            "steps_completed": state["steps_completed"] + ["create_executive_summary"]
        }
    
    def _format_response(self, state: AnalysisState) -> Dict[str, Any]:
        """Format the final response."""
        
        # Check if this was a simple query
        if state.get("simple_result"):
            return {
                "final_response": state["simple_result"],
                "completed_at": datetime.now().isoformat()
            }
        
        # Format multi-step analysis response
        parts = ["## 🔄 Multi-Step Analysis Report\n"]
        
        # Data Overview
        data = state.get("data_overview", {})
        if data:
            parts.append("### Step 1: Data Overview 📊")
            parts.append(f"**Tables:** {data.get('total_tables', 0)}")
            parts.append(f"**Total Records:** {data.get('total_records', 0):,}\n")
        
        # Compliance
        compliance = state.get("compliance_result", {})
        if compliance:
            parts.append("### Step 2: Compliance Check ✅")
            critical = compliance.get('critical_count', 0)
            warnings = compliance.get('warning_count', 0)
            parts.append(f"**Critical Issues:** {critical} {'🔴' if critical else '✅'}")
            parts.append(f"**Warnings:** {warnings} {'🟡' if warnings else '✅'}\n")
        
        # Strategic
        strategic = state.get("strategic_result", {})
        if strategic:
            parts.append("### Step 3: Strategic Analysis 📈")
            vendors = strategic.get('vendor_rankings', [])
            if vendors:
                parts.append("**Top Vendors:**")
                for v in vendors[:3]:
                    parts.append(f"  - {v.get('name')}: Score {v.get('score', 0):.0f}")
            parts.append("")
        
        # Recommendations
        recs = state.get("recommendations", [])
        if recs:
            parts.append("### Step 4: Recommendations 💡")
            for i, rec in enumerate(recs, 1):
                if isinstance(rec, dict) and "title" in rec:
                    priority = rec.get('priority', 'medium').upper()
                    icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(priority, "")
                    parts.append(f"\n**{i}.** {icon} [{rec.get('category', '').upper()}] {rec.get('title')}")
                    for action in rec.get('action_items', [])[:2]:
                        parts.append(f"   → {action}")
            parts.append("")
        
        # Executive Summary
        summary = state.get("executive_summary")
        if summary:
            parts.append("### Step 5: Executive Summary 📋")
            parts.append(summary)
            parts.append("")
        
        parts.append("---")
        parts.append(f"✅ **Analysis Complete!** {len(state.get('steps_completed', []))} steps finished.")
        
        return {
            "final_response": "\n".join(parts),
            "completed_at": datetime.now().isoformat()
        }
    
    # ========================================================================
    # Public API
    # ========================================================================
    
    def run(self, user_input: str, customer_id: Optional[str] = None) -> str:
        """
        Run the workflow for a user input.
        
        Args:
            user_input: The user's query
            customer_id: Optional customer ID for context
            
        Returns:
            The final response string
        """
        
        initial_state = create_initial_state(user_input, customer_id)
        
        # Run the graph
        final_state = self.app.invoke(initial_state)
        
        return final_state.get("final_response", "No response generated")
    
    async def arun(self, user_input: str, customer_id: Optional[str] = None) -> str:
        """Async version of run."""
        
        initial_state = create_initial_state(user_input, customer_id)
        final_state = await self.app.ainvoke(initial_state)
        return final_state.get("final_response", "No response generated")
    
    def stream(self, user_input: str, customer_id: Optional[str] = None):
        """
        Stream the workflow execution, yielding updates as each step completes.
        
        Args:
            user_input: The user's query
            customer_id: Optional customer ID
            
        Yields:
            Dict with step name and partial state
        """
        
        initial_state = create_initial_state(user_input, customer_id)
        
        for event in self.app.stream(initial_state):
            # event is a dict with node name as key
            for node_name, state_update in event.items():
                yield {
                    "step": node_name,
                    "state": state_update
                }
    
    def get_graph_diagram(self) -> str:
        """Get ASCII representation of the graph."""
        
        return """
LangGraph Workflow:

    ┌─────────────────┐
    │      START      │
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │  route_intent   │
    └────────┬────────┘
             │
    ┌────────┴────────┬──────────────┬──────────────┐
    │                 │              │              │
    ▼                 ▼              ▼              ▼
┌────────┐    ┌────────────┐  ┌────────────┐  ┌────────────────┐
│  data  │    │ knowledge  │  │ compliance │  │  multi_step    │
│ query  │    │   query    │  │   check    │  │   analysis     │
└────┬───┘    └─────┬──────┘  └─────┬──────┘  └───────┬────────┘
     │              │               │                  │
     │              │               │         ┌───────┴───────┐
     │              │               │         ▼               │
     │              │               │    data_overview        │
     │              │               │         │               │
     │              │               │         ▼               │
     │              │               │    compliance           │
     │              │               │         │               │
     │              │               │         ▼               │
     │              │               │    strategic            │
     │              │               │         │               │
     │              │               │         ▼               │
     │              │               │    recommendations      │
     │              │               │         │               │
     │              │               │         ▼               │
     │              │               │    executive_summary    │
     │              │               │         │               │
     └──────────────┴───────────────┴─────────┴───────────────┘
                                    │
                                    ▼
                           ┌─────────────────┐
                           │ format_response │
                           └────────┬────────┘
                                    │
                                    ▼
                           ┌─────────────────┐
                           │       END       │
                           └─────────────────┘
"""
