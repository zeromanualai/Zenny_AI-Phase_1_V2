# ZENNY CORE — BATCH 1 PYTHON MIGRATION
## Installation & Setup Guide

---

## WHAT YOU RECEIVED (30 Files)

### Core Application (12 files)
| File | Purpose |
|------|---------|
| `pyproject.toml` | Poetry dependencies (FastAPI, Pydantic, Supabase, Redis, etc.) |
| `src/main.py` | FastAPI app factory + health check + middleware |
| `src/config.py` | Pydantic-Settings env validation |
| `src/types.py` | All Pydantic models (requests, responses, contexts) |
| `src/api/routes.py` | Route registry |
| `src/api/webhook.py` | Voiceflow DMAPI + escalation fix (Gap #9) |
| `src/api/channels.py` | Channel gateway (Web, WhatsApp, Email, Messenger) |
| `src/api/ingest.py` | Merchant onboarding + KB upload |
| `src/api/admin.py` | Internal dashboard endpoints + cost analytics |

### Services (9 files)
| File | Purpose |
|------|---------|
| `src/services/db.py` | Supabase client + cost logging (Gap #3 fix) |
| `src/services/redis_client.py` | Async Redis (sessions, cache, cross-channel merge) |
| `src/services/llm_router.py` | Tiered routing T1/T2/T3 + cost tracking |
| `src/services/policy_guard.py` | Deterministic business rules |
| `src/services/state_manager.py` | Session + slot + async action management |
| `src/services/rag.py` | KB retrieval via pgvector |
| `src/services/action_engine.py` | n8n webhook caller |
| `src/services/prompt_manager.py` | YAML prompt loader + tenant overrides (Gap #1) |
| `src/services/pii_redactor.py` | PII redaction before LLM calls (Gap #10) |

### Config & Deploy (5 files)
| File | Purpose |
|------|---------|
| `Procfile` | Railway: Gunicorn + Uvicorn workers |
| `railway.json` | Railway build + deploy config |
| `.env.example` | Template for local development |
| `README.md` | Quick start guide |

### Tests (4 files)
| File | Purpose |
|------|---------|
| `tests/conftest.py` | Pytest fixtures |
| `tests/test_policy_guard.py` | 6 policy guard tests |
| `tests/test_pii_redactor.py` | 6 PII redaction tests |
| `tests/test_health.py` | Health endpoint test |

---

## WHERE TO PLACE FILES

### In Your Repo

```
Zenny-AI---Phase-1/
├── docs/                          # KEEP existing docs
│   ├── GUIDE.md
│   └── env*.md (create these)
│
├── scripts/                       # KEEP existing scripts
│   ├── infrastructure/
│   ├── n8n-workflows/
│   └── testing/
│
├── zenny-core/                    # REPLACE with new Python code
│   ├── pyproject.toml             # ← NEW (replace package.json)
│   ├── Procfile                   # ← NEW
│   ├── railway.json               # ← NEW (update start command)
│   ├── .env.example               # ← NEW
│   ├── README.md                  # ← NEW
│   ├── supabase-setup.sql         # KEEP existing
│   │
│   ├── src/                       # ← NEW (replace src/)
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── types.py
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── routes.py
│   │   │   ├── webhook.py
│   │   │   ├── channels.py
│   │   │   ├── ingest.py
│   │   │   └── admin.py
│   │   │
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── db.py
│   │       ├── redis_client.py
│   │       ├── llm_router.py
│   │       ├── policy_guard.py
│   │       ├── state_manager.py
│   │       ├── rag.py
│   │       ├── action_engine.py
│   │       ├── prompt_manager.py
│   │       └── pii_redactor.py
│   │
│   └── tests/                     # ← NEW
│       ├── __init__.py
│       ├── conftest.py
│       ├── test_policy_guard.py
│       ├── test_pii_redactor.py
│       └── test_health.py
│
└── dashboard/                     # Phase 2 (not in this batch)
```

### What to Delete from Old Repo
```bash
# Remove old TypeScript files
rm -rf zenny-core/src/*.ts
rm -rf zenny-core/src/api/*.ts
rm -rf zenny-core/src/services/*.ts
rm -rf zenny-core/src/integrations/*.ts
rm -rf zenny-core/src/channels/*.ts
rm -rf zenny-core/src/evals/*.ts
rm zenny-core/package.json
rm zenny-core/package-lock.json
rm zenny-core/tsconfig.json

# Keep these:
# zenny-core/supabase-setup.sql
# zenny-core/src/prompts/ecommerce-v1.0/*.yml
# scripts/*
# docs/*
```

---

## STEP-BY-STEP SETUP

### Step 1: Install Poetry
```bash
curl -sSL https://install.python-poetry.org | python3 -
# Or on macOS: brew install poetry
```

### Step 2: Copy Files
```bash
# Copy all batch1 files into zenny-core/
cp -r batch1_python_migration/* zenny-core/
```

### Step 3: Install Dependencies
```bash
cd zenny-core
poetry install
```

### Step 4: Set Environment Variables
```bash
# Copy template
cp .env.example .env

# Edit .env with your real keys
nano .env
```

### Step 5: Run Locally
```bash
poetry run uvicorn src.main:app --reload
```

### Step 6: Test
```bash
# Health check
curl http://localhost:8000/health

# Run tests
poetry run pytest
```

---

## DEPLOY TO RAILWAY

### Step 1: Push to GitHub
```bash
git add .
git commit -m "Migrate to Python/FastAPI - Batch 1"
git push origin main
```

### Step 2: Railway Dashboard
1. Go to Railway dashboard
2. Your project auto-detects Python (from `pyproject.toml`)
3. Set env vars from `docs/env-railway.md`
4. Deploy

### Step 3: Update Voiceflow
Change API step URLs from old TypeScript domain to new Railway domain:
```
# Old
https://old-zenny-api.zeromanual.com/v1/webhook?client_id={slug}

# New
https://new-zenny-api.zeromanual.com/v1/webhook?client_id={slug}
```

---

## GAPS CLOSED IN THIS BATCH

| Gap | Status | How |
|-----|--------|-----|
| #1 Prompt Manager | ✅ | `services/prompt_manager.py` loads YAML + tenant overrides |
| #3 Cost Logging | ✅ | `db.py` uses dedicated `llm_cost_logs` table |
| #9 Escalation | ✅ | `webhook.py` calls n8n → Zendesk + Slack |
| #10 PII Redaction | ✅ | `pii_redactor.py` strips CC, SSN, phone, email |

---

## WHAT'S NOT IN THIS BATCH (Batch 2)

These will come in the next batch:
- `integrations/shopify.py`, `stripe.py`, `zendesk.py`, `woocommerce.py`
- `channels/web.py`, `whatsapp.py`, `email.py`, `messenger.py`
- `evals/suite.py`, `evals/runner.py`
- Full end-to-end conversation flow

---

## TROUBLESHOOTING

| Error | Fix |
|-------|-----|
| `ModuleNotFoundError: No module named 'src'` | Run from `zenny-core/` directory, not `zenny-core/src/` |
| `Redis connection refused` | Check `REDIS_HOST` env var. Upstash uses TLS. |
| `Supabase URL invalid` | Must include `https://` and end with `.supabase.co` |
| `Gemini API key invalid` | Get key from Google AI Studio |
| `Tests fail` | Make sure `.env` is filled with real keys, or mock in `conftest.py` |

---

*Batch 1 of 2. Core scaffold + services complete.*
