"""
Price Data Fetcher for CSE Stocks

Fetches daily OHLCV price data from CSE and other financial data providers.
Handles data validation, cleaning, and storage with proper error handling
and rate limiting.
"""

import logging
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

import pandas as pd
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from utils.throttling import rate_limit
from storage.db import get_db_manager

logger = logging.getLogger(__name__)


@rate_limit(calls=5, period=60)  # Rate limit: 5 calls per minute
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def fetch_price_data(
    symbols: List[str],
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    config: Optional[Dict] = None
) -> pd.DataFrame:
    """
    Fetch daily price data for specified symbols.
    
    TODO: Implement actual CSE data source integration
    Currently generates sample data for development purposes.
    
    Args:
        symbols: List of stock symbols
        start_date: Start date for data retrieval
        end_date: End date for data retrieval  
        config: Optional configuration dictionary
        
    Returns:
        DataFrame with OHLCV price data
        
    Raises:
        NotImplementedError: Full implementation pending
    """
    logger.warning(
        f"fetch_price_data: Using sample data for {len(symbols)} symbols. "
        "TODO: Implement CSE data source integration"
    )
    
    if start_date is None:
        start_date = date.today() - timedelta(days=30)
    if end_date is None:
        end_date = date.today()
    
    # Generate sample price data for development
    import numpy as np
    
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    # Filter to weekdays only (no trading on weekends)
    date_range = date_range[date_range.weekday < 5]
    
    price_data = []
    
    for symbol in symbols:
        # Generate realistic price movements
        np.random.seed(hash(symbol) % (2**32))  # Consistent random data per symbol
        base_price = np.random.uniform(10, 500)  # Random base price
        
        for i, current_date in enumerate(date_range):
            # Random walk for price generation
            change = np.random.normal(0, 0.02)  # 2% daily volatility
            if i == 0:
                close_price = base_price
            else:
                close_price = price_data[-1]["close_price"] * (1 + change)
                close_price = max(close_price, 0.1)  # Prevent negative prices
            
            # Generate OHLC from close price
            high_low_range = close_price * np.random.uniform(0.01, 0.05)
            high_price = close_price + np.random.uniform(0, high_low_range)
            low_price = close_price - np.random.uniform(0, high_low_range)
            open_price = low_price + np.random.uniform(0, high_price - low_price)
            
            # Generate volume
            volume = int(np.random.uniform(1000, 100000))
            turnover = volume * close_price
            
            price_data.append({
                "symbol": symbol,
                "date": current_date.date(),
                "open_price": round(open_price, 2),
                "high_price": round(high_price, 2),
                "low_price": round(low_price, 2),
                "close_price": round(close_price, 2),
                "volume": volume,
                "turnover": round(turnover, 2),
                "trades_count": int(np.random.uniform(10, 500)),
                "adjusted_close": round(close_price, 2)  # No adjustments yet
            })
    
    df = pd.DataFrame(price_data)
    logger.info(f"Generated {len(df)} price records for {len(symbols)} symbols")
    
    return df


def store_price_data(price_df: pd.DataFrame, config: Dict) -> None:
    """
    Store price data in database.
    
    Args:
        price_df: DataFrame with price data
        config: Application configuration
    """
    if price_df.empty:
        logger.warning("No price data to store")
        return
    
    db_manager = get_db_manager(config)
    
    logger.info(f"Storing {len(price_df)} price records")
    
    with db_manager.get_session() as session:
        try:
            for _, row in price_df.iterrows():
                # Insert or replace price data
                session.execute(
                    """
                    INSERT OR REPLACE INTO prices 
                    (symbol, date, open_price, high_price, low_price, close_price,
                     volume, turnover, trades_count, adjusted_close, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        row["symbol"],
                        row["date"],
                        row["open_price"],
                        row["high_price"],
                        row["low_price"],
                        row["close_price"],
                        row["volume"],
                        row["turnover"],
                        row["trades_count"],
                        row["adjusted_close"],
                        datetime.now()
                    )
                )
            
            session.commit()
            logger.info("Price data stored successfully")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error storing price data: {e}")
            raise


def get_price_data(
    symbols: List[str],
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    config: Optional[Dict] = None
) -> pd.DataFrame:
    """
    Retrieve price data from database.
    
    Args:
        symbols: List of stock symbols
        start_date: Start date for data retrieval
        end_date: End date for data retrieval
        config: Configuration dictionary
        
    Returns:
        DataFrame with price data
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
        conditions.append("date >= ?")
        params.append(start_date)
    
    if end_date:
        conditions.append("date <= ?")
        params.append(end_date)
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    sql = f"""
        SELECT symbol, date, open_price, high_price, low_price, close_price,
               volume, turnover, trades_count, adjusted_close
        FROM prices
        WHERE {where_clause}
        ORDER BY symbol, date
    """
    
    with db_manager.get_session() as session:
        result = session.execute(sql, params)
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
    
    return df


def fetch_and_store_prices(
    symbols: List[str],
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    config: Optional[Dict] = None
) -> None:
    """
    Fetch and store price data in one operation.
    
    Args:
        symbols: List of stock symbols
        start_date: Start date for data retrieval
        end_date: End date for data retrieval
        config: Configuration dictionary
    """
    if config is None:
        raise ValueError("Configuration required")
    
    try:
        # Fetch price data
        price_df = fetch_price_data(symbols, start_date, end_date, config)
        
        # Store in database
        store_price_data(price_df, config)
        
        logger.info(f"Successfully fetched and stored price data for {len(symbols)} symbols")
        
    except Exception as e:
        logger.error(f"Error in fetch_and_store_prices: {e}")
        raise


def validate_price_data(price_df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate and clean price data.
    
    Args:
        price_df: Raw price data DataFrame
        
    Returns:
        Cleaned price data DataFrame
    """
    if price_df.empty:
        return price_df
    
    logger.info(f"Validating {len(price_df)} price records")
    
    # Remove records with invalid prices
    initial_count = len(price_df)
    
    # Basic validation
    price_df = price_df[price_df["close_price"] > 0]
    price_df = price_df[price_df["high_price"] >= price_df["low_price"]]
    price_df = price_df[price_df["high_price"] >= price_df["close_price"]]
    price_df = price_df[price_df["low_price"] <= price_df["close_price"]]
    price_df = price_df[price_df["volume"] >= 0]
    
    # Remove duplicates
    price_df = price_df.drop_duplicates(subset=["symbol", "date"])
    
    final_count = len(price_df)
    removed_count = initial_count - final_count
    
    if removed_count > 0:
        logger.warning(f"Removed {removed_count} invalid price records")
    
    logger.info(f"Price data validation completed: {final_count} valid records")
    
    return price_df