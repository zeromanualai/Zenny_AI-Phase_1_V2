"""
Policy Guard — Deterministic Business Rules
Code, not prompts. The LLM never sees these decisions.
All rules execute BEFORE any AI generation or action.
"""

from typing import Optional, Literal
from src.types import PolicyResult


class PolicyGuard:
    """
    Deterministic guardrails for all business actions.
    One fraudulent refund costs more than 100 successful conversations.
    """

    async def evaluate(
        self,
        action_type: str,
        context: dict,
        client_policy: dict,
    ) -> PolicyResult:
        """
        Evaluate an action against deterministic rules.

        Args:
            action_type: e.g. "REFUND", "CANCEL_SUBSCRIPTION", "HUMAN_HANDOFF"
            context: {order, user, subscription, sentiment, ...}
            client_policy: {max_return_days, fraud_threshold, ...}
        """
        action_type = action_type.upper()

        if action_type == "REFUND":
            return self._check_refund(context, client_policy)

        if action_type == "CANCEL_SUBSCRIPTION":
            return self._check_cancel_subscription(context)

        if action_type == "HUMAN_HANDOFF":
            return self._check_human_handoff(context)

        if action_type == "SHARE_ORDER_DETAILS":
            return self._check_share_order_details(context)

        if action_type == "GENERATE_RETURN_LABEL":
            return self._check_return_label(context, client_policy)

        # Default: allow
        return PolicyResult(allowed=True)

    # ── REFUND ──

    def _check_refund(self, context: dict, client_policy: dict) -> PolicyResult:
        order = context.get("order", {})
        user = context.get("user", {})
        policy_days = client_policy.get("max_return_days", 30)
        fraud_threshold = client_policy.get("fraud_threshold", 0.8)

        # Rule 1: Fraud score too high
        if order.get("fraud_score", 0) > fraud_threshold:
            return PolicyResult(
                allowed=False,
                reason="FRAUD_REVIEW",
                escalate=True,
                priority="high",
            )

        # Rule 2: Return window expired
        if order.get("age_days", 0) > policy_days:
            return PolicyResult(
                allowed=False,
                reason="POLICY_EXPIRED",
                suggestion="Explain return policy window to customer",
            )

        # Rule 3: High-value + unverified
        if order.get("total", 0) > 500 and not user.get("verified", False):
            return PolicyResult(
                allowed=False,
                reason="MANUAL_REVIEW_REQUIRED",
                escalate=True,
                priority="high",
            )

        return PolicyResult(allowed=True)

    # ── CANCEL SUBSCRIPTION ──

    def _check_cancel_subscription(self, context: dict) -> PolicyResult:
        subscription = context.get("subscription", {})

        if subscription.get("type") == "annual":
            return PolicyResult(
                allowed=False,
                reason="ANNUAL_CANCELLATION_BLOCKED",
                suggestion="OFFER_PAUSE_INSTEAD",
            )

        return PolicyResult(allowed=True)

    # ── HUMAN HANDOFF ──

    def _check_human_handoff(self, context: dict) -> PolicyResult:
        sentiment = context.get("sentiment", 0)
        intent = context.get("intent", "")
        user = context.get("user", {})

        if sentiment < -0.6:
            return PolicyResult(allowed=True, priority="high")

        if intent in ("legal", "dispute", "complaint"):
            return PolicyResult(allowed=True, priority="high")

        if user.get("vip", False):
            return PolicyResult(allowed=True, priority="high")

        return PolicyResult(allowed=False)

    # ── SHARE ORDER DETAILS ──

    def _check_share_order_details(self, context: dict) -> PolicyResult:
        order = context.get("order", {})
        user = context.get("user", {})

        # Require verification for high-value orders
        if order.get("total", 0) > 200 and not user.get("verified", False):
            return PolicyResult(
                allowed=False,
                reason="VERIFICATION_REQUIRED",
                suggestion="Ask customer to verify identity",
            )

        return PolicyResult(allowed=True)

    # ── GENERATE RETURN LABEL ──

    def _check_return_label(self, context: dict, client_policy: dict) -> PolicyResult:
        # Same checks as refund
        return self._check_refund(context, client_policy)


# Singleton
policy_guard = PolicyGuard()
