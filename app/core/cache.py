import json
from typing import Any, Optional

import redis.asyncio as aioredis

from app.core.config import settings

redis_client: Optional[aioredis.Redis] = None
redis_available: bool = True


async def get_redis_client() -> Optional[aioredis.Redis]:
    global redis_client, redis_available
    if not settings.CACHE_ENABLED or not redis_available:
        return None

    if redis_client is None:
        try:
            client = aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_timeout=0.1,
                socket_connect_timeout=0.1,
            )
            await client.ping()
            redis_client = client
        except Exception:
            redis_available = False
            return None
    return redis_client


async def get_cache(key: str) -> Optional[Any]:
    client = await get_redis_client()
    if not client:
        return None
    try:
        val = await client.get(key)
        return json.loads(val) if val else None
    except Exception:
        # Neu Redis offline thi bo qua cache de app van hoat dong
        return None


async def set_cache(key: str, value: Any, expire_seconds: int = 60) -> None:
    client = await get_redis_client()
    if not client:
        return
    try:
        await client.set(key, json.dumps(value), ex=expire_seconds)
    except Exception:
        return


async def delete_cache(pattern: str) -> None:
    client = await get_redis_client()
    if not client:
        return
    try:
        keys = await client.keys(pattern)
        if keys:
            await client.delete(*keys)
    except Exception:
        return
