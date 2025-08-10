"""
Test cases for the document processor.
"""
import pytest
import io
from src.processors.document_processor import DocumentProcessor
from src.utils.config import Config

class TestDocumentProcessor:
    """Test cases for DocumentProcessor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = Config()
        self.processor = DocumentProcessor(self.config)
    
    def test_supported_formats(self):
        """Test that processor supports expected file formats."""
        expected_formats = ['.pdf', '.docx', '.doc', '.png', '.jpg', '.jpeg']
        assert self.processor.supported_formats == expected_formats
    
    def test_is_table_line(self):
        """Test table line detection."""
        # Test line with financial data
        financial_line = "Revenue $12,500,000 15.3% increase"
        assert self.processor._is_table_line(financial_line)
        
        # Test regular text line
        text_line = "This is a regular paragraph of text"
        assert not self.processor._is_table_line(text_line)
        
        # Test line with multiple numbers
        number_line = "Assets 1,250,000 Liabilities 850,000 Equity 400,000"
        assert self.processor._is_table_line(number_line)
    
    def test_extract_metrics_from_text(self):
        """Test financial metrics extraction from text."""
        sample_text = """
        Company Financial Results
        Revenue: $12,500,000
        Net Income: $2,100,000
        Total Assets: $15,000,000
        Total Equity: $8,500,000
        """
        
        metrics = self.processor._extract_metrics_from_text(sample_text)
        
        assert 'revenue' in metrics
        assert metrics['revenue'] == 12500000
        assert 'net_income' in metrics
        assert metrics['net_income'] == 2100000
