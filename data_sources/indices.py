"""
Market Indices Data Fetcher

Fetches market index data including ASI (All Share Index), S&P SL20,
and other CSE indices for market context and relative performance analysis.
"""

import logging
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential

from utils.throttling import rate_limit
from storage.db import get_db_manager

logger = logging.getLogger(__name__)


# Common CSE indices
CSE_INDICES = {
    "ASI": "All Share Index",
    "SPL20": "S&P SL20 Index", 
    "SPL": "S&P Sri Lanka Index",
    "MPI": "Milanka Price Index",
    "ASPI": "All Share Price Index"
}


@rate_limit(calls=5, period=60)  # Rate limit: 5 calls per minute
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def fetch_indices(
    index_codes: Optional[List[str]] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    config: Optional[Dict] = None
) -> pd.DataFrame:
    """
    Fetch market index data for specified indices.
    
    TODO: Implement actual CSE index data scraping
    Currently generates sample data for development purposes.
    
    Args:
        index_codes: List of index codes to fetch (defaults to major CSE indices)
        start_date: Start date for data retrieval
        end_date: End date for data retrieval
        config: Optional configuration dictionary
        
    Returns:
        DataFrame with index data
        
    Raises:
        NotImplementedError: Full implementation pending
    """
    logger.warning(
        "fetch_indices: Using sample data. "
        "TODO: Implement CSE index data scraping"
    )
    
    if index_codes is None:
        index_codes = list(CSE_INDICES.keys())
    
    if start_date is None:
        start_date = date.today() - timedelta(days=30)
    if end_date is None:
        end_date = date.today()
    
    # Generate sample index data for development
    import numpy as np
    
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    # Filter to weekdays only (no trading on weekends)
    date_range = date_range[date_range.weekday < 5]
    
    index_data = []
    
    for index_code in index_codes:
        # Generate realistic index movements
        np.random.seed(hash(index_code) % (2**32))
        base_value = np.random.uniform(5000, 15000)  # Realistic index range
        
        for i, current_date in enumerate(date_range):
            # Random walk for index generation
            change = np.random.normal(0, 0.015)  # 1.5% daily volatility
            if i == 0:
                close_value = base_value
            else:
                close_value = index_data[-1]["close_value"] * (1 + change)
                close_value = max(close_value, 100)  # Prevent unrealistic drops
            
            # Generate OHLC from close value
            high_low_range = close_value * np.random.uniform(0.005, 0.02)
            high_value = close_value + np.random.uniform(0, high_low_range)
            low_value = close_value - np.random.uniform(0, high_low_range)
            open_value = low_value + np.random.uniform(0, high_value - low_value)
            
            # Generate volume and market cap
            volume = int(np.random.uniform(1000000, 50000000))  # Index volume
            market_cap = close_value * np.random.uniform(1000000, 5000000)  # Market cap proxy
            
            index_data.append({
                "index_code": index_code,
                "index_name": CSE_INDICES.get(index_code, f"{index_code} Index"),
                "date": current_date.date(),
                "open_value": round(open_value, 2),
                "high_value": round(high_value, 2),
                "low_value": round(low_value, 2),
                "close_value": round(close_value, 2),
                "volume": volume,
                "market_cap": round(market_cap, 2)
            })
    
    df = pd.DataFrame(index_data)
    logger.info(f"Generated {len(df)} index records for {len(index_codes)} indices")
    
    return df


