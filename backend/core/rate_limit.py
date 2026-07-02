from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from time import monotonic

from fastapi import Request


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    limit: int
    remaining: int
    retry_after_seconds: int


class FixedWindowRateLimiter:
    def __init__(self, window_seconds: int, limits_by_prefix: dict[str, int], default_limit: int) -> None:
        self.window_seconds = max(1, int(window_seconds))
        self.limits_by_prefix = dict(limits_by_prefix)
        self.default_limit = max(1, int(default_limit))
        self._lock = Lock()
        self._buckets: dict[tuple[str, str], tuple[float, int]] = {}

    def _limit_for_path(self, path: str) -> tuple[str, int]:
        for prefix, limit in sorted(self.limits_by_prefix.items(), key=lambda item: len(item[0]), reverse=True):
            if path.startswith(prefix):
                return prefix, max(1, int(limit))
        return "default", self.default_limit

    def check(self, client_id: str, path: str) -> RateLimitDecision:
        bucket_name, limit = self._limit_for_path(path)
        key = (client_id, bucket_name)
        now = monotonic()

        with self._lock:
            window_start, count = self._buckets.get(key, (now, 0))
            elapsed = now - window_start
            if elapsed >= self.window_seconds:
                window_start = now
                count = 0

            count += 1
            self._buckets[key] = (window_start, count)
            remaining = max(0, limit - count)
            retry_after = max(1, int(self.window_seconds - (now - window_start)))

            return RateLimitDecision(
                allowed=count <= limit,
                limit=limit,
                remaining=remaining,
                retry_after_seconds=retry_after,
            )


def client_id_from_request(request: Request) -> str:
    if request.client and request.client.host:
        return request.client.host
    return "unknown"
