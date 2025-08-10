"""
Data models for the financial analyzer.
"""
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class DocumentType(Enum):
    """Supported document types."""
    PDF = "pdf"
    WORD = "word"
    IMAGE = "image"

class AnalysisType(Enum):
    """Types of financial analysis."""
    QUICK = "quick"
    STANDARD = "standard"
    COMPREHENSIVE = "comprehensive"

@dataclass
class UploadedDocument:
    """Represents an uploaded financial document."""
    filename: str
    file_type: DocumentType
    size_bytes: int
    upload_timestamp: datetime
    processed: bool = False
    processing_error: Optional[str] = None

@dataclass
class FinancialStatement:
    """Base class for financial statements."""
    statement_type: str
    period_end: Optional[datetime] = None
    currency: str = "USD"
    data: Dict[str, Any] = None

@dataclass
class IncomeStatement(FinancialStatement):
    """Income statement data."""
    revenue: Optional[float] = None
    cost_of_goods_sold: Optional[float] = None
    gross_profit: Optional[float] = None
    operating_expenses: Optional[float] = None
    operating_income: Optional[float] = None
    interest_expense: Optional[float] = None
    net_income: Optional[float] = None

@dataclass
class BalanceSheet(FinancialStatement):
    """Balance sheet data."""
    total_assets: Optional[float] = None
    current_assets: Optional[float] = None
    cash_and_equivalents: Optional[float] = None
    accounts_receivable: Optional[float] = None
    inventory: Optional[float] = None
    total_liabilities: Optional[float] = None
    current_liabilities: Optional[float] = None
    total_equity: Optional[float] = None

@dataclass
class CashFlowStatement(FinancialStatement):
    """Cash flow statement data."""
    operating_cash_flow: Optional[float] = None
    investing_cash_flow: Optional[float] = None
    financing_cash_flow: Optional[float] = None
    net_change_in_cash: Optional[float] = None
    beginning_cash_balance: Optional[float] = None
    ending_cash_balance: Optional[float] = None

@dataclass
class CompanyInfo:
    """Company information."""
    name: Optional[str] = None
    ticker: Optional[str] = None
    industry: Optional[str] = None
    sector: Optional[str] = None
    market_cap: Optional[float] = None
    employees: Optional[int] = None