def store_indices(indices_df: pd.DataFrame, config: Dict) -> None:
    """
    Store index data in database.
    
    Args:
        indices_df: DataFrame with index data
        config: Application configuration
    """
    if indices_df.empty:
        logger.warning("No index data to store")
        return
    
    db_manager = get_db_manager(config)
    
    logger.info(f"Storing {len(indices_df)} index records")
    
    with db_manager.get_session() as session:
        try:
            for _, row in indices_df.iterrows():
                session.execute(
                    """
                    INSERT OR REPLACE INTO indices
                    (index_code, index_name, date, open_value, high_value, low_value,
                     close_value, volume, market_cap, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        row["index_code"],
                        row["index_name"],
                        row["date"],
                        row["open_value"],
                        row["high_value"],
                        row["low_value"],
                        row["close_value"],
                        row["volume"],
                        row["market_cap"],
                        datetime.now()
                    )
                )
            
            session.commit()
            logger.info("Index data stored successfully")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error storing index data: {e}")
            raise


def get_index_data(
    index_codes: Optional[List[str]] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    config: Optional[Dict] = None
) -> pd.DataFrame:
    """
    Retrieve index data from database.
    
    Args:
        index_codes: List of index codes
        start_date: Start date for data retrieval
        end_date: End date for data retrieval
        config: Configuration dictionary
        
    Returns:
        DataFrame with index data
    """
    if config is None:
        raise ValueError("Configuration required")
    
    db_manager = get_db_manager(config)
    
    conditions = []
    params = []
    
    # Build dynamic query
    if index_codes:
        placeholders = ",".join(["?" for _ in index_codes])
        conditions.append(f"index_code IN ({placeholders})")
        params.extend(index_codes)
    
    if start_date:
        conditions.append("date >= ?")
        params.append(start_date)
    
    if end_date:
        conditions.append("date <= ?")
        params.append(end_date)
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    sql = f"""
        SELECT index_code, index_name, date, open_value, high_value, low_value,
               close_value, volume, market_cap
        FROM indices
        WHERE {where_clause}
        ORDER BY index_code, date
    """
    
    with db_manager.get_session() as session:
        result = session.execute(sql, params)
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
    
    return df


def fetch_and_store_indices(
    index_codes: Optional[List[str]] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    config: Optional[Dict] = None
) -> None:
    """
    Fetch and store index data in one operation.
    
    Args:
        index_codes: List of index codes
        start_date: Start date for data retrieval
        end_date: End date for data retrieval
        config: Configuration dictionary
    """
    if config is None:
        raise ValueError("Configuration required")
    
    try:
        # Fetch index data
        indices_df = fetch_indices(index_codes, start_date, end_date, config)
        
        # Store in database
        store_indices(indices_df, config)
        
        logger.info(f"Successfully fetched and stored index data")
        
    except Exception as e:
        logger.error(f"Error in fetch_and_store_indices: {e}")
        raise


def calculate_index_returns(
    index_code: str,
    periods: List[int] = [1, 5, 20],
    config: Optional[Dict] = None
) -> pd.DataFrame:
    """
    Calculate index returns for specified periods.
    
    Args:
        index_code: Index code
        periods: List of periods for return calculation
        config: Configuration dictionary
        
    Returns:
        DataFrame with index returns
    """
    if config is None:
        raise ValueError("Configuration required")
    
    # Get recent index data
    end_date = date.today()
    start_date = end_date - timedelta(days=max(periods) + 30)  # Buffer for weekends
    
    index_df = get_index_data([index_code], start_date, end_date, config)
    
    if index_df.empty:
        logger.warning(f"No data found for index {index_code}")
        return pd.DataFrame()
    
    index_df = index_df.sort_values('date')
    index_df['date'] = pd.to_datetime(index_df['date'])
    
    # Calculate returns for each period
    returns_data = []
    
    for period in periods:
        if len(index_df) > period:
            current_value = index_df.iloc[-1]['close_value']
            past_value = index_df.iloc[-(period+1)]['close_value']
            
            return_pct = ((current_value - past_value) / past_value) * 100
            
            returns_data.append({
                "index_code": index_code,
                "period_days": period,
                "return_percentage": round(return_pct, 2),
                "current_value": current_value,
                "past_value": past_value,
                "calculation_date": index_df.iloc[-1]['date'].date()
            })
    
    return pd.DataFrame(returns_data)


def get_market_summary(config: Dict) -> Dict:
    """
    Get market summary with key indices performance.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Dictionary with market summary data
    """
    summary = {}
    
    for index_code, index_name in CSE_INDICES.items():
        try:
            returns_df = calculate_index_returns(index_code, [1, 5, 20], config)
            
            if not returns_df.empty:
                summary[index_code] = {
                    "name": index_name,
                    "returns": returns_df.set_index('period_days')['return_percentage'].to_dict(),
                    "current_value": returns_df.iloc[0]['current_value']
                }
        except Exception as e:
            logger.error(f"Error calculating returns for {index_code}: {e}")
            continue
    
    return summary