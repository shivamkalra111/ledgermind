"""
Strategist Agent - Vendor Analysis, Cash Flow Forecasting, Profit Optimization
Provides strategic recommendations based on financial data
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import date, timedelta
import statistics

from core.data_engine import DataEngine
from llm.client import LLMClient
from config import FORECAST_MONTHS, MSME_CLASSIFICATION


@dataclass
class VendorScore:
    """Vendor reliability score."""
    vendor_name: str
    total_transactions: int
    total_value: float
    avg_payment_days: Optional[float]
    is_msme: Optional[bool]
    reliability_score: float  # 0-100
    risk_factors: List[str]


@dataclass
class CashFlowForecast:
    """Cash flow forecast for a period."""
    period: str  # e.g., "January 2026"
    projected_inflows: float
    projected_outflows: float
    projected_tax_liability: float
    net_cash_flow: float
    confidence: float


@dataclass
class StrategistReport:
    """Complete strategist analysis report."""
    vendor_rankings: List[VendorScore]
    cash_flow_forecasts: List[CashFlowForecast]
    profit_insights: List[str]
    recommendations: List[str]


class StrategistAgent:
    """
    Agent 3: Strategist (Optimizer)
    
    Responsibilities:
    - Rank vendors by reliability
    - Identify MSME vs non-MSME vendor risks
    - Forecast cash flow and tax liabilities
    - Identify high-margin products/services
    - Provide profit optimization recommendations
    """
    
    def __init__(
        self,
        data_engine: Optional[DataEngine] = None,
        llm_client: Optional[LLMClient] = None
    ):
        self.data_engine = data_engine or DataEngine()
        self.llm = llm_client
        
    def run_full_analysis(self) -> StrategistReport:
        """Run complete strategic analysis."""
        
        vendor_rankings = self.analyze_vendors()
        cash_flow_forecasts = self.forecast_cash_flow()
        profit_insights = self.analyze_profit_margins()
        recommendations = self._generate_recommendations(
            vendor_rankings, cash_flow_forecasts, profit_insights
        )
        
        return StrategistReport(
            vendor_rankings=vendor_rankings,
            cash_flow_forecasts=cash_flow_forecasts,
            profit_insights=profit_insights,
            recommendations=recommendations
        )
    
    def analyze_vendors(self) -> List[VendorScore]:
        """Analyze and rank vendors by reliability."""
        
        vendor_scores = []
        
        tables = self.data_engine.list_tables()
        purchase_tables = [t for t in tables if 'purchase' in t.lower()]
        
        if not purchase_tables:
            return vendor_scores
        
        for table in purchase_tables:
            try:
                # Aggregate by vendor
                df = self.data_engine.query(f"""
                    SELECT * FROM {table}
                """)
                
                # Find vendor column
                vendor_col = None
                for col in ["vendor", "party_name", "supplier", "vendor_name"]:
                    if col in df.columns:
                        vendor_col = col
                        break
                
                if not vendor_col:
                    continue
                
                # Find amount column
                amount_col = None
                for col in ["total_value", "total_amount", "bill_amount", "amount"]:
                    if col in df.columns:
                        amount_col = col
                        break
                
                # Group by vendor
                vendors = df.groupby(vendor_col).agg({
                    vendor_col: 'count'
                }).reset_index(names=['vendor'])
                
                for _, row in vendors.iterrows():
                    vendor_name = str(row['vendor']) if 'vendor' in row else str(row[vendor_col])
                    
                    # Calculate metrics
                    vendor_data = df[df[vendor_col] == vendor_name]
                    total_transactions = len(vendor_data)
                    total_value = vendor_data[amount_col].sum() if amount_col else 0
                    
                    # Calculate reliability score (simplified)
                    # In reality, would consider payment history, delivery performance, etc.
                    reliability_score = min(100, 50 + total_transactions * 5)
                    
                    risk_factors = []
                    if total_transactions < 3:
                        risk_factors.append("Limited transaction history")
                    
                    vendor_scores.append(VendorScore(
                        vendor_name=vendor_name[:50],
                        total_transactions=total_transactions,
                        total_value=float(total_value) if total_value else 0,
                        avg_payment_days=None,  # Would need payment data
                        is_msme=None,  # Would need MSME registration data
                        reliability_score=reliability_score,
                        risk_factors=risk_factors
                    ))
                    
            except Exception as e:
                print(f"Error analyzing vendors in {table}: {e}")
        
        # Sort by reliability score
        vendor_scores.sort(key=lambda x: x.reliability_score, reverse=True)
        
        return vendor_scores[:20]  # Top 20
    
    def forecast_cash_flow(self, months: int = FORECAST_MONTHS) -> List[CashFlowForecast]:
        """Forecast cash flow for upcoming months."""
        
        forecasts = []
        
        tables = self.data_engine.list_tables()
        
        # Get historical data
        sales_tables = [t for t in tables if 'sales' in t.lower()]
        purchase_tables = [t for t in tables if 'purchase' in t.lower()]
        
        # Calculate historical averages (simplified)
        avg_monthly_sales = 0
        avg_monthly_purchases = 0
        
        for table in sales_tables:
            try:
                df = self.data_engine.query(f"SELECT * FROM {table}")
                for col in ["total_value", "total_amount", "amount"]:
                    if col in df.columns:
                        avg_monthly_sales = df[col].sum() / max(1, len(df) / 30)
                        break
            except:
                pass
        
        for table in purchase_tables:
            try:
                df = self.data_engine.query(f"SELECT * FROM {table}")
                for col in ["total_value", "total_amount", "amount"]:
                    if col in df.columns:
                        avg_monthly_purchases = df[col].sum() / max(1, len(df) / 30)
                        break
            except:
                pass
        
        # Generate forecasts
        today = date.today()
        
        for i in range(months):
            forecast_date = today + timedelta(days=30 * (i + 1))
            period = forecast_date.strftime("%B %Y")
            
            # Apply some variance
            variance = 1 + (i * 0.05)  # Increase uncertainty over time
            
            projected_inflows = avg_monthly_sales * variance
            projected_outflows = avg_monthly_purchases * variance
            
            # Estimate tax liability (18% on net)
            net_taxable = max(0, projected_inflows - projected_outflows)
            projected_tax = net_taxable * 0.18 * 0.5  # Rough estimate
            
            forecasts.append(CashFlowForecast(
                period=period,
                projected_inflows=projected_inflows,
                projected_outflows=projected_outflows,
                projected_tax_liability=projected_tax,
                net_cash_flow=projected_inflows - projected_outflows - projected_tax,
                confidence=max(0.5, 1 - i * 0.15)  # Decrease confidence over time
            ))
        
        return forecasts
    
    def analyze_profit_margins(self) -> List[str]:
        """Analyze profit margins by product/service."""
        
        insights = []
        
        tables = self.data_engine.list_tables()
        sales_tables = [t for t in tables if 'sales' in t.lower()]
        
        for table in sales_tables:
            try:
                df = self.data_engine.query(f"SELECT * FROM {table}")
                
                # Find relevant columns
                item_col = None
                for col in ["description", "item", "product", "particulars"]:
                    if col in df.columns:
                        item_col = col
                        break
                
                amount_col = None
                for col in ["total_value", "total_amount", "amount"]:
                    if col in df.columns:
                        amount_col = col
                        break
                
                if item_col and amount_col:
                    # Group by item
                    top_items = df.groupby(item_col)[amount_col].sum().sort_values(ascending=False).head(5)
                    
                    for item, value in top_items.items():
                        insights.append(f"Top revenue item: '{str(item)[:30]}' - ₹{value:,.0f}")
                        
            except Exception as e:
                print(f"Error analyzing profits in {table}: {e}")
        
        if not insights:
            insights.append("Insufficient data for profit margin analysis")
        
        return insights
    
    def _generate_recommendations(
        self,
        vendor_rankings: List[VendorScore],
        cash_flow_forecasts: List[CashFlowForecast],
        profit_insights: List[str]
    ) -> List[str]:
        """Generate strategic recommendations."""
        
        recommendations = []
        
        # Vendor recommendations
        risky_vendors = [v for v in vendor_rankings if v.reliability_score < 60]
        if risky_vendors:
            recommendations.append(
                f"🚨 {len(risky_vendors)} vendors have low reliability scores. "
                "Consider diversifying supplier base."
            )
        
        # Check for MSME vendor issues
        msme_unknown = [v for v in vendor_rankings if v.is_msme is None and v.total_value > 100000]
        if msme_unknown:
            recommendations.append(
                f"📋 Verify MSME status of {len(msme_unknown)} major vendors "
                "for Section 43B(h) compliance."
            )
        
        # Cash flow recommendations
        negative_months = [f for f in cash_flow_forecasts if f.net_cash_flow < 0]
        if negative_months:
            recommendations.append(
                f"⚠️ Projected negative cash flow in {len(negative_months)} months. "
                "Consider accelerating receivables or deferring non-essential expenses."
            )
        
        # Tax planning
        total_projected_tax = sum(f.projected_tax_liability for f in cash_flow_forecasts)
        if total_projected_tax > 0:
            recommendations.append(
                f"💰 Estimated tax liability for next {len(cash_flow_forecasts)} months: "
                f"₹{total_projected_tax:,.0f}. Plan advance tax accordingly."
            )
        
        if not recommendations:
            recommendations.append("✅ No immediate strategic concerns identified.")
        
        return recommendations

