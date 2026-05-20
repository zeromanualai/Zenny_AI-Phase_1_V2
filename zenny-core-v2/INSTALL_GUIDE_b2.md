# ZENNY CORE — BATCH 2 INSTALLATION GUIDE
## Integrations, Channels, Evaluations

---

## WHAT YOU RECEIVED (18 Files)

### Integrations (4 files)
| File | Purpose |
|------|---------|
| `src/integrations/shopify.py` | Shopify Admin API (orders, products, customers) |
| `src/integrations/woocommerce.py` | WooCommerce REST API (Gap #2 — NEW) |
| `src/integrations/stripe.py` | Stripe (refunds, charges, subscriptions) |
| `src/integrations/zendesk.py` | Zendesk (tickets, users, comments) |

### Channel Adapters (5 files)
| File | Purpose |
|------|---------|
| `src/channels/__init__.py` | Adapter registry |
| `src/channels/web.py` | Web widget passthrough |
| `src/channels/whatsapp.py` | Twilio / 360dialog (Gap #4) |
| `src/channels/email.py` | SendGrid inbound parse + HTML-to-text (Gap #4) |
| `src/channels/messenger.py` | Meta Graph API (Gap #4) |

### Evaluation Framework (2 files)
| File | Purpose |
|------|---------|
| `src/evals/suite.py` | 8 test case definitions |
| `src/evals/runner.py` | Pytest runner + CI integration |

### Tests (5 files)
| File | Purpose |
|------|---------|
| `tests/test_integrations.py` | Shopify, WooCommerce, Stripe, Zendesk tests |
| `tests/test_channels.py` | All 4 channel adapter tests |
| `tests/test_evals.py` | Eval suite + runner tests |
| `tests/test_state_manager.py` | Session + slot tests |

---

## WHERE TO PLACE FILES

### Copy into your existing Batch 1 structure:

```
zenny-core/
  src/
    integrations/          ← NEW directory
      __init__.py
      shopify.py
      woocommerce.py       ← Gap #2
      stripe.py
      zendesk.py

    channels/              ← NEW directory
      __init__.py
      web.py
      whatsapp.py          ← Gap #4
      email.py             ← Gap #4
      messenger.py         ← Gap #4

    evals/                 ← NEW directory
      __init__.py
      suite.py
      runner.py

  tests/                   ← ADD to existing
    test_integrations.py
    test_channels.py
    test_evals.py
    test_state_manager.py
```

---

## STEP-BY-STEP SETUP

### Step 1: Copy Files
```bash
# From batch2 directory, copy into your zenny-core/
cp -r src/integrations/* zenny-core/src/integrations/
cp -r src/channels/* zenny-core/src/channels/
cp -r src/evals/* zenny-core/src/evals/
cp -r tests/* zenny-core/tests/
```

### Step 2: Update Channel Gateway
Edit `zenny-core/src/api/channels.py` to use the new adapters:

```python
from src.channels import WebAdapter, WhatsAppAdapter, EmailAdapter, MessengerAdapter

ADAPTERS = {
    "web": WebAdapter(),
    "whatsapp": WhatsAppAdapter(provider="twilio"),  # or "360dialog"
    "email": EmailAdapter(),
    "messenger": MessengerAdapter(),
}
```

### Step 3: Update Webhook for Integrations
Edit `zenny-core/src/api/webhook.py` to use Shopify/WooCommerce:

```python
from src.integrations.shopify import get_shopify_client
from src.integrations.woocommerce import get_woocommerce_client

# In the webhook handler, after intent detection:
if intent == "order_status":
    if client.platform == "shopify" and client.shopify_domain:
        shopify = get_shopify_client(client.shopify_domain, client.shopify_access_token)
        orders = await shopify.get_orders_by_email(user_email)
        # ... format response
    elif client.platform == "woocommerce" and client.woocommerce_url:
        woo = get_woocommerce_client(client.woocommerce_url, client.woocommerce_consumer_key, client.woocommerce_consumer_secret)
        orders = await woo.get_orders_by_email(user_email)
        # ... format response
```

### Step 4: Run Tests
```bash
cd zenny-core

# All tests
poetry run pytest

# Specific test files
poetry run pytest tests/test_integrations.py -v
poetry run pytest tests/test_channels.py -v
poetry run pytest tests/test_evals.py -v

# Eval suite
poetry run pytest src/evals/runner.py -v
```

### Step 5: Update n8n Workflows
Add WooCommerce workflow to n8n:
```bash
# Import into n8n
curl -X POST https://your-n8n.com/api/v1/workflows   -H "Content-Type: application/json"   -d @scripts/n8n-workflows/woocommerce-order-lookup.json
```

---

## GAPS CLOSED IN BATCH 2

| Gap | Status | How |
|-----|--------|-----|
| #2 WooCommerce | ✅ | `integrations/woocommerce.py` + n8n workflow |
| #4 Channel Adapters | ✅ | `channels/whatsapp.py`, `email.py`, `messenger.py` |
| #5 Calendly | ⚠️ Partial | Not included — use Google Calendar for now |
| #6 Dashboard | ❌ | Phase 2 — not in this batch |
| #7 Freshness | ❌ | Low priority — add cron later |
| #8 Hybrid Search | ⚠️ Stub | `rag.py` has `query_hybrid()` stub |

---

## ENV VARIABLES TO ADD

Add these to your `.env` and platform dashboards:

```bash
# Channel providers (pick one for WhatsApp)
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_ACCOUNT_SID=your-twilio-sid
# OR
THREESIXTY_DIALOG_API_KEY=your-360dialog-key

# Meta (Messenger)
META_APP_SECRET=your-meta-app-secret
META_PAGE_ACCESS_TOKEN=your-page-token

# SendGrid (Email)
SENDGRID_API_KEY=your-sendgrid-key
SENDGRID_WEBHOOK_SECRET=your-webhook-secret
```

---

## NEXT STEPS

1. **Test end-to-end**: Send a message through each channel
2. **Connect real stores**: Add Shopify/WooCommerce credentials in Supabase
3. **Run eval suite**: `poetry run pytest src/evals/runner.py`
4. **Deploy**: Push to Railway, update Voiceflow API URLs

---

*Batch 2 of 2. All core features complete.*
