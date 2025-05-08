import os
import time
import hashlib
import logging
import json
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta
from diskcache import Cache, FanoutCache

# Setup logger
logger = logging.getLogger(__name__)

# Default cache settings
DEFAULT_CACHE_DIR = os.path.join(os.path.expanduser("~"), ".ytpro_cache")
DEFAULT_TTL = 60 * 60 * 24 * 30  # 30 days in seconds
DEFAULT_SIZE_LIMIT = 1024 * 1024 * 1024  # 1 GB


class CacheType(Enum):
    """Enum for different types of cache data"""
    TRANSCRIPTION = auto()
    TRANSLATION = auto()
    DOWNLOAD = auto()
    METADATA = auto()


class CacheStats:
    """Class to track cache statistics"""
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.stores = 0
        self.deletes = 0
        self.errors = 0
        self.last_access = None
        self.last_store = None
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary"""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "stores": self.stores,
            "deletes": self.deletes,
            "errors": self.errors,
            "hit_ratio": self.hit_ratio,
            "last_access": self.last_access,
            "last_store": self.last_store
        }
    
    @property
    def hit_ratio(self) -> float:
        """Calculate cache hit ratio"""
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return self.hits / total


class CacheManager:
    """
    Manages multiple cache types for the application.
    Provides methods for storing, retrieving, and managing cached data.
    """
    
    def __init__(self, base_dir: str = DEFAULT_CACHE_DIR, ttl: int = DEFAULT_TTL, size_limit: int = DEFAULT_SIZE_LIMIT):
        """
        Initialize the cache manager.
        
        Args:
            base_dir: Base directory for all caches
            ttl: Default time-to-live for cache items in seconds
            size_limit: Maximum size of the cache in bytes
        """
        self.base_dir = base_dir
        self.default_ttl = ttl
        self.size_limit = size_limit
        self.stats = {cache_type: CacheStats() for cache_type in CacheType}
        self._create_caches()
        
        # Initialize statistics and metadata
        self._init_metadata()
        logger.info(f"Cache initialized at {base_dir} with TTL {ttl}s and size limit {size_limit/1024/1024:.1f}MB")
    
    def _create_caches(self):
        """Initialize all cache instances"""
        os.makedirs(self.base_dir, exist_ok=True)
        
        # Create a separate cache for each type with sharding for better performance
        self.caches = {}
        for cache_type in CacheType:
            cache_dir = os.path.join(self.base_dir, cache_type.name.lower())
            self.caches[cache_type] = FanoutCache(
                directory=cache_dir,
                size_limit=self.size_limit,
                eviction_policy='least-recently-used'
            )
    
    def _init_metadata(self):
        """Initialize cache metadata"""
        metadata_cache = self.caches[CacheType.METADATA]
        
        # Set initial metadata if it doesn't exist
        if 'created_at' not in metadata_cache:
            metadata_cache['created_at'] = datetime.now().isoformat()
            metadata_cache['access_count'] = 0
            metadata_cache['last_cleanup'] = None
    
    def _update_metadata(self, key: str, value: Any):
        """Update a specific metadata value"""
        metadata_cache = self.caches[CacheType.METADATA]
        metadata_cache[key] = value
    
    def _get_metadata(self, key: str, default: Any = None) -> Any:
        """Get a specific metadata value"""
        metadata_cache = self.caches[CacheType.METADATA]
        return metadata_cache.get(key, default)
    
    def _get_cache_key(self, data_key: str, params: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a unique cache key based on the data key and optional parameters.
        
        Args:
            data_key: Primary key (e.g., YouTube URL)
            params: Additional parameters affecting the cached content
            
        Returns:
            A unique hash-based key
        """
        # Start with the main key
        key_parts = [data_key]
        
        # Add sorted parameters if provided
        if params:
            for k, v in sorted(params.items()):
                key_parts.append(f"{k}={v}")
        
        # Join and hash to get a consistent key
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode('utf-8')).hexdigest()
    
    def get(self, cache_type: CacheType, key: str, params: Optional[Dict[str, Any]] = None) -> Optional[Any]:
        """
        Retrieve data from the cache.
        
        Args:
            cache_type: Type of cache to use
            key: Primary key to look up
            params: Additional parameters affecting the cached content
            
        Returns:
            The cached data or None if not found/expired
        """
        cache_key = self._get_cache_key(key, params)
        cache = self.caches[cache_type]
        
        try:
            result = cache.get(cache_key)
            
            if result is not None:
                # Update stats and metadata
                self.stats[cache_type].hits += 1
                self.stats[cache_type].last_access = datetime.now().isoformat()
                if cache_type != CacheType.METADATA:
                    access_count = self._get_metadata('access_count', 0)
                    self._update_metadata('access_count', access_count + 1)
                    self._update_metadata('last_access', datetime.now().isoformat())
                
                logger.debug(f"Cache hit for {cache_type.name}:{cache_key[:8]}")
                return result
            else:
                # Update miss stats
                self.stats[cache_type].misses += 1
                logger.debug(f"Cache miss for {cache_type.name}:{cache_key[:8]}")
                return None
                
        except Exception as e:
            self.stats[cache_type].errors += 1
            logger.error(f"Error retrieving from cache {cache_type.name}: {str(e)}")
            return None
    
    def store(self, cache_type: CacheType, key: str, data: Any, params: Optional[Dict[str, Any]] = None, 
              ttl: Optional[int] = None) -> bool:
        """
        Store data in the cache.
        
        Args:
            cache_type: Type of cache to use
            key: Primary key for the data
            data: The data to store
            params: Additional parameters affecting the cached content
            ttl: Time-to-live in seconds (uses default if None)
            
        Returns:
            True if storage was successful, False otherwise
        """
        cache_key = self._get_cache_key(key, params)
        cache = self.caches[cache_type]
        actual_ttl = ttl if ttl is not None else self.default_ttl
        
        try:
            success = cache.set(cache_key, data, expire=actual_ttl)
            
            if success:
                # Update stats
                self.stats[cache_type].stores += 1
                self.stats[cache_type].last_store = datetime.now().isoformat()
                if cache_type != CacheType.METADATA:
                    self._update_metadata('last_store', datetime.now().isoformat())
                
                logger.debug(f"Stored in cache {cache_type.name}:{cache_key[:8]} with TTL {actual_ttl}s")
                return True
            else:
                logger.warning(f"Failed to store in cache {cache_type.name}:{cache_key[:8]}")
                return False
                
        except Exception as e:
            self.stats[cache_type].errors += 1
            logger.error(f"Error storing in cache {cache_type.name}: {str(e)}")
            return False
    
    def delete(self, cache_type: CacheType, key: str, params: Optional[Dict[str, Any]] = None) -> bool:
        """
        Delete an item from the cache.
        
        Args:
            cache_type: Type of cache to use
            key: Primary key to delete
            params: Additional parameters affecting the cached content
            
        Returns:
            True if deletion was successful, False otherwise
        """
        cache_key = self._get_cache_key(key, params)
        cache = self.caches[cache_type]
        
        try:
            deleted = cache.delete(cache_key)
            
            if deleted:
                self.stats[cache_type].deletes += 1
                logger.debug(f"Deleted from cache {cache_type.name}:{cache_key[:8]}")
            
            return deleted
            
        except Exception as e:
            self.stats[cache_type].errors += 1
            logger.error(f"Error deleting from cache {cache_type.name}: {str(e)}")
            return False
    
    def clear(self, cache_type: Optional[CacheType] = None) -> bool:
        """
        Clear the entire cache or a specific cache type.
        
        Args:
            cache_type: Type of cache to clear, or None to clear all
            
        Returns:
            True if clearing was successful, False otherwise
        """
        try:
            if cache_type is None:
                # Clear all caches except metadata
                for ct in CacheType:
                    if ct != CacheType.METADATA:
                        self.caches[ct].clear()
                        self.stats[ct].deletes += 1
                
                logger.info("Cleared all caches")
                return True
            else:
                # Clear only the specified cache
                self.caches[cache_type].clear()
                self.stats[cache_type].deletes += 1
                
                logger.info(f"Cleared cache {cache_type.name}")
                return True
                
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            return False
    
    def cleanup(self, max_age: Optional[int] = None) -> Tuple[int, int]:
        """
        Clean up old cache entries based on age.
        
        Args:
            max_age: Maximum age of entries in seconds, uses default TTL if None
            
        Returns:
            Tuple of (total items before cleanup, items removed)
        """
        max_age_seconds = max_age if max_age is not None else self.default_ttl
        items_before = 0
        items_removed = 0
        
        for cache_type in CacheType:
            if cache_type == CacheType.METADATA:
                continue
                
            cache = self.caches[cache_type]
            try:
                type_before = len(cache)
                items_before += type_before
                
                # Use the diskcache's built-in expire mechanism
                expired = cache.expire()
                items_removed += expired
                
                logger.debug(f"Expired {expired} items from {cache_type.name} cache")
                
            except Exception as e:
                self.stats[cache_type].errors += 1
                logger.error(f"Error during cleanup of {cache_type.name} cache: {str(e)}")
        
        # Update metadata
        self._update_metadata('last_cleanup', datetime.now().isoformat())
        logger.info(f"Cache cleanup removed {items_removed} of {items_before} items")
        
        return items_before, items_removed
    
    def get_size(self, cache_type: Optional[CacheType] = None) -> int:
        """
        Get the size of the cache(s) in bytes.
        
        Args:
            cache_type: Type of cache to check, or None to get total size
            
        Returns:
            Size in bytes
        """
        try:
            if cache_type is None:
                # Sum the size of all caches
                total_size = 0
                for ct in CacheType:
                    cache = self.caches[ct]
                    total_size += cache.volume()
                return total_size
            else:
                # Get size of specific cache
                return self.caches[cache_type].volume()
                
        except Exception as e:
            logger.error(f"Error getting cache size: {str(e)}")
            return 0
    
    def get_count(self, cache_type: Optional[CacheType] = None) -> int:
        """
        Get the number of items in the cache(s).
        
        Args:
            cache_type: Type of cache to check, or None to get total count
            
        Returns:
            Number of items
        """
        try:
            if cache_type is None:
                # Sum the count of all caches
                total_count = 0
                for ct in CacheType:
                    cache = self.caches[ct]
                    total_count += len(cache)
                return total_count
            else:
                # Get count of specific cache
                return len(self.caches[cache_type])
                
        except Exception as e:
            logger.error(f"Error getting cache count: {str(e)}")
            return 0
    
    def get_stats(self, cache_type: Optional[CacheType] = None) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Args:
            cache_type: Type of cache to get stats for, or None to get all stats
            
        Returns:
            Dictionary of statistics
        """
        try:
            if cache_type is None:
                # Get stats for all caches
                all_stats = {}
                for ct in CacheType:
                    all_stats[ct.name] = {
                        "stats": self.stats[ct].to_dict(),
                        "size_bytes": self.get_size(ct),
                        "item_count": self.get_count(ct)
                    }
                
                # Add overall metadata
                all_stats["metadata"] = {
                    "created_at": self._get_metadata("created_at"),
                    "access_count": self._get_metadata("access_count", 0),
                    "last_access": self._get_metadata("last_access
