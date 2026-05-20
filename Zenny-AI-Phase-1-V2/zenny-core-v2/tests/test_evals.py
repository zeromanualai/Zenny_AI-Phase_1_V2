"""
Evaluation Framework Tests
"""

import pytest
from src.evals.suite import get_all_tests, get_test
from src.evals.runner import EvalRunner


class TestEvalSuite:
    def test_get_all_tests(self):
        tests = get_all_tests()
        assert len(tests) == 8
        ids = [t["id"] for t in tests]
        assert "order_status_known" in ids
        assert "refund_fraud_guard" in ids

    def test_get_single_test(self):
        test = get_test("refund_fraud_guard")
        assert test is not None
        assert test["policy_check"]["action"] == "REFUND"

    def test_get_missing_test(self):
        test = get_test("nonexistent")
        assert test is None


class TestEvalRunner:
    @pytest.mark.asyncio
    async def test_policy_only_test(self):
        """Test that policy-only tests (no LLM call) work."""
        runner = EvalRunner()
        test = {
            "id": "test_policy_only",
            "input": "test",
            "context": {
                "order": {"fraud_score": 0.92, "total": 299, "age_days": 5},
                "user": {"verified": False},
            },
            "policy_check": {"action": "REFUND", "expected": "BLOCKED", "reason": "FRAUD_REVIEW"},
        }
        result = await runner._run_single(test)
        assert result["passed"] is True

    @pytest.mark.asyncio
    async def test_pii_detection_in_input(self):
        """Test that PII in eval input is flagged."""
        runner = EvalRunner()
        test = {
            "id": "test_pii",
            "input": "My card is 4111-1111-1111-1111",
            "context": {},
        }
        result = await runner._run_single(test)
        assert result["passed"] is False
        assert "PII" in result["errors"][0]
