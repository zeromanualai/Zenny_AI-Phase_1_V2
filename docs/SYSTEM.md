# ZENNY AI --- SYSTEM CONTEXT
## For LLM Assistants (Kimi, Claude, GPT, etc.)
### Read This First Before Any Task
#### Last updae: 22 May
---

## YOUR ROLE

You are assisting the ZeroManual team in building **Zenny AI** --- an agentic customer support platform for Shopify and WooCommerce stores. You are NOT building a chatbot. You are building an **operations platform** where AI handles only the language layer, and deterministic code handles all business logic.

---

## PROJECT STRUCTURE

```
zeromanualai-zenny_ai-phase_1_v2/
├── docs/                          # Documentation
│   ├── GUIDE.md                   # [OUTDATED - TypeScript guide]
│   ├── GUIDE_PYTHON_v2.1.md       # [TODO - Rewrite for Python]
│   ├── ARCHITECTURE.md            # [TODO - Create]
│   └── ZENNY_LOG.md               # [LIVE - Master status tracker]
│
├── scripts/
│   ├── infrastructure/            # Docker, Nginx, setup scripts
│   ├── n8n-workflows/             # Importable JSON workflows
│   └── testing/                   # Shell test scripts
│
└── zenny-core-v2/                 # PYTHON BACKEND (FastAPI)
    ├── src/
    │   ├── main.py                # FastAPI app entry
    │   ├── config.py              # Pydantic-Settings env validation
    │   ├── types.py               # All Pydantic models
    │   │
    │   ├── api/                   # HTTP routes
    │   │   ├── webhook.py         # Voiceflow DMAPI + escalation
    │   │   ├── channels.py        # Channel gateway [PARTIAL - adapters imported but not used]
    │   │   ├── ingest.py          # Onboarding + KB [PARTIAL]
    │   │   ├── admin.py           # Internal dashboard
    │   │   └── routes.py          # Route registry
    │   │
    │   ├── services/              # Business logic
    │   │   ├── db.py              # Supabase client
    │   │   ├── redis_client.py    # Redis sessions [PARTIAL - SSL wrong]
    │   │   ├── llm_router.py      # Tiered AI routing [PARTIAL - Prompt Manager not wired]
    │   │   ├── policy_guard.py    # Deterministic rules [DONE]
    │   │   ├── state_manager.py   # Session management [DONE]
    │   │   ├── rag.py             # KB retrieval [PARTIAL - never used in flow]
    │   │   ├── action_engine.py   # n8n integration [DONE - n8n not deployed]
    │   │   ├── prompt_manager.py  # YAML loader [DONE - missing json import]
    │   │   └── pii_redactor.py    # PII redaction [DONE]
    │   │
    │   ├── integrations/          # External APIs
    │   │   ├── shopify.py         # Shopify Admin API [DONE]
    │   │   ├── woocommerce.py     # WooCommerce REST API [DONE]
    │   │   ├── stripe.py          # Stripe API [DONE]
    │   │   └── zendesk.py         # Zendesk API [DONE]
    │   │
    │   ├── channels/              # Channel adapters [DONE - not wired]
    │   │   ├── web.py
    │   │   ├── whatsapp.py
    │   │   ├── email.py
    │   │   └── messenger.py
    │   │
    │   ├── evals/                 # Test framework
    │   │   ├── suite.py           # 8 test cases
    │   │   └── runner.py          # Pytest runner
    │   │
    │   └── prompts/               # YAML prompt templates
    │       └── ecommerce-v1.0/
    │           ├── welcome.yml
    │           ├── fallback.yml
    │           ├── order_status.yml
    │           └── return_request.yml
    │
    ├── tests/                     # Pytest test suite
    ├── supabase-setup.sql         # Database schema [PARTIAL - missing llm_cost_logs]
    ├── pyproject.toml             # Poetry dependencies
    ├── Procfile                   # Railway deploy config
    ├── railway.json               # Railway build config
    └── .env.example               # [MISSING - needs creation]
```

---

## KEY ARCHITECTURAL PRINCIPLES

