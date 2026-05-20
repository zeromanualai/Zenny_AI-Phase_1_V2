"""
WooCommerce Integration
REST API wrapper for orders, products, customers.
Gap #2 — NEW file, not in original TypeScript repo.
"""

from typing import Optional
import httpx
from urllib.parse import urljoin


class WooCommerceClient:
    """WooCommerce REST API client."""

    def __init__(self, base_url: str, consumer_key: str, consumer_secret: str):
        self.base_url = base_url.rstrip("/")
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.api_base = urljoin(self.base_url + "/", "wp-json/wc/v3")
        self.auth = (consumer_key, consumer_secret)

    async def get_orders_by_email(self, email: str, limit: int = 5):
        """Get orders by customer email."""
        url = f"{self.api_base}/orders"
        params = {
            "email": email,
            "per_page": limit,
            "orderby": "date",
            "order": "desc",
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(url, auth=self.auth, params=params, timeout=10.0)
            response.raise_for_status()
            return response.json()

    async def get_order(self, order_id: int):
        """Get single order by ID."""
        url = f"{self.api_base}/orders/{order_id}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, auth=self.auth, timeout=10.0)
            response.raise_for_status()
            return response.json()

    async def get_products(self, limit: int = 10):
        """Get store products."""
        url = f"{self.api_base}/products"
        params = {"per_page": limit}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, auth=self.auth, params=params, timeout=10.0)
            response.raise_for_status()
            return response.json()

    async def get_customer_by_email(self, email: str):
        """Get customer by email."""
        url = f"{self.api_base}/customers"
        params = {"email": email}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, auth=self.auth, params=params, timeout=10.0)
            response.raise_for_status()
            customers = response.json()
            return customers[0] if customers else None

    def format_order_for_response(self, order: dict) -> str:
        """Format order data into human-readable string for LLM."""
        status = order.get("status", "pending")
        total = order.get("total", "0.00")
        created = order.get("date_created", "")[:10]
        items = order.get("line_items", [])
        item_names = ", ".join([i.get("name", "Unknown") for i in items[:3]])

        tracking = ""
        shipping = order.get("shipping_lines", [])
        if shipping:
            tracking = f" Shipping via {shipping[0].get('method_title', 'standard')}."

        return (
            f"Order #{order.get('id')} — "
            f"{status.replace('-', ' ').title()}, ${total}, placed {created}. "
            f"Items: {item_names}.{tracking}"
        )


def get_woocommerce_client(base_url: str, consumer_key: str, consumer_secret: str) -> WooCommerceClient:
    """Factory function."""
    return WooCommerceClient(base_url, consumer_key, consumer_secret)
