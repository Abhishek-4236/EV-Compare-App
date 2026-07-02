import sys
import unittest
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


from core.rate_limit import FixedWindowRateLimiter


class RateLimitTests(unittest.TestCase):
    def test_fixed_window_limiter_blocks_after_prefix_limit(self):
        limiter = FixedWindowRateLimiter(
            window_seconds=60,
            limits_by_prefix={"/api/chat": 2},
            default_limit=10,
        )

        first = limiter.check("client-a", "/api/chat/stream")
        second = limiter.check("client-a", "/api/chat/stream")
        third = limiter.check("client-a", "/api/chat/stream")

        self.assertTrue(first.allowed)
        self.assertEqual(first.remaining, 1)
        self.assertTrue(second.allowed)
        self.assertEqual(second.remaining, 0)
        self.assertFalse(third.allowed)
        self.assertEqual(third.limit, 2)
        self.assertGreaterEqual(third.retry_after_seconds, 1)

    def test_limiter_isolated_by_client(self):
        limiter = FixedWindowRateLimiter(
            window_seconds=60,
            limits_by_prefix={"/api/auth": 1},
            default_limit=10,
        )

        self.assertTrue(limiter.check("client-a", "/api/auth/login").allowed)
        self.assertFalse(limiter.check("client-a", "/api/auth/login").allowed)
        self.assertTrue(limiter.check("client-b", "/api/auth/login").allowed)


if __name__ == "__main__":
    unittest.main()
