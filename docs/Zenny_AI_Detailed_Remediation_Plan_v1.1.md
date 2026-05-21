# ZENNY AI --- DETAILED REMEDIATION PLAN
## From "Code Exists" to "Store #1 Pilot Ready"
### Version: 1.0 | Date: May 2026 | Status: ACTION REQUIRED

---

## EXECUTIVE SUMMARY

**Current State:** ~40% complete. All components exist as isolated modules. Critical wiring gaps prevent any end-to-end conversation flow from working.

**Target State:** Store #1 pilot ready --- a real merchant can send "Where is my order?" and get a correct response with real Shopify data.

**Timeline:** 2 weeks (10 working days) if executed sequentially. 1 week if parallelized with your team.

**Critical Path:** Fix SQL schema -> Wire components -> Deploy n8n -> Test end-to-end

---

## PHASE A: FOUNDATION FIXES (Days 1-2)
*Fix things that will crash immediately*

---

### A1. Fix `supabase-setup.sql` --- ADD MISSING `llm_cost_logs` TABLE

**Priority:** CRITICAL (App crashes on first LLM call without this)
**File:** `zenny-core-v2/supabase-setup.sql`
**Effort:** 15 minutes

**Add this block BEFORE the `-- DONE` comment:**

```sql
-- =====================================================
-- LLM COST LOGS (Gap #3 Fix)
-- =====================================================

CREATE TABLE IF NOT EXISTS llm_cost_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id UUID REFERENCES clients(id),
  conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
  model_used TEXT NOT NULL,
  input_tokens INT NOT NULL DEFAULT 0,
  output_tokens INT NOT NULL DEFAULT 0,
  cost_usd DECIMAL(10,6) NOT NULL DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_llm_cost_logs_client_created 
  ON llm_cost_logs(client_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_llm_cost_logs_model 
  ON llm_cost_logs(model_used, created_at DESC);
```

**Action:**
1. Open Supabase SQL Editor
2. Run the above SQL
3. Verify: `SELECT * FROM llm_cost_logs LIMIT 1;` should return empty (not error)

**Verification:**
```bash
# Run against cloud dev instance (Railway)
curl -X POST https://zenny-dev.up.railway.app/v1/webhook \
  -H "Content-Type: application/json" \
  -d '{"client_id":"test-store","user_id":"u1","message":"hello","action":"request"}'
# Should NOT crash with "relation llm_cost_logs does not exist"
```

---

### A2. Fix `prompt_manager.py` --- ADD MISSING `json` IMPORT

**Priority:** CRITICAL (App crashes when Prompt Manager is called)
**File:** `zenny-core-v2/src/services/prompt_manager.py`
**Effort:** 1 minute

**At the top of the file, add:**
```python
import json  # <-- ADD THIS LINE
import os
import yaml
from string import Template
from typing import Optional
```

**Root Cause:** The `_render()` method calls `json.dumps()` but `json` was never imported.

**Verification:**
```bash
# Static import check (local OK)
poetry run python -c "from src.services.prompt_manager import prompt_manager; print('OK')"

# Full prompt load test (cloud only — via CI or curl to dev instance)
curl -X POST https://zenny-dev.up.railway.app/v1/admin/test-prompt \
  -H "Content-Type: application/json" \
  -d '{"prompt_name":"welcome","version":"ecommerce-v1.0"}'
```

---

### A3. Fix `webhook.py` --- SAFE `user_email` EXTRACTION

**Priority:** HIGH (Crashes when `session_context` is None)
**File:** `zenny-core-v2/src/api/webhook.py`
**Effort:** 5 minutes

**Replace this block (around line 65-70):**
```python
# OLD --- CRASHES if session_context is None
user_email = session.get("slots", {}).get("user_email") or payload.session_context.get("user_email") if payload.session_context else None
```

**With:**
```python
# NEW --- Safe extraction
user_email = None
if session and session.get("slots"):
    user_email = session["slots"].get("user_email")
if not user_email and payload.session_context:
    user_email = payload.session_context.get("user_email")
```

