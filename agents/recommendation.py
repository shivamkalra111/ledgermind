"""
Recommendation Agent - Generates actionable recommendations from analysis context
Synthesizes findings from other agents into prioritized action items
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from core.data_engine import DataEngine
from llm.client import LLMClient


class RecommendationPriority(Enum):
    """Priority levels for recommendations."""
    CRITICAL = "critical"      # Must do immediately
    HIGH = "high"              # Should do soon
    MEDIUM = "medium"          # Plan to do
    LOW = "low"                # Nice to have


class RecommendationCategory(Enum):
    """Categories for recommendations."""
    COMPLIANCE = "compliance"           # Tax/legal compliance
    DATA_QUALITY = "data_quality"       # Data issues to fix
    CASH_FLOW = "cash_flow"             # Cash management
    VENDOR = "vendor"                   # Vendor relationships
    TAX_SAVINGS = "tax_savings"         # Tax optimization
    OPERATIONAL = "operational"         # Process improvements
    RISK = "risk"                       # Risk mitigation


@dataclass
class Recommendation:
    """A single actionable recommendation."""
    id: str
    title: str
    description: str
    category: RecommendationCategory
    priority: RecommendationPriority
    impact_score: float  # 0-100, estimated impact
    effort_score: float  # 0-100, estimated effort (lower = easier)
    action_items: List[str] = field(default_factory=list)
    related_issues: List[str] = field(default_factory=list)
    deadline: Optional[str] = None
    estimated_savings: Optional[float] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class AnalysisContext:
    """Context from previous analysis steps."""
    data_summary: Optional[Dict[str, Any]] = None
    compliance_issues: Optional[List[Dict]] = None
    strategic_insights: Optional[Dict[str, Any]] = None
    custom_context: Optional[str] = None


@dataclass
class RecommendationReport:
    """Complete recommendation report."""
    recommendations: List[Recommendation]
    summary: str
    total_potential_savings: float
    critical_count: int
    high_count: int
    generated_at: datetime = field(default_factory=datetime.now)


class RecommendationAgent:
    """
    Agent 4: Recommendation (Advisor)
    
    Responsibilities:
    - Synthesize findings from other agents
    - Generate prioritized, actionable recommendations
    - Categorize by type (compliance, cash flow, vendor, etc.)
    - Score by impact and effort
    - Provide specific action items
    """
    
    def __init__(
        self,
        data_engine: Optional[DataEngine] = None,
        llm_client: Optional[LLMClient] = None
    ):
        self.data_engine = data_engine or DataEngine()
        self.llm = llm_client
        
        # Templates for different recommendation types
        self._recommendation_templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, Dict]:
        """Load recommendation templates for common scenarios."""
        return {
            "high_null_values": {
                "category": RecommendationCategory.DATA_QUALITY,
                "priority": RecommendationPriority.MEDIUM,
                "title": "Address missing data in {table}",
                "description": "Table '{table}' has {count} records with missing values in critical columns.",
                "action_items": [
                    "Review source data for completeness",
                    "Implement data validation at entry point",
                    "Consider setting default values where appropriate"
                ]
            },
            "critical_compliance": {
                "category": RecommendationCategory.COMPLIANCE,
                "priority": RecommendationPriority.CRITICAL,
                "title": "Address critical compliance issue: {issue_type}",
                "description": "{description}",
                "action_items": [
                    "Review the flagged transactions immediately",
                    "Consult with tax advisor if needed",
                    "File corrections before due date"
                ]
            },
            "negative_cash_flow": {
                "category": RecommendationCategory.CASH_FLOW,
                "priority": RecommendationPriority.HIGH,
                "title": "Prepare for projected cash flow deficit",
                "description": "Negative cash flow projected for {periods}. Total deficit: ₹{amount:,.0f}",
                "action_items": [
                    "Accelerate accounts receivable collection",
                    "Negotiate extended payment terms with suppliers",
                    "Review and defer non-essential expenses",
                    "Consider short-term financing options"
                ]
            },
            "vendor_risk": {
                "category": RecommendationCategory.VENDOR,
                "priority": RecommendationPriority.MEDIUM,
                "title": "Diversify vendor base to reduce risk",
                "description": "{count} vendors have low reliability scores. Over-reliance on few vendors increases supply chain risk.",
                "action_items": [
                    "Identify alternative suppliers for critical items",
                    "Conduct vendor performance reviews",
                    "Negotiate backup supply agreements"
                ]
            },
            "msme_verification": {
                "category": RecommendationCategory.COMPLIANCE,
                "priority": RecommendationPriority.HIGH,
                "title": "Verify MSME status of major vendors",
                "description": "Section 43B(h) requires payment to MSME vendors within 45 days. {count} major vendors have unverified MSME status.",
                "action_items": [
                    "Request MSME registration certificates from vendors",
                    "Update vendor master with MSME flags",
                    "Set up payment alerts for MSME vendors"
                ],
                "deadline": "Before next filing"
            }
        }
    
    def generate_recommendations(
        self,
        context: AnalysisContext,
        max_recommendations: int = 10
    ) -> RecommendationReport:
        """
        Generate recommendations from analysis context.
        
        Args:
            context: Analysis context from previous steps
            max_recommendations: Maximum number of recommendations to generate
            
        Returns:
            RecommendationReport with prioritized recommendations
        """
        recommendations = []
        
        # Step 1: Generate rule-based recommendations from templates
        template_recs = self._generate_from_templates(context)
        recommendations.extend(template_recs)
        
        # Step 2: Generate LLM-based recommendations for nuanced insights
        if self.llm:
            llm_recs = self._generate_from_llm(context, existing_count=len(recommendations))
            recommendations.extend(llm_recs)
        
        # Step 3: Deduplicate and prioritize
        recommendations = self._deduplicate(recommendations)
        recommendations = self._prioritize(recommendations)
        
        # Step 4: Limit to max
        recommendations = recommendations[:max_recommendations]
        
        # Step 5: Generate summary
        summary = self._generate_summary(recommendations, context)
        
        # Calculate totals
        total_savings = sum(r.estimated_savings or 0 for r in recommendations)
        critical_count = sum(1 for r in recommendations if r.priority == RecommendationPriority.CRITICAL)
        high_count = sum(1 for r in recommendations if r.priority == RecommendationPriority.HIGH)
        
        return RecommendationReport(
            recommendations=recommendations,
            summary=summary,
            total_potential_savings=total_savings,
            critical_count=critical_count,
            high_count=high_count
        )
    
    def _generate_from_templates(self, context: AnalysisContext) -> List[Recommendation]:
        """Generate recommendations using rule-based templates."""
        recommendations = []
        rec_id = 1
        
        # Check data quality issues
        if context.data_summary:
            for table, info in context.data_summary.get('tables', {}).items():
                if isinstance(info, dict):
                    null_cols = info.get('null_columns', {})
                    total_nulls = sum(null_cols.values())
                    if total_nulls > 10:
                        template = self._recommendation_templates['high_null_values']
                        rec = Recommendation(
                            id=f"REC-{rec_id:03d}",
                            title=template['title'].format(table=table),
                            description=template['description'].format(table=table, count=total_nulls),
                            category=template['category'],
                            priority=template['priority'],
                            impact_score=40,
                            effort_score=30,
                            action_items=template['action_items'].copy()
                        )
                        recommendations.append(rec)
                        rec_id += 1
        
        # Check compliance issues
        if context.compliance_issues:
            critical_issues = [i for i in context.compliance_issues if i.get('severity') == 'critical']
            for issue in critical_issues[:3]:  # Top 3 critical
                template = self._recommendation_templates['critical_compliance']
                rec = Recommendation(
                    id=f"REC-{rec_id:03d}",
                    title=template['title'].format(issue_type=issue.get('type', 'Unknown')),
                    description=issue.get('description', 'Critical compliance issue detected'),
                    category=template['category'],
                    priority=template['priority'],
                    impact_score=90,
                    effort_score=50,
                    action_items=template['action_items'].copy(),
                    related_issues=[issue.get('type', 'Unknown')],
                    estimated_savings=issue.get('amount_impact')
                )
                recommendations.append(rec)
                rec_id += 1
        
        # Check strategic insights
        if context.strategic_insights:
            # Cash flow issues
            forecasts = context.strategic_insights.get('cash_flow_forecasts', [])
            negative_periods = [f for f in forecasts if f.get('net_cash_flow', 0) < 0]
            if negative_periods:
                template = self._recommendation_templates['negative_cash_flow']
                total_deficit = sum(abs(f.get('net_cash_flow', 0)) for f in negative_periods)
                periods = ', '.join(f.get('period', 'Unknown') for f in negative_periods[:3])
                rec = Recommendation(
                    id=f"REC-{rec_id:03d}",
                    title=template['title'],
                    description=template['description'].format(periods=periods, amount=total_deficit),
                    category=template['category'],
                    priority=template['priority'],
                    impact_score=85,
                    effort_score=60,
                    action_items=template['action_items'].copy()
                )
                recommendations.append(rec)
                rec_id += 1
            
            # Vendor risk
            vendors = context.strategic_insights.get('vendor_rankings', [])
            risky_vendors = [v for v in vendors if v.get('score', 100) < 60]
            if len(risky_vendors) >= 2:
                template = self._recommendation_templates['vendor_risk']
                rec = Recommendation(
                    id=f"REC-{rec_id:03d}",
                    title=template['title'],
                    description=template['description'].format(count=len(risky_vendors)),
                    category=template['category'],
                    priority=template['priority'],
                    impact_score=60,
                    effort_score=40,
                    action_items=template['action_items'].copy()
                )
                recommendations.append(rec)
                rec_id += 1
        
        return recommendations
    
    def _generate_from_llm(
        self,
        context: AnalysisContext,
        existing_count: int = 0
    ) -> List[Recommendation]:
        """Generate additional recommendations using LLM for nuanced insights."""
        
        if not self.llm:
            return []
        
        # Build context string
        context_str = self._build_context_string(context)
        
        prompt = f"""Based on this business analysis, generate 3-5 specific, actionable recommendations that are NOT already covered by standard compliance, cash flow, or vendor checks.

