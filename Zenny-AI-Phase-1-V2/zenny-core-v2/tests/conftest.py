"""
Pytest Fixtures
Shared test setup: mock Redis, mock Supabase, test client.
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def mock_client_config():
    """Sample client config for tests."""
    return {
        "id": "test-client-id",
        "slug": "test-store",
        "industry": "ecommerce",
        "platform": "shopify",
        "agent_name": "Zenny",
        "tone": "friendly_professional",
        "primary_color": "#6366F1",
        "channels_enabled": {"web": True},
        "timezone": "UTC",
        "return_policy_days": 30,
        "fraud_threshold": 0.8,
        "plan": "starter",
    }


@pytest.fixture
def mock_order():
    """Sample order for policy guard tests."""
    return {
        "id": "1122",
        "status": "shipped",
        "tracking": "1Z999AA12345",
        "carrier": "UPS",
        "total": 89.00,
        "age_days": 5,
        "fraud_score": 0.2,
    }
