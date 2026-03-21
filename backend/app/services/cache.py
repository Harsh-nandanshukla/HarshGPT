import redis
import json
import hashlib
import os

# Init Redis
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=0,
    decode_responses=True
)

# Cache expiry - 24 hours
CACHE_TTL = 60 * 60 * 24

def get_cache_key(query: str) -> str:
    """Generate consistent cache key from query"""
    return f"harshgpt:{hashlib.md5(query.lower().strip().encode()).hexdigest()}"

def get_cached_response(query: str) -> dict | None:
    """Return cached response if exists"""
    try:
        key = get_cache_key(query)
        cached = redis_client.get(key)
        if cached:
            print(f"Cache HIT: {query}")
            return json.loads(cached)
        print(f"Cache MISS: {query}")
        return None
    except Exception as e:
        print(f"Redis error: {e}")
        return None

def set_cached_response(query: str, response: dict) -> None:
    """Cache response for 24 hours"""
    try:
        key = get_cache_key(query)
        redis_client.setex(
            key,
            CACHE_TTL,
            json.dumps(response)
        )
    except Exception as e:
        print(f"Redis cache set error: {e}")