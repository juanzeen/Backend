import json
from typing import Callable, Any, Optional
import redis.asyncio as aioredis


async def get_cached_or_db(
    redis: aioredis.Redis,
    cache_key: str,
    fetch_from_db: Callable,
    expire_seconds: int = 3600,
) -> Optional[Any]:
    cached_data = await redis.get(cache_key)
    if cached_data:
        return json.loads(cached_data)

    db_data = await fetch_from_db
    if not db_data:
        return None
    await redis.set(cache_key, json.dumps(db_data), ex=expire_seconds)
    return db_data


async def get_cached(redis: aioredis.Redis, cache_key: str) -> Optional[Any]:
    cached_data = await redis.get(cache_key)
    if cached_data:
        return json.loads(cached_data)
    return None


async def set_cache(
    redis: aioredis.Redis, cache_key: str, data: Any, expire_seconds: int
) -> bool:
    if data:
        succes_set = await redis.set(cache_key, json.dumps(data), ex=expire_seconds)
        return succes_set
    return False