**Also fix the Shopify/WooCommerce block (lines 72-82):**
The current code fetches orders but does nothing with them. Replace with actual order context handling that stores results in session slots and passes to prompt builder.

---

### A4. Fix `redis_client.py` --- FORCE SSL FOR UPSTASH

**Priority:** HIGH (Redis connection fails in dev and prod)
**File:** `zenny-core-v2/src/services/redis_client.py`
**Effort:** 2 minutes

**Replace:**
```python
_redis = redis.from_url(
    settings.redis_url,
    decode_responses=True,
    ssl=True if settings.is_production else False,
)
```

**With:**
```python
_redis = redis.from_url(
    settings.redis_url,
    decode_responses=True,
    ssl=True,  # Upstash requires TLS always
)
```

**Root Cause:** Upstash is a cloud Redis service. It requires TLS regardless of environment.

---

### A5. Create `.env.example` FILE

**Priority:** HIGH (New developers cannot boot the app)
**File:** `zenny-core-v2/.env.example` (NEW FILE)
**Effort:** 10 minutes

```env
# ============================================
# ZENNY CORE --- Environment Variables Template
# Copy to .env and fill with real values
# NEVER commit .env to Git
# ============================================

# Server
PORT=8000
HOST=0.0.0.0
ENVIRONMENT=development

# Supabase (Required)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...

# Redis / Upstash (Required)
REDIS_HOST=your-host.upstash.io
REDIS_PORT=6379
REDIS_PASSWORD=your-password
REDIS_USERNAME=default

# LLM Providers (Required)
GEMINI_API_KEY=AIza...
DEEPSEEK_API_KEY=sk-...

# Voiceflow (Required)
VOICEFLOW_DMAPI_KEY=VF.DM...

# n8n (Required)
N8N_WEBHOOK_URL=https://your-n8n-domain.com/webhook
N8N_SECRET=your-secret-key

# Integrations --- Channels (Optional, enable as needed)
SENDGRID_API_KEY=SG...
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_ACCOUNT_SID=AC...
META_APP_SECRET=your-meta-secret
META_PAGE_ACCESS_TOKEN=your-page-token

# Security (Required)
ADMIN_PASSWORD=your-secure-admin-password
JWT_SECRET=random-string-32-chars-min
```

---

## PHASE B: COMPONENT WIRING (Days 3-5)
*Make isolated modules talk to each other*

---

### B1. Wire Prompt Manager into LLM Router

**Priority:** CRITICAL (Tenant customization does not work)
**File:** `zenny-core-v2/src/services/llm_router.py`
**Effort:** 2 hours

**Step 1: Import Prompt Manager**
```python
# At top of llm_router.py, add:
from src.services.prompt_manager import prompt_manager
```

**Step 2: Replace `_build_prompt()` method entirely**

The new method should:
1. Determine prompt template name from intent
2. Build variables dict from client config + kb_context + order_context
3. Call `prompt_manager.load(version, prompt_name, variables, client_id)`
4. Fall back to inline prompt if YAML not found

**Step 3: Fix Prompt Manager path resolution**

In `prompt_manager.py`, the path lookup is wrong. The YAML files are at `prompts/ecommerce-v1.0/` not `prompts/v1.0/ecommerce/`.

**Replace `_load_base()`:**
```python
    def _load_base(self, version: str, prompt_name: str) -> str:
        path = os.path.join(PROMPTS_DIR, version, f"{prompt_name}.yml")
        if not os.path.exists(path):
            raise FileNotFoundError(f"Prompt not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data.get("base", "")
```

**Verification:**
```bash
# Local: static syntax check only
poetry run python -m py_compile src/services/llm_router.py

# Cloud (Railway dev instance):
curl -X POST https://zenny-dev.up.railway.app/v1/webhook \
  -H "Content-Type: application/json" \
  -d '{"client_id":"test-store","user_id":"u1","message":"hi","action":"request"}'
# Response should contain brand-aware welcome text loaded from YAML
```

---

### B2. Wire RAG Context into LLM Prompts

**Priority:** HIGH (KB retrieval is wasted)
**File:** `zenny-core-v2/src/services/llm_router.py` (covered in B1)
**Effort:** Included in B1

