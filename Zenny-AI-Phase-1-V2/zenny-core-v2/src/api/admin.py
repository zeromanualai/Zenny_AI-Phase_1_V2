"""
Admin Dashboard API
Internal endpoints for PM/dev team to monitor and debug.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from datetime import datetime, timedelta

from src.services.db import get_supabase
from src.config import settings

router = APIRouter()


def verify_admin(password: str):
    """Simple password check for admin endpoints."""
    if password != settings.admin_password:
        raise HTTPException(status_code=401, detail="Invalid admin password")
    return True


@router.get("/clients")
async def list_clients(password: str):
    """List all clients."""
    verify_admin(password)
    db = get_supabase()
    result = db.table("clients").select("*").execute()
    return result.data or []


@router.get("/conversations")
async def list_conversations(
    password: str,
    client_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    """List conversations with optional client filter."""
    verify_admin(password)
    db = get_supabase()
    query = db.table("conversations").select("*").order("created_at", desc=True).limit(limit).offset(offset)
    if client_id:
        query = query.eq("client_id", client_id)
    result = query.execute()
    return result.data or []


@router.get("/conversations/{conversation_id}")
async def get_conversation(password: str, conversation_id: str):
    """Get single conversation with full transcript."""
    verify_admin(password)
    db = get_supabase()
    result = db.table("conversations").select("*").eq("id", conversation_id).single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return result.data


@router.get("/costs")
async def get_cost_analytics(
    password: str,
    client_id: Optional[str] = None,
    days: int = 7,
):
    """
    Cost analytics from llm_cost_logs table.
    Returns daily breakdown of LLM costs.
    """
    verify_admin(password)
    db = get_supabase()

    since = (datetime.utcnow() - timedelta(days=days)).isoformat()
    query = db.table("llm_cost_logs").select("*").gte("created_at", since)
    if client_id:
        query = query.eq("client_id", client_id)
    result = query.execute()

    logs = result.data or []

    # Aggregate by day and model
    from collections import defaultdict
    daily = defaultdict(lambda: {"total": 0.0, "models": defaultdict(float), "tokens": 0})

    for log in logs:
        day = log["created_at"][:10]  # YYYY-MM-DD
        cost = float(log.get("cost_usd", 0))
        model = log.get("model_used", "unknown")
        tokens = log.get("input_tokens", 0) + log.get("output_tokens", 0)

        daily[day]["total"] += cost
        daily[day]["models"][model] += cost
        daily[day]["tokens"] += tokens

    return {
        "period_days": days,
        "total_cost_usd": sum(d["total"] for d in daily.values()),
        "total_tokens": sum(d["tokens"] for d in daily.values()),
        "daily_breakdown": dict(daily),
    }


@router.get("/action-logs")
async def list_action_logs(
    password: str,
    client_id: Optional[str] = None,
    action_name: Optional[str] = None,
    limit: int = 50,
):
    """List action execution logs."""
    verify_admin(password)
    db = get_supabase()
    query = db.table("action_logs").select("*").order("created_at", desc=True).limit(limit)
    if client_id:
        query = query.eq("client_id", client_id)
    if action_name:
        query = query.eq("action_name", action_name)
    result = query.execute()
    return result.data or []


@router.get("/health/detailed")
async def detailed_health(password: str):
    """Detailed health check with service status."""
    verify_admin(password)

    # Check Redis
    from src.services.redis_client import get_redis
    redis = await get_redis()
    redis_ok = await redis.ping()

    # Check Supabase
    db = get_supabase()
    db_ok = False
    try:
        db.table("clients").select("count").limit(1).execute()
        db_ok = True
    except Exception:
        pass

    return {
        "status": "healthy" if (redis_ok and db_ok) else "degraded",
        "redis": "connected" if redis_ok else "disconnected",
        "database": "connected" if db_ok else "disconnected",
        "timestamp": datetime.utcnow().isoformat(),
    }
