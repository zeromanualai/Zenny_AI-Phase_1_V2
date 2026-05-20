"""
Channel Gateway
Unified ingress for all channels: Web, WhatsApp, Email, Messenger.
Normalizes to internal format, then routes to Voiceflow DMAPI.
"""

from fastapi import APIRouter, HTTPException
from typing import Literal

from src.types import NormalizedMessage
from src.services.state_manager import state_manager
from src.services.db import get_client_by_slug
from src.channels import WebAdapter, WhatsAppAdapter, EmailAdapter, MessengerAdapter

ADAPTERS = {
    "web": WebAdapter(),
    "whatsapp": WhatsAppAdapter(provider="twilio"),  # or "360dialog"
    "email": EmailAdapter(),
    "messenger": MessengerAdapter(),
}

router = APIRouter()
legacy_router = APIRouter()


@router.post("/{channel}")
async def receive_message(channel: Literal["web", "whatsapp", "email", "messenger"], payload: dict):
    """
    Unified channel handler.
    All channels normalize to the same internal format.
    """
    # 1. Validate client
    client_id = payload.get("client_id")
    if not client_id:
        raise HTTPException(status_code=400, detail="client_id required")

    client_data = await get_client_by_slug(client_id)
    if not client_data:
        raise HTTPException(status_code=404, detail="Client not found")

    # 2. Check channel enabled
    channels_enabled = client_data.get("channels_enabled", {})
    if not channels_enabled.get(channel, False) and channel != "web":
        raise HTTPException(status_code=403, detail=f"Channel {channel} not enabled for this client")

    # 3. Normalize message
    normalized = NormalizedMessage(
        channel=channel,
        client_id=client_id,
        user_id=payload.get("user_id", payload.get("from", "anonymous")),
        message=payload.get("message", payload.get("text", "")),
        metadata=payload.get("metadata", {}),
    )

    # 4. Get or create session
    session = await state_manager.get_or_merge_session(
        client_id=client_id,
        user_id=normalized.user_id,
        channel=channel,
        identifiers={
            "email": payload.get("email"),
            "phone": payload.get("phone"),
        },
    )

    # 5. Forward to Voiceflow DMAPI (or Zenny Core directly in Phase 3)
    # For now, return acknowledgment. Full routing in Batch 2.
    return {
        "received": True,
        "channel": channel,
        "client_id": client_id,
        "user_id": normalized.user_id,
        "session_slots": session.get("slots", {}),
        "reply": "Message received. Processing...",
    }


# ── Legacy endpoints for backward compatibility ──

@legacy_router.post("/channel/web")
async def legacy_web(payload: dict):
    """Legacy web widget endpoint."""
    return await receive_message("web", payload)


@legacy_router.post("/whatsapp")
async def legacy_whatsapp(payload: dict):
    """Legacy WhatsApp endpoint."""
    return await receive_message("whatsapp", payload)


@legacy_router.post("/email")
async def legacy_email(payload: dict):
    """Legacy email endpoint."""
    return await receive_message("email", payload)


@legacy_router.post("/messenger")
async def legacy_messenger(payload: dict):
    """Legacy Messenger endpoint."""
    return await receive_message("messenger", payload)
