"""
Market Disclosures Data Fetcher

Fetches corporate disclosures and announcements from CSE including
price-sensitive information, regulatory filings, and company updates.
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
def fetch_disclosures(
    symbols: List[str],
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    config: Optional[Dict] = None
) -> pd.DataFrame:
    """
    Fetch corporate disclosures and announcements for specified symbols.
    
    TODO: Implement actual CSE disclosures scraping
    Currently returns empty DataFrame as placeholder.
    
    Args:
        symbols: List of stock symbols
        start_date: Start date for data retrieval
        end_date: End date for data retrieval
        config: Optional configuration dictionary
        
    Returns:
        DataFrame with disclosure data
        
    Raises:
        NotImplementedError: Full implementation pending
    """
    logger.warning(
        f"fetch_disclosures: Stub implementation for {len(symbols)} symbols. "
        "TODO: Implement CSE disclosures scraping"
    )
    
    # Return empty DataFrame for now
    # TODO: Implement actual disclosures fetching logic
    columns = [
        "symbol", "announcement_date", "time_published", "category",
        "title", "content", "url", "sentiment_score"
    ]
    
    return pd.DataFrame(columns=columns)


def classify_disclosure_category(title: str, content: str) -> str:
    """
    Classify disclosure category based on title and content.
    
    Args:
        title: Disclosure title
        content: Disclosure content
        
    Returns:
        Classified category
    """
    title_lower = title.lower()
    content_lower = content.lower()
    
    # Price-sensitive categories
    if any(keyword in title_lower for keyword in ["results", "financial", "quarterly", "annual"]):
        return "financial_results"
    elif any(keyword in title_lower for keyword in ["acquisition", "merger", "takeover"]):
        return "corporate_action"
    elif any(keyword in title_lower for keyword in ["dividend", "bonus", "rights"]):
        return "dividend_announcement"
    elif any(keyword in title_lower for keyword in ["director", "appointment", "resignation"]):
        return "board_changes"
    elif any(keyword in title_lower for keyword in ["contract", "agreement", "deal"]):
        return "business_update"
    elif any(keyword in title_lower for keyword in ["suspension", "halt", "delisting"]):
        return "trading_update"
    else:
        return "general"


def calculate_sentiment_score(title: str, content: str) -> Optional[float]:
    """
    Calculate sentiment score for disclosure content.
    
    TODO: Implement proper sentiment analysis using NLP models
    
    Args:
        title: Disclosure title
        content: Disclosure content
        
    Returns:
        Sentiment score between -1 (negative) and 1 (positive)
    """
    # Simple keyword-based sentiment (placeholder)
    # TODO: Replace with proper sentiment analysis model
    
    positive_keywords = ["profit", "growth", "increase", "expansion", "success", "positive"]
    negative_keywords = ["loss", "decline", "decrease", "closure", "negative", "suspension"]
    
    text = (title + " " + content).lower()
    
    positive_count = sum(1 for keyword in positive_keywords if keyword in text)
    negative_count = sum(1 for keyword in negative_keywords if keyword in text)
    
    if positive_count + negative_count == 0:
        return 0.0
    
    sentiment = (positive_count - negative_count) / (positive_count + negative_count)
    return round(sentiment, 2)


def store_disclosures(disclosures_df: pd.DataFrame, config: Dict) -> None:
    """
    Store disclosure data in database.
    
    Args:
        disclosures_df: DataFrame with disclosure data
        config: Application configuration
    """
    if disclosures_df.empty:
        logger.info("No disclosure data to store")
        return
    
    db_manager = get_db_manager(config)
    
    logger.info(f"Storing {len(disclosures_df)} disclosure records")
    
    with db_manager.get_session() as session:
        try:
            for _, row in disclosures_df.iterrows():
                session.execute(
                    """
                    INSERT OR REPLACE INTO announcements
                    (symbol, announcement_date, time_published, category,
                     title, content, url, sentiment_score, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        row["symbol"],
                        row["announcement_date"],
                        row.get("time_published"),
                        row.get("category", "general"),
                        row["title"],
                        row.get("content", ""),
                        row.get("url", ""),
                        row.get("sentiment_score"),
                        datetime.now()
                    )
                )
            
            session.commit()
            logger.info("Disclosure data stored successfully")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error storing disclosure data: {e}")
            raise


def fetch_and_store_disclosures(
    symbols: List[str],
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    config: Optional[Dict] = None
) -> None:
    """
    Fetch and store disclosure data in one operation.
    
    Args:
        symbols: List of stock symbols
        start_date: Start date for data retrieval
        end_date: End date for data retrieval
        config: Configuration dictionary
    """
    if config is None:
        raise ValueError("Configuration required")
    
    try:
        # Fetch disclosure data
        disclosures_df = fetch_disclosures(symbols, start_date, end_date, config)
        
        # Process disclosures
        if not disclosures_df.empty:
            disclosures_df["category"] = disclosures_df.apply(
                lambda row: classify_disclosure_category(row["title"], row.get("content", "")),
                axis=1
            )
            disclosures_df["sentiment_score"] = disclosures_df.apply(
                lambda row: calculate_sentiment_score(row["title"], row.get("content", "")),
                axis=1
            )
        
        # Store in database
        store_disclosures(disclosures_df, config)
        
        logger.info(f"Successfully processed disclosures for {len(symbols)} symbols")
        
    except Exception as e:
        logger.error(f"Error in fetch_and_store_disclosures: {e}")
        raise


def get_recent_disclosures(
    symbols: List[str],
    days: int = 30,
    config: Optional[Dict] = None
) -> pd.DataFrame:
    """
    Get recent disclosures for specified symbols.
    
    Args:
        symbols: List of stock symbols
        days: Number of days to look back
        config: Configuration dictionary
        
    Returns:
        DataFrame with recent disclosures
    """
    if config is None:
        raise ValueError("Configuration required")
    
    end_date = date.today()
    start_date = date.today().replace(day=end_date.day - days)
    
    db_manager = get_db_manager(config)
    
    placeholders = ",".join(["?" for _ in symbols])
    sql = f"""
        SELECT symbol, announcement_date, category, title, sentiment_score
        FROM announcements
        WHERE symbol IN ({placeholders})
        AND announcement_date BETWEEN ? AND ?
        ORDER BY announcement_date DESC, symbol
    """
    
    params = symbols + [start_date, end_date]
    
    with db_manager.get_session() as session:
        result = session.execute(sql, params)
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    
    return df