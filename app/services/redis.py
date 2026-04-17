import os
import redis.asyncio as redis
from app.core.config import settings

class MockRedis:
    """A simple in-memory mock for Redis asyncio client."""
    _storage = {}

    def __init__(self):
        print("⚠️ Using Mock (In-Memory) Redis")

    async def get(self, name):
        return self._storage.get(name)

    async def set(self, name, value, ex=None, px=None, nx=False, xx=False):
        self._storage[name] = str(value)
        return True

    async def delete(self, *names):
        count = 0
        for name in names:
            if name in self._storage:
                del self._storage[name]
                count += 1
        return count

    async def close(self):
        pass

# Initialize real client
try:
    # If on Vercel and URL is localhost, don't even try to connect (fail fast)
    if os.environ.get("VERCEL") and "localhost" in settings.REDIS_URL:
        raise ConnectionError("Local Redis not available on Vercel")
    
    redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
except Exception as e:
    print(f"❌ Redis connection failed: {e}")
    redis_client = MockRedis()

async def get_redis():
    return redis_client
