"""
Zenny Core Type Definitions
All request/response/context models in one place.
Replaces TypeScript interfaces with Pydantic v2 BaseModel.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Any, Literal
from datetime import datetime
from decimal import Decimal


# ──────────────────────────────────────────
# Client / Tenant Models
# ──────────────────────────────────────────

class ClientConfig(BaseModel):
    """Per-tenant configuration loaded from Supabase clients table."""
    id: str
    slug: str
    industry: str = "ecommerce"
    platform: Literal["shopify", "woocommerce"] = "shopify"
    agent_name: str = "Zenny"
    welcome_message: Optional[str] = None
    tone: str = "friendly_professional"
    primary_color: str = "#6366F1"
    channels_enabled: dict = Field(default_factory=lambda: {"web": True})
    business_hours: Optional[dict] = None
    escalation_email: Optional[str] = None
    timezone: str = "UTC"
    return_policy_days: int = 30
    fraud_threshold: float = 0.8
    plan: str = "starter"
    monthly_conversation_limit: int = 2000
    # Commerce credentials (encrypted at app layer)
    shopify_domain: Optional[str] = None
    shopify_access_token: Optional[str] = None
    woocommerce_url: Optional[str] = None
    woocommerce_consumer_key: Optional[str] = None
    woocommerce_consumer_secret: Optional[str] = None
    stripe_account_id: Optional[str] = None
    zendesk_subdomain: Optional[str] = None
    zendesk_api_token: Optional[str] = None


# ──────────────────────────────────────────
# Conversation / Message Models
# ──────────────────────────────────────────

class NormalizedMessage(BaseModel):
    """Unified message format across all channels."""
    channel: Literal["web", "whatsapp", "email", "messenger"]
    client_id: str
    user_id: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict = Field(default_factory=dict)


class ConversationTurn(BaseModel):
    """Single turn in a conversation transcript."""
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    model_used: Optional[str] = None
    cost_usd: Optional[Decimal] = None


class ConversationContext(BaseModel):
    """Full context for a conversation turn."""
    client: ClientConfig
    user_id: str
    session: "SessionState"
    transcript: list[ConversationTurn] = Field(default_factory=list)
    kb_context: Optional[str] = None


# ──────────────────────────────────────────
# Session / State Models
# ──────────────────────────────────────────

class SessionState(BaseModel):
    """Redis session object."""
    client_id: str
    user_id: str
    channel: str
    slots: dict = Field(default_factory=dict)
    intent_history: list[str] = Field(default_factory=list)
    turn_count: int = 0
    created_at: int = Field(default_factory=lambda: int(datetime.utcnow().timestamp()))
    last_activity: int = Field(default_factory=lambda: int(datetime.utcnow().timestamp()))
    merged_from: Optional[list[str]] = None

    @field_validator("slots", mode="before")
    @classmethod
    def ensure_dict(cls, v):
        return v or {}


# ──────────────────────────────────────────
# LLM / AI Models
# ──────────────────────────────────────────

class LLMRequest(BaseModel):
    """Input to LLM Router."""
    message: str
    intent: str
    complexity: float = 0.0
    sentiment: float = 0.0
    client_tier: str = "starter"
    context: ConversationContext
    max_tokens: Optional[int] = None


class LLMResponse(BaseModel):
    """Output from LLM Router."""
    content: str
    model_used: str
    tier: Literal["T1", "T2", "T3"]
    input_tokens: int
    output_tokens: int
    cost_usd: Decimal
    cached: bool = False
    latency_ms: int = 0


# ──────────────────────────────────────────
# Policy / Action Models
# ──────────────────────────────────────────

class PolicyResult(BaseModel):
    """Output from Policy Guard."""
    allowed: bool
    reason: Optional[str] = None
    escalate: bool = False
    priority: Optional[Literal["low", "medium", "high", "urgent"]] = None
    suggestion: Optional[str] = None


class ActionRequest(BaseModel):
    """Input to Action Engine."""
    action_name: str
    params: dict = Field(default_factory=dict)
    client_id: str
    conversation_id: Optional[str] = None


class ActionResult(BaseModel):
    """Output from Action Engine."""
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None
    latency_ms: int = 0


# ──────────────────────────────────────────
# Webhook / API Models
# ──────────────────────────────────────────

class VoiceflowWebhookPayload(BaseModel):
    """Payload from Voiceflow DMAPI."""
    action: str
    user_id: str
    client_id: str
    message: Optional[str] = None
    session_context: Optional[dict] = None
    slots: Optional[dict] = None


class EscalationPayload(BaseModel):
    """Payload for escalation webhook."""
    client_id: str
    user_id: str
    transcript: list[ConversationTurn]
    reason: str
    priority: Optional[str] = "medium"
    user_email: Optional[str] = None


class IngestConfigPayload(BaseModel):
    """Payload for merchant onboarding."""
    store_name: str
    store_url: str
    platform: Literal["shopify", "woocommerce"]
    agent_name: Optional[str] = "Zenny"
    tone: Optional[str] = "friendly_professional"
    welcome_message: Optional[str] = None
    business_hours: Optional[dict] = None
    escalation_email: Optional[str] = None
    timezone: Optional[str] = "UTC"
    return_policy_days: Optional[int] = 30
    channels: Optional[list[str]] = None
    integrations: Optional[dict] = None


# ──────────────────────────────────────────
# Admin / Analytics Models
# ──────────────────────────────────────────

class CostLogEntry(BaseModel):
    """Entry in llm_cost_logs table."""
    id: Optional[str] = None
    client_id: str
    conversation_id: Optional[str] = None
    model_used: str
    input_tokens: int
    output_tokens: int
    cost_usd: Decimal
    created_at: Optional[datetime] = None


class ConversationSummary(BaseModel):
    """Summary for admin dashboard."""
    id: str
    client_id: str
    user_email: Optional[str] = None
    channel: str
    resolved: bool
    escalated: bool
    model_used: Optional[str] = None
    llm_cost_usd: Optional[Decimal] = None
    created_at: datetime