1. **Voiceflow is replaceable infrastructure** --- not the product. Zenny Core owns all logic.
2. **n8n is glue, not brain** --- it calls APIs but never makes business decisions.
3. **Policy Guard is code, not prompts** --- deterministic rules run BEFORE any AI generation.
4. **Cost-first LLM routing** --- T1 (Gemini Flash-Lite, ~93%), T2 (DeepSeek, ~5%), T3 (Gemini Pro, ~2%).
5. **Tenant isolation via RLS** --- every query sets `app.current_client_id`.
6. **No .env files in repo** --- all secrets via platform settings.

---

## CRITICAL GAPS (Do NOT Ignore)

| Gap | File | Issue | Fix |
|-----|------|-------|-----|
| #1 | `llm_router.py` | Prompt Manager not wired | Import and call `prompt_manager.load()` |
| #2 | `channels.py` | Adapters imported but not used | Call `adapter.normalize()` and `adapter.format_response()` |
| #3 | `supabase-setup.sql` | `llm_cost_logs` table missing | Add CREATE TABLE statement |
| #4 | `prompt_manager.py` | Missing `import json` | Add at top of file |
| #5 | `webhook.py` | Unsafe `user_email` extraction | Use safe null-checking |
| #6 | `redis_client.py` | SSL default wrong | Set `ssl=True` always |
| #7 | `webhook.py` | Order lookup fetches but ignores data | Store in session slots, pass to prompt |
| #8 | `webhook.py` | Conversation not persisted | Call `create_conversation`/`update_conversation` |
| #9 | `rag.py` | KB context never used in responses | Pass `kb_context` to prompt builder |
| #10 | `llm_router.py` | Policy Guard called with wrong args | Pass `context` and `client_policy` separately |

---

## ENVIRONMENT VARIABLES

### Required (App won't start without these)

| Variable | Source | Purpose |
|----------|--------|---------|
| `SUPABASE_URL` | Supabase Project Settings | Database |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase API Settings | Database auth |
| `REDIS_HOST` | Upstash Database Details | Cache/sessions |
| `REDIS_PASSWORD` | Upstash Database Details | Redis auth |
| `GEMINI_API_KEY` | Google AI Studio | T1/T3 LLM |
| `DEEPSEEK_API_KEY` | DeepSeek Platform | T2 LLM |
| `VOICEFLOW_DMAPI_KEY` | Voiceflow Integrations | Dialogue orchestration |
| `N8N_WEBHOOK_URL` | Your n8n instance | Workflow automation |
| `N8N_SECRET` | n8n Settings | Webhook auth |
| `ADMIN_PASSWORD` | You create this | Admin dashboard |
| `JWT_SECRET` | You create this | Token signing |

### Optional (For specific channels)

| Variable | Needed For |
|----------|------------|
| `SENDGRID_API_KEY` | Email channel |
| `TWILIO_AUTH_TOKEN` | WhatsApp via Twilio |
| `META_APP_SECRET` | Messenger |

---

## LLM TIER STRATEGY

| Tier | Model | Cost (per 1M tokens) | Use Case | Traffic % |
|------|-------|---------------------|----------|-----------|
| T1 | Gemini 2.5 Flash-Lite | $0.15 in / $0.35 out | FAQ, greetings, order status | ~93% |
| T2 | DeepSeek-Chat | $0.20 in / $0.60 out | Complex returns, troubleshooting | ~5% |
| T3 | Gemini 2.5 Pro | $1.25 in / $2.25 out | Fraud disputes, high-value escalations | ~2% |

**Rule:** If T3 usage exceeds 2%, your prompts or policy guards are weak.

---

## N8N WORKFLOWS

| Workflow | File | Trigger | Status |
|----------|------|---------|--------|
| Shopify Order Lookup | `shopify-order-lookup.json` | Zenny webhook | JSON ready, not deployed |
| Stripe Refund | `stripe-refund.json` | Zenny webhook | JSON ready, not deployed |
| Zendesk Ticket | `zendesk-ticket-create.json` | Escalation | JSON ready, not deployed |
| Google Calendar | `gcal-find-slots.json` | Booking intent | JSON ready, not deployed |
| Slack Notify | `slack-notify.json` | Escalation/failure | JSON ready, not deployed |
| WooCommerce Lookup | [NOT CREATED] | Zenny webhook | Needs creation |

