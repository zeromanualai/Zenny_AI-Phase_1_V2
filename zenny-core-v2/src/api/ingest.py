"""
Onboarding & KB Ingestion
Merchant signup, config creation, KB upload trigger.
"""

from fastapi import APIRouter, HTTPException
from src.types import IngestConfigPayload
from src.services.db import get_supabase

router = APIRouter()


@router.post("/ingest-config")
async def ingest_config(payload: IngestConfigPayload):
    """
    Merchant onboarding endpoint.
    Creates client row in Supabase, triggers KB processing.
    """
    db = get_supabase()

    # 1. Check if slug exists
    existing = db.table("clients").select("id").eq("slug", payload.store_name.lower().replace(" ", "-")).execute()
    if existing.data:
        raise HTTPException(status_code=409, detail="Store with this name already exists")

    # 2. Create client row
    client_data = {
        "slug": payload.store_name.lower().replace(" ", "-"),
        "industry": "ecommerce",
        "platform": payload.platform,
        "agent_name": payload.agent_name or "Zenny",
        "welcome_message": payload.welcome_message,
        "tone": payload.tone or "friendly_professional",
        "channels_enabled": {ch: True for ch in (payload.channels or ["web"])},
        "business_hours": payload.business_hours,
        "escalation_email": payload.escalation_email,
        "timezone": payload.timezone or "UTC",
        "return_policy_days": payload.return_policy_days or 30,
        # Commerce credentials will be added later via OAuth/API key flow
    }

    result = db.table("clients").insert(client_data).execute()
    client = result.data[0] if result.data else None

    if not client:
        raise HTTPException(status_code=500, detail="Failed to create client")

    # 3. Trigger KB processing (via n8n or direct)
    # TODO: Trigger n8n workflow to process uploaded docs

    return {
        "created": True,
        "client_id": client["id"],
        "slug": client["slug"],
        "next_steps": [
            "Connect Shopify/WooCommerce OAuth",
            "Upload knowledge base documents",
            "Configure Voiceflow template",
        ],
    }


@router.post("/ingest-kb")
async def ingest_kb(payload: dict):
    """
    Knowledge Base upload trigger.
    Queues document for chunking + embedding.
    """
    client_id = payload.get("client_id")
    documents = payload.get("documents", [])

    if not client_id or not documents:
        raise HTTPException(status_code=400, detail="client_id and documents required")

    # TODO: Queue documents for processing
    # 1. Upload to Supabase Storage
    # 2. Trigger n8n workflow: extract → chunk → embed → store

    return {
        "queued": True,
        "client_id": client_id,
        "documents_count": len(documents),
        "status": "processing",
    }
