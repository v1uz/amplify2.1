"""
Cache management utility module.
This module provides functionality for managing application caches.
"""

import logging
from app import cache

# Set up logging
logger = logging.getLogger(__name__)

def clear_cache():
    """
    Clear the entire application cache.
    
    Returns:
        int: Number of items cleared from the cache
    """
    count = len(cache)
    cache.clear()
    logger.info(f"Cleared {count} items from cache")
    return count

def get_cache_stats():
    """
    Get statistics about the current cache usage.
    
    Returns:
        dict: Dictionary containing cache statistics
    """
    return {
        'size': len(cache),
        'maxsize': cache.maxsize,
        'currsize': cache.currsize,
        'usage_percentage': (len(cache) / cache.maxsize) * 100 if cache.maxsize > 0 else 0
    }

def remove_from_cache(key):
    """
    Remove a specific item from the cache.
    
    Args:
        key (str): The cache key to remove
        
    Returns:
        bool: True if the item was removed, False if it wasn't in the cache
    """
    if key in cache:
        del cache[key]
        logger.info(f"Removed {key} from cache")
        return True
    logger.warning(f"Key not found in cache: {key}")
    return False

def update_ttl(seconds):
    """
    Update the TTL (time-to-live) for the cache.
    Note: This affects only new cache entries, not existing ones.
    
    Args:
        seconds (int): New TTL in seconds
        
    Returns:
        int: The new TTL value
    """
    from cachetools import TTLCache
    import copy
    
    global cache
    
    # Create a new cache with the updated TTL
    new_cache = TTLCache(maxsize=cache.maxsize, ttl=seconds)
    
    # Copy existing entries that haven't expired
    for key, value in cache.items():
        new_cache[key] = value
        
    # Replace the old cache with the new one
    cache = new_cache
    
    logger.info(f"Updated cache TTL to {seconds} seconds")
    return seconds