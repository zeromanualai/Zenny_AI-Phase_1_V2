"""
LLM Router — Tiered Cost-Optimized Routing
T1: Gemini Flash-Lite (~93-97%) | T2: DeepSeek-Chat (~2-5%) | T3: Gemini Pro (~0-2%)
"""

from src.services.prompt_manager import prompt_manager
import time
import json
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

import google.generativeai as genai
from openai import AsyncOpenAI

from src.config import settings
from src.services import redis_client
from src.services.db import log_llm_cost
from src.services.policy_guard import policy_guard
from src.types import LLMRequest, LLMResponse, PolicyResult


# ── Model Config ──
MODELS = {
    "T1": {
        "name": "gemini-2.5-flash-lite-preview-06-17",
        "provider": "google",
        "input_cost": Decimal("0.15"),   # per 1M tokens
        "output_cost": Decimal("0.35"),  # per 1M tokens
        "max_tokens": 500,
    },
    "T2": {
        "name": "deepseek-chat",
        "provider": "deepseek",
        "input_cost": Decimal("0.20"),
        "output_cost": Decimal("0.60"),
        "max_tokens": 2000,
    },
    "T3": {
        "name": "gemini-2.5-pro-preview-06-05",
        "provider": "google",
        "input_cost": Decimal("1.25"),
        "output_cost": Decimal("2.25"),
        "max_tokens": 4000,
    },
}

# ── Provider Setup ──
genai.configure(api_key=settings.gemini_api_key)

deepseek_client = AsyncOpenAI(
    api_key=settings.deepseek_api_key,
    base_url="https://api.deepseek.com/v1",
)


class LLMRouter:
    """Routes requests to the right model tier. Caches T1. Logs costs."""

    async def route(self, request: LLMRequest) -> LLMResponse:
        """Main entry point."""
        start_time = time.time()

        # 1. Policy Guard first (non-LLM)
        if request.intent in ("refund_request", "return_request"):
            policy = await policy_guard.evaluate(
                "REFUND",
                request.context.model_dump(),
                request.context.client.model_dump(),
            )
            if not policy.allowed:
                return self._policy_response(policy, request, start_time)

        # 2. Cache check (T1 only)
        cache_key_data = {
            "message": request.message,
            "intent": request.intent,
            "client_id": request.context.client.id,
        }
        cached = await redis_client.get_cache("llm", cache_key_data)
        if cached:
            return LLMResponse(
                content=cached["content"],
                model_used=cached["model_used"],
                tier=cached["tier"],
                input_tokens=0,
                output_tokens=0,
                cost_usd=Decimal("0"),
                cached=True,
                latency_ms=int((time.time() - start_time) * 1000),
            )

        # 3. Tier routing
        tier = self._select_tier(request)
        model_config = MODELS[tier]

        # 4. Build prompt
        prompt = await self._build_prompt(request)

        # 5. Execute
        content, input_tokens, output_tokens = await self._call_provider(
            tier, model_config, prompt
        )

        # 6. Calculate cost
        cost = self._calculate_cost(model_config, input_tokens, output_tokens)

        # 7. Cache T1 responses
        if tier == "T1":
            await redis_client.set_cache(
                "llm",
                cache_key_data,
                {"content": content, "model_used": model_config["name"], "tier": tier},
                ttl=86400,
            )

        # 8. Log cost (to dedicated table, NOT empty conversation rows)
        await log_llm_cost(
            client_id=request.context.client.id,
            conversation_id=None,  # Will be set by caller if available
            model_used=model_config["name"],
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=float(cost),
        )

        latency_ms = int((time.time() - start_time) * 1000)

        return LLMResponse(
            content=content,
            model_used=model_config["name"],
            tier=tier,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            cached=False,
            latency_ms=latency_ms,
        )

    def _select_tier(self, request: LLMRequest) -> str:
        """Determine model tier based on intent, complexity, client tier."""
        intent = request.intent
        complexity = request.complexity
        client_tier = request.client_tier

        # T3: High-stakes only
        if client_tier == "enterprise" or intent in ("dispute", "legal", "compliance", "fraud_review"):
            return "T3"

        # T2: Multi-step reasoning
        if intent in ("refund_logic", "technical_debug", "compare_products", "calendar_conflict") or complexity > 0.7:
            return "T2"

        # T1: Everything else
        return "T1"

    async def _build_prompt(self, request: LLMRequest) -> str:
        """
        Build prompt from context.
        TODO: Wire Prompt Manager here when Gap #1 is filled.
        For now, inline construction (same as TypeScript).
        """
        client = request.context.client
        kb = request.context.kb_context or ""
        history = request.context.transcript

        # Build conversation history string
        history_str = "\n".join([
            f"{'User' if t.role == 'user' else 'Assistant'}: {t.content}"
            for t in history[-6:]  # Last 6 turns
        ])

        prompt = f"""You are {client.agent_name}, the support assistant for {client.slug}.
Tone: {client.tone}. Timezone: {client.timezone}.

Guidelines:
- Always confirm the order number before providing details
- Never promise delivery dates not in tracking data
- For returns, mention the policy window: {client.return_policy_days} days

Knowledge Base Context:
{kb}

Conversation History:
{history_str}

User message: {request.message}

Respond helpfully and concisely:"""

        return prompt

    async def _call_provider(
        self,
        tier: str,
        model_config: dict,
        prompt: str,
    ) -> tuple[str, int, int]:
        """Call the appropriate LLM provider."""
        provider = model_config["provider"]
        model_name = model_config["name"]
        max_tokens = model_config["max_tokens"]

        if provider == "google":
            return await self._call_gemini(model_name, prompt, max_tokens)

        if provider == "deepseek":
            return await self._call_deepseek(model_name, prompt, max_tokens)

        raise ValueError(f"Unknown provider: {provider}")

    async def _call_gemini(self, model_name: str, prompt: str, max_tokens: int) -> tuple[str, int, int]:
        """Call Google Gemini API."""
        model = genai.GenerativeModel(model_name)
        response = await model.generate_content_async(
            prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=0.7,
            ),
        )
        content = response.text or ""
        # Gemini doesn't always return token counts; estimate if missing
        input_tokens = getattr(response.usage_metadata, "prompt_token_count", len(prompt) // 4)
        output_tokens = getattr(response.usage_metadata, "candidates_token_count", len(content) // 4)
        return content, input_tokens, output_tokens

    async def _call_deepseek(self, model_name: str, prompt: str, max_tokens: int) -> tuple[str, int, int]:
        """Call DeepSeek API (OpenAI-compatible)."""
        response = await deepseek_client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.7,
        )
        content = response.choices[0].message.content or ""
        input_tokens = response.usage.prompt_tokens if response.usage else len(prompt) // 4
        output_tokens = response.usage.completion_tokens if response.usage else len(content) // 4
        return content, input_tokens, output_tokens

    def _calculate_cost(self, model_config: dict, input_tokens: int, output_tokens: int) -> Decimal:
        """Calculate cost in USD."""
        input_cost = (Decimal(input_tokens) / Decimal("1000000")) * model_config["input_cost"]
        output_cost = (Decimal(output_tokens) / Decimal("1000000")) * model_config["output_cost"]
        total = input_cost + output_cost
        return total.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)

    def _policy_response(self, policy: PolicyResult, request: LLMRequest, start_time: float) -> LLMResponse:
        """Generate response when Policy Guard blocks action."""
        reason_map = {
            "FRAUD_REVIEW": "This order has been flagged for review. A support agent will contact you within 24 hours.",
            "POLICY_EXPIRED": f"Our return policy covers orders within {request.context.client.return_policy_days} days. This order is outside that window.",
            "MANUAL_REVIEW_REQUIRED": "This request requires manual review. I've escalated this to our team.",
            "ANNUAL_CANCELLATION_BLOCKED": "Annual subscriptions cannot be cancelled mid-term. I can offer to pause your subscription instead.",
        }
        content = reason_map.get(policy.reason, "I'm unable to process this request. Let me connect you with a support agent.")

        latency_ms = int((time.time() - start_time) * 1000)

        return LLMResponse(
            content=content,
            model_used="policy-guard",
            tier="T1",
            input_tokens=0,
            output_tokens=0,
            cost_usd=Decimal("0"),
            cached=False,
            latency_ms=latency_ms,
        )


# Singleton
llm_router = LLMRouter()
