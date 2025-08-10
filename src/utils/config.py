"""
Configuration management for the Agentic Financial Analyzer.
"""
import os
from dataclasses import dataclass
from typing import Optional

# Try to import dotenv, but don't fail if it's not available
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

@dataclass
class Config:
    """Application configuration class."""
    # AI Model Settings
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    # Database Settings
    database_url: str = "sqlite:///financial_analyzer.db"
    vector_db_path: str = "./data/vector_db"
    
    # Application Settings
    debug: bool = False
    log_level: str = "INFO"
    max_file_size_mb: int = 50
    
    # Financial Data APIs
    alpha_vantage_api_key: Optional[str] = None
    yahoo_finance_api_key: Optional[str] = None
    
    # UI Settings
    streamlit_port: int = 8501
    streamlit_host: str = "localhost"

def load_config() -> Config:
    """Load configuration from environment variables."""
    # Load .env file if it exists and dotenv is available
    if DOTENV_AVAILABLE:
        load_dotenv()
    
    return Config(
        # AI Model Settings
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        
        # Database Settings
        database_url=os.getenv("DATABASE_URL", "sqlite:///financial_analyzer.db"),
        vector_db_path=os.getenv("VECTOR_DB_PATH", "./data/vector_db"),
        
        # Application Settings
        debug=os.getenv("DEBUG", "False").lower() == "true",
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        max_file_size_mb=int(os.getenv("MAX_FILE_SIZE_MB", "50")),
        
        # Financial Data APIs
        alpha_vantage_api_key=os.getenv("ALPHA_VANTAGE_API_KEY"),
        yahoo_finance_api_key=os.getenv("YAHOO_FINANCE_API_KEY"),
        
        # UI Settings
        streamlit_port=int(os.getenv("STREAMLIT_PORT", "8501")),
        streamlit_host=os.getenv("STREAMLIT_HOST", "localhost")
    )
