"""
Financial analysis engine for processing and analyzing financial data.
"""
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from src.utils.logger import logger

@dataclass
class FinancialMetrics:
    """Container for financial metrics and ratios."""
    
    # Profitability Ratios
    gross_profit_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    net_profit_margin: Optional[float] = None
    return_on_assets: Optional[float] = None
    return_on_equity: Optional[float] = None
    
    # Liquidity Ratios
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None
    cash_ratio: Optional[float] = None
    
    # Leverage Ratios
    debt_to_equity: Optional[float] = None
    debt_to_assets: Optional[float] = None
    interest_coverage: Optional[float] = None
    
    # Efficiency Ratios
    asset_turnover: Optional[float] = None
    inventory_turnover: Optional[float] = None
    receivables_turnover: Optional[float] = None
    
    # Growth Metrics
    revenue_growth: Optional[float] = None
    income_growth: Optional[float] = None
    
    # Additional metrics
    calculated_at: datetime = field(default_factory=datetime.now)
    warnings: List[str] = field(default_factory=list)

@dataclass
class FinancialAnalysis:
    """Complete financial analysis result."""
    metrics: FinancialMetrics
    insights: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    trend_analysis: Dict[str, Any] = field(default_factory=dict)

class FinancialAnalyzer:
    """Engine for analyzing financial documents and calculating metrics."""
    
    def __init__(self, config: Any):
        """Initialize financial analyzer."""
        self.config = config
        
        # Industry benchmarks (could be loaded from external data)
        self.industry_benchmarks = {
            'current_ratio': {'good': 2.0, 'acceptable': 1.5, 'poor': 1.0},
            'debt_to_equity': {'good': 0.3, 'acceptable': 0.5, 'poor': 1.0},
            'roa': {'good': 0.10, 'acceptable': 0.05, 'poor': 0.02},
            'roe': {'good': 0.15, 'acceptable': 0.10, 'poor': 0.05},
            'net_margin': {'good': 0.10, 'acceptable': 0.05, 'poor': 0.02}
        }
    
    def analyze_document(self, processed_data: Dict[str, Any]) -> FinancialAnalysis:
        """Analyze a processed financial document."""
        try:
            # Extract financial data
            financial_data = processed_data.get('financial_data', {})
            
            # Calculate metrics
            metrics = self._calculate_metrics(financial_data)
            
            # Generate insights
            insights = self._generate_insights(metrics)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(metrics)
            
            # Identify risk factors
            risk_factors = self._identify_risks(metrics)
            
            # Identify strengths
            strengths = self._identify_strengths(metrics)
            
            return FinancialAnalysis(
                metrics=metrics,
                insights=insights,
                recommendations=recommendations,
                risk_factors=risk_factors,
                strengths=strengths
            )
        
        except Exception as e:
            logger.error(f"Error analyzing document: {e}")
            return FinancialAnalysis(
                metrics=FinancialMetrics(),
                insights=[f"Analysis error: {str(e)}"]
            )
    
    def _calculate_metrics(self, financial_data: Dict[str, Any]) -> FinancialMetrics:
        """Calculate financial metrics from extracted data."""
        metrics = FinancialMetrics()
        
        # Extract key values
        revenue = financial_data.get('revenue', 0)
        net_income = financial_data.get('net_income', 0)
        gross_profit = financial_data.get('gross_profit', 0)
        operating_income = financial_data.get('operating_income', 0)
        total_assets = financial_data.get('total_assets', 0)
        total_equity = financial_data.get('total_equity', 0)
        current_assets = financial_data.get('current_assets', 0)
        current_liabilities = financial_data.get('current_liabilities', 0)
        total_debt = financial_data.get('total_debt', 0)
        cash = financial_data.get('cash', 0)
        inventory = financial_data.get('inventory', 0)
        accounts_receivable = financial_data.get('accounts_receivable', 0)
        interest_expense = financial_data.get('interest_expense', 0)
        
        # Calculate profitability ratios
        if revenue > 0:
            if gross_profit > 0:
                metrics.gross_profit_margin = gross_profit / revenue
            if operating_income > 0:
                metrics.operating_margin = operating_income / revenue
            if net_income > 0:
                metrics.net_profit_margin = net_income / revenue
        
        if total_assets > 0:
            if net_income > 0:
                metrics.return_on_assets = net_income / total_assets
            if revenue > 0:
                metrics.asset_turnover = revenue / total_assets
        
        if total_equity > 0 and net_income > 0:
            metrics.return_on_equity = net_income / total_equity
        
        # Calculate liquidity ratios
        if current_liabilities > 0:
            if current_assets > 0:
                metrics.current_ratio = current_assets / current_liabilities
            
            # Quick ratio (current assets - inventory) / current liabilities
            quick_assets = current_assets - inventory if inventory > 0 else current_assets
            if quick_assets > 0:
                metrics.quick_ratio = quick_assets / current_liabilities
            
            if cash > 0:
                metrics.cash_ratio = cash / current_liabilities
        
        # Calculate leverage ratios
        if total_equity > 0 and total_debt > 0:
            metrics.debt_to_equity = total_debt / total_equity
        
        if total_assets > 0 and total_debt > 0:
            metrics.debt_to_assets = total_debt / total_assets
        
        if interest_expense > 0 and operating_income > 0:
            metrics.interest_coverage = operating_income / interest_expense
        
        # Calculate efficiency ratios
        if inventory > 0 and revenue > 0:
            # Simplified - should use COGS
            metrics.inventory_turnover = revenue / inventory
        
        if accounts_receivable > 0 and revenue > 0:
            metrics.receivables_turnover = revenue / accounts_receivable
        
        return metrics
    
    def _generate_insights(self, metrics: FinancialMetrics) -> List[str]:
        """Generate insights based on calculated metrics."""
        insights = []
        
        # Profitability insights
        if metrics.net_profit_margin is not None:
            if metrics.net_profit_margin > 0.10:
                insights.append("Strong profitability with net margin above 10%")
            elif metrics.net_profit_margin < 0.02:
                insights.append("Low profitability - net margin below 2%")
        
        if metrics.return_on_equity is not None:
            if metrics.return_on_equity > 0.15:
                insights.append("Excellent return on equity above 15%")
            elif metrics.return_on_equity < 0.05:
                insights.append("Poor return on equity below 5%")
        
        # Liquidity insights
        if metrics.current_ratio is not None:
            if metrics.current_ratio > 2.0:
                insights.append("Strong liquidity position with current ratio above 2.0")
            elif metrics.current_ratio < 1.0:
                insights.append("Liquidity concern - current ratio below 1.0")
        
        # Leverage insights
        if metrics.debt_to_equity is not None:
            if metrics.debt_to_equity > 1.0:
                insights.append("High leverage - debt-to-equity ratio above 1.0")
            elif metrics.debt_to_equity < 0.3:
                insights.append("Conservative debt levels with low leverage")
        
        return insights
    
    def _generate_recommendations(self, metrics: FinancialMetrics) -> List[str]:
        """Generate recommendations based on metrics."""
        recommendations = []
        
        # Profitability recommendations
        if metrics.net_profit_margin is not None and metrics.net_profit_margin < 0.05:
            recommendations.append("Focus on improving operational efficiency and cost management")
        
        if metrics.gross_profit_margin is not None and metrics.gross_profit_margin < 0.30:
            recommendations.append("Consider pricing strategy review and cost of goods optimization")
        
        # Liquidity recommendations
        if metrics.current_ratio is not None:
            if metrics.current_ratio < 1.5:
                recommendations.append("Improve working capital management and cash flow")
            elif metrics.current_ratio > 3.0:
                recommendations.append("Consider investing excess cash for better returns")
        
        # Leverage recommendations
        if metrics.debt_to_equity is not None:
            if metrics.debt_to_equity > 0.6:
                recommendations.append("Consider debt reduction to improve financial stability")
            elif metrics.debt_to_equity < 0.2:
                recommendations.append("Could leverage debt for growth opportunities")
        
        # Efficiency recommendations
        if metrics.asset_turnover is not None and metrics.asset_turnover < 0.5:
            recommendations.append("Improve asset utilization and operational efficiency")
        
        return recommendations
    
    def _identify_risks(self, metrics: FinancialMetrics) -> List[str]:
        """Identify potential risk factors."""
        risks = []
        
        # Liquidity risks
        if metrics.current_ratio is not None and metrics.current_ratio < 1.0:
            risks.append("Liquidity risk - insufficient current assets to cover short-term obligations")
        
        if metrics.cash_ratio is not None and metrics.cash_ratio < 0.1:
            risks.append("Cash flow risk - low cash reserves relative to current liabilities")
        
        # Leverage risks
        if metrics.debt_to_equity is not None and metrics.debt_to_equity > 1.0:
            risks.append("High leverage risk - debt levels may be unsustainable")
        
        if metrics.interest_coverage is not None and metrics.interest_coverage < 2.0:
            risks.append("Interest coverage risk - earnings may not adequately cover interest payments")
        
        # Profitability risks
        if metrics.net_profit_margin is not None and metrics.net_profit_margin < 0:
            risks.append("Profitability risk - company is operating at a loss")
        
        if metrics.return_on_assets is not None and metrics.return_on_assets < 0.02:
            risks.append("Asset efficiency risk - poor return on invested assets")
        
        return risks
    
    def _identify_strengths(self, metrics: FinancialMetrics) -> List[str]:
        """Identify financial strengths."""
        strengths = []
        
        # Profitability strengths
        if metrics.net_profit_margin is not None and metrics.net_profit_margin > 0.10:
            strengths.append("Strong profitability margins")
        
        if metrics.return_on_equity is not None and metrics.return_on_equity > 0.15:
            strengths.append("Excellent shareholder returns")
        
        # Liquidity strengths
        if metrics.current_ratio is not None and metrics.current_ratio > 2.0:
            strengths.append("Strong liquidity position")
        
        if metrics.quick_ratio is not None and metrics.quick_ratio > 1.0:
            strengths.append("Good short-term liquidity without relying on inventory")
        
        # Leverage strengths
        if metrics.debt_to_equity is not None and metrics.debt_to_equity < 0.3:
            strengths.append("Conservative debt management")
        
        if metrics.interest_coverage is not None and metrics.interest_coverage > 5.0:
            strengths.append("Strong ability to service debt obligations")
        
        # Efficiency strengths
        if metrics.asset_turnover is not None and metrics.asset_turnover > 1.0:
            strengths.append("Efficient asset utilization")
        
        return strengths
    
    def compare_to_benchmarks(self, metrics: FinancialMetrics) -> Dict[str, str]:
        """Compare metrics to industry benchmarks."""
        comparisons = {}
        
        metric_mapping = {
            'current_ratio': metrics.current_ratio,
            'debt_to_equity': metrics.debt_to_equity,
            'roa': metrics.return_on_assets,
            'roe': metrics.return_on_equity,
            'net_margin': metrics.net_profit_margin
        }
        
        for benchmark_name, metric_value in metric_mapping.items():
            if metric_value is not None and benchmark_name in self.industry_benchmarks:
                benchmark = self.industry_benchmarks[benchmark_name]
                
                if metric_value >= benchmark['good']:
                    comparisons[benchmark_name] = 'Good'
                elif metric_value >= benchmark['acceptable']:
                    comparisons[benchmark_name] = 'Acceptable'
                else:
                    comparisons[benchmark_name] = 'Below Average'
        
        return comparisons
    
    def calculate_trend_analysis(
        self,
        historical_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate trend analysis from historical financial data."""
        if len(historical_data) < 2:
            return {"message": "Insufficient data for trend analysis"}
        
        trends = {}
        
        # Extract time series data
        metrics_over_time = []
        for period_data in historical_data:
            metrics = self._calculate_metrics(period_data.get('financial_data', {}))
            metrics_over_time.append(metrics)
        
        # Calculate trends for key metrics
        if len(metrics_over_time) >= 2:
            latest = metrics_over_time[-1]
            previous = metrics_over_time[-2]
            
            trend_metrics = {
                'net_profit_margin': (latest.net_profit_margin, previous.net_profit_margin),
                'return_on_equity': (latest.return_on_equity, previous.return_on_equity),
                'current_ratio': (latest.current_ratio, previous.current_ratio),
                'debt_to_equity': (latest.debt_to_equity, previous.debt_to_equity)
            }
            
            for metric_name, (current_val, prev_val) in trend_metrics.items():
                if current_val is not None and prev_val is not None:
                    change = ((current_val - prev_val) / prev_val) * 100
                    trends[metric_name] = {
                        'current': current_val,
                        'previous': prev_val,
                        'change_percent': change,
                        'direction': 'improving' if change > 0 else 'declining'
                    }
        
        return trends
