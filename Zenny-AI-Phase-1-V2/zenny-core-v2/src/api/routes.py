"""
API Route Registry
Registers all routes with the FastAPI app.
"""

from fastapi import FastAPI

from src.api import webhook, channels, ingest, admin


def register_routes(app: FastAPI) -> None:
    """Register all API routes."""

    # ── Webhook (Voiceflow integration) ──
    app.include_router(
        webhook.router,
        prefix="/v1/webhook",
        tags=["webhook"],
    )

    # ── Channels (Web, WhatsApp, Email, Messenger) ──
    app.include_router(
        channels.router,
        prefix="/v1/channel",
        tags=["channels"],
    )

    # ── Legacy channel endpoints (backward compat) ──
    app.include_router(
        channels.legacy_router,
        prefix="/v1",
        tags=["channels-legacy"],
    )

    # ── Onboarding & KB ──
    app.include_router(
        ingest.router,
        prefix="/v1",
        tags=["ingest"],
    )

    # ── Admin Dashboard ──
    app.include_router(
        admin.router,
        prefix="/admin",
        tags=["admin"],
    )
