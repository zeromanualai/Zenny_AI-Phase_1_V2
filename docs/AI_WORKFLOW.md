# ZENNY AI --- LLM WORKFLOW GUIDE
## How to Use AI Assistants Effectively on This Project
### For ZeroManual Team Members

---

## THE PROBLEM WE SOLVED

Your previous docs were:
- Scattered across multiple files
- Some claimed things were "done" when they weren't wired
- No single source of truth for current status
- LLMs couldn't quickly understand where you actually were

**This system fixes that.**

---

## THE THREE FILES

### 1. `ZENNY_LOG.md` --- THE HEARTBEAT

**What it is:** A living log. Every task, every fix, every decision gets appended here.

**Who updates it:** Both humans AND AI assistants. After every interaction.

**Format:**
```markdown
### [2026-05-21 14:30] --- LOG-002 --- COMPLETED
**Who:** Kimi K2.6
**What:** Added llm_cost_logs table to Supabase SQL
**Files Changed:** `zenny-core-v2/supabase-setup.sql`
**Details:**
- Added CREATE TABLE llm_cost_logs
- Added two indexes for query performance
- Ran SQL in Supabase editor successfully
**Blockers:** None
**Next:** Test LLM call writes to new table
```

**Rules:**
- APPEND ONLY --- never edit existing entries
- Use the template at the bottom of the file
- Increment LOG-XXX numbers sequentially
- Be specific about what changed
- Always note blockers if any

---

### 2. `SYSTEM.md` --- THE CONTEXT

**What it is:** A static reference file that tells any LLM everything it needs to know about the project.

**Who updates it:** Humans, when architecture changes.

**When to update:**
- New integration added
- Stack changes
- New environment variables
- New testing procedures
- Architecture decisions

**How to use it:**
```
When starting a new chat with any AI assistant, say:
"Read SYSTEM.md first for project context, then read ZENNY_LOG.md for current status."
```

---

### 3. `Zenny_AI_Detailed_Remediation_Plan_vX.X.md` --- THE ROADMAP

**What it is:** The master plan. What needs to be done, in what order, with specific code changes.

**Who updates it:** Lead developer / CTO, after major milestones.

**How to use it:**
- Pick a task from the plan
- Read ZENNY_LOG.md to see what's already done
- Execute the task
- Append result to ZENNY_LOG.md
- Mark task as done in the plan (or create new plan version)

---

## WORKFLOW FOR EACH AI SESSION

### Step 1: Give Context (You Do This)

```
"I'm working on Zenny AI, an agentic customer support platform.
Before we start, please:
1. Read SYSTEM.md for project architecture
2. Read ZENNY_LOG.md for current status
3. Then tell me what you understand about our current state

After that, I want you to [specific task]."
```

### Step 2: AI Reads and Confirms (AI Does This)

The AI should respond with:
- Summary of current status
- What it understands the task to be
- Any clarifying questions

### Step 3: Execute Task (AI Does This)

AI performs the work, referencing specific files and gaps.

### Step 4: Update Log (YOU Must Do This)

After the AI finishes, YOU append to ZENNY_LOG.md:

```markdown
### [2026-05-21 15:45] --- LOG-003 --- COMPLETED
**Who:** Kimi K2.6
**What:** Wired Prompt Manager into LLM Router
**Files Changed:** `zenny-core-v2/src/services/llm_router.py`
**Details:**
- Imported prompt_manager
- Replaced _build_prompt() with YAML loading
- Added fallback to inline prompt if YAML missing
- Tested with welcome.yml --- loads correctly
**Blockers:** None
**Next:** Test with tenant override from Supabase
```

### Step 5: Next Task (You Decide)

Pick the next task from the remediation plan, or ask the AI what should come next based on ZENNY_LOG.md.

---

## EXAMPLE CONVERSATION FLOW

**You:** "Read SYSTEM.md and ZENNY_LOG.md. We're working on Zenny AI. I need to fix Gap #3 --- the missing llm_cost_logs table."

**AI:** *[Reads files]* "I understand. The supabase-setup.sql is missing the llm_cost_logs table that db.py's log_llm_cost() tries to write to. This will crash on the first LLM call. I'll add the SQL and show you what to run."

**AI:** *[Provides SQL, explains how to run it]*

**You:** *[Run the SQL in Supabase, verify it works]*

**You:** *[Append to ZENNY_LOG.md]*

```markdown
### [2026-05-21 16:00] --- LOG-004 --- COMPLETED
**Who:** [Your name] + Kimi K2.6
**What:** Fixed Gap #3 --- Added llm_cost_logs table
**Files Changed:** `zenny-core-v2/supabase-setup.sql`
**Details:**
- Added CREATE TABLE llm_cost_logs with all columns
- Added indexes for client_id and model_used
- Ran successfully in Supabase SQL Editor
- Verified with SELECT * FROM llm_cost_logs LIMIT 1
**Blockers:** None
**Next:** Fix Gap #4 --- missing json import in prompt_manager.py
```

**You:** "Next task: Fix Gap #4. Read ZENNY_LOG.md for current status."

**AI:** *[Reads log, sees LOG-004 is latest, knows what to do next]*

---

## TIPS FOR EFFECTIVE AI COLLABORATION

### Be Specific

**Bad:** "Fix the code"
**Good:** "In `webhook.py`, the `user_email` variable crashes when `payload.session_context` is None. Make it safe."

### Reference Gaps

**Bad:** "The prompt thing doesn't work"
**Good:** "Gap #1: Wire Prompt Manager into LLM Router. The `_build_prompt()` method in `llm_router.py` still builds prompts inline. It should call `prompt_manager.load()` instead."

### Provide Context

Always start with: "Read SYSTEM.md and ZENNY_LOG.md first."

This saves 10 minutes of the AI asking "what's the project?" questions.

### Verify Before Logging

Don't append to ZENNY_LOG.md until you've actually tested the change.

**Bad:** Log "Fixed" before testing
**Good:** Log "Fixed and verified" after testing

### Use the Same AI Model for Consistency

If you're using Kimi, stick with Kimi for related tasks. Different models have different coding styles.

---

## FILE LOCATIONS

| File | Path | Purpose |
|------|------|---------|
| ZENNY_LOG.md | `docs/ZENNY_LOG.md` or root | Live status tracker |
| SYSTEM.md | `docs/SYSTEM.md` or root | Project context for AI |
| Remediation Plan | `docs/Zenny_AI_Detailed_Remediation_Plan_vX.X.md` | Master roadmap |
| This Guide | `docs/AI_WORKFLOW.md` | How to use the system |

---

## CHECKLIST FOR EACH SESSION

- [ ] AI read SYSTEM.md
- [ ] AI read ZENNY_LOG.md
- [ ] AI confirmed understanding
- [ ] Task executed
- [ ] Change tested
- [ ] ZENNY_LOG.md updated
- [ ] Next task identified

---

*This system only works if you use it consistently. One missed log entry creates confusion. Ten missed entries creates chaos.*