{context_str}

Focus on:
1. Unique insights from the specific data patterns
2. Industry-specific optimizations
3. Tax savings opportunities
4. Operational improvements
5. Growth opportunities

For each recommendation, provide:
- A clear title (one line)
- A brief description (1-2 sentences)
- 2-3 specific action items
- Priority: CRITICAL, HIGH, MEDIUM, or LOW
- Category: COMPLIANCE, DATA_QUALITY, CASH_FLOW, VENDOR, TAX_SAVINGS, OPERATIONAL, or RISK

Format each recommendation as:
TITLE: [title]
DESCRIPTION: [description]
PRIORITY: [priority]
CATEGORY: [category]
ACTIONS:
- [action 1]
- [action 2]
---
"""
        
        try:
            response = self.llm.generate(prompt, max_tokens=800)
            return self._parse_llm_recommendations(response, start_id=existing_count + 1)
        except Exception as e:
            print(f"LLM recommendation generation failed: {e}")
            return []
    
    def _build_context_string(self, context: AnalysisContext) -> str:
        """Build a context string for LLM."""
        parts = []
        
        if context.data_summary:
            parts.append(f"DATA ANALYZED:")
            parts.append(f"- {context.data_summary.get('total_tables', 0)} tables")
            parts.append(f"- {context.data_summary.get('total_records', 0)} total records")
            for table, info in context.data_summary.get('tables', {}).items():
                if isinstance(info, dict):
                    parts.append(f"- {table}: {info.get('row_count', 0)} rows, {info.get('column_count', 0)} columns")
        
        if context.compliance_issues:
            parts.append(f"\nCOMPLIANCE STATUS:")
            critical = len([i for i in context.compliance_issues if i.get('severity') == 'critical'])
            warnings = len([i for i in context.compliance_issues if i.get('severity') == 'warning'])
            parts.append(f"- {critical} critical issues, {warnings} warnings")
            for issue in context.compliance_issues[:5]:
                parts.append(f"- {issue.get('type', 'Unknown')}: {issue.get('description', '')[:60]}")
        
        if context.strategic_insights:
            parts.append(f"\nSTRATEGIC INSIGHTS:")
            vendors = context.strategic_insights.get('vendor_rankings', [])
            if vendors:
                parts.append(f"- Top vendor: {vendors[0].get('name', 'Unknown')} (score: {vendors[0].get('score', 0)})")
            forecasts = context.strategic_insights.get('cash_flow_forecasts', [])
            if forecasts:
                net = sum(f.get('net_cash_flow', 0) for f in forecasts)
                parts.append(f"- Projected net cash flow: ₹{net:,.0f}")
        
        if context.custom_context:
            parts.append(f"\nADDITIONAL CONTEXT:")
            parts.append(context.custom_context)
        
        return "\n".join(parts)
    
    def _parse_llm_recommendations(self, response: str, start_id: int = 1) -> List[Recommendation]:
        """Parse LLM response into Recommendation objects."""
        recommendations = []
        rec_id = start_id
        
        # Split by recommendation separator
        blocks = response.split('---')
        
        for block in blocks:
            block = block.strip()
            if not block:
                continue
            
            try:
                # Parse fields
                title = self._extract_field(block, 'TITLE')
                description = self._extract_field(block, 'DESCRIPTION')
                priority_str = self._extract_field(block, 'PRIORITY')
                category_str = self._extract_field(block, 'CATEGORY')
                actions = self._extract_actions(block)
                
                if not title or not description:
                    continue
                
                # Map priority
                priority_map = {
                    'CRITICAL': RecommendationPriority.CRITICAL,
                    'HIGH': RecommendationPriority.HIGH,
                    'MEDIUM': RecommendationPriority.MEDIUM,
                    'LOW': RecommendationPriority.LOW
                }
                priority = priority_map.get(priority_str.upper(), RecommendationPriority.MEDIUM)
                
                # Map category
                category_map = {
                    'COMPLIANCE': RecommendationCategory.COMPLIANCE,
                    'DATA_QUALITY': RecommendationCategory.DATA_QUALITY,
                    'CASH_FLOW': RecommendationCategory.CASH_FLOW,
                    'VENDOR': RecommendationCategory.VENDOR,
                    'TAX_SAVINGS': RecommendationCategory.TAX_SAVINGS,
                    'OPERATIONAL': RecommendationCategory.OPERATIONAL,
                    'RISK': RecommendationCategory.RISK
                }
                category = category_map.get(category_str.upper(), RecommendationCategory.OPERATIONAL)
                
                # Calculate scores based on priority
                impact_scores = {
                    RecommendationPriority.CRITICAL: 95,
                    RecommendationPriority.HIGH: 75,
                    RecommendationPriority.MEDIUM: 50,
                    RecommendationPriority.LOW: 25
                }
                
                rec = Recommendation(
                    id=f"REC-{rec_id:03d}",
                    title=title,
                    description=description,
                    category=category,
                    priority=priority,
                    impact_score=impact_scores.get(priority, 50),
                    effort_score=50,  # Default medium effort
                    action_items=actions
                )
                recommendations.append(rec)
                rec_id += 1
                
            except Exception:
                continue
        
        return recommendations
    
    def _extract_field(self, text: str, field: str) -> str:
        """Extract a field value from text."""
        for line in text.split('\n'):
            if line.strip().upper().startswith(f'{field}:'):
                return line.split(':', 1)[1].strip()
        return ""
    
    def _extract_actions(self, text: str) -> List[str]:
        """Extract action items from text."""
        actions = []
        in_actions = False
        
        for line in text.split('\n'):
            line = line.strip()
            if 'ACTIONS' in line.upper():
                in_actions = True
                continue
            if in_actions and line.startswith('-'):
                action = line[1:].strip()
                if action:
                    actions.append(action)
            elif in_actions and line and not line.startswith('-'):
                # End of actions section
                break
        
        return actions
    
    def _deduplicate(self, recommendations: List[Recommendation]) -> List[Recommendation]:
        """Remove duplicate recommendations."""
        seen_titles = set()
        unique = []
        
        for rec in recommendations:
            # Normalize title for comparison
            normalized = rec.title.lower().strip()
            if normalized not in seen_titles:
                seen_titles.add(normalized)
                unique.append(rec)
        
        return unique
    
    def _prioritize(self, recommendations: List[Recommendation]) -> List[Recommendation]:
        """Sort recommendations by priority and impact."""
        
        priority_order = {
            RecommendationPriority.CRITICAL: 0,
            RecommendationPriority.HIGH: 1,
            RecommendationPriority.MEDIUM: 2,
            RecommendationPriority.LOW: 3
        }
        
        return sorted(
            recommendations,
            key=lambda r: (priority_order.get(r.priority, 99), -r.impact_score)
        )
    
    def _generate_summary(
        self,
        recommendations: List[Recommendation],
        context: AnalysisContext
    ) -> str:
        """Generate a summary of recommendations."""
        
        if not recommendations:
            return "No specific recommendations at this time. Your business appears to be in good standing."
        
        critical = [r for r in recommendations if r.priority == RecommendationPriority.CRITICAL]
        high = [r for r in recommendations if r.priority == RecommendationPriority.HIGH]
        
        summary_parts = []
        
        if critical:
            summary_parts.append(f"🔴 {len(critical)} CRITICAL item(s) require immediate attention.")
        
        if high:
            summary_parts.append(f"🟠 {len(high)} HIGH priority item(s) should be addressed soon.")
        
        # Group by category
        categories = {}
        for rec in recommendations:
            cat = rec.category.value
            categories[cat] = categories.get(cat, 0) + 1
        
        top_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:3]
        if top_categories:
            cat_str = ", ".join(f"{cat} ({count})" for cat, count in top_categories)
            summary_parts.append(f"Top focus areas: {cat_str}")
        
        return " ".join(summary_parts)
    
    def get_recommendation_by_id(
        self,
        report: RecommendationReport,
        rec_id: str
    ) -> Optional[Recommendation]:
        """Get a specific recommendation by ID."""
        for rec in report.recommendations:
            if rec.id == rec_id:
                return rec
        return None
    
    def filter_by_category(
        self,
        report: RecommendationReport,
        category: RecommendationCategory
    ) -> List[Recommendation]:
        """Filter recommendations by category."""
        return [r for r in report.recommendations if r.category == category]
    
    def filter_by_priority(
        self,
        report: RecommendationReport,
        priority: RecommendationPriority
    ) -> List[Recommendation]:
        """Filter recommendations by priority."""
        return [r for r in report.recommendations if r.priority == priority]