---

## TESTING

```bash
# --- LOCAL MACHINE (Static checks only) ---
# Syntax / import validation
poetry run python -m py_compile src/main.py

# Linting
poetry run black src/ --check
poetry run ruff check src/

# --- CLOUD TESTING (All integration & E2E tests) ---
# Trigger full CI suite on Railway preview/staging
gh workflow run staging-tests.yml --ref main

# Health check against cloud dev/staging instance
curl https://zenny-dev.up.railway.app/health

# Manual webhook smoke test against cloud instance
curl -X POST https://zenny-dev.up.railway.app/v1/webhook?client_id=test-store \
  -H "Content-Type: application/json" \
  -d '{"action":"request","user_id":"u1","message":"hello"}'

# Run cloud E2E script locally (hits staging, not localhost)
export ZENNY_BASE_URL=https://zenny-staging.up.railway.app
poetry run python scripts/testing/test-e2e-cloud.py
```

> **Rule:** No `pytest`, no `uvicorn --reload`, and no `localhost:8000` on developer laptops.  
> All test execution that requires services (Supabase, Redis, LLMs, n8n) runs in Railway CI or against the cloud staging URL.

---

## BEFORE YOU START ANY TASK

1. **Read `ZENNY_LOG.md`** --- Check current status and recent changes
2. **Check this file** --- Understand the architecture
3. **Identify which gap you're fixing** --- Reference Gap # above
4. **After completing, append to `ZENNY_LOG.md`** --- Keep status current

---

## COMMON MISTAKES TO AVOID

1. **Don't put business logic in n8n** --- n8n calls APIs only. Decisions happen in Zenny Core.
2. **Don't let LLM make refund decisions** --- Policy Guard blocks ALL refunds before LLM sees them.
3. **Don't commit .env files** --- Use platform settings (Railway, Hetzner, GitHub Secrets).
4. **Don't use GPT-4 for everything** --- T1 handles 93% of traffic at 1/50th the cost.
5. **Don't build for hypothetical demand** --- Phase 1 = Shopify/WooCommerce only.

---

## TESTING & DEPLOYMENT PHILOSOPHY

### Cloud-First Testing (No Local Test Deployment)

**Rule:** Zenny AI does not support local test deployments. All integration tests, E2E validation, and service boot verification must run against cloud environments.

**Why:** The stack requires managed services (Supabase, Upstash Redis, LLM APIs, n8n) that cannot be reliably mocked locally. Local development is limited to:
- Static code linting/type checks
- Simple `curl` or `poetry run` commands against the **cloud dev instance**
- Unit tests that require no external services (if any)

**Cloud Test Environments:**

| Environment | Platform | Purpose | Trigger |
|-------------|----------|---------|---------|
| Dev Preview | Railway (ephemeral) | PR-level smoke tests | Git push to `develop` |
| Staging | Railway (persistent) | E2E + eval suite | Merge to `main` |
| n8n Test | OCI Free Tier | Workflow validation | Manual / CI |

**Local Machine --- Allowed Only:**
```bash
# Check syntax / imports
poetry run python -m py_compile src/main.py

# Hit the cloud dev instance (never localhost:8000)
curl https://zenny-dev-preview.up.railway.app/health

# Trigger CI test suite remotely
gh workflow run staging-tests.yml --ref develop
```

**Local Machine --- Explicitly Forbidden:**
- `poetry run pytest tests/` (use CI instead)
- `docker-compose up` for local n8n (use OCI)
- `uvicorn src.main:app --reload` for integration testing
- Any test that requires Supabase, Redis, or LLM keys to be "local"

---

## DECISIONS MADE

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-05-20 | Python/FastAPI over TypeScript | Team skillset, ML ecosystem |
| 2026-05-17 | Voiceflow as temporary orchestrator | Speed to market, replaceable later |
| 2026-05-17 | n8n on OCI Free Tier for testing | Cost savings during development |
| 2026-05-16 | Gemini + DeepSeek over GPT-4 | 50x cost savings, same quality for support Q&A |

---

*Read ZENNY_LOG.md for current status. Read this file for context. Then start working.*
