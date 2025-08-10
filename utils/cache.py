"""
Caching utilities for data and computation results.

Provides decorators and classes for caching expensive operations,
API responses, and computed features to improve performance.
"""

import functools
import hashlib
import json
import logging
import pickle
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Union

logger = logging.getLogger(__name__)


class FileCache:
    """
    File-based cache for storing computation results.
    """
    
    def __init__(self, cache_dir: str = "data/cache", default_ttl: int = 3600):
        """
        Initialize file cache.
        
        Args:
            cache_dir: Directory for cache files
            default_ttl: Default time-to-live in seconds
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.default_ttl = default_ttl
    
    def _get_cache_path(self, key: str) -> Path:
        """Get cache file path for a given key."""
        # Create safe filename from key
        safe_key = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{safe_key}.cache"
    
    def _get_metadata_path(self, key: str) -> Path:
        """Get metadata file path for a given key."""
        safe_key = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{safe_key}.meta"
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Store value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds
        """
        try:
            cache_path = self._get_cache_path(key)
            meta_path = self._get_metadata_path(key)
            
            # Store value
            with open(cache_path, 'wb') as f:
                pickle.dump(value, f)
            
            # Store metadata
            metadata = {
                "key": key,
                "created_at": time.time(),
                "ttl": ttl or self.default_ttl,
                "size": cache_path.stat().st_size
            }
            
            with open(meta_path, 'w') as f:
                json.dump(metadata, f)
            
            logger.debug(f"Cached value for key: {key}")
            
        except Exception as e:
            logger.error(f"Error storing cache for key {key}: {e}")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        try:
            cache_path = self._get_cache_path(key)
            meta_path = self._get_metadata_path(key)
            
            if not cache_path.exists() or not meta_path.exists():
                return None
            
            # Check metadata and expiration
            with open(meta_path, 'r') as f:
                metadata = json.load(f)
            
            created_at = metadata["created_at"]
            ttl = metadata["ttl"]
            
            if time.time() - created_at > ttl:
                # Expired, clean up
                self.delete(key)
                return None
            
            # Load and return value
            with open(cache_path, 'rb') as f:
                value = pickle.load(f)
            
            logger.debug(f"Cache hit for key: {key}")
            return value
            
        except Exception as e:
            logger.error(f"Error retrieving cache for key {key}: {e}")
            return None
    
    def delete(self, key: str) -> None:
        """
        Delete cached value.
        
        Args:
            key: Cache key
        """
        try:
            cache_path = self._get_cache_path(key)
            meta_path = self._get_metadata_path(key)
            
            if cache_path.exists():
                cache_path.unlink()
            if meta_path.exists():
                meta_path.unlink()
                
            logger.debug(f"Deleted cache for key: {key}")
            
        except Exception as e:
            logger.error(f"Error deleting cache for key {key}: {e}")
    
    def clear(self) -> None:
        """Clear all cached values."""
        try:
            for file_path in self.cache_dir.glob("*.cache"):
                file_path.unlink()
            for file_path in self.cache_dir.glob("*.meta"):
                file_path.unlink()
                
            logger.info("Cache cleared")
            
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        try:
            cache_files = list(self.cache_dir.glob("*.cache"))
            meta_files = list(self.cache_dir.glob("*.meta"))
            
            total_size = sum(f.stat().st_size for f in cache_files)
            
            # Count expired files
            expired_count = 0
            for meta_file in meta_files:
                try:
                    with open(meta_file, 'r') as f:
                        metadata = json.load(f)
                    
                    created_at = metadata["created_at"]
                    ttl = metadata["ttl"]
                    
                    if time.time() - created_at > ttl:
                        expired_count += 1
                except:
                    continue
            
            return {
                "total_entries": len(cache_files),
                "total_size_bytes": total_size,
                "total_size_mb": total_size / (1024 * 1024),
                "expired_entries": expired_count,
                "cache_directory": str(self.cache_dir)
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}
    
    def cleanup_expired(self) -> int:
        """
        Clean up expired cache entries.
        
        Returns:
            Number of entries cleaned up
        """
        cleaned_count = 0
        
        try:
            meta_files = list(self.cache_dir.glob("*.meta"))
            
            for meta_file in meta_files:
                try:
                    with open(meta_file, 'r') as f:
                        metadata = json.load(f)
                    
                    created_at = metadata["created_at"]
                    ttl = metadata["ttl"]
                    
                    if time.time() - created_at > ttl:
                        key = metadata["key"]
                        self.delete(key)
                        cleaned_count += 1
                        
                except Exception as e:
                    logger.error(f"Error checking expiration for {meta_file}: {e}")
                    continue
            
            logger.info(f"Cleaned up {cleaned_count} expired cache entries")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error during cache cleanup: {e}")
            return 0


# Global cache instance
_global_cache: Optional[FileCache] = None


def get_cache(cache_dir: str = "data/cache", default_ttl: int = 3600) -> FileCache:
    """
    Get global cache instance.
    
    Args:
        cache_dir: Cache directory
        default_ttl: Default TTL in seconds
        
    Returns:
        FileCache instance
    """
    global _global_cache
    
    if _global_cache is None:
        _global_cache = FileCache(cache_dir, default_ttl)
    
    return _global_cache


def cache_result(ttl: int = 3600, key_prefix: str = "", use_args: bool = True):
    """
    Decorator to cache function results.
    
    Args:
        ttl: Time-to-live in seconds
        key_prefix: Prefix for cache key
        use_args: Whether to include function arguments in cache key
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        cache = get_cache()
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if use_args:
                # Create key from function name and arguments
                key_parts = [
                    key_prefix,
                    func.__module__,
                    func.__name__,
                    str(hash(str(args))),
                    str(hash(str(sorted(kwargs.items()))))
                ]
                cache_key = "_".join(filter(None, key_parts))
            else:
                cache_key = f"{key_prefix}_{func.__module__}_{func.__name__}"
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Compute and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            
            return result
        
        wrapper._cache_info = {"ttl": ttl, "key_prefix": key_prefix, "use_args": use_args}
        return wrapper
    
    return decorator


def cache_dataframe(ttl: int = 3600, key_prefix: str = "df"):
    """
    Decorator specifically for caching pandas DataFrames.
    
    Args:
        ttl: Time-to-live in seconds
        key_prefix: Prefix for cache key
        
    Returns:
        Decorated function
    """
    return cache_result(ttl=ttl, key_prefix=key_prefix, use_args=True)


def invalidate_cache(pattern: str = None) -> None:
    """
    Invalidate cache entries matching pattern.
    
    Args:
        pattern: Pattern to match cache keys (if None, clears all)
    """
    cache = get_cache()
    
    if pattern is None:
        cache.clear()
    else:
        # For pattern matching, we'd need to store keys differently
        # For now, just clear all
        logger.warning("Pattern-based cache invalidation not implemented, clearing all")
        cache.clear()


class MemoryCache:
    """
    Simple in-memory cache with TTL support.
    """
    
    def __init__(self, default_ttl: int = 3600, max_size: int = 1000):
        """
        Initialize memory cache.
        
        Args:
            default_ttl: Default time-to-live in seconds
            max_size: Maximum number of entries
        """
        self.default_ttl = default_ttl
        self.max_size = max_size
        self.cache: Dict[str, Dict[str, Any]] = {}
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Store value in memory cache."""
        # Clean up if at max size
        if len(self.cache) >= self.max_size:
            self._cleanup_expired()
            
            # If still at max size, remove oldest
            if len(self.cache) >= self.max_size:
                oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]["created_at"])
                del self.cache[oldest_key]
        
        self.cache[key] = {
            "value": value,
            "created_at": time.time(),
            "ttl": ttl or self.default_ttl
        }
    
    def get(self, key: str) -> Optional[Any]:
        """Retrieve value from memory cache."""
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        
        # Check expiration
        if time.time() - entry["created_at"] > entry["ttl"]:
            del self.cache[key]
            return None
        
        return entry["value"]
    
    def delete(self, key: str) -> None:
        """Delete cached value."""
        if key in self.cache:
            del self.cache[key]
    
    def clear(self) -> None:
        """Clear all cached values."""
        self.cache.clear()
    
    def _cleanup_expired(self) -> None:
        """Remove expired entries."""
        now = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if now - entry["created_at"] > entry["ttl"]
        ]
        
        for key in expired_keys:
            del self.cache[key]