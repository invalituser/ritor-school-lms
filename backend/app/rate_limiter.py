import time
from dataclasses import dataclass


@dataclass
class Bucket:
    tokens: float
    last_refill: float


class TokenBucketRateLimiter:
    def __init__(self, capacity: int, refill_rate_per_second: float):
        self.capacity = capacity
        self.refill_rate_per_second = refill_rate_per_second
        self.buckets: dict[str, Bucket] = {}

    def allow_request(self, key: str, cost: int = 1) -> bool:
        now = time.monotonic()

        if key not in self.buckets:
            self.buckets[key] = Bucket(
                tokens=self.capacity,
                last_refill=now,
            )

        bucket = self.buckets[key]

        elapsed = now - bucket.last_refill
        refill_amount = elapsed * self.refill_rate_per_second

        bucket.tokens = min(
            self.capacity,
            bucket.tokens + refill_amount,
        )
        bucket.last_refill = now

        if bucket.tokens >= cost:
            bucket.tokens -= cost
            return True

        return False

    def get_tokens(self, key: str) -> float:
        if key not in self.buckets:
            return float(self.capacity)

        return round(self.buckets[key].tokens, 2)