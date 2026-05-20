# ZENNY AI — PHASE 1 TECHNICAL BUILD GUIDE v2.0
## Complete Step-by-Step Implementation
### From Zero to Live Shopify Support Agent

---

**Version:** 2.0  
**Date:** May 2026  
**Status:** Build Reference  
**Audience:** CTO, Dev Team, PM  
**Companion:** This guide references files in `scripts/` and `zenny-core/` directories.

---

## TABLE OF CONTENTS

1. [Prerequisites & Accounts](#1-prerequisites--accounts)
2. [Infrastructure Setup](#2-infrastructure-setup)
3. [Database (Supabase)](#3-database-supabase)
4. [Zenny Core API](#4-zenny-core-api)
5. [LLM Router Service](#5-llm-router-service)
6. [Policy Guard](#6-policy-guard)
7. [Channel Gateway](#7-channel-gateway)
8. [RAG / Knowledge Base Pipeline](#8-rag--knowledge-base-pipeline)
9. [n8n Integration Hub](#9-n8n-integration-hub)
10. [Voiceflow Template Setup](#10-voiceflow-template-setup)
11. [Internal Admin Dashboard](#11-internal-admin-dashboard)
12. [Evaluation Framework](#12-evaluation-framework)
13. [Environment Variables](#13-environment-variables)
14. [Deployment Checklist](#14-deployment-checklist)
15. [Troubleshooting](#15-troubleshooting)

---

## 1. PREREQUISITES & ACCOUNTS

Create these accounts before writing any code:

| Service | URL | Plan | Cost | Free Tier Note |
|---------|-----|------|------|----------------|
| **Voiceflow** | voiceflow.com | Free Workspace | $0 | 1 project, $5 credit. Use tempmail for extra accounts if needed. |
| **Supabase** | supabase.com | Free Tier | $0 | 500MB DB, 2GB bandwidth. Upgrade to Pro (~$25) when needed. |
| **Railway** | railway.app | Free Tier | $0 | $5 credit/month, sleeps after inactivity. Fine for testing. |
| **Hetzner** | hetzner.com | CX11 | ~$6/mo | No free tier. Cheapest reliable VPS. |
| **Upstash** | upstash.com | Free Tier | $0 | 10,000 commands/day, 256MB storage. |
| **Google AI Studio** | makersuite.google.com | - | $0 | 1,500 requests/day free on Gemini 2.5 Flash-Lite. |
| **DeepSeek** | platform.deepseek.com | - | Pay-as-you-go | Usually offers initial free credits. |
| **SendGrid** | sendgrid.com | Free Tier | $0 | 100 emails/day free. |
| **GitHub** | github.com | Free | $0 | Private repos free. |
| **Stripe** | stripe.com | - | $0 until revenue | For billing later. |

**Budget-Conscious Path:**
- Start with Voiceflow Free + Supabase Free + Railway Free + Hetzner CX11 + Upstash Free
- Total: ~$6/mo (Hetzner only)
- Upgrade Supabase/Railway/Voiceflow only when you hit limits or need features

---

## 2. INFRASTRUCTURE SETUP

### 2.1 Hetzner VPS (n8n + Langfuse)

**Step 1: Create Server**
1. Go to Hetzner Cloud Console
2. Click "Add Server"
3. Location: Choose closest to you
4. Image: Ubuntu 22.04
5. Type: CX11 (1 vCPU, 2GB RAM)
6. Name: `zenny-n8n`
7. Add SSH key

**Generate SSH Key (if needed):**
```bash
ssh-keygen -t ed25519 -C "your-email@example.com"
cat ~/.ssh/id_ed25519.pub
# Copy this and paste into Hetzner SSH Keys section
```

**Step 2: Run Automated Setup Script**

Instead of manual commands, use the provided script:

**File:** `scripts/infrastructure/hetzner-setup.sh`

```bash
# Copy script to server
scp scripts/infrastructure/hetzner-setup.sh root@YOUR_SERVER_IP:/tmp/

# SSH and run
ssh root@YOUR_SERVER_IP
bash /tmp/hetzner-setup.sh
```

This script automatically:
- Updates Ubuntu
- Installs Docker, Docker Compose, Nginx, Certbot
- Configures UFW firewall (ports 22, 80, 443, 5678, 3001)
- Creates `/opt/zenny` directory

**Step 3: Configure Environment**

**File:** `scripts/infrastructure/.env.example`

Copy and edit on the server:
```bash
cp scripts/infrastructure/.env.example /opt/zenny/.env
nano /opt/zenny/.env
# Fill in your values
```

**Step 4: Deploy n8n + Langfuse**

**File:** `scripts/infrastructure/docker-compose.yml`

```bash
cp scripts/infrastructure/docker-compose.yml /opt/zenny/
cd /opt/zenny
docker compose up -d
```

**Step 5: Secure with HTTPS**

**File:** `scripts/infrastructure/nginx-n8n.conf`

```bash
# Copy nginx config
cp scripts/infrastructure/nginx-n8n.conf /etc/nginx/sites-available/n8n
ln -s /etc/nginx/sites-available/n8n /etc/nginx/sites-enabled/
nginx -t

# Get SSL certificate
certbot --nginx -d n8n.yourdomain.com

# Update docker-compose .env:
# N8N_PROTOCOL=https
# WEBHOOK_URL=https://n8n.yourdomain.com/
```

**Step 6: Verify**
```bash
docker ps
# Should show n8n and langfuse containers running

# Test n8n
curl http://YOUR_SERVER_IP:5678
# Or visit https://n8n.yourdomain.com
```

---

### 2.2 Railway Project (Zenny Core API)

**Option A: Railway CLI**
```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Create project
railway init
```

**Option B: Railway Web UI**
1. Go to railway.app
2. Click "New Project"
3. Choose "Deploy from GitHub repo"
4. Connect your GitHub account
5. Select your zenny-core repository

**Railway Settings:**
- Runtime: Node.js 18+
- Build Command: `npm install && npm run build`
- Start Command: `npm start`
- Healthcheck Path: `/health`

**Files:** `zenny-core/railway.json` and `zenny-core/Procfile` (already configured)

---

### 2.3 Upstash Redis

**Step 1: Create Database**
1. Go to upstash.com
2. Click "Create Database"
3. Name: `zenny-redis`
4. Region: Same as your Railway/Supabase region (e.g., US East)
5. Click "Create"

**Step 2: Copy Credentials**
Go to your database page and copy:
- `UPSTASH_REDIS_REST_URL`
- `UPSTASH_REDIS_REST_TOKEN`

**Step 3: Test Connection**
```bash
curl -X POST $UPSTASH_REDIS_REST_URL/set/foo/bar \
  -H "Authorization: Bearer $UPSTASH_REDIS_REST_TOKEN"
```

If you see `{"result":"OK"}`, it's working.

---

### 2.4 Supabase Project

**Step 1: Create Project**
1. Go to supabase.com
2. Click "New Project"
3. Name: `zenny-core`
4. Password: Create a strong password (save in password manager)
5. Region: US East (or closest to your users)
6. Click "Create new project"

**Step 2: Get Credentials**
1. Go to Project Settings (gear icon)
2. Click "Database"
3. Copy "Connection string" (Postgres format)
4. Go to Project Settings -> "API"
5. Copy:
   - `anon public` key
   - `service_role` key (keep this secret!)

**Step 3: Enable pgvector Extension**
1. In Supabase dashboard, click "SQL Editor" (left sidebar)
2. Click "New query"
3. Paste and run:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
```

4. Click "Run"

---

## 3. DATABASE (SUPABASE)

### 3.1 Run Setup SQL

**File:** `zenny-core/supabase-setup.sql`

Open Supabase SQL Editor and run the entire file. This creates:
- All tables (`clients`, `kb_chunks`, `conversations`, `action_logs`, `prompt_overrides`)
- Row Level Security (RLS) policies
- Helper functions (`set_tenant_context`, `match_kb_chunks`)
- Indexes for performance

**Verify:**
```sql
SELECT * FROM pg_extension WHERE extname = 'vector';
-- Should return 1 row

SELECT * FROM clients LIMIT 1;
-- Should return empty (no clients yet)
```

---

## 4. ZENNY CORE API

### 4.1 Install & Build

The Zenny Core code is in the `zenny-core/` directory.

```bash
cd zenny-core
npm install
npm run build
```

### 4.2 Environment Variables

**File:** `zenny-core/.env.example`

```bash
cp zenny-core/.env.example zenny-core/.env
# Edit with your real credentials
```

### 4.3 Start Development Server

```bash
npm run dev
# Server runs on http://localhost:3000
```

### 4.4 Verify Health

```bash
curl http://localhost:3000/health
# Expected: {"status":"ok","version":"1.0.0","timestamp":"..."}
```

### 4.5 Project Structure

```
zenny-core/
├── src/
│   ├── index.ts              # Server entry
│   ├── config.ts             # Environment config
│   ├── types.ts              # TypeScript types
│   ├── api/
│   │   ├── routes.ts         # Route registry
│   │   ├── webhook.ts        # Voiceflow webhooks
│   │   ├── channels.ts       # Channel adapters
│   │   ├── ingest.ts         # Onboarding & KB
│   │   └── admin.ts          # Internal dashboard
│   ├── services/
│   │   ├── db.ts             # Supabase client
│   │   ├── redis.ts          # Redis / sessions
│   │   ├── llm-router.ts     # Tiered LLM routing
│   │   ├── policy-guard.ts   # Deterministic rules
│   │   ├── state-manager.ts  # Session management
│   │   ├── rag.ts            # KB retrieval
│   │   └── action-engine.ts  # n8n integration
│   ├── integrations/
│   │   ├── shopify.ts        # Shopify API
│   │   ├── stripe.ts         # Stripe API
│   │   └── zendesk.ts        # Zendesk API
│   ├── prompts/
│   │   └── ecommerce-v1.0/   # Prompt templates
│   └── evals/
│       ├── suite.ts          # Eval test cases
│       └── runner.ts         # Eval runner
├── package.json
├── tsconfig.json
├── .env.example
├── .gitignore
├── railway.json
├── Procfile
├── README.md
└── supabase-setup.sql
```

---

## 5. LLM ROUTER SERVICE

**File:** `zenny-core/src/services/llm-router.ts`

The LLM Router is already implemented. It handles:
- **T1 (Gemini 2.5 Flash-Lite):** 93-97% of traffic -- FAQ, order status, greetings
- **T2 (DeepSeek-V4-Flash):** 2-5% -- Multi-step reasoning, complex returns
- **T3 (Gemini 2.5 Pro):** 0-2% -- High-stakes disputes, fraud review

**Key features:**
- Redis caching for T1 responses (24h TTL)
- Automatic cost logging per client
- Tier routing based on intent + complexity + client tier

**No changes needed** -- it's production-ready.

---

## 6. POLICY GUARD

**File:** `zenny-core/src/services/policy-guard.ts`

Deterministic rules that execute **before** any AI generation:

| Action | Rule | Result |
|--------|------|--------|
| REFUND | `fraud_score > 0.8` | Block + escalate |
| REFUND | `order.age_days > return_policy_days` | Block |
| REFUND | `order.total > 500 && !user.verified` | Block + escalate |
| CANCEL_SUBSCRIPTION | `subscription.type === 'annual'` | Block + offer pause |
| HUMAN_HANDOFF | `user.vip === true` | Allow + high priority |

**No changes needed** -- extend by adding new cases to `PolicyGuard.evaluate()`.

---

## 7. CHANNEL GATEWAY

**Files:**
- `zenny-core/src/api/webhook.ts`
- `zenny-core/src/api/channels.ts`

Unified ingress for all channels:
- `/v1/webhook` -- Voiceflow DMAPI
- `/v1/webhook/classify` -- Intent classification
- `/v1/webhook/escalate` -- Human handoff
- `/v1/channel/:channel` -- Unified channel handler (web, whatsapp, email, messenger)

**Features:**
- Cross-channel session merging (WhatsApp -> Web)
- Async action handling
- Slot persistence across turns
- Policy Guard integration

---

## 8. RAG / KNOWLEDGE BASE PIPELINE

**File:** `zenny-core/src/services/rag.ts`

**Ingestion:**
```bash
# Upload via API
curl -X POST http://localhost:3000/v1/ingest-kb/your-store \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Your return policy text here...",
    "source_url": "return-policy.pdf",
    "source_type": "pdf"
  }'
```

**Retrieval:**
- Automatic embedding via Gemini Embedding API
- Vector search with pgvector
- Freshness scoring + hybrid BM25
- Injected into LLM prompts with source attribution

---

## 9. N8N INTEGRATION HUB

### 9.1 Import Workflow Templates

Instead of building manually, import these JSON files directly into n8n:

| Workflow | File | Purpose |
|----------|------|---------|
| Shopify Order Lookup | `scripts/n8n-workflows/shopify-order-lookup.json` | Get orders by email |
| Zendesk Ticket | `scripts/n8n-workflows/zendesk-ticket-create.json` | Create escalation tickets |
| Google Calendar | `scripts/n8n-workflows/gcal-find-slots.json` | Find available slots |
| Stripe Refund | `scripts/n8n-workflows/stripe-refund.json` | Process refunds |
| Slack Notify | `scripts/n8n-workflows/slack-notify.json` | Alert channel |

**Import steps:**
1. Open n8n -> Click "..." (top right) -> "Import from File"
2. Select the JSON file
3. Update credentials in each node
4. Save and activate

### 9.2 Connect n8n to Zenny Core

**File:** `zenny-core/src/services/action-engine.ts`

The Action Engine already points to your n8n instance. Just set:
```env
N8N_WEBHOOK_URL=http://your-hetzner-ip:5678/webhook
N8N_SECRET=your-secret-key
```

### 9.3 n8n Boundaries (Critical)

**n8n DOES:**
- Call external APIs
- Transform JSON payloads
- Retry failed requests (3x exponential backoff)
- Send Slack notifications
- Schedule cron jobs

**n8n DOES NOT:**
- Decide refund eligibility
- Route between LLM tiers
- Enforce business policies
- Store tenant state
- Make escalation decisions

**Rule:** If you find yourself writing an `if` node in n8n that affects customer experience, move it to Zenny Core.

---

## 10. VOICEFLOW TEMPLATE SETUP

### 10.1 Create Free Account

1. Go to voiceflow.com
2. Sign up with email (use tempmail if needed for extra accounts)
3. You get 1 project and $5 credit on free workspace

### 10.2 Create Master Template

1. Click "New Project"
2. Choose "Blank Project"
3. Name: `Zenny -- Shopify Master (v1.0)`

### 10.3 Set Up Global Variables

1. Click "Variables" (left sidebar)
2. Add these variables:

| Variable Name | Type | Default Value |
|--------------|------|---------------|
| `client_id` | Text | (empty) |
| `user_id` | Text | (empty) |
| `agent_name` | Text | "Zenny" |
| `welcome_message` | Text | "Hi! I'm Zenny. How can I help?" |
| `tone` | Text | "friendly_professional" |
| `kb_context` | Text | (empty) |
| `order_context` | Any | (empty) |
| `escalate` | Boolean | false |

### 10.4 Build the Flow

**Step 1: Start Block**
1. Drag "Start" block onto canvas
2. Connect to "Set Variable" block

**Step 2: Set Variables Block**
1. Drag "Set Variable" block
2. Set:
   - `client_id` = `{client_id}` (from API request)
   - `user_id` = `{user_id}` (from API request)

**Step 3: Welcome Message**
1. Drag "Speak" block
2. Text: `{welcome_message}`

**Step 4: Capture User Input**
1. Drag "Capture" block
2. Capture: `user_message`
3. Connect to "API" block

**Step 5: API Block (Intent Classification)**
1. Drag "API" block
2. Method: POST
3. URL: `https://zenny-api.zeromanual.com/v1/webhook/classify`
4. Headers:
   - `Content-Type`: `application/json`
5. Body:
```json
{
  "client_id": "{client_id}",
  "user_id": "{user_id}",
  "message": "{user_message}"
}
```
6. Response Mapping:
   - `intent` -> variable `intent`
   - `complexity` -> variable `complexity`
   - `sentiment` -> variable `sentiment`

**Step 6: Condition Block**
1. Drag "Condition" block
2. Add conditions:
   - `intent` == `"order_status"`
   - `intent` == `"return_request"`
   - `intent` == `"faq"` OR `intent` == `"product_question"`
   - `intent` == `"human"` OR `intent` == `"escalate"`
   - Else -> `general`

**Step 7: Order Status Branch**
1. Drag "API" block
2. Method: POST
3. URL: `https://zenny-api.zeromanual.com/v1/webhook?client_id={client_id}`
4. Body:
```json
{
  "client_id": "{client_id}",
  "user_id": "{user_id}",
  "message": "{user_message}",
  "intent": "{intent}",
  "session_context": {
    "turn_count": "{turn_count}",
    "slots": "{slots}"
  }
}
```
5. Response Mapping:
   - `reply` -> variable `api_reply`
6. Drag "Speak" block -> Text: `{api_reply}`
7. Connect: API -> Speak -> Capture (for follow-up)

**Step 8: Return Request Branch**
Same as Order Status, but:
- After API block, add "Condition" checking `{policy_reason}`
- If `policy_reason` == `"FRAUD_REVIEW"` -> Set `escalate` = true -> Go to Escalation Flow
- Else -> Speak -> Capture

**Step 9: FAQ Branch**
Same as Order Status, but intent is `faq`.

**Step 10: Human/Escalate Branch**
1. Set Variable: `escalate` = true
2. Connect to Escalation Flow

**Step 11: Escalation Flow**
1. Drag "API" block
2. URL: `https://zenny-api.zeromanual.com/v1/webhook/escalate`
3. Body: Include full transcript and context
4. Drag "Speak" block
5. Text: "I'm connecting you with our team. They'll have all the context."
6. Drag "End" block

### 10.5 API Step Configuration Reference

For EVERY API block in Voiceflow:

**Integration Type:** API
**Method:** POST
**URL:** `https://zenny-api.zeromanual.com/v1/webhook?client_id={client_id}`
**Headers:**
```
Content-Type: application/json
```
**Body Template:**
```json
{
  "client_id": "{client_id}",
  "user_id": "{user_id}",
  "message": "{last_response}",
  "intent": "{intent}",
  "session_context": {
    "turn_count": "{turn_count}",
    "slots": "{slots}"
  }
}
```
**Response Mapping:**
- `reply` -> `api_reply`
- `escalate` -> `escalate`
- `policy_reason` -> `policy_reason`
- `model_used` -> `model_used`

### 10.6 Dialog Manager API (DMAPI) Setup

For programmatic access from your Channel Gateway:

**Get DMAPI Key:**
1. Voiceflow -> Project Settings (gear icon)
2. Click "API Keys"
3. Generate new key
4. Copy the key

**Example API Call:**
```bash
curl -X POST \
  https://general-runtime.voiceflow.com/state/user/test-user-123/interact \
  -H "Authorization: VF.DM.YOUR_KEY_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "action": {
      "type": "text",
      "payload": "Where is my order?"
    },
    "config": {
      "tts": false,
      "stripSSML": true
    },
    "state": {
      "variables": {
        "client_id": "test-store",
        "user_id": "test-user-123"
      }
    }
  }'
```

### 10.7 PM Clone Process

When onboarding a new client:

1. PM opens Voiceflow dashboard
2. Finds project: `Zenny -- Shopify Master (v1.0)`
3. Clicks three dots (...) -> "Duplicate"
4. Renames to: `Zenny -- {Store Name}`
5. Updates variables:
   - `agent_name` = store's chosen name
   - `welcome_message` = store's welcome text
   - `tone` = store's tone
6. Updates ALL API step URLs:
   - Old: `?client_id=test`
   - New: `?client_id={store-slug}`
7. Tests in "Test Chat" (bottom left)
8. Copies Project ID
9. Pastes Project ID into Supabase `voiceflow_project_id` field

---

## 11. INTERNAL ADMIN DASHBOARD

### 11.1 Access Admin Endpoints

Zenny Core includes built-in admin endpoints. No separate dashboard needed for Phase 1.

**Base URL:** `https://zenny-api.zeromanual.com/admin`
**Auth:** `Authorization: Bearer {ADMIN_PASSWORD}`

### 11.2 Available Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admin/clients` | List all clients |
| GET | `/admin/clients/:slug` | Client details |
| GET | `/admin/clients/:slug/conversations` | Conversation history |
| GET | `/admin/clients/:slug/replay/:id` | Replay conversation |
| GET | `/admin/clients/:slug/kb` | KB chunks |
| GET | `/admin/clients/:slug/actions` | Action logs |
| GET | `/admin/analytics/:slug` | Analytics summary |

### 11.3 Example: View Client Analytics

```bash
curl -H "Authorization: Bearer $ADMIN_PASSWORD" \
  https://zenny-api.zeromanual.com/admin/analytics/acme-store
```

**Response:**
```json
{
  "client_slug": "acme-store",
  "total_conversations": 152,
  "resolved_count": 128,
  "escalated_count": 24,
  "containment_rate": "84.2%",
  "total_llm_cost_usd": "2.3400",
  "avg_cost_per_conversation": "0.015395",
  "model_usage": {
    "gemini-2.5-flash-lite": 145,
    "deepseek-chat": 6,
    "gemini-2.5-pro": 1
  }
}
```

---

## 12. EVALUATION FRAMEWORK

**File:** `zenny-core/src/evals/suite.ts`

### 12.1 Run Evaluations

**File:** `scripts/testing/test-eval.sh`

```bash
# From project root
cd zenny-core
npm run test:eval
```

Or manually:
```bash
cd zenny-core
npx ts-node src/evals/runner.ts
```

### 12.2 Test Cases Covered

| Test ID | Scenario | Policy Check |
|---------|----------|--------------|
| `order_status_known` | "Where is my order?" | None |
| `refund_fraud_guard` | Refund on fraud order | BLOCKED (FRAUD_REVIEW) |
| `return_label_eligible` | Return eligible shoes | ALLOWED |
| `woocommerce_order` | WooCommerce tracking | None |
| `calendar_booking` | Book a call | None |
| `after_hours` | Message at 11 PM | None |
| `high_value_refund` | $600 refund unverified | BLOCKED (MANUAL_REVIEW) |
| `annual_cancel` | Cancel annual sub | BLOCKED (ANNUAL_CANCELLATION) |

### 12.3 CI/CD Integration

Add to your deployment pipeline:
```bash
# Before deploy
npm run test:eval

# If exit code != 0, block deploy
```

---

## 13. ENVIRONMENT VARIABLES

### 13.1 Zenny Core (.env)

**File:** `zenny-core/.env.example`

```env
# Server
PORT=3000
HOST=0.0.0.0
NODE_ENV=production

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...
SUPABASE_ANON_KEY=eyJ...

# Redis (Upstash)
REDIS_HOST=your-db.upstash.io
REDIS_PORT=6379
REDIS_PASSWORD=your-password
REDIS_TLS=true

# LLM APIs
GEMINI_API_KEY=AIzaSy...
DEEPSEEK_API_KEY=sk-...

# Voiceflow
VOICEFLOW_DMAPI_KEY=VF.DM...

# n8n
N8N_WEBHOOK_URL=http://your-hetzner-ip:5678/webhook
N8N_SECRET=random-string-for-auth

# Integrations
SHOPIFY_API_VERSION=2024-04

# Email
SENDGRID_API_KEY=SG...

# Security
JWT_SECRET=random-256-bit-string
ADMIN_PASSWORD=strong-password-for-internal-dashboard
```

### 13.2 Infrastructure (.env)

**File:** `scripts/infrastructure/.env.example`

```env
# Hetzner / n8n Environment
N8N_HOST=your-hetzner-ip-or-domain
N8N_PASSWORD=strong-password-here
N8N_ENCRYPTION_KEY=random-32-char-string-for-encryption
N8N_WEBHOOK_URL=https://n8n.yourdomain.com/webhook

# Langfuse (optional)
LANGFUSE_DATABASE_URL=postgresql://user:pass@localhost:5432/langfuse
LANGFUSE_SECRET=random-secret-key
LANGFUSE_SALT=random-salt-string

# Zenny Core webhook secret (must match zenny-core .env)
ZENNY_N8N_SECRET=matching-secret-from-zenny-core-env
```

**Important:**
- Never commit `.env` to Git
- Add `.env` to `.gitignore`
- Use different keys for development and production

---

## 14. DEPLOYMENT CHECKLIST

### Before Store #1

- [ ] All `.env` variables set and tested
- [ ] Supabase tables created + RLS enabled (`supabase-setup.sql`)
- [ ] Redis connection tested (Upstash)
- [ ] n8n running on Hetzner (`docker ps` shows container)
- [ ] Zenny Core deployed to Railway
- [ ] Health check `GET /health` returns `{"status":"ok"}`
- [ ] Voiceflow template created and tested in Test Chat
- [ ] Shopify test API call succeeds (use your own store or test store)
- [ ] Evaluation suite runs and all tests pass (`npm run test:eval`)
- [ ] Internal admin dashboard accessible
- [ ] PM Playbook v1 written (step-by-step onboarding doc)

### Per Client Onboarding

- [ ] Client fills onboarding form
- [ ] Supabase row created with all fields
- [ ] Shopify/WooCommerce API credentials validated (test connection)
- [ ] Voiceflow template cloned and configured
- [ ] n8n workflow duplicated and credentials updated
- [ ] KB documents uploaded and indexed (test search)
- [ ] Web widget embedded on store (visible on site)
- [ ] WhatsApp number connected (if applicable, test inbound)
- [ ] 10 test questions asked and answered correctly
- [ ] Policy Guard tested with fraud scenario (should block)
- [ ] Escalation tested (human handoff creates ticket)
- [ ] Merchant approves launch (verbal or email confirmation)

---

## 15. TROUBLESHOOTING

### Zenny Core won't start

**Check:**
```bash
# Is PORT already in use?
lsof -i :3000

# Are all env variables set?
cat .env | grep -v "^#" | grep -v "^$"

# Can you reach Supabase?
curl $SUPABASE_URL/rest/v1/
```

**Fix:**
- Change PORT to 3001 if 3000 is taken
- Add missing env variables
- Check Supabase IP restrictions (Settings -> Database -> Network Restrictions)

---

### Supabase connection fails

**Check:**
```bash
# Test connection
psql "YOUR_CONNECTION_STRING" -c "SELECT 1"
```

**Fix:**
- Use Service Role Key (not Anon Key) for backend
- Disable IP restrictions temporarily for testing
- Verify `pgvector` extension is enabled:
  ```sql
  SELECT * FROM pg_extension WHERE extname = 'vector';
  ```

---

### n8n webhook not reachable

**Check:**
```bash
# On Hetzner server
ufw status
docker ps
docker logs n8n
```

**Fix:**
- UFW must allow port 5678
- Docker container must be running
- Webhook URL must use public IP, not localhost
- Test with curl from your local machine:
  ```bash
  curl http://YOUR_HETZNER_IP:5678/webhook/shopify-order-lookup \
    -X POST -H "Content-Type: application/json" -d '{"test":true}'
  ```

---

### Voiceflow API step returns 500

**Check Zenny Core logs in Railway:**
```bash
# View logs
railway logs
```

**Test webhook directly:**
```bash
curl -X POST https://zenny-api.zeromanual.com/v1/webhook?client_id=test-store \
  -H "Content-Type: application/json" \
  -d '{"message":"Where is my order?","user_id":"test"}'
```

**Fix:**
- Verify `client_id` in URL matches Supabase slug
- Check Zenny Core is running and reachable
- Check Voiceflow API step body format matches expected schema

---

### LLM costs are too high

**Check:**
```bash
# View LLM cost logs
railway logs | grep "LLM Cost"
```

**Fix:**
- If T3 usage > 2%: review intent classification accuracy
- Add Redis caching for top 20 FAQs
- Verify token limits are enforced in code
- Check if caching is working (should see "cached" in model_used)

---

### Redis connection fails

**Check:**
```bash
# Test with redis-cli
redis-cli -u redis://default:PASSWORD@HOST:PORT
```

**Fix:**
- Upstash uses TLS: ensure `REDIS_TLS=true` in .env
- Check if password contains special characters (wrap in quotes)
- Verify host and port from Upstash dashboard

---

### Shopify API 401 Unauthorized

**Check:**
```bash
# Test Shopify API directly
curl -X GET \
  "https://YOUR_STORE.myshopify.com/admin/api/2024-04/orders.json?limit=1" \
  -H "X-Shopify-Access-Token: YOUR_TOKEN"
```

**Fix:**
- Token may have expired or been revoked
- Check if token has `read_orders` scope
- Verify shop domain format: `store-name.myshopify.com`
- Regenerate token in Shopify Admin -> Apps -> Private apps

---

## APPENDIX A: Testing Scripts

**Files in `scripts/testing/`:**

| Script | Purpose | Usage |
|--------|---------|-------|
| `test-connection.sh` | Test all service connections | `./test-connection.sh` |
| `test-shopify.sh` | Test Shopify API | `./test-shopify.sh <domain> <token>` |
| `test-webhook.sh` | Test Zenny webhook | `./test-webhook.sh <slug> [message]` |
| `test-eval.sh` | Run eval suite | `./test-eval.sh` |

---

## APPENDIX B: File Reference

### Infrastructure
- `scripts/infrastructure/hetzner-setup.sh` -- Ubuntu server setup
- `scripts/infrastructure/docker-compose.yml` -- n8n + Langfuse deployment
- `scripts/infrastructure/nginx-n8n.conf` -- Nginx reverse proxy config
- `scripts/infrastructure/.env.example` -- Infrastructure env vars

### n8n Workflows (Importable JSON)
- `scripts/n8n-workflows/shopify-order-lookup.json`
- `scripts/n8n-workflows/zendesk-ticket-create.json`
- `scripts/n8n-workflows/gcal-find-slots.json`
- `scripts/n8n-workflows/stripe-refund.json`
- `scripts/n8n-workflows/slack-notify.json`

### Testing
- `scripts/testing/test-connection.sh`
- `scripts/testing/test-shopify.sh`
- `scripts/testing/test-webhook.sh`
- `scripts/testing/test-eval.sh`

### Zenny Core (Full API)
- `zenny-core/` -- Complete Node.js/TypeScript API
- See `zenny-core/README.md` for detailed API docs

---

## DOCUMENT CONTROL

| Version | Date | Author | Purpose |
|---------|------|--------|---------|
| 1.1 | May 2026 | ZeroManual Dev Team | Phase 1 build reference |
| 2.0 | May 2026 | ZeroManual Dev Team | Reorganized with file references, downloadable scripts, and n8n workflow JSONs |

**Next Update:** After Store #1 deployment (incorporate real fixes).

---

*Build it. Ship it. Fix it.*
