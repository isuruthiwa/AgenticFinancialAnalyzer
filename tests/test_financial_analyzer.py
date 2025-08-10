"""
Test cases for the financial analyzer.
"""
import pytest
from src.analysis.financial_analyzer import FinancialAnalyzer, FinancialMetrics
from src.utils.config import Config

class TestFinancialAnalyzer:
    """Test cases for FinancialAnalyzer class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = Config()
        self.analyzer = FinancialAnalyzer(self.config)
    
    def test_calculate_profitability_ratios(self):
        """Test profitability ratio calculations."""
        financial_data = {
            'revenue': 12500000,
            'gross_profit': 5625000,
            'operating_income': 2250000,
            'net_income': 1875000,
            'total_assets': 15000000,
            'total_equity': 8500000
        }
        
        metrics = self.analyzer._calculate_metrics(financial_data)
        
        # Test gross profit margin: 5,625,000 / 12,500,000 = 0.45
        assert abs(metrics.gross_profit_margin - 0.45) < 0.001
        
        # Test operating margin: 2,250,000 / 12,500,000 = 0.18
        assert abs(metrics.operating_margin - 0.18) < 0.001
        
        # Test net profit margin: 1,875,000 / 12,500,000 = 0.15
        assert abs(metrics.net_profit_margin - 0.15) < 0.001
        
        # Test ROA: 1,875,000 / 15,000,000 = 0.125
        assert abs(metrics.return_on_assets - 0.125) < 0.001
        
        # Test ROE: 1,875,000 / 8,500,000 ≈ 0.22
        assert abs(metrics.return_on_equity - 0.2206) < 0.001
    
    def test_calculate_liquidity_ratios(self):
        """Test liquidity ratio calculations."""
        financial_data = {
            'current_assets': 5000000,
            'current_liabilities': 2500000,
            'inventory': 1500000,
            'cash': 800000
        }
        
        metrics = self.analyzer._calculate_metrics(financial_data)
        
        # Test current ratio: 5,000,000 / 2,500,000 = 2.0
        assert abs(metrics.current_ratio - 2.0) < 0.001
        
        # Test quick ratio: (5,000,000 - 1,500,000) / 2,500,000 = 1.4
        assert abs(metrics.quick_ratio - 1.4) < 0.001
        
        # Test cash ratio: 800,000 / 2,500,000 = 0.32
        assert abs(metrics.cash_ratio - 0.32) < 0.001
    
    def test_generate_insights(self):
        """Test insight generation."""
        metrics = FinancialMetrics()
        metrics.net_profit_margin = 0.15  # Strong profitability
        metrics.current_ratio = 2.5  # Strong liquidity
        metrics.debt_to_equity = 0.25  # Conservative debt
        
        insights = self.analyzer._generate_insights(metrics)
        
        assert len(insights) > 0
        assert any("profitability" in insight.lower() for insight in insights)
        assert any("liquidity" in insight.lower() for insight in insights)
        assert any("conservative" in insight.lower() for insight in insights)
    
    def test_identify_risks(self):
        """Test risk identification."""
        metrics = FinancialMetrics()
        metrics.current_ratio = 0.8  # Liquidity risk
        metrics.debt_to_equity = 1.5  # High leverage risk
        metrics.net_profit_margin = -0.05  # Loss-making
        
        risks = self.analyzer._identify_risks(metrics)
        
        assert len(risks) > 0
        assert any("liquidity" in risk.lower() for risk in risks)
        assert any("leverage" in risk.lower() for risk in risks)
        assert any("loss" in risk.lower() or "profitability" in risk.lower() for risk in risks)
