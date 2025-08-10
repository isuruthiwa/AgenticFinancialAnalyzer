"""
Foreign Exchange Rates Data Fetcher

Fetches FX rates relevant to Sri Lankan market including USD/LKR, EUR/LKR,
GBP/LKR, and other major currency pairs from Central Bank and financial data providers.
"""

import logging
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential

from utils.throttling import rate_limit
from storage.db import get_db_manager

logger = logging.getLogger(__name__)


# Common FX pairs for Sri Lankan market
MAJOR_FX_PAIRS = [
    "USD/LKR",
    "EUR/LKR", 
    "GBP/LKR",
    "JPY/LKR",
    "INR/LKR",
    "AUD/LKR",
    "CAD/LKR"
]


@rate_limit(calls=5, period=60)  # Rate limit: 5 calls per minute
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def fetch_fx_rates(
    currency_pairs: Optional[List[str]] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    config: Optional[Dict] = None
) -> pd.DataFrame:
    """
    Fetch foreign exchange rates for specified currency pairs.
    
    TODO: Implement actual FX data source integration (Central Bank of Sri Lanka, financial APIs)
    Currently generates sample data for development purposes.
    
    Args:
        currency_pairs: List of currency pairs (e.g., ["USD/LKR", "EUR/LKR"])
        start_date: Start date for data retrieval
        end_date: End date for data retrieval
        config: Optional configuration dictionary
        
    Returns:
        DataFrame with FX rate data
        
    Raises:
        NotImplementedError: Full implementation pending
    """
    logger.warning(
        "fetch_fx_rates: Using sample data. "
        "TODO: Implement Central Bank of Sri Lanka / financial API integration"
    )
    
    if currency_pairs is None:
        currency_pairs = MAJOR_FX_PAIRS
    
    if start_date is None:
        start_date = date.today() - timedelta(days=30)
    if end_date is None:
        end_date = date.today()
    
    # Generate sample FX data for development
    import numpy as np
    
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    
    fx_data = []
    
    # Base rates (approximate as of 2024)
    base_rates = {
        "USD/LKR": 320.0,
        "EUR/LKR": 350.0,
        "GBP/LKR": 400.0,
        "JPY/LKR": 2.2,
        "INR/LKR": 3.8,
        "AUD/LKR": 210.0,
        "CAD/LKR": 235.0
    }
    
    for pair in currency_pairs:
        if pair not in base_rates:
            logger.warning(f"Unknown currency pair: {pair}")
            continue
            
        # Generate realistic FX movements
        np.random.seed(hash(pair) % (2**32))
        base_rate = base_rates[pair]
        
        for i, current_date in enumerate(date_range):
            # Random walk for FX rate generation (lower volatility than stocks)
            change = np.random.normal(0, 0.005)  # 0.5% daily volatility
            if i == 0:
                rate = base_rate
            else:
                rate = fx_data[-1]["rate"] * (1 + change)
                rate = max(rate, base_rate * 0.5)  # Prevent unrealistic drops
            
            fx_data.append({
                "currency_pair": pair,
                "date": current_date.date(),
                "rate": round(rate, 4),
                "rate_type": "spot",
                "source": "sample_data"
            })
    
    df = pd.DataFrame(fx_data)
    logger.info(f"Generated {len(df)} FX records for {len(currency_pairs)} pairs")
    
    return df


