"""
Shopify Integration
Admin API wrapper for orders, products, customers.
"""

from typing import Optional
import httpx
from src.config import settings


class ShopifyClient:
    """Shopify Admin API client."""

    def __init__(self, domain: str, access_token: str):
        self.domain = domain.replace("https://", "").replace("http://", "").rstrip("/")
        self.access_token = access_token
        self.base_url = f"https://{self.domain}/admin/api/2024-04"
        self.headers = {
            "X-Shopify-Access-Token": access_token,
            "Content-Type": "application/json",
        }

    async def get_orders_by_email(self, email: str, limit: int = 5):
        """Get orders by customer email."""
        url = f"{self.base_url}/orders.json"
        params = {
            "email": email,
            "limit": limit,
            "status": "any",
            "fields": "id,name,email,total_price,financial_status,fulfillment_status,created_at,line_items,shipping_address",
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, params=params, timeout=10.0)
            response.raise_for_status()
            return response.json().get("orders", [])

    async def get_order(self, order_id: str):
        """Get single order by ID."""
        url = f"{self.base_url}/orders/{order_id}.json"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, timeout=10.0)
            response.raise_for_status()
            return response.json().get("order")

    async def get_products(self, limit: int = 10):
        """Get store products."""
        url = f"{self.base_url}/products.json"
        params = {"limit": limit, "fields": "id,title,variants,images"}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, params=params, timeout=10.0)
            response.raise_for_status()
            return response.json().get("products", [])

    async def get_customer_by_email(self, email: str):
        """Get customer by email."""
        url = f"{self.base_url}/customers/search.json"
        params = {"query": f"email:{email}", "fields": "id,email,first_name,last_name,orders_count,total_spent"}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, params=params, timeout=10.0)
            response.raise_for_status()
            customers = response.json().get("customers", [])
            return customers[0] if customers else None

    def format_order_for_response(self, order: dict) -> str:
        """Format order data into human-readable string for LLM."""
        status = order.get("fulfillment_status", "unfulfilled") or "unfulfilled"
        financial = order.get("financial_status", "pending")
        total = order.get("total_price", "0.00")
        created = order.get("created_at", "")[:10]
        items = order.get("line_items", [])
        item_names = ", ".join([i.get("title", "Unknown") for i in items[:3]])

        tracking = ""
        fulfillments = order.get("fulfillments", [])
        if fulfillments:
            tracking_num = fulfillments[0].get("tracking_number", "")
            carrier = fulfillments[0].get("tracking_company", "")
            if tracking_num:
                tracking = f" Tracking: {carrier} {tracking_num}."

        return (
            f"Order #{order.get('name', order.get('id'))} — "
            f"{status.title()}, ${total}, placed {created}. "
            f"Items: {item_names}.{tracking}"
        )


def get_shopify_client(domain: str, access_token: str) -> ShopifyClient:
    """Factory function."""
    return ShopifyClient(domain, access_token)
