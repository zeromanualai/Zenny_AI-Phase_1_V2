"""
Evaluation Runner
Executes eval suite against Zenny Core.
CI/CD command: `poetry run pytest evals/`
"""

import sys
import asyncio
from typing import Any

import pytest
from src.evals.suite import get_all_tests
from src.services.policy_guard import policy_guard
from src.services.llm_router import llm_router
from src.services.pii_redactor import pii_redactor
from src.types import LLMRequest, ConversationContext, ClientConfig, SessionState


class EvalRunner:
    """Runs evaluation suite and reports results."""

    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0

    async def run_all(self) -> dict:
        """Run all eval tests."""
        tests = get_all_tests()
        print(f"\n🧪 Running {len(tests)} evaluation tests...\n")

        for test in tests:
            result = await self._run_single(test)
            self.results.append(result)
            if result["passed"]:
                self.passed += 1
                print(f"  ✅ {test['id']}")
            else:
                self.failed += 1
                print(f"  ❌ {test['id']}: {result['errors']}")

        summary = {
            "total": len(tests),
            "passed": self.passed,
            "failed": self.failed,
            "pass_rate": round(self.passed / len(tests) * 100, 1),
            "results": self.results,
        }

        print(f"\n📊 Results: {self.passed}/{len(tests)} passed ({summary['pass_rate']}%)\n")
        return summary

    async def _run_single(self, test: dict) -> dict:
        """Run a single eval test."""
        errors = []

        # 1. Policy Guard check
        if test.get("policy_check"):
            policy_result = await self._check_policy(test)
            if not policy_result["passed"]:
                errors.extend(policy_result["errors"])

        # 2. LLM response check (if not purely policy-based)
        if test.get("expected_contains") or test.get("forbidden_contains"):
            llm_result = await self._check_llm_response(test)
            if not llm_result["passed"]:
                errors.extend(llm_result["errors"])

        # 3. PII check
        if pii_redactor.has_pii(test["input"]):
            errors.append("Input contains unredacted PII")

        return {
            "id": test["id"],
            "passed": len(errors) == 0,
            "errors": errors,
        }

    async def _check_policy(self, test: dict) -> dict:
        """Check Policy Guard decision."""
        check = test["policy_check"]
        context = test.get("context", {})
        client_policy = context.get("policy", {})

        result = await policy_guard.evaluate(
            check["action"],
            context,
            client_policy,
        )

        errors = []
        expected_allowed = check["expected"] == "ALLOWED"

        if result.allowed != expected_allowed:
            errors.append(
                f"Policy: expected allowed={expected_allowed}, got {result.allowed}"
            )

        if check.get("reason") and result.reason != check["reason"]:
            errors.append(
                f"Policy reason: expected '{check['reason']}', got '{result.reason}'"
            )

        return {"passed": len(errors) == 0, "errors": errors}

    async def _check_llm_response(self, test: dict) -> dict:
        """Check LLM response content."""
        # Build minimal context
        client = ClientConfig(
            id="eval-client",
            slug="eval-store",
            agent_name="Zenny",
            tone="friendly_professional",
        )
        session = SessionState(
            client_id="eval-client",
            user_id="eval-user",
            channel="web",
        )
        context = ConversationContext(
            client=client,
            user_id="eval-user",
            session=session,
        )

        request = LLMRequest(
            message=test["input"],
            intent=test.get("model_tier", "T1").lower(),
            context=context,
        )

        try:
            response = await llm_router.route(request)
            content = response.content.lower()
        except Exception as e:
            return {"passed": False, "errors": [f"LLM call failed: {str(e)}"]}

        errors = []

        # Check expected substrings
        for expected in test.get("expected_contains", []):
            if expected.lower() not in content:
                errors.append(f"Missing expected text: '{expected}'")

        # Check forbidden substrings
        for forbidden in test.get("forbidden_contains", []):
            if forbidden.lower() in content:
                errors.append(f"Found forbidden text: '{forbidden}'")

        # Check token limit
        if test.get("max_tokens") and response.output_tokens > test["max_tokens"]:
            errors.append(f"Token limit exceeded: {response.output_tokens} > {test['max_tokens']}")

        return {"passed": len(errors) == 0, "errors": errors}


# ── Pytest Integration ──

@pytest.mark.asyncio
async def test_eval_suite():
    """Pytest entry point. Runs full eval suite."""
    runner = EvalRunner()
    result = await runner.run_all()

    assert result["failed"] == 0, f"{result['failed']} eval tests failed"


# ── CLI Entry Point ──

async def main():
    """Run eval suite from command line."""
    runner = EvalRunner()
    result = await runner.run_all()

    if result["failed"] > 0:
        print("\n❌ EVAL SUITE FAILED — Deploy blocked\n")
        sys.exit(1)
    else:
        print("\n✅ EVAL SUITE PASSED — Ready to deploy\n")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
