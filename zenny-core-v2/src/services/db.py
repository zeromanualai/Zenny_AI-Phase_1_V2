"""
Supabase Database Client
Singleton async wrapper around Supabase REST API.
Uses supabase-py with async postgrest client.
"""

from supabase import create_client, Client
from src.config import settings

_supabase: Client | None = None


def get_supabase() -> Client:
    """Return singleton Supabase client."""
    global _supabase
    if _supabase is None:
        _supabase = create_client(
            settings.supabase_url,
            settings.supabase_service_role_key,
        )
    return _supabase


async def set_tenant_context(client_id: str) -> None:
    """Set RLS tenant context before every tenant-scoped query."""
    db = get_supabase()
    # Execute raw SQL to set config var for RLS policies
    await db.rpc("set_tenant_context", {"client_id": client_id}).execute()


async def get_client_by_slug(slug: str):
    """Fetch client config by slug (used in webhooks)."""
    db = get_supabase()
    result = (
        db.table("clients")
        .select("*")
        .eq("slug", slug)
        .single()
        .execute()
    )
    return result.data if result.data else None


async def get_client_by_id(client_id: str):
    """Fetch client config by UUID."""
    db = get_supabase()
    result = (
        db.table("clients")
        .select("*")
        .eq("id", client_id)
        .single()
        .execute()
    )
    return result.data if result.data else None


async def create_conversation(client_id: str, user_email: str | None, channel: str):
    """Create a new conversation row."""
    db = get_supabase()
    result = (
        db.table("conversations")
        .insert({
            "client_id": client_id,
            "user_email": user_email,
            "channel": channel,
            "transcript": [],
        })
        .execute()
    )
    return result.data[0] if result.data else None


async def update_conversation(conversation_id: str, updates: dict):
    """Update conversation fields."""
    db = get_supabase()
    result = (
        db.table("conversations")
        .update(updates)
        .eq("id", conversation_id)
        .execute()
    )
    return result.data[0] if result.data else None


async def log_action(
    client_id: str,
    conversation_id: str | None,
    action_name: str,
    payload: dict,
    response_json: dict | None,
    success: bool,
    latency_ms: int,
    idempotency_key: str | None = None,
):
    """Immutable action log entry."""
    db = get_supabase()
    result = (
        db.table("action_logs")
        .insert({
            "client_id": client_id,
            "conversation_id": conversation_id,
            "action_name": action_name,
            "payload": payload,
            "response_json": response_json,
            "success": success,
            "latency_ms": latency_ms,
            "idempotency_key": idempotency_key,
        })
        .execute()
    )
    return result.data[0] if result.data else None


async def log_llm_cost(
    client_id: str,
    conversation_id: str | None,
    model_used: str,
    input_tokens: int,
    output_tokens: int,
    cost_usd: float,
):
    """Dedicated cost logging — no empty conversation rows."""
    db = get_supabase()
    result = (
        db.table("llm_cost_logs")
        .insert({
            "client_id": client_id,
            "conversation_id": conversation_id,
            "model_used": model_used,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": cost_usd,
        })
        .execute()
    )
    return result.data[0] if result.data else None
