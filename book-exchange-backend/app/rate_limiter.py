"""Rate limiting configuration for auth endpoints."""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# Rate limit tiers
LOGIN_RATE_LIMIT = "5/minute"  # Strictest: 5 attempts per minute
REGISTER_RATE_LIMIT = "3/minute"  # Very strict: 3 signups per minute
REFRESH_RATE_LIMIT = "10/minute"  # Moderate: 10 refreshes per minute
LOGOUT_RATE_LIMIT = "20/minute"  # Relaxed: 20 logouts per minute
ME_RATE_LIMIT = "30/minute"  # Relaxed: 30 profile reads per minute
