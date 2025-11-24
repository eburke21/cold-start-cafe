"""Shared test configuration.

Sets environment variables before any app imports to ensure test-friendly
defaults (e.g., rate limiting disabled).
"""

import os

# Disable rate limiting during tests — tests make many rapid requests
# from the same IP, which would trigger the sliding window limiter.
os.environ["RATE_LIMIT_ENABLED"] = "false"
