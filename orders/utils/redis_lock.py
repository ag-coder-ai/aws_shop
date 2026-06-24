import time
import redis
from django.conf import settings

redis_client = redis.StrictRedis.from_url(
    "redis://127.0.0.1:6379/1",
    decode_responses=True
)

class RedisLock:
    def __init__(self, key, timeout=10):
        self.key = key
        self.timeout = timeout
        self.locked = False

    def acquire(self):
        # SET NX EX = atomic lock
        self.locked = redis_client.set(
            self.key,
            "1",
            nx=True,
            ex=self.timeout
        )
        return self.locked

    def release(self):
        if self.locked:
            redis_client.delete(self.key)