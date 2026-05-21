"""
Redis Async Client
Session store, cache, cross-channel merge, async action queue.
Uses redis-py with asyncio support.
"""

import json
import hashlib
from typing import Optional

import redis.asyncio as redis
from src.config import settings

_redis: redis.Redis | None = None


async def get_redis() -> redis.Redis:
    """Return singleton async Redis client."""
    global _redis
    if _redis is None:
        _redis = redis.from_url(
            settings.redis_url,
            decode_responses=True,
            ssl=True,  # Upstash requires TLS always
        )
    return _redis


async def close_redis() -> None:
    """Close Redis connection on shutdown."""
    global _redis
    if _redis:
        await _redis.close()
        _redis = None


# ── Session Keys ──

def _session_key(client_id: str, user_id: str, channel: str) -> str:
    return f"session:{client_id}:{user_id}:{channel}"


def _async_key(session_id: str) -> str:
    return f"async:{session_id}"


def _cache_key(prefix: str, data: dict) -> str:
    """Deterministic cache key from dict."""
    raw = json.dumps(data, sort_keys=True, default=str)
    return f"{prefix}:{hashlib.sha256(raw.encode()).hexdigest()[:16]}"


# ── Session Operations ──

async def get_session(client_id: str, user_id: str, channel: str) -> Optional[dict]:
    """Get session from Redis. Returns None if expired/missing."""
    r = await get_redis()
    key = _session_key(client_id, user_id, channel)
    raw = await r.get(key)
    if raw:
        return json.loads(raw)
    return None


async def save_session(client_id: str, user_id: str, channel: str, session: dict, ttl: int = 3600) -> None:
    """Save session to Redis with TTL (default 1 hour)."""
    r = await get_redis()
    key = _session_key(client_id, user_id, channel)
    await r.setex(key, ttl, json.dumps(session))


async def delete_session(client_id: str, user_id: str, channel: str) -> None:
    """Delete session from Redis."""
    r = await get_redis()
    key = _session_key(client_id, user_id, channel)
    await r.delete(key)


# ── Cross-Channel Merge ──

async def find_cross_channel_session(client_id: str, identifiers: dict) -> Optional[dict]:
    """
    Scan Redis for sessions matching email or phone.
    identifiers = {"email": "john@store.com", "phone": "+1234567890"}
    """
    r = await get_redis()
    pattern = f"session:{client_id}:*"
    cursor = 0
    matches = []

    while True:
        cursor, keys = await r.scan(cursor, match=pattern, count=100)
        for key in keys:
            raw = await r.get(key)
            if not raw:
                continue
            session = json.loads(raw)
            slots = session.get("slots", {})
            if identifiers.get("email") and slots.get("email") == identifiers["email"]:
                matches.append(session)
            if identifiers.get("phone") and slots.get("phone") == identifiers["phone"]:
                matches.append(session)

        if cursor == 0:
            break

    if len(matches) > 1:
        # Merge: keep latest slots, combine intent history
        merged = matches[-1].copy()
        all_intents = []
        for s in matches:
            all_intents.extend(s.get("intent_history", []))
        merged["intent_history"] = list(dict.fromkeys(all_intents))  # dedupe, preserve order
        merged["merged_from"] = [s.get("channel") for s in matches]
        return merged

    return matches[0] if matches else None


# ── Async Action Queue ──

async def set_async_action(session_id: str, action: dict, ttl: int = 30) -> None:
    """Queue an async action (e.g., slow Shopify API call)."""
    r = await get_redis()
    key = _async_key(session_id)
    await r.setex(key, ttl, json.dumps({"action": action, "status": "pending"}))


async def get_async_action(session_id: str) -> Optional[dict]:
    """Check if an async action is pending."""
    r = await get_redis()
    key = _async_key(session_id)
    raw = await r.get(key)
    return json.loads(raw) if raw else None


async def clear_async_action(session_id: str) -> None:
    """Clear pending async action."""
    r = await get_redis()
    await r.delete(_async_key(session_id))


# ── Cache Operations ──

async def get_cache(prefix: str, data: dict) -> Optional[dict]:
    """Get cached LLM response or other data."""
    r = await get_redis()
    key = _cache_key(prefix, data)
    raw = await r.get(key)
    return json.loads(raw) if raw else None


async def set_cache(prefix: str, data: dict, value: dict, ttl: int = 86400) -> None:
    """Cache data with TTL (default 24h for T1 responses)."""
    r = await get_redis()
    key = _cache_key(prefix, data)
    await r.setex(key, ttl, json.dumps(value))
