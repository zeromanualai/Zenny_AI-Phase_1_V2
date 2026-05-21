"""
Action Engine
Calls n8n webhooks for external integrations.
Thin wrapper — n8n handles API calls, retries, transforms.
Zenny Core decides WHAT to call, n8n handles HOW.
"""

import time
import uuid
from typing import Optional

import httpx
from src.config import settings
from src.services.db import log_action
from src.types import ActionResult


class ActionEngine:
    """
    Executes actions via n8n webhooks.
    All actions are idempotent (idempotency_key prevents double execution).
    """

    async def execute(
        self,
        action_name: str,
        params: dict,
        client_id: str,
        conversation_id: Optional[str] = None,
    ) -> ActionResult:
        """
        Execute an action via n8n webhook.

        Args:
            action_name: e.g. "shopify_order_lookup", "stripe_refund"
            params: Action-specific parameters
            client_id: Tenant ID
            conversation_id: For action log linkage
        """
        start_time = time.time()
        idempotency_key = str(uuid.uuid4())

        # Build webhook URL
        webhook_url = f"{settings.n8n_webhook_url}/{action_name}"

        # Build payload
        payload = {
            "client_id": client_id,
            "conversation_id": conversation_id,
            "idempotency_key": idempotency_key,
            **params,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    webhook_url,
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "X-N8N-Secret": settings.n8n_secret,
                    },
                )
                response.raise_for_status()
                data = response.json()

                latency_ms = int((time.time() - start_time) * 1000)

                # Log action
                await log_action(
                    client_id=client_id,
                    conversation_id=conversation_id,
                    action_name=action_name,
                    payload=params,
                    response_json=data,
                    success=True,
                    latency_ms=latency_ms,
                    idempotency_key=idempotency_key,
                )

                return ActionResult(
                    success=True,
                    data=data,
                    latency_ms=latency_ms,
                )

        except httpx.HTTPStatusError as e:
            latency_ms = int((time.time() - start_time) * 1000)
            error_msg = f"HTTP {e.response.status_code}: {e.response.text}"

            await log_action(
                client_id=client_id,
                conversation_id=conversation_id,
                action_name=action_name,
                payload=params,
                response_json={"error": error_msg},
                success=False,
                latency_ms=latency_ms,
                idempotency_key=idempotency_key,
            )

            return ActionResult(
                success=False,
                error=error_msg,
                latency_ms=latency_ms,
            )

        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)

            await log_action(
                client_id=client_id,
                conversation_id=conversation_id,
                action_name=action_name,
                payload=params,
                response_json={"error": str(e)},
                success=False,
                latency_ms=latency_ms,
                idempotency_key=idempotency_key,
            )

            return ActionResult(
                success=False,
                error=str(e),
                latency_ms=latency_ms,
            )


# Singleton
action_engine = ActionEngine()
