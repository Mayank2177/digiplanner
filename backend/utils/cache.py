"""
Simple in-memory cache for processed receipts.

Caches extracted data by image hash to avoid reprocessing identical receipts.
"""

import hashlib
from typing import Any, Dict, Optional
from collections import OrderedDict


class ReceiptCache:
    """LRU cache for processed receipts."""
    
    def __init__(self, max_size: int = 100):
        self.cache = OrderedDict()
        self.max_size = max_size
    
    def _compute_hash(self, file_bytes: bytes) -> str:
        """Compute SHA256 hash of file bytes."""
        return hashlib.sha256(file_bytes).hexdigest()[:16]  # First 16 chars
    
    def get(self, file_bytes: bytes) -> Optional[Dict[str, Any]]:
        """Get cached result by file hash."""
        key = self._compute_hash(file_bytes)
        
        if key in self.cache:
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            return self.cache[key]
        
        return None
    
    def put(self, file_bytes: bytes, result: Dict[str, Any]) -> None:
        """Cache a result."""
        key = self._compute_hash(file_bytes)
        
        # Add to cache
        self.cache[key] = result
        self.cache.move_to_end(key)
        
        # Evict oldest if over max size
        if len(self.cache) > self.max_size:
            self.cache.popitem(last=False)
    
    def clear(self) -> None:
        """Clear all cached results."""
        self.cache.clear()
    
    def size(self) -> int:
        """Get current cache size."""
        return len(self.cache)


# Global cache instance
_receipt_cache = ReceiptCache(max_size=100)


def get_cached_result(file_bytes: bytes) -> Optional[Dict[str, Any]]:
    """Get cached OCR result if available."""
    return _receipt_cache.get(file_bytes)


def cache_result(file_bytes: bytes, result: Dict[str, Any]) -> None:
    """Cache OCR result for future use."""
    _receipt_cache.put(file_bytes, result)


def clear_cache() -> None:
    """Clear the entire cache."""
    _receipt_cache.clear()


def get_cache_stats() -> Dict[str, int]:
    """Get cache statistics."""
    return {
        "size": _receipt_cache.size(),
        "max_size": _receipt_cache.max_size
    }
