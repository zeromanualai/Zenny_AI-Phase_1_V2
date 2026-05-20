"""
Integration Tests
Shopify, WooCommerce, Stripe, Zendesk
"""

import pytest
from unittest.mock import AsyncMock, patch

from src.integrations.shopify import ShopifyClient
from src.integrations.woocommerce import WooCommerceClient
from src.integrations.stripe import StripeClient
from src.integrations.zendesk import ZendeskClient


class TestShopify:
    """Shopify integration tests."""

    def test_format_order(self):
        order = {
            "name": "#1122",
            "fulfillment_status": "shipped",
            "total_price": "89.00",
            "created_at": "2026-05-15T10:00:00Z",
            "line_items": [{"title": "Running Shoes"}],
            "fulfillments": [{"tracking_number": "1Z999AA12345", "tracking_company": "UPS"}],
        }
        client = ShopifyClient("test-store.myshopify.com", "fake-token")
        result = client.format_order_for_response(order)
        assert "shipped" in result
        assert "$89.00" in result
        assert "UPS" in result
        assert "Running Shoes" in result

    @pytest.mark.asyncio
    async def test_get_orders_by_email(self):
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.json.return_value = {
                "orders": [{"id": "1", "name": "#1001"}]
            }
            mock_response.raise_for_status = AsyncMock()
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

            client = ShopifyClient("test-store.myshopify.com", "fake-token")
            orders = await client.get_orders_by_email("test@example.com")
            assert len(orders) == 1
            assert orders[0]["name"] == "#1001"


class TestWooCommerce:
    """WooCommerce integration tests."""

    def test_format_order(self):
        order = {
            "id": 789,
            "status": "processing",
            "total": "45.00",
            "date_created": "2026-05-15T10:00:00",
            "line_items": [{"name": "T-Shirt"}],
            "shipping_lines": [{"method_title": "Flat Rate"}],
        }
        client = WooCommerceClient("https://test-store.com", "ck_xxx", "cs_xxx")
        result = client.format_order_for_response(order)
        assert "Processing" in result
        assert "$45.00" in result
        assert "T-Shirt" in result


class TestStripe:
    """Stripe integration tests."""

    def test_format_charge(self):
        charge = {
            "amount": 5000,
            "currency": "usd",
            "status": "succeeded",
            "refunded": False,
            "refunds": {"data": []},
        }
        client = StripeClient("sk_test_xxx")
        result = client.format_charge_for_response(charge)
        assert "$50.00" in result
        assert "succeeded" in result


class TestZendesk:
    """Zendesk integration tests."""

    def test_client_init(self):
        client = ZendeskClient("testsubdomain", "api_token_xxx")
        assert client.subdomain == "testsubdomain"
        assert "testsubdomain.zendesk.com" in client.base_url
