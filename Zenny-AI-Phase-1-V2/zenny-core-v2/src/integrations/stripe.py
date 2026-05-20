"""
Stripe Integration
Refunds, charge lookups, subscriptions.
"""

from typing import Optional
import httpx


class StripeClient:
    """Stripe API client."""

    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.base_url = "https://api.stripe.com/v1"
        self.headers = {
            "Authorization": f"Bearer {secret_key}",
        }

    async def get_charge(self, charge_id: str):
        """Get charge details."""
        url = f"{self.base_url}/charges/{charge_id}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, timeout=10.0)
            response.raise_for_status()
            return response.json()

    async def create_refund(self, charge_id: str, amount: Optional[int] = None, idempotency_key: Optional[str] = None):
        """
        Create a refund.
        amount: in cents. If None, full refund.
        idempotency_key: prevents double refunds.
        """
        url = f"{self.base_url}/refunds"
        data = {"charge": charge_id}
        if amount:
            data["amount"] = amount

        headers = self.headers.copy()
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, data=data, timeout=10.0)
            response.raise_for_status()
            return response.json()

    async def get_subscription(self, subscription_id: str):
        """Get subscription details."""
        url = f"{self.base_url}/subscriptions/{subscription_id}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, timeout=10.0)
            response.raise_for_status()
            return response.json()

    async def cancel_subscription(self, subscription_id: str, idempotency_key: Optional[str] = None):
        """Cancel a subscription."""
        url = f"{self.base_url}/subscriptions/{subscription_id}"
        headers = self.headers.copy()
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key

        async with httpx.AsyncClient() as client:
            response = await client.delete(url, headers=headers, timeout=10.0)
            response.raise_for_status()
            return response.json()

    def format_charge_for_response(self, charge: dict) -> str:
        """Format charge for LLM response."""
        amount = charge.get("amount", 0) / 100
        currency = charge.get("currency", "usd").upper()
        status = charge.get("status", "unknown")
        created = charge.get("created", "")
        refunded = charge.get("refunded", False)
        refund_amount = sum(r.get("amount", 0) for r in charge.get("refunds", {}).get("data", [])) / 100

        return (
            f"Charge: ${amount:.2f} {currency}, "
            f"status: {status}, "
            f"refunded: {'Yes' if refunded else 'No'}"
            f"{' ($' + str(refund_amount) + ')' if refund_amount > 0 else ''}."
        )


def get_stripe_client(secret_key: str) -> StripeClient:
    """Factory function."""
    return StripeClient(secret_key)
