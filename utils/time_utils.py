"""
Time utilities for date/time operations and market calendar handling.

Provides helper functions for working with trading days, date ranges,
and time zone conversions for the Sri Lankan market.
"""

import logging
from datetime import date, datetime, timedelta
from typing import List, Optional, Tuple

import pandas as pd
from dateutil import parser as date_parser

logger = logging.getLogger(__name__)

# Sri Lanka holidays (major public holidays that affect trading)
# Note: This is a simplified list - real implementation should use a comprehensive holiday calendar
SRI_LANKA_HOLIDAYS = [
    # Fixed holidays
    "01-01",  # New Year's Day
    "02-04",  # Independence Day
    "05-01",  # May Day
    "12-25",  # Christmas Day
    "12-31",  # New Year's Eve
    
    # Note: Buddhist holidays, Hindu holidays, and Islamic holidays vary by year
    # TODO: Implement proper holiday calendar with lunar calendar calculations
]


def is_trading_day(check_date: date) -> bool:
    """
    Check if a given date is a trading day on CSE.
    
    Args:
        check_date: Date to check
        
    Returns:
        True if it's a trading day, False otherwise
    """
    # Check if it's a weekend (Saturday = 5, Sunday = 6)
    if check_date.weekday() >= 5:
        return False
    
    # Check if it's a public holiday
    date_str = check_date.strftime("%m-%d")
    if date_str in SRI_LANKA_HOLIDAYS:
        return False
    
    # TODO: Add more sophisticated holiday checking
    # For now, assume all weekdays are trading days except listed holidays
    return True


def get_trading_days(start_date: date, end_date: date) -> List[date]:
    """
    Get list of trading days between start and end dates.
    
    Args:
        start_date: Start date (inclusive)
        end_date: End date (inclusive)
        
    Returns:
        List of trading days
    """
    trading_days = []
    current_date = start_date
    
    while current_date <= end_date:
        if is_trading_day(current_date):
            trading_days.append(current_date)
        current_date += timedelta(days=1)
    
    return trading_days


def get_last_trading_day(reference_date: Optional[date] = None) -> date:
    """
    Get the last trading day before or on the reference date.
    
    Args:
        reference_date: Reference date (defaults to today)
        
    Returns:
        Last trading day
    """
    if reference_date is None:
        reference_date = date.today()
    
    current_date = reference_date
    
    # Look back up to 10 days to find a trading day
    for _ in range(10):
        if is_trading_day(current_date):
            return current_date
        current_date -= timedelta(days=1)
    
    # If no trading day found in last 10 days, something is wrong
    logger.warning(f"No trading day found within 10 days of {reference_date}")
    return reference_date


def get_next_trading_day(reference_date: Optional[date] = None) -> date:
    """
    Get the next trading day after the reference date.
    
    Args:
        reference_date: Reference date (defaults to today)
        
    Returns:
        Next trading day
    """
    if reference_date is None:
        reference_date = date.today()
    
    current_date = reference_date + timedelta(days=1)
    
    # Look forward up to 10 days to find a trading day
    for _ in range(10):
        if is_trading_day(current_date):
            return current_date
        current_date += timedelta(days=1)
    
    # If no trading day found in next 10 days, something is wrong
    logger.warning(f"No trading day found within 10 days after {reference_date}")
    return reference_date + timedelta(days=1)


def get_trading_days_back(num_days: int, from_date: Optional[date] = None) -> List[date]:
    """
    Get specified number of trading days going back from a reference date.
    
    Args:
        num_days: Number of trading days to get
        from_date: Reference date (defaults to today)
        
    Returns:
        List of trading days in chronological order
    """
    if from_date is None:
        from_date = date.today()
    
    trading_days = []
    current_date = from_date
    
    # Look back up to num_days * 2 calendar days to account for weekends/holidays
    max_search_days = num_days * 2 + 20
    
    for _ in range(max_search_days):
        if is_trading_day(current_date):
            trading_days.append(current_date)
            
            if len(trading_days) >= num_days:
                break
        
        current_date -= timedelta(days=1)
    
    # Return in chronological order (oldest first)
    return list(reversed(trading_days))


def get_trading_days_forward(num_days: int, from_date: Optional[date] = None) -> List[date]:
    """
    Get specified number of trading days going forward from a reference date.
    
    Args:
        num_days: Number of trading days to get
        from_date: Reference date (defaults to today)
        
    Returns:
        List of trading days in chronological order
    """
    if from_date is None:
        from_date = date.today()
    
    trading_days = []
    current_date = from_date
    
    # Look forward up to num_days * 2 calendar days
    max_search_days = num_days * 2 + 20
    
    for _ in range(max_search_days):
        if is_trading_day(current_date):
            trading_days.append(current_date)
            
            if len(trading_days) >= num_days:
                break
        
        current_date += timedelta(days=1)
    
    return trading_days


def parse_date_string(date_string: str) -> Optional[date]:
    """
    Parse various date string formats into date object.
    
    Args:
        date_string: Date string to parse
        
    Returns:
        Parsed date or None if parsing failed
    """
    try:
        parsed_date = date_parser.parse(date_string)
        return parsed_date.date()
    except Exception as e:
        logger.error(f"Error parsing date string '{date_string}': {e}")
        return None