def store_fx_rates(fx_df: pd.DataFrame, config: Dict) -> None:
    """
    Store FX rate data in database.
    
    Args:
        fx_df: DataFrame with FX rate data
        config: Application configuration
    """
    if fx_df.empty:
        logger.warning("No FX rate data to store")
        return
    
    db_manager = get_db_manager(config)
    
    logger.info(f"Storing {len(fx_df)} FX rate records")
    
    with db_manager.get_session() as session:
        try:
            for _, row in fx_df.iterrows():
                session.execute(
                    """
                    INSERT OR REPLACE INTO fx_rates
                    (currency_pair, date, rate, rate_type, source, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        row["currency_pair"],
                        row["date"],
                        row["rate"],
                        row.get("rate_type", "spot"),
                        row.get("source", "unknown"),
                        datetime.now()
                    )
                )
            
            session.commit()
            logger.info("FX rate data stored successfully")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error storing FX rate data: {e}")
            raise


def get_fx_rates(
    currency_pairs: Optional[List[str]] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    config: Optional[Dict] = None
) -> pd.DataFrame:
    """
    Retrieve FX rate data from database.
    
    Args:
        currency_pairs: List of currency pairs
        start_date: Start date for data retrieval
        end_date: End date for data retrieval
        config: Configuration dictionary
        
    Returns:
        DataFrame with FX rate data
    """
    if config is None:
        raise ValueError("Configuration required")
    
    db_manager = get_db_manager(config)
    
    conditions = []
    params = []
    
    # Build dynamic query
    if currency_pairs:
        placeholders = ",".join(["?" for _ in currency_pairs])
        conditions.append(f"currency_pair IN ({placeholders})")
        params.extend(currency_pairs)
    
    if start_date:
        conditions.append("date >= ?")
        params.append(start_date)
    
    if end_date:
        conditions.append("date <= ?")
        params.append(end_date)
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    sql = f"""
        SELECT currency_pair, date, rate, rate_type, source
        FROM fx_rates
        WHERE {where_clause}
        ORDER BY currency_pair, date
    """
    
    with db_manager.get_session() as session:
        result = session.execute(sql, params)
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
    
    return df


def fetch_and_store_fx_rates(
    currency_pairs: Optional[List[str]] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    config: Optional[Dict] = None
) -> None:
    """
    Fetch and store FX rate data in one operation.
    
    Args:
        currency_pairs: List of currency pairs
        start_date: Start date for data retrieval
        end_date: End date for data retrieval
        config: Configuration dictionary
    """
    if config is None:
        raise ValueError("Configuration required")
    
    try:
        # Fetch FX rate data
        fx_df = fetch_fx_rates(currency_pairs, start_date, end_date, config)
        
        # Store in database
        store_fx_rates(fx_df, config)
        
        logger.info(f"Successfully fetched and stored FX rate data")
        
    except Exception as e:
        logger.error(f"Error in fetch_and_store_fx_rates: {e}")
        raise


def get_latest_fx_rates(
    currency_pairs: Optional[List[str]] = None,
    config: Optional[Dict] = None
) -> pd.DataFrame:
    """
    Get latest FX rates for specified currency pairs.
    
    Args:
        currency_pairs: List of currency pairs
        config: Configuration dictionary
        
    Returns:
        DataFrame with latest FX rates
    """
    if config is None:
        raise ValueError("Configuration required")
    
    if currency_pairs is None:
        currency_pairs = MAJOR_FX_PAIRS
    
    db_manager = get_db_manager(config)
    
    placeholders = ",".join(["?" for _ in currency_pairs])
    sql = f"""
        SELECT 
            currency_pair,
            rate,
            date,
            source
        FROM fx_rates
        WHERE currency_pair IN ({placeholders})
        AND date = (
            SELECT MAX(date) 
            FROM fx_rates fx2 
            WHERE fx2.currency_pair = fx_rates.currency_pair
        )
        ORDER BY currency_pair
    """
    
    with db_manager.get_session() as session:
        result = session.execute(sql, currency_pairs)
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    
    return df


def calculate_fx_changes(
    currency_pairs: Optional[List[str]] = None,
    periods: List[int] = [1, 7, 30],
    config: Optional[Dict] = None
) -> pd.DataFrame:
    """
    Calculate FX rate changes for specified periods.
    
    Args:
        currency_pairs: List of currency pairs
        periods: List of periods for change calculation (in days)
        config: Configuration dictionary
        
    Returns:
        DataFrame with FX rate changes
    """
    if config is None:
        raise ValueError("Configuration required")
    
    if currency_pairs is None:
        currency_pairs = MAJOR_FX_PAIRS
    
    # Get recent FX data
    end_date = date.today()
    start_date = end_date - timedelta(days=max(periods) + 10)  # Buffer
    
    fx_df = get_fx_rates(currency_pairs, start_date, end_date, config)
    
    if fx_df.empty:
        logger.warning("No FX data found for change calculation")
        return pd.DataFrame()
    
    changes_data = []
    
    for pair in currency_pairs:
        pair_data = fx_df[fx_df['currency_pair'] == pair].sort_values('date')
        
        if len(pair_data) == 0:
            continue
        
        current_rate = pair_data.iloc[-1]['rate']
        
        for period in periods:
            if len(pair_data) > period:
                past_rate = pair_data.iloc[-(period+1)]['rate']
                change_pct = ((current_rate - past_rate) / past_rate) * 100
                
                changes_data.append({
                    "currency_pair": pair,
                    "period_days": period,
                    "change_percentage": round(change_pct, 2),
                    "current_rate": current_rate,
                    "past_rate": past_rate,
                    "calculation_date": pair_data.iloc[-1]['date'].date()
                })
    
    return pd.DataFrame(changes_data)


def get_fx_volatility(
    currency_pair: str,
    days: int = 30,
    config: Optional[Dict] = None
) -> float:
    """
    Calculate FX rate volatility over specified period.
    
    Args:
        currency_pair: Currency pair
        days: Number of days for volatility calculation
        config: Configuration dictionary
        
    Returns:
        Annualized volatility percentage
    """
    if config is None:
        raise ValueError("Configuration required")
    
    end_date = date.today()
    start_date = end_date - timedelta(days=days + 5)  # Buffer
    
    fx_df = get_fx_rates([currency_pair], start_date, end_date, config)
    
    if fx_df.empty or len(fx_df) < 2:
        logger.warning(f"Insufficient data for volatility calculation: {currency_pair}")
        return 0.0
    
    fx_df = fx_df.sort_values('date')
    
    # Calculate daily returns
    fx_df['daily_return'] = fx_df['rate'].pct_change()
    
    # Calculate volatility (annualized)
    daily_vol = fx_df['daily_return'].std()
    annual_vol = daily_vol * (252 ** 0.5) * 100  # Assuming 252 trading days
    
    return round(annual_vol, 2)