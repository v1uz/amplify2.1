"""
Cache management utilities for the Amplify SEO application.
"""
import time
import threading
import json
import os
import hashlib
from typing import Dict, Any, Optional, Union, Callable
import logging

logger = logging.getLogger(__name__)

class CacheManager:
    """Simple in-memory and file-based cache manager with TTL."""
    
    def __init__(self, cache_dir: str = 'cache', default_ttl: int = 3600, max_memory_items: int = 1000, start_cleanup_thread: bool = True):
        """
        Initialize the cache manager.
        
        Args:
            cache_dir: Directory for file-based cache
            default_ttl: Default time-to-live in seconds
            max_memory_items: Maximum number of items to keep in memory
        """
        self.memory_cache = {}
        self.cache_timestamps = {}
        self.default_ttl = default_ttl
        self.max_memory_items = max_memory_items
        self.cache_dir = cache_dir
        
        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)
        
        # Lock for thread-safety
        self.lock = threading.RLock()
        
        # Start cleanup thread
        if start_cleanup_thread:
            self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
            self.cleanup_thread.start()
    
    def _cleanup_loop(self) -> None:
        """Background thread to periodically clean up expired cache items."""
        while True:
            try:
                self.cleanup()
            except Exception as e:
                logger.error(f"Error in cache cleanup: {e}")
            # Sleep for 5 minutes
            time.sleep(300)
    
    def _generate_key(self, key: str) -> str:
        """
        Generate a standardized cache key.
        
        Args:
            key: Original cache key
            
        Returns:
            Standardized cache key
        """
        # Convert key to string if it's not already
        if not isinstance(key, str):
            key = str(key)
            
        # Generate a hash for the key to ensure it's safe for filenames
        return hashlib.md5(key.encode()).hexdigest()
    
    def _get_cache_path(self, key: str) -> str:
        """
        Get the filesystem path for a cache key.
        
        Args:
            key: Cache key
            
        Returns:
            Path to cache file
        """
        hashed_key = self._generate_key(key)
        return os.path.join(self.cache_dir, f"{hashed_key}.json")
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None, expiry: Optional[int] = None) -> None:
        with self.lock:
            # Handle expiry alias for ttl
            if ttl is None and expiry is not None:
                ttl = expiry
                
            # Use default TTL if not specified
            if ttl is None:
                ttl = self.default_ttl
                
            # Get standardized key
            std_key = self._generate_key(key)
            
            # Set expiration timestamp
            expiration = time.time() + ttl
            
            # Store in memory cache
            self.memory_cache[std_key] = value
            self.cache_timestamps[std_key] = expiration
            
            # Check if we need to clean up memory cache
            if len(self.memory_cache) > self.max_memory_items:
                self._cleanup_memory_cache()
                
            # Also store in file cache for persistence
            try:
                cache_data = {
                    'value': value,
                    'expiration': expiration
                }
                
                cache_path = self._get_cache_path(key)
                with open(cache_path, 'w') as f:
                    json.dump(cache_data, f)
            except Exception as e:
                logger.error(f"Failed to write to file cache: {e}")
        
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            default: Default value if key not found or expired
            
        Returns:
            Cached value or default
        """
        with self.lock:
            # Get standardized key
            std_key = self._generate_key(key)
            
            # Check memory cache first
            if std_key in self.memory_cache:
                # Check if expired
                if self.cache_timestamps[std_key] > time.time():
                    return self.memory_cache[std_key]
                else:
                    # Expired, remove from memory
                    del self.memory_cache[std_key]
                    del self.cache_timestamps[std_key]
            
            # Not in memory or expired, check file cache
            try:
                cache_path = self._get_cache_path(key)
                if os.path.exists(cache_path):
                    with open(cache_path, 'r') as f:
                        cache_data = json.load(f)
                    
                    # Check if expired
                    if cache_data['expiration'] > time.time():
                        # Add to memory cache for faster access next time
                        self.memory_cache[std_key] = cache_data['value']
                        self.cache_timestamps[std_key] = cache_data['expiration']
                        return cache_data['value']
                    else:
                        # Expired, remove file
                        os.remove(cache_path)
            except Exception as e:
                logger.error(f"Failed to read from file cache: {e}")
            
            # Not found or expired
            return default
    
    def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if deleted, False if not found
        """
        with self.lock:
            # Get standardized key
            std_key = self._generate_key(key)
            
            # Delete from memory cache
            found_memory = False
            if std_key in self.memory_cache:
                del self.memory_cache[std_key]
                del self.cache_timestamps[std_key]
                found_memory = True
            
            # Delete from file cache
            found_file = False
            try:
                cache_path = self._get_cache_path(key)
                if os.path.exists(cache_path):
                    os.remove(cache_path)
                    found_file = True
            except Exception as e:
                logger.error(f"Failed to delete from file cache: {e}")
            
            return found_memory or found_file
    
    def exists(self, key: str) -> bool:
        """
        Check if a key exists in the cache and is not expired.
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists and is not expired
        """
        with self.lock:
            # Get standardized key
            std_key = self._generate_key(key)
            
            # Check memory cache first
            if std_key in self.memory_cache:
                # Check if expired
                if self.cache_timestamps[std_key] > time.time():
                    return True
                else:
                    # Expired, remove from memory
                    del self.memory_cache[std_key]
                    del self.cache_timestamps[std_key]
            
            # Not in memory or expired, check file cache
            try:
                cache_path = self._get_cache_path(key)
                if os.path.exists(cache_path):
                    with open(cache_path, 'r') as f:
                        cache_data = json.load(f)
                    
                    # Check if expired
                    if cache_data['expiration'] > time.time():
                        # Add to memory cache for faster access next time
                        self.memory_cache[std_key] = cache_data['value']
                        self.cache_timestamps[std_key] = cache_data['expiration']
                        return True
                    else:
                        # Expired, remove file
                        os.remove(cache_path)
            except Exception:
                pass
            
            # Not found or expired
            return False
    
    def clear(self) -> None:
        """Clear all cache items from memory and disk."""
        with self.lock:
            # Clear memory cache
            self.memory_cache.clear()
            self.cache_timestamps.clear()
            
            # Clear file cache
            try:
                for filename in os.listdir(self.cache_dir):
                    if filename.endswith('.json'):
                        os.remove(os.path.join(self.cache_dir, filename))
            except Exception as e:
                logger.error(f"Failed to clear file cache: {e}")
                
                
    def cleanup(self) -> int:
        with self.lock:
            count = 0
            
            # Clean up memory cache
            current_time = time.time()
            expired_keys = [k for k, t in self.cache_timestamps.items() if t <= current_time]
            for key in expired_keys:
                if key in self.memory_cache:
                    del self.memory_cache[key]
                    del self.cache_timestamps[key]
                    count += 1
            
            # Clean up file cache
            try:
                if not os.path.exists(self.cache_dir):
                    os.makedirs(self.cache_dir, exist_ok=True)
                    return count
                    
                for filename in os.listdir(self.cache_dir):
                    if filename.endswith('.json'):
                        filepath = os.path.join(self.cache_dir, filename)
                        try:
                            if not os.path.exists(filepath):
                                continue
                                
                            with open(filepath, 'r') as f:
                                cache_data = json.load(f)
                            
                            if cache_data['expiration'] <= current_time:
                                if os.path.exists(filepath):  # Double-check it still exists
                                    os.remove(filepath)
                                    count += 1
                        except (FileNotFoundError, json.JSONDecodeError) as e:
                            # File might have been removed by another process
                            logger.debug(f"Skipping cache file {filename}: {str(e)}")
                            continue
                        except Exception as e:
                            # Other errors: log but continue processing other files
                            logger.debug(f"Error processing cache file {filename}: {str(e)}")
                            continue
            except Exception as e:
                logger.error(f"Failed to clean up file cache: {str(e)}")
            
            return count     
                    
    def cached(self, ttl: Optional[int] = None) -> Callable:
        """
        Decorator for caching function results.
        
        Args:
            ttl: Time-to-live in seconds (None for default)
            
        Returns:
            Decorator function
        """
        def decorator(func: Callable) -> Callable:
            def wrapper(*args, **kwargs) -> Any:
                # Generate cache key from function name and arguments
                key_parts = [func.__name__]
                key_parts.extend([str(arg) for arg in args])
                key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
                cache_key = ":".join(key_parts)
                
                # Check if result is in cache
                cached_result = self.get(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # Call function and cache result
                result = func(*args, **kwargs)
                self.set(cache_key, result, ttl)
                return result
            
            return wrapper
        
        return decorator


# Create a global instance for convenience
cache = CacheManager()