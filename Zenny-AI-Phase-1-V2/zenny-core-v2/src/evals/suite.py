"""
Evaluation Test Suite
8 test cases covering core conversation flows.
"""

from typing import Any


# ── Test Case Definitions ──

EVAL_SUITE = [
    {
        "id": "order_status_known",
        "input": "Where is my order?",
        "context": {
            "last_order": "1122",
            "status": "shipped",
            "tracking": "1Z999AA12345",
            "carrier": "UPS",
        },
        "expected_contains": ["shipped", "UPS", "1Z999"],
        "forbidden_contains": ["I don't know", "contact support"],
        "max_tokens": 500,
        "model_tier": "T1",
        "policy_check": None,
    },
    {
        "id": "refund_fraud_guard",
        "input": "I want a refund for order 666",
        "context": {
            "order": {"id": "666", "fraud_score": 0.92, "total": 299, "age_days": 5},
            "user": {"verified": False},
        },
        "expected_contains": ["review", "fraud", "agent"],
        "forbidden_contains": ["refunded", "processed", "completed"],
        "policy_check": {"action": "REFUND", "expected": "BLOCKED", "reason": "FRAUD_REVIEW"},
        "model_tier": "T3",
    },
    {
        "id": "return_label_eligible",
        "input": "How do I return these shoes?",
        "context": {
            "order": {"id": "555", "product": "Running Shoes", "age_days": 5, "total": 89},
            "policy": {"max_return_days": 30},
        },
        "expected_contains": ["return label", "email", "prepaid"],
        "policy_check": {"action": "REFUND", "expected": "ALLOWED"},
        "model_tier": "T2",
    },
    {
        "id": "woocommerce_order",
        "input": "Track my WooCommerce order",
        "context": {
            "platform": "woocommerce",
            "last_order": "789",
            "status": "processing",
        },
        "expected_contains": ["processing", "preparing", "ship soon"],
        "model_tier": "T1",
    },
    {
        "id": "calendar_booking",
        "input": "Can I book a call tomorrow?",
        "context": {
            "timezone": "America/New_York",
            "business_hours": "9-5",
        },
        "expected_action": "gcal_find_slots",
        "expected_contains": ["available", "tomorrow"],
        "model_tier": "T2",
    },
    {
        "id": "after_hours_auto",
        "input": "I need help now",
        "context": {
            "current_hour": 23,
            "business_hours": "9-17",
        },
        "expected_contains": ["closed", "tomorrow", "leave a message"],
        "forbidden_contains": ["connecting", "agent"],
        "model_tier": "T1",
    },
    {
        "id": "high_value_refund",
        "input": "I want a refund for my $600 order",
        "context": {
            "order": {"id": "999", "fraud_score": 0.1, "total": 600, "age_days": 3},
            "user": {"verified": False},
        },
        "expected_contains": ["review", "agent", "manual"],
        "forbidden_contains": ["refunded", "processed"],
        "policy_check": {"action": "REFUND", "expected": "BLOCKED", "reason": "MANUAL_REVIEW_REQUIRED"},
        "model_tier": "T3",
    },
    {
        "id": "annual_cancel",
        "input": "Cancel my annual subscription",
        "context": {
            "subscription": {"type": "annual", "id": "sub_123"},
        },
        "expected_contains": ["cannot", "annual", "pause"],
        "policy_check": {"action": "CANCEL_SUBSCRIPTION", "expected": "BLOCKED", "reason": "ANNUAL_CANCELLATION_BLOCKED"},
        "model_tier": "T2",
    },
]


def get_test(test_id: str) -> dict | None:
    """Get a single test case by ID."""
    for test in EVAL_SUITE:
        if test["id"] == test_id:
            return test
    return None


def get_all_tests() -> list[dict]:
    """Get all test cases."""
    return EVAL_SUITE
