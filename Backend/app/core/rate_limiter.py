"""
Rate limiting for API endpoints to prevent abuse.
Uses in-memory storage with time-based cleanup.
"""

from datetime import datetime, timedelta
from typing import Dict, Optional
import threading


class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self._requests: Dict[str, list] = {}
        self._lock = threading.Lock()
    
    def _cleanup_old_requests(self, key: str, window_seconds: int):
        """Remove requests older than the time window"""
        if key not in self._requests:
            return
        
        cutoff_time = datetime.now() - timedelta(seconds=window_seconds)
        self._requests[key] = [
            req_time for req_time in self._requests[key]
            if req_time > cutoff_time
        ]
        
        # Remove key if no requests remain
        if not self._requests[key]:
            del self._requests[key]
    
    def is_rate_limited(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> tuple[bool, Optional[int]]:
        """
        Check if key has exceeded rate limit.
        
        Args:
            key: Identifier (e.g., user email or IP)
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
        
        Returns:
            (is_limited, seconds_until_reset)
        """
        with self._lock:
            # Clean up old requests
            self._cleanup_old_requests(key, window_seconds)
            
            # Initialize if new key
            if key not in self._requests:
                self._requests[key] = []
            
            # Check if limit exceeded
            if len(self._requests[key]) >= max_requests:
                # Calculate time until oldest request expires
                oldest_request = min(self._requests[key])
                time_until_reset = (
                    oldest_request + timedelta(seconds=window_seconds) - datetime.now()
                ).total_seconds()
                return True, int(time_until_reset) + 1
            
            # Add new request
            self._requests[key].append(datetime.now())
            return False, None
    
    def reset(self, key: str):
        """Reset rate limit for a key"""
        with self._lock:
            if key in self._requests:
                del self._requests[key]
    
    def clear_all(self):
        """Clear all rate limiting data"""
        with self._lock:
            self._requests.clear()


# Global rate limiter instance
rate_limiter = RateLimiter()
