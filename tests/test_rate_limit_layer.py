import pytest
import time
from src.auth.config import AuthConfig
from src.auth.rate_limit import RateLimiter

def test_rate_limiter_burst():
    config = AuthConfig(
        ebay_client_id="test",
        ebay_client_secret="test",
        rate_limit_default_rps=100, # Very fast
        rate_limit_default_burst=5
    )
    limiter = RateLimiter(config)
    
    start = time.time()
    for _ in range(5):
        limiter.acquire("test_op")
    end = time.time()
    
    # Should be instant because of burst
    assert end - start < 0.1

def test_rate_limiter_throttling():
    config = AuthConfig(
        ebay_client_id="test",
        ebay_client_secret="test",
        rate_limit_default_rps=2, # 0.5s per request
        rate_limit_default_burst=1
    )
    limiter = RateLimiter(config)
    
    limiter.acquire("test_op") # First one instant
    start = time.time()
    limiter.acquire("test_op") # Second one should wait ~0.5s
    end = time.time()
    
    assert end - start >= 0.4
    assert end - start < 0.7

def test_rate_limiter_dry_run_bypass():
    config = AuthConfig(
        ebay_client_id="test",
        ebay_client_secret="test",
        rate_limit_default_rps=1,
        rate_limit_default_burst=1
    )
    limiter = RateLimiter(config)
    
    limiter.acquire("test_op")
    start = time.time()
    limiter.acquire("test_op", dry_run=True) # Should bypass
    end = time.time()
    
    assert end - start < 0.1
