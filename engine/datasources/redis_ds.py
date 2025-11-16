import redis.asyncio as redis
from typing import Optional, Any


class RedisDS:
    def __init__(self, host: str, port: int, password: Optional[str] = None, db: int = 0):
        self.host = host
        self.port = port
        self.password = password
        self.db = db
        self.redis = None

    async def connect(self):
        self.redis = redis.Redis(
            host=self.host,
            port=self.port,
            password=self.password,
            db=self.db
        )
        return self.redis

    async def disconnect(self):
        if self.redis:
            await self.redis.close()

    async def get(self, key: str):
        if self.redis:
            return await self.redis.get(key)
        return None

    async def set(self, key: str, value: str):
        if self.redis:
            await self.redis.set(key, value)

    async def script_load(self, script: str) -> str:
        if self.redis:
            return await self.redis.script_load(script)
        raise AttributeError("Redis client not initialized")

    def __getattr__(self, name: str) -> Any:
        if self.redis and hasattr(self.redis, name):
            return getattr(self.redis, name)
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