The `_build_prompt()` method in B1 already accepts `kb_context`. The `webhook.py` already calls `rag_service.query()`. Just ensure the `ConversationContext` is built correctly with `kb_context` passed through.

---

### B3. Wire Channel Adapters into API

**Priority:** HIGH (Channels do not actually work)
**File:** `zenny-core-v2/src/api/channels.py`
**Effort:** 1 hour

**Replace the entire `receive_message()` function to:**
1. Use the adapter's `normalize()` method on incoming payload
2. Extract identifiers for cross-channel merge
3. Build full ConversationContext with PII redaction + RAG
4. Route through LLM Router
5. Use adapter's `format_response()` on the output
6. Return formatted response

**Add missing imports:**
```python
from src.types import ClientConfig, ConversationTurn, ConversationContext, LLMRequest
from src.services.llm_router import llm_router
from src.services.rag import rag_service
from src.services.pii_redactor import pii_redactor
```

---

### B4. Add Conversation Persistence

**Priority:** HIGH (No conversation history = no analytics)
**File:** `zenny-core-v2/src/api/webhook.py` AND `zenny-core-v2/src/api/channels.py`
**Effort:** 1 hour

**Create a helper function `_persist_conversation()` that:**
1. Checks for existing conversation for this user today
2. Appends new turns to transcript
3. Updates cost and model info
4. Returns conversation_id

**Call this in both webhook handlers before returning the response.**

---

### B5. Fix Policy Guard Context Passing

**Priority:** MEDIUM (Wrong policy parameters)
**File:** `zenny-core-v2/src/services/llm_router.py`
**Effort:** 15 minutes

**Replace the Policy Guard call to pass:**
- `context`: with `order` (from session slots) and `user` (verification status)
- `client_policy`: with `max_return_days` and `fraud_threshold` from client config

Not the entire `model_dump()` of context and client.

---

## PHASE C: N8N DEPLOYMENT (Days 6-7)
*Get the glue running*

---

### C1. Deploy n8n on OCI (Test Environment)

**Priority:** CRITICAL (No actions work without n8n)
**Effort:** 3 hours

**Option A: Oracle Cloud Free Tier (Recommended for testing)**

1. **Create OCI Account:**
   - Go to cloud.oracle.com
   - Sign up for Free Tier (always-free resources)
   - Create a VM.Standard.E2.1.Micro instance (1 OCPU, 1GB RAM --- FREE forever)

2. **SSH into instance:**
```bash
ssh -i ~/.ssh/oci_key ubuntu@YOUR_OCI_IP
```

3. **Install Docker:**
```bash
sudo apt update
sudo apt install -y docker.io docker-compose
sudo usermod -aG docker ubuntu
# Log out and back in
```

4. **Create `.env` file:**
```bash
mkdir -p ~/zenny-n8n
cd ~/zenny-n8n
cat > .env << 'EOF'
N8N_HOST=YOUR_OCI_IP
N8N_PASSWORD=your-secure-password
N8N_ENCRYPTION_KEY=your-32-char-encryption-key
N8N_WEBHOOK_URL=http://YOUR_OCI_IP:5678/
EOF
```

5. **Create `docker-compose.yml`:**
```yaml
version: '3.8'
services:
  n8n:
    image: n8nio/n8n:latest
    restart: always
    ports:
      - "5678:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=zenny
      - N8N_BASIC_AUTH_PASSWORD=${N8N_PASSWORD}
      - N8N_HOST=${N8N_HOST}
      - N8N_PORT=5678
      - N8N_PROTOCOL=http
      - WEBHOOK_URL=${N8N_WEBHOOK_URL}
      - GENERIC_TIMEZONE=UTC
      - N8N_ENCRYPTION_KEY=${N8N_ENCRYPTION_KEY}
    volumes:
      - n8n_data:/home/node/.n8n
volumes:
  n8n_data:
```

6. **Start n8n:**
```bash
docker compose up -d
docker logs -f zenny-n8n-n8n-1  # Wait for "Editor is now accessible"
```

7. **Open n8n:** `http://YOUR_OCI_IP:5678`
   - Login: `zenny` / your password

