"""
Policy Guard Tests
"""

import pytest
from src.services.policy_guard import policy_guard
from src.types import PolicyResult


@pytest.mark.asyncio
async def test_refund_allowed():
    result = await policy_guard.evaluate(
        "REFUND",
        {
            "order": {"fraud_score": 0.2, "total": 89, "age_days": 5},
            "user": {"verified": True},
        },
        {"max_return_days": 30, "fraud_threshold": 0.8},
    )
    assert result.allowed is True


@pytest.mark.asyncio
async def test_refund_blocked_fraud():
    result = await policy_guard.evaluate(
        "REFUND",
        {
            "order": {"fraud_score": 0.92, "total": 299, "age_days": 5},
            "user": {"verified": False},
        },
        {"max_return_days": 30, "fraud_threshold": 0.8},
    )
    assert result.allowed is False
    assert result.reason == "FRAUD_REVIEW"
    assert result.escalate is True


@pytest.mark.asyncio
async def test_refund_blocked_expired():
    result = await policy_guard.evaluate(
        "REFUND",
        {
            "order": {"fraud_score": 0.2, "total": 89, "age_days": 45},
            "user": {"verified": True},
        },
        {"max_return_days": 30, "fraud_threshold": 0.8},
    )
    assert result.allowed is False
    assert result.reason == "POLICY_EXPIRED"


@pytest.mark.asyncio
async def test_refund_blocked_high_value_unverified():
    result = await policy_guard.evaluate(
        "REFUND",
        {
            "order": {"fraud_score": 0.2, "total": 600, "age_days": 5},
            "user": {"verified": False},
        },
        {"max_return_days": 30, "fraud_threshold": 0.8},
    )
    assert result.allowed is False
    assert result.reason == "MANUAL_REVIEW_REQUIRED"
    assert result.escalate is True


@pytest.mark.asyncio
async def test_annual_cancel_blocked():
    result = await policy_guard.evaluate(
        "CANCEL_SUBSCRIPTION",
        {"subscription": {"type": "annual"}},
        {},
    )
    assert result.allowed is False
    assert result.reason == "ANNUAL_CANCELLATION_BLOCKED"
    assert result.suggestion == "OFFER_PAUSE_INSTEAD"


@pytest.mark.asyncio
async def test_human_handoff_vip():
    result = await policy_guard.evaluate(
        "HUMAN_HANDOFF",
        {"user": {"vip": True}, "sentiment": 0.5, "intent": "general"},
        {},
    )
    assert result.allowed is True
    assert result.priority == "high"
