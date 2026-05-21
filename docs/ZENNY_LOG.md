# ZENNY AI --- MASTER LOG
## Real-Time Project Status Tracker
### For LLM-Based Development Workflows

---

## HOW TO USE THIS FILE

**Rule:** Every time you (human or AI) complete a task, modify code, or make a decision, **append an entry** to this file. Do NOT edit existing entries --- only append new ones at the bottom.

**Format for each entry:**
```
### [YYYY-MM-DD HH:MM] --- [TASK_ID] --- [STATUS]
**Who:** [Human name / AI model]
**What:** [One-line description]
**Files Changed:** [list of files]
**Details:** [Brief explanation of what was done]
**Blockers:** [Any issues encountered]
**Next:** [What should happen next]
```

---

## PROJECT OVERVIEW

| Field | Value |
|-------|-------|
| **Product** | Zenny AI --- Agentic Customer Support for E-Commerce |
| **Company** | ZeroManual |
| **Phase** | Phase 1 (Weeks 1-8) |
| **Current Sprint** | Remediation Sprint (Post-Code-Review) |
| **Target** | Store #1 Pilot Ready |
| **Stack** | Python/FastAPI, Supabase, Redis, n8n, Voiceflow |
| **Overall Completion** | ~40% |

---

## CURRENT STATUS SUMMARY

### Last Updated: 2026-05-21 02:40

| Component | Status | Blocker |
|-----------|--------|---------|
| FastAPI App | DONE | None |
| Config/Types | DONE | None |
| Supabase Schema | PARTIAL | Missing `llm_cost_logs` table |
| Redis Client | PARTIAL | SSL default wrong |
| LLM Router | PARTIAL | Prompt Manager not wired |
| Policy Guard | DONE | None |
| State Manager | DONE | None |
| RAG Service | PARTIAL | Never used in response flow |
| Action Engine | DONE | n8n not deployed |
| Prompt Manager | DONE | Not wired to LLM Router |
| PII Redactor | DONE | Not in state manager |
| Shopify Integration | DONE | Never called with real data |
| WooCommerce Integration | DONE | Never called with real data |
| Stripe Integration | DONE | n8n not deployed |
| Zendesk Integration | DONE | n8n not deployed |
| Web Channel | PARTIAL | API returns hardcoded response |
| WhatsApp Channel | DONE | API doesn't use adapter |
| Email Channel | DONE | API doesn't use adapter |
| Messenger Channel | DONE | API doesn't use adapter |
| Webhook API | PARTIAL | Order lookup fetches but ignores data |
| Channel API | PARTIAL | Adapters imported but not used |
| Ingest API | PARTIAL | KB processing not implemented |
| Admin API | DONE | None |
| Eval Suite | DONE | Requires live API keys |
| Tests | DONE | Some need running app |
| n8n Workflows | DONE | Not deployed |
| Voiceflow Template | NOT STARTED | Needs manual setup |
| Documentation | OUTDATED | GUIDE.md is TypeScript |

---

## CRITICAL BLOCKERS (Must Fix First)

| # | Blocker | Impact | Owner | ETA |
|---|---------|--------|-------|-----|
| 1 | `llm_cost_logs` table missing from SQL | App crashes on LLM call | TBD | ASAP |
| 2 | Prompt Manager not wired to LLM Router | Tenant customization broken | TBD | ASAP |
| 3 | Channel adapters not used in API | Channels don't work | TBD | ASAP |
| 4 | n8n not deployed | No actions work | TBD | Day 6-7 |
| 5 | `json` import missing in prompt_manager.py | Crash on prompt load | TBD | ASAP |
| 6 | `user_email` unsafe in webhook.py | Crash when session_context is None | TBD | ASAP |
| 7 | Redis SSL wrong default | Connection fails | TBD | ASAP |
| 8 | No `.env.example` | New devs can't boot app | TBD | ASAP |
| 9 | GUIDE.md is TypeScript | Wrong documentation | TBD | Day 10 |
| 10 | Conversation not persisted | No analytics/history | TBD | Day 3-5 |

---

## LOG ENTRIES (Newest at Bottom)

### [2026-05-21 02:40] --- LOG-001 --- INITIAL_STATUS
**Who:** Kimi K2.6 (AI Review)
**What:** Complete codebase review and gap analysis
**Files Changed:** None (review only)
**Details:**
- Scanned all 48 files in zenny-core-v2/
- Identified 10 critical blockers
- Found components exist but are not wired together
- Estimated ~40% completion toward Store #1 pilot
- Created remediation plan and tracking system
**Blockers:** None (this is the baseline)
**Next:** Execute Phase A fixes (SQL schema, imports, safety checks)

### [2026-05-21 23:11] --- LOG-002 --- DECISION
**Who:** Human (ZeroManual Team)
**What:** Mandate cloud-only testing — remove all local test deployment references
**Files Changed:** SYSTEM.md, ZENNY_LOG.md, Zenny_AI_Detailed_Remediation_Plan_v1.0.md —> ...v1.1.md
**Details:**
- Local machines may only run static checks and `curl` against cloud instances
- All pytest, E2E, n8n, and integration validation moves to Railway/CI or OCI
- Remediation Plan Phase D (Testing) must be rewritten for cloud environments
- Prevents "works on my machine" drift and ensures tests always hit real infra
**Blockers:** None
**Next:** Update Remediation Plan Phase D and Go/No-Go checklist to reference Railway staging URLs and GitHub Actions workflows instead of localhost commands
---

### [TEMPLATE --- COPY AND FILL FOR NEW ENTRIES]

### [YYYY-MM-DD HH:MM] --- [LOG-XXX] --- [STATUS]
**Who:** 
**What:** 
**Files Changed:** 
**Details:**
- 
**Blockers:**
- 
**Next:** 

---

## COMPLETED PHASES

| Phase | Name | Status | Date Completed |
|-------|------|--------|----------------|
| - | - | - | - |

## ACTIVE PHASE

**Phase:** Remediation Sprint
**Started:** 2026-05-21
**Target End:** 2026-06-04 (2 weeks)
**Current Day:** Day 0

---

## METRICS

| Metric | Target | Current |
|--------|--------|---------|
| Unit Tests Passing | 25+ | 0 (not run yet) |
| Eval Tests Passing | 8/8 | 0 (not run yet) |
| E2E Tests Passing | 5/5 | 0 (not run yet) |
| Code Coverage | >70% | Unknown |
| Critical Bugs | 0 | 10 |
| n8n Deployed | Yes | No |
| Store #1 Pilot | Ready | Not Ready |

---

## DECISION LOG

| Date | Decision | Context | Impact |
|------|----------|---------|--------|
| 2026-05-21 | Use OCI Free Tier for n8n testing | Cheaper than Hetzner for test phase | Saves $6/mo during testing |
| 2026-05-21 | Prioritize wiring over new features | Components exist but don't connect | Faster path to working product |

---

*Append only. No edits to existing entries. This is the source of truth.*