8. **Import workflows:**
   - Settings (gear icon) -> Import from File
   - Import each JSON from `scripts/n8n-workflows/`
   - Update credentials in each node
   - Activate each workflow

9. **Test webhook:**
```bash
curl -X POST http://YOUR_OCI_IP:5678/webhook/slack-notify \
  -H "Content-Type: application/json" \
  -d '{"message":"Test from Zenny","channel":"#zenny-alerts"}'
```

10. **Update Zenny Core `.env`:**
```env
N8N_WEBHOOK_URL=http://YOUR_OCI_IP:5678/webhook
N8N_SECRET=your-secret-key
```

---

### C2. Create WooCommerce n8n Workflow

**Priority:** MEDIUM (Needed for Store #3)
**File:** `scripts/n8n-workflows/woocommerce-order-lookup.json` (NEW)
**Effort:** 30 minutes

Create a new n8n workflow JSON for WooCommerce order lookup that:
1. Receives webhook with `woocommerce_url`, `email`, credentials
2. Calls WooCommerce REST API `/wp-json/wc/v3/orders?email={email}`
3. Transforms response to Zenny format
4. Responds to webhook

---

## PHASE D: CLOUD TESTING & VALIDATION (Days 8-9)
*Prove it works without local deployment*

---

### D1. Configure GitHub Actions CI for Cloud Tests

**File:** `.github/workflows/staging-tests.yml` (NEW)
**Effort:** 1 hour

Create a workflow that triggers on push to `main`:
1. Deploys current branch to Railway preview environment
2. Runs pytest against the preview URL (not localhost)
3. Runs eval suite against staging secrets (stored in GitHub Secrets)
4. Runs E2E smoke tests via `curl` to the preview URL
5. Tears down preview on completion

**Required GitHub Secrets:**
- `RAILWAY_TOKEN`
- `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`
- `GEMINI_API_KEY`, `DEEPSEEK_API_KEY`
- `N8N_WEBHOOK_URL`, `N8N_SECRET`

---

### D2. Create Cloud E2E Test Script

**File:** `scripts/testing/test-e2e-cloud.py` (NEW)
**Effort:** 1 hour

Create a Python script that hits the **cloud base URL** (passed via `ZENNY_BASE_URL` env var):
1. Health check: `GET $ZENNY_BASE_URL/health`
2. Webhook order status flow: `POST $ZENNY_BASE_URL/v1/webhook`
3. Web channel message: `POST $ZENNY_BASE_URL/v1/channel/web`
4. Admin action logs access: `GET $ZENNY_BASE_URL/admin/clients`
5. PII redaction verification: send fake SSN, check logs in Supabase
6. Policy Guard blocking: send refund request, verify blocked

**Run locally against cloud:**
```bash
export ZENNY_BASE_URL=https://zenny-staging.up.railway.app
poetry run python scripts/testing/test-e2e-cloud.py
```

---

### D3. Run Full Test Suite (Cloud Only)
```bash
# 1. Trigger CI (local machine — just the trigger command)
gh workflow run staging-tests.yml --ref main

# 2. Or run E2E script against staging manually
export ZAILWAY_BASE_URL=https://zenny-staging.up.railway.app
poetry run python scripts/testing/test-e2e-cloud.py

# 3. Manual smoke checks (local curl to cloud instance)
curl https://zenny-staging.up.railway.app/health

curl -X POST https://zenny-staging.up.railway.app/v1/channel/web \
  -H "Content-Type: application/json" \
  -d '{"client_id":"test-store","user_id":"u1","message":"Where is my order?"}'
`````
### D4. LOCAL MACHINE BOUNDARY (Reference)

**What developers MAY do on their laptop:**
- Edit code and push to Git
- Run `poetry run python -m py_compile &lt;file&gt;` for syntax checks
- Run `poetry run black src/` / `poetry run ruff check src/` for linting
- `curl` the staging/preview URL to manually verify behavior
- Run `gh workflow run` to trigger cloud tests

**What developers MAY NOT do on their laptop:**
- `poetry run pytest tests/` (use CI)
- `docker-compose up` for n8n (use OCI)
- `uvicorn src.main:app --reload` and treat it as a test server
- Any test that requires Supabase, Redis, or LLM keys to be "local"

---

## PHASE E: DOCUMENTATION (Day 10)
*Make it maintainable*

---

### E1. Rewrite `docs/GUIDE.md` for Python Stack

**Priority:** HIGH (Current guide is TypeScript)
**Effort:** 2 hours

Create `docs/GUIDE_PYTHON_v2.1.md` with:
- Python/ Poetry setup (not npm)
- FastAPI routes (not Fastify)
- Poetry commands (not npm run)
- Updated file paths (`.py` not `.ts`)
- Railway Python deployment (not Node.js)

**Key sections to update:**
1. Prerequisites: Add Python 3.11+, Poetry
2. Install: `poetry install` not `npm install`
3. Dev server: `poetry run uvicorn src.main:app --reload` not `npm run dev`
4. Project structure: Python files
5. Testing: `poetry run pytest` not `npm run test:eval`

---

### E2. Create `docs/ARCHITECTURE.md`

**File:** `docs/ARCHITECTURE.md` (NEW)
**Effort:** 1 hour

Document:
- Request flow diagram (Channel -> Adapter -> State Manager -> RAG -> LLM Router -> Response)
- Data flow (Supabase tables, Redis keys)
- Integration points (Voiceflow, n8n, Shopify, etc.)
- Security model (RLS, PII redaction, Policy Guard)

---

## GO/NO-GO CHECKLIST (Before Store #1)

| # | Check | How to Verify (Cloud Only) |
|---|-------|--------------------------|
| 1 | `llm_cost_logs` table exists | `psql $SUPABASE_URL -c "SELECT 1 FROM llm_cost_logs LIMIT 1"` |
| 2 | Prompt Manager loads YAML | CI job: `python -c "from src.services.prompt_manager import prompt_manager; ..."` |
| 3 | Channel adapters used in API | `curl -X POST $STAGING_URL/v1/channel/web` returns real response |
| 4 | Shopify order lookup works | Set Shopify creds in staging, ask "Where is my order?", get real data |
| 5 | Escalation creates ticket | Trigger escalation in staging, check Zendesk + Slack |
| 6 | PII redaction works | Send credit card number to staging, verify `[REDACTED_CC]` in Supabase logs |
| 7 | Conversation persisted | Check Supabase `conversations` table has rows from staging traffic |
| 8 | Cost logging clean | `llm_cost_logs` has entries, `conversations` has no empty rows |
| 9 | n8n running | `curl http://OCI_IP:5678/healthz` returns OK |
| 10 | All 8 eval tests pass | GitHub Actions `staging-tests.yml` green |
| 11 | 25+ unit tests pass | GitHub Actions `staging-tests.yml` green |
| 12 | Health check OK | `curl $STAGING_URL/health` returns `{"status":"ok"}` |
| 13 | Admin dashboard works | `GET $STAGING_URL/admin/clients?password=xxx` returns data |
| 14 | Redis sessions persist | Same user on Web + WhatsApp gets merged session in staging |
| 15 | No critical errors 24h | Monitor Railway logs / Sentry for 24h |

**ALL 15 MUST PASS BEFORE ONBOARDING STORE #1.**
**NONE of these checks may use `localhost`.**

---

## RISK MITIGATION

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| OCI free tier runs out | Low | Hetzner CX11 backup ($6/mo) |
| Gemini API rate limit | Medium | Implement request queuing, fallback to DeepSeek |
| Shopify API changes | Low | Abstract in n8n, not Zenny Core |
| n8n webhook timeout | Medium | Increase timeout to 30s, add retry logic |
| Redis connection drops | Low | Add reconnection logic in `redis_client.py` |
| Team loses track | High | **Use ZENNY_LOG.md system (see below)** |

---

## DOCUMENT CONTROL

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | May 2026 | ZeroManual Team | Initial remediation plan |

**Next Update:** After each phase completion

---

*Fix the foundation. Wire the components. Deploy the glue. Test everything. Then ship.*
