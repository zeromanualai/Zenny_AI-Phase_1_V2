"""
Webhook Routes — Voiceflow DMAPI Integration
Handles all Voiceflow callbacks + escalation fix (Gap #9).
"""

from fastapi import APIRouter, HTTPException, status
from typing import Optional

from src.services.db import get_client_by_slug, create_conversation, update_conversation
from src.services.state_manager import state_manager
from src.services.llm_router import llm_router
from src.services.policy_guard import policy_guard
from src.services.action_engine import action_engine
from src.services.rag import rag_service
from src.services.pii_redactor import pii_redactor
from src.integrations.shopify import get_shopify_client
from src.integrations.woocommerce import get_woocommerce_client
from src.types import (
    VoiceflowWebhookPayload,
    EscalationPayload,
    LLMRequest,
    ConversationContext,
    ConversationTurn,
    ClientConfig,
)

router = APIRouter()


@router.post("/")
async def voiceflow_webhook(payload: VoiceflowWebhookPayload):
    """
    Main Voiceflow webhook handler.
    Voiceflow calls this for every user message.
    """
    # 1. Load client config
    client_data = await get_client_by_slug(payload.client_id)
    if not client_data:
        raise HTTPException(status_code=404, detail="Client not found")

    client = ClientConfig(**client_data)

    # 2. Get or create session
    session = await state_manager.get_or_merge_session(
        client_id=client.id,
        user_id=payload.user_id,
        channel="web",  # Voiceflow calls are web by default
    )

    # 3. Check for async action pending
    async_action = await state_manager.get_async_action(session.get("id", ""))
    if async_action and async_action.get("status") == "pending":
        return {
            "reply": await state_manager.generate_wait_ack(session),
            "slots": session.get("slots", {}),
        }

    # 4. Build conversation context
    transcript = [
        ConversationTurn(role="user", content=payload.message or "")
    ]

    # 5. PII Redaction
    safe_message, redactions = pii_redactor.redact_with_log(payload.message or "")

    # 6. RAG if needed
    kb_context = None
    if payload.message:
        kb_context = await rag_service.query(client.id, payload.message)

    # 7. Build LLM request
    context = ConversationContext(
        client=client,
        user_id=payload.user_id,
        session=session,
        transcript=transcript,
        kb_context=kb_context,
    )

    intent = payload.session_context.get("intent", "general") if payload.session_context else "general"
    # NEW --- Safe extraction
    user_email = None
    if session and session.get("slots"):
        user_email = session["slots"].get("user_email")
    if not user_email and payload.session_context:
        user_email = payload.session_context.get("user_email")

    # ---- INTEGRATED CODE INSERTION ----
    if intent == "order_status":
        if client.platform == "shopify" and client.shopify_domain:
            shopify = get_shopify_client(client.shopify_domain, client.shopify_access_token)
            orders = await shopify.get_orders_by_email(user_email)
            # ... format response
        elif client.platform == "woocommerce" and client.woocommerce_url:
            woo = get_woocommerce_client(client.woocommerce_url, client.woocommerce_consumer_key, client.woocommerce_consumer_secret)
            orders = await woo.get_orders_by_email(user_email)
            # ... format response
    # -----------------------------------

    llm_request = LLMRequest(
        message=safe_message,
        intent=intent,
        context=context,
    )

    # 8. Route to LLM
    llm_response = await llm_router.route(llm_request)

    # 9. Update session
    await state_manager.update_intent(client.id, payload.user_id, "web", llm_request.intent)

    # 10. Return to Voiceflow
    return {
        "reply": llm_response.content,
        "slots": session.get("slots", {}),
        "model_used": llm_response.model_used,
        "tier": llm_response.tier,
        "cost_usd": str(llm_response.cost_usd),
    }


@router.post("/escalate")
async def escalate(payload: EscalationPayload):
    """
    Escalation handler — FIXES GAP #9.
    Creates Zendesk ticket + sends Slack alert.
    """
    # 1. Load client
    client_data = await get_client_by_slug(payload.client_id)
    if not client_data:
        raise HTTPException(status_code=404, detail="Client not found")

    client = ClientConfig(**client_data)

    # 2. Format transcript for ticket
    transcript_text = "\n\n".join([
        f"{'User' if t.role == 'user' else 'Zenny'}: {t.content}"
        for t in payload.transcript
    ])

    ticket_body = f"""Escalation Reason: {payload.reason}
Priority: {payload.priority}
User ID: {payload.user_id}
User Email: {payload.user_email or 'N/A'}

--- Conversation Transcript ---
{transcript_text}"""

    # 3. Create Zendesk ticket
    zendesk_result = None
    if client.zendesk_subdomain and client.zendesk_api_token:
        zendesk_result = await action_engine.execute(
            action_name="zendesk-ticket-create",
            params={
                "subject": f"Escalation: {payload.reason}",
                "body": ticket_body,
                "email": payload.user_email or client.escalation_email,
                "priority": payload.priority,
                "subdomain": client.zendesk_subdomain,
                "api_token": client.zendesk_api_token,
            },
            client_id=client.id,
        )

    # 4. Send Slack alert
    slack_result = await action_engine.execute(
        action_name="slack-notify",
        params={
            "channel": "#zenny-alerts",
            "message": f"🚨 Escalation from `{payload.client_id}`\nReason: {payload.reason}\nPriority: {payload.priority}\nUser: {payload.user_id}",
        },
        client_id=client.id,
    )

    # 5. Return acknowledgment
    return {
        "escalated": True,
        "ticket_created": zendesk_result.success if zendesk_result else False,
        "ticket_id": zendesk_result.data.get("ticket_id") if zendesk_result and zendesk_result.data else None,
        "slack_notified": slack_result.success if slack_result else False,
        "reason": payload.reason,
    }


@router.post("/action")
async def execute_action(payload: dict):
    """
    Generic action execution endpoint.
    Used by Voiceflow for specific actions (order lookup, refund, etc.).
    """
    client_id = payload.get("client_id")
    action_name = payload.get("action_name")
    params = payload.get("params", {})

    if not client_id or not action_name:
        raise HTTPException(status_code=400, detail="client_id and action_name required")

    result = await action_engine.execute(
        action_name=action_name,
        params=params,
        client_id=client_id,
    )

    return {
        "success": result.success,
        "data": result.data,
        "error": result.error,
        "latency_ms": result.latency_ms,
    }