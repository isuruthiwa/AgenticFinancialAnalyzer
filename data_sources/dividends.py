"""
Dividends Data Fetcher

Fetches dividend announcements and payment data from CSE including cash dividends,
interim dividends, and final dividends with yield calculations.
"""

import logging
from datetime import date, datetime
from typing import Dict, List, Optional

import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential

from utils.throttling import rate_limit
from storage.db import get_db_manager

logger = logging.getLogger(__name__)


@rate_limit(calls=5, period=60)  # Rate limit: 5 calls per minute
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def fetch_dividends(
    symbols: List[str],
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    config: Optional[Dict] = None
) -> pd.DataFrame:
    """
    Fetch dividend data for specified symbols.
    
    TODO: Implement actual CSE dividend data scraping
    Currently returns empty DataFrame as placeholder.
    
    Args:
        symbols: List of stock symbols
        start_date: Start date for data retrieval
        end_date: End date for data retrieval
        config: Optional configuration dictionary
        
    Returns:
        DataFrame with dividend data
        
    Raises:
        NotImplementedError: Full implementation pending
    """
    logger.warning(
        f"fetch_dividends: Stub implementation for {len(symbols)} symbols. "
        "TODO: Implement CSE dividend data scraping"
    )
    
    # Return empty DataFrame for now
    # TODO: Implement actual dividend fetching logic
    columns = [
        "symbol", "dividend_type", "announcement_date", "ex_date",
        "record_date", "payment_date", "amount", "currency", "yield_percentage"
    ]
    
    return pd.DataFrame(columns=columns)


def calculate_dividend_yield(
    dividend_amount: float,
    stock_price: float
) -> Optional[float]:
    """
    Calculate dividend yield percentage.
    
    Args:
        dividend_amount: Dividend amount per share
        stock_price: Stock price at ex-dividend date
        
    Returns:
        Dividend yield as percentage, None if calculation not possible
    """
    if stock_price <= 0 or dividend_amount <= 0:
        return None
    
    yield_percentage = (dividend_amount / stock_price) * 100
    return round(yield_percentage, 2)


def classify_dividend_type(description: str) -> str:
    """
    Classify dividend type based on description.
    
    Args:
        description: Dividend description text
        
    Returns:
        Classified dividend type
    """
    description_lower = description.lower()
    
    if "interim" in description_lower:
        return "interim"
    elif "final" in description_lower:
        return "final"
    elif "special" in description_lower:
        return "special"
    elif "stock" in description_lower:
        return "stock"
    else:
        return "cash"


def store_dividends(dividends_df: pd.DataFrame, config: Dict) -> None:
    """
    Store dividend data in database.
    
    Args:
        dividends_df: DataFrame with dividend data
        config: Application configuration
    """
    if dividends_df.empty:
        logger.info("No dividend data to store")
        return
    
    db_manager = get_db_manager(config)
    
    logger.info(f"Storing {len(dividends_df)} dividend records")
    
    with db_manager.get_session() as session:
        try:
            for _, row in dividends_df.iterrows():
                session.execute(
                    """
                    INSERT OR REPLACE INTO dividends
                    (symbol, dividend_type, announcement_date, ex_date, record_date,
                     payment_date, amount, currency, yield_percentage, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        row["symbol"],
                        row.get("dividend_type", "cash"),
                        row["announcement_date"],
                        row.get("ex_date"),
                        row.get("record_date"),
                        row.get("payment_date"),
                        row.get("amount"),
                        row.get("currency", "LKR"),
                        row.get("yield_percentage"),
                        datetime.now()
                    )
                )
            
            session.commit()
            logger.info("Dividend data stored successfully")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error storing dividend data: {e}")
            raise


def get_dividends(
    symbols: List[str],
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    dividend_types: Optional[List[str]] = None,
    config: Optional[Dict] = None
) -> pd.DataFrame:
    """
    Retrieve dividend data from database.
    
    Args:
        symbols: List of stock symbols
        start_date: Start date for data retrieval
        end_date: End date for data retrieval
        dividend_types: List of dividend types to filter by
        config: Configuration dictionary
        
    Returns:
        DataFrame with dividend data
    """
    if config is None:
        raise ValueError("Configuration required")
    
    db_manager = get_db_manager(config)
    
    conditions = []
    params = []
    
    # Build dynamic query
    if symbols:
        placeholders = ",".join(["?" for _ in symbols])
        conditions.append(f"symbol IN ({placeholders})")
        params.extend(symbols)
    
    if start_date:
        conditions.append("announcement_date >= ?")
        params.append(start_date)
    
    if end_date:
        conditions.append("announcement_date <= ?")
        params.append(end_date)
    
    if dividend_types:
        placeholders = ",".join(["?" for _ in dividend_types])
        conditions.append(f"dividend_type IN ({placeholders})")
        params.extend(dividend_types)
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    sql = f"""
        SELECT symbol, dividend_type, announcement_date, ex_date, record_date,
               payment_date, amount, currency, yield_percentage
        FROM dividends
        WHERE {where_clause}
        ORDER BY symbol, announcement_date
    """
    
    with db_manager.get_session() as session:
        result = session.execute(sql, params)
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    
    return df


def fetch_and_store_dividends(
    symbols: List[str],
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    config: Optional[Dict] = None
) -> None:
    """
    Fetch and store dividend data in one operation.
    
    Args:
        symbols: List of stock symbols
        start_date: Start date for data retrieval
        end_date: End date for data retrieval
        config: Configuration dictionary
    """
    if config is None:
        raise ValueError("Configuration required")
    
    try:
        # Fetch dividend data
        dividends_df = fetch_dividends(symbols, start_date, end_date, config)
        
        # TODO: Enhance dividend data with yield calculations
        # This would require fetching corresponding stock prices
        
        # Store in database
        store_dividends(dividends_df, config)
        
        logger.info(f"Successfully processed dividends for {len(symbols)} symbols")
        
    except Exception as e:
        logger.error(f"Error in fetch_and_store_dividends: {e}")
        raise


def get_dividend_calendar(
    start_date: date,
    end_date: date,
    config: Dict
) -> pd.DataFrame:
    """
    Get dividend calendar for specified date range.
    
    Args:
        start_date: Start date for calendar
        end_date: End date for calendar
        config: Configuration dictionary
        
    Returns:
        DataFrame with dividend calendar data
    """
    db_manager = get_db_manager(config)
    
    sql = """
        SELECT symbol, dividend_type, ex_date, amount, yield_percentage
        FROM dividends
        WHERE ex_date BETWEEN ? AND ?
        ORDER BY ex_date, symbol
    """
    
    with db_manager.get_session() as session:
        result = session.execute(sql, (start_date, end_date))
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    
    return df


def get_dividend_history(
    symbol: str,
    years: int = 5,
    config: Optional[Dict] = None
) -> pd.DataFrame:
    """
    Get dividend history for a specific symbol.
    
    Args:
        symbol: Stock symbol
        years: Number of years of history to retrieve
        config: Configuration dictionary
        
    Returns:
        DataFrame with dividend history
    """
    if config is None:
        raise ValueError("Configuration required")
    
    end_date = date.today()
    start_date = date(end_date.year - years, end_date.month, end_date.day)
    
    return get_dividends([symbol], start_date, end_date, config=config)