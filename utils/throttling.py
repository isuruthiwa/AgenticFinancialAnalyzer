"""
Rate limiting utilities for API calls and web scraping.

Provides decorators and classes for implementing rate limiting to prevent
overwhelming external services and comply with usage policies.
"""

import functools
import logging
import time
from collections import defaultdict, deque
from threading import Lock
from typing import Callable, Dict, Optional

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Token bucket rate limiter for controlling API call frequency.
    """
    
    def __init__(self, calls: int, period: int):
        """
        Initialize rate limiter.
        
        Args:
            calls: Maximum number of calls allowed
            period: Time period in seconds
        """
        self.calls = calls
        self.period = period
        self.call_times: deque = deque()
        self.lock = Lock()
    
    def wait_if_needed(self) -> None:
        """
        Wait if rate limit would be exceeded.
        """
        with self.lock:
            now = time.time()
            
            # Remove old calls outside the window
            while self.call_times and self.call_times[0] <= now - self.period:
                self.call_times.popleft()
            
            # Check if we need to wait
            if len(self.call_times) >= self.calls:
                # Calculate wait time
                oldest_call = self.call_times[0]
                wait_time = oldest_call + self.period - now
                
                if wait_time > 0:
                    logger.debug(f"Rate limit reached, waiting {wait_time:.2f}s")
                    time.sleep(wait_time)
                    
                    # Clean up after waiting
                    now = time.time()
                    while self.call_times and self.call_times[0] <= now - self.period:
                        self.call_times.popleft()
            
            # Record this call
            self.call_times.append(now)
    
    def get_current_usage(self) -> Dict[str, float]:
        """
        Get current rate limiter usage statistics.
        
        Returns:
            Dictionary with usage stats
        """
        with self.lock:
            now = time.time()
            
            # Clean up old calls
            while self.call_times and self.call_times[0] <= now - self.period:
                self.call_times.popleft()
            
            current_calls = len(self.call_times)
            usage_percentage = (current_calls / self.calls) * 100
            
            next_reset = None
            if self.call_times:
                next_reset = self.call_times[0] + self.period - now
            
            return {
                "current_calls": current_calls,
                "max_calls": self.calls,
                "period_seconds": self.period,
                "usage_percentage": usage_percentage,
                "next_reset_seconds": max(0, next_reset) if next_reset else 0
            }


# Global rate limiters for different services
_rate_limiters: Dict[str, RateLimiter] = {}
_rate_limiters_lock = Lock()


def get_rate_limiter(name: str, calls: int, period: int) -> RateLimiter:
    """
    Get or create a named rate limiter.
    
    Args:
        name: Rate limiter name
        calls: Maximum calls allowed
        period: Time period in seconds
        
    Returns:
        RateLimiter instance
    """
    with _rate_limiters_lock:
        if name not in _rate_limiters:
            _rate_limiters[name] = RateLimiter(calls, period)
        return _rate_limiters[name]


def rate_limit(calls: int, period: int, name: Optional[str] = None):
    """
    Decorator to apply rate limiting to a function.
    
    Args:
        calls: Maximum number of calls allowed
        period: Time period in seconds
        name: Optional rate limiter name (defaults to function name)
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        limiter_name = name or f"{func.__module__}.{func.__name__}"
        limiter = get_rate_limiter(limiter_name, calls, period)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            limiter.wait_if_needed()
            return func(*args, **kwargs)
        
        # Add rate limiter info to function
        wrapper._rate_limiter = limiter
        wrapper._rate_limit_info = {"calls": calls, "period": period, "name": limiter_name}
        
        return wrapper
    
    return decorator