def format_date_for_display(date_obj: date) -> str:
    """
    Format date for display purposes.
    
    Args:
        date_obj: Date to format
        
    Returns:
        Formatted date string
    """
    return date_obj.strftime("%Y-%m-%d")


def get_quarter_dates(year: int, quarter: int) -> Tuple[date, date]:
    """
    Get start and end dates for a given quarter.
    
    Args:
        year: Year
        quarter: Quarter (1-4)
        
    Returns:
        Tuple of (start_date, end_date)
    """
    if quarter not in [1, 2, 3, 4]:
        raise ValueError("Quarter must be 1, 2, 3, or 4")
    
    quarter_starts = {
        1: (1, 1),   # Jan 1
        2: (4, 1),   # Apr 1
        3: (7, 1),   # Jul 1
        4: (10, 1)   # Oct 1
    }
    
    quarter_ends = {
        1: (3, 31),   # Mar 31
        2: (6, 30),   # Jun 30
        3: (9, 30),   # Sep 30
        4: (12, 31)   # Dec 31
    }
    
    start_month, start_day = quarter_starts[quarter]
    end_month, end_day = quarter_ends[quarter]
    
    start_date = date(year, start_month, start_day)
    end_date = date(year, end_month, end_day)
    
    return start_date, end_date


def get_financial_year_dates(year: int, start_month: int = 4) -> Tuple[date, date]:
    """
    Get start and end dates for a financial year.
    
    Args:
        year: Year (start year of financial year)
        start_month: Starting month of financial year (default: April)
        
    Returns:
        Tuple of (start_date, end_date)
    """
    start_date = date(year, start_month, 1)
    
    # End date is March 31 of next year (for April start)
    if start_month == 1:
        end_date = date(year, 12, 31)
    else:
        end_date = date(year + 1, start_month - 1, 31)
        # Handle February
        if start_month - 1 == 2:
            # Check for leap year
            if (year + 1) % 4 == 0 and ((year + 1) % 100 != 0 or (year + 1) % 400 == 0):
                end_date = date(year + 1, 2, 29)
            else:
                end_date = date(year + 1, 2, 28)
    
    return start_date, end_date


def calculate_trading_days_between(start_date: date, end_date: date) -> int:
    """
    Calculate number of trading days between two dates.
    
    Args:
        start_date: Start date (inclusive)
        end_date: End date (inclusive)
        
    Returns:
        Number of trading days
    """
    return len(get_trading_days(start_date, end_date))


def add_trading_days(start_date: date, num_days: int) -> date:
    """
    Add specified number of trading days to a date.
    
    Args:
        start_date: Starting date
        num_days: Number of trading days to add
        
    Returns:
        Resulting date after adding trading days
    """
    trading_days = get_trading_days_forward(num_days + 1, start_date)
    
    if len(trading_days) > num_days:
        return trading_days[num_days]
    else:
        logger.warning(f"Could not find {num_days} trading days forward from {start_date}")
        return start_date + timedelta(days=num_days)


def subtract_trading_days(start_date: date, num_days: int) -> date:
    """
    Subtract specified number of trading days from a date.
    
    Args:
        start_date: Starting date
        num_days: Number of trading days to subtract
        
    Returns:
        Resulting date after subtracting trading days
    """
    trading_days = get_trading_days_back(num_days + 1, start_date)
    
    if len(trading_days) > num_days:
        return trading_days[-(num_days + 1)]
    else:
        logger.warning(f"Could not find {num_days} trading days back from {start_date}")
        return start_date - timedelta(days=num_days)


def get_market_time_sri_lanka() -> datetime:
    """
    Get current market time in Sri Lanka timezone.
    
    Returns:
        Current datetime in Sri Lanka timezone
    """
    # Sri Lanka is UTC+5:30
    # For simplicity, we'll use local time
    # TODO: Implement proper timezone handling with pytz
    return datetime.now()


def is_market_open(check_time: Optional[datetime] = None) -> bool:
    """
    Check if CSE market is currently open.
    
    Args:
        check_time: Time to check (defaults to current time)
        
    Returns:
        True if market is open, False otherwise
    """
    if check_time is None:
        check_time = get_market_time_sri_lanka()
    
    # Check if it's a trading day
    if not is_trading_day(check_time.date()):
        return False
    
    # CSE trading hours: 9:30 AM to 2:30 PM Sri Lanka time
    market_open = check_time.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = check_time.replace(hour=14, minute=30, second=0, microsecond=0)
    
    return market_open <= check_time <= market_close


def get_date_range_for_period(period: str, reference_date: Optional[date] = None) -> Tuple[date, date]:
    """
    Get date range for common period descriptions.
    
    Args:
        period: Period description ('1M', '3M', '6M', '1Y', '2Y', etc.)
        reference_date: Reference date (defaults to today)
        
    Returns:
        Tuple of (start_date, end_date)
    """
    if reference_date is None:
        reference_date = date.today()
    
    period_upper = period.upper()
    
    if period_upper.endswith('D'):
        days = int(period_upper[:-1])
        start_date = reference_date - timedelta(days=days)
    elif period_upper.endswith('M'):
        months = int(period_upper[:-1])
        start_date = reference_date - timedelta(days=months * 30)  # Approximate
    elif period_upper.endswith('Y'):
        years = int(period_upper[:-1])
        start_date = reference_date - timedelta(days=years * 365)  # Approximate
    else:
        raise ValueError(f"Unsupported period format: {period}")
    
    return start_date, reference_date