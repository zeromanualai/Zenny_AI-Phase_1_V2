# Zenny Core — Python/FastAPI

AI-powered customer support infrastructure. Python rewrite of TypeScript backend.

## Quick Start

```bash
# 1. Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# 2. Install dependencies
poetry install

# 3. Copy env template
cp .env.example .env
# Edit .env with your keys

# 4. Run locally
poetry run uvicorn src.main:app --reload

# 5. Test health
curl http://localhost:8000/health
```

## Deploy to Railway

```bash
# Push to GitHub, Railway auto-detects Python
# Set env vars in Railway dashboard (see docs/env-railway.md)
```

## Project Structure

```
src/
  main.py              # FastAPI app entry
  config.py            # Pydantic-Settings env validation
  types.py             # Pydantic models
  services/            # Business logic
    db.py              # Supabase client
    redis_client.py    # Redis sessions
    llm_router.py      # Tiered AI routing
    policy_guard.py    # Deterministic rules
    state_manager.py   # Session management
    rag.py             # KB retrieval
    action_engine.py   # n8n integration
    prompt_manager.py  # YAML prompt loader
    pii_redactor.py    # PII redaction
```

## Testing

```bash
poetry run pytest
```