class AdaptiveRateLimiter:
    """
    Adaptive rate limiter that adjusts based on error responses.
    """
    
    def __init__(self, initial_calls: int, initial_period: int, max_calls: int):
        """
        Initialize adaptive rate limiter.
        
        Args:
            initial_calls: Initial number of calls allowed
            initial_period: Initial time period in seconds
            max_calls: Maximum calls allowed (upper bound)
        """
        self.initial_calls = initial_calls
        self.initial_period = initial_period
        self.max_calls = max_calls
        self.current_calls = initial_calls
        self.current_period = initial_period
        self.lock = Lock()
        self.limiter = RateLimiter(self.current_calls, self.current_period)
        self.error_count = 0
        self.success_count = 0
    
    def wait_if_needed(self) -> None:
        """Wait if rate limit would be exceeded."""
        self.limiter.wait_if_needed()
    
    def record_success(self) -> None:
        """Record a successful API call."""
        with self.lock:
            self.success_count += 1
            self.error_count = max(0, self.error_count - 1)  # Decay errors
            
            # Gradually increase rate if we have enough successes
            if self.success_count >= 10 and self.current_calls < self.max_calls:
                self.current_calls = min(self.max_calls, self.current_calls + 1)
                self.limiter = RateLimiter(self.current_calls, self.current_period)
                self.success_count = 0
                logger.debug(f"Increased rate limit to {self.current_calls} calls per {self.current_period}s")
    
    def record_error(self, error_type: str = "unknown") -> None:
        """
        Record an API error and adjust rate limit.
        
        Args:
            error_type: Type of error (rate_limit, server_error, etc.)
        """
        with self.lock:
            self.error_count += 1
            self.success_count = 0
            
            # Decrease rate limit on errors
            if error_type == "rate_limit" or self.error_count >= 3:
                self.current_calls = max(1, self.current_calls // 2)
                self.current_period = min(300, self.current_period * 2)  # Max 5 min period
                self.limiter = RateLimiter(self.current_calls, self.current_period)
                logger.warning(f"Decreased rate limit to {self.current_calls} calls per {self.current_period}s due to {error_type}")
                self.error_count = 0


def adaptive_rate_limit(initial_calls: int, initial_period: int, max_calls: int, name: Optional[str] = None):
    """
    Decorator for adaptive rate limiting.
    
    Args:
        initial_calls: Initial number of calls allowed
        initial_period: Initial time period in seconds
        max_calls: Maximum calls allowed
        name: Optional rate limiter name
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        limiter_name = name or f"{func.__module__}.{func.__name__}_adaptive"
        limiter = AdaptiveRateLimiter(initial_calls, initial_period, max_calls)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            limiter.wait_if_needed()
            
            try:
                result = func(*args, **kwargs)
                limiter.record_success()
                return result
            except Exception as e:
                # Classify error type
                error_type = "unknown"
                if "rate limit" in str(e).lower() or "429" in str(e):
                    error_type = "rate_limit"
                elif "server error" in str(e).lower() or "5" in str(e)[:1]:
                    error_type = "server_error"
                
                limiter.record_error(error_type)
                raise
        
        wrapper._adaptive_rate_limiter = limiter
        wrapper._rate_limit_info = {
            "initial_calls": initial_calls,
            "initial_period": initial_period,
            "max_calls": max_calls,
            "name": limiter_name,
            "adaptive": True
        }
        
        return wrapper
    
    return decorator


def get_rate_limit_status() -> Dict[str, Dict]:
    """
    Get status of all active rate limiters.
    
    Returns:
        Dictionary with rate limiter statuses
    """
    status = {}
    
    with _rate_limiters_lock:
        for name, limiter in _rate_limiters.items():
            status[name] = limiter.get_current_usage()
    
    return status


def reset_rate_limiters() -> None:
    """Reset all rate limiters."""
    with _rate_limiters_lock:
        for limiter in _rate_limiters.values():
            with limiter.lock:
                limiter.call_times.clear()
    
    logger.info("All rate limiters reset")


def sleep_with_jitter(base_delay: float, max_jitter: float = 0.1) -> None:
    """
    Sleep with random jitter to avoid thundering herd.
    
    Args:
        base_delay: Base delay in seconds
        max_jitter: Maximum jitter as fraction of base_delay
    """
    import random
    
    jitter = random.uniform(-max_jitter, max_jitter) * base_delay
    total_delay = base_delay + jitter
    
    if total_delay > 0:
        time.sleep(total_delay)