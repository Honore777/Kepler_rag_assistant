"""Simple IP-based rate limiting for public endpoints (registration, login).

Uses in-memory storage with window-based expiration.
"""

import time
from typing import Dict, Tuple

class IPRateLimiter:
    """Rate limiter based on client IP address for public endpoints."""
    
    def __init__(self):
        # Store: {ip: [(timestamp, endpoint), ...]}
        self.requests: Dict[str, list] = {}
        self.window_seconds = 60  # 1 minute window
    
    def _clean_old_requests(self, ip: str):
        """Remove requests outside the time window."""
        now = time.time()
        if ip in self.requests:
            self.requests[ip] = [
                req for req in self.requests[ip]
                if now - req[0] < self.window_seconds
            ]
    
    def is_allowed(self, ip: str, endpoint: str, max_requests: int = 5) -> Tuple[bool, int]:
        """Check if request is allowed and return remaining count."""
        now = time.time()
        
        # Clean old requests
        self._clean_old_requests(ip)
        
        # Get current request count for this endpoint
        if ip not in self.requests:
            self.requests[ip] = []
        
        endpoint_requests = [
            req for req in self.requests[ip]
            if req[1] == endpoint
        ]
        
        if len(endpoint_requests) >= max_requests:
            return False, 0
        
        # Record this request
        self.requests[ip].append((now, endpoint))
        
        remaining = max_requests - len(endpoint_requests) - 1
        return True, remaining

# Global instance
ip_rate_limiter = IPRateLimiter()


def check_ip_rate_limit(ip: str, endpoint: str, max_requests: int = 5) -> Tuple[bool, int]:
    """Convenience function to check IP rate limit."""
    return ip_rate_limiter.is_allowed(ip, endpoint, max_requests)
