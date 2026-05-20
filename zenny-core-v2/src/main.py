"""
Zenny Core — FastAPI Application Entry Point
Boots the API, registers routes, sets up middleware.
"""

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.services.db import get_supabase
from src.services.redis_client import get_redis, close_redis


# ── Lifespan: startup / shutdown ──
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Connect to Redis on startup, close on shutdown."""
    await get_redis()
    print(f"✅ Zenny Core booted — {settings.environment} mode")
    yield
    await close_redis()
    print("🛑 Zenny Core shutdown")


# ── App Factory ──
app = FastAPI(
    title="Zenny Core API",
    description="ZeroManual AI Customer Support Infrastructure",
    version="2.1.0",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    lifespan=lifespan,
)

# ── CORS ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: restrict to client domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request Timing Middleware ──
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    latency = round((time.time() - start) * 1000)
    response.headers["X-Process-Time-Ms"] = str(latency)
    return response


# ── Global Exception Handler ──
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "detail": str(exc) if not settings.is_production else "Contact support",
        },
    )


# ── Health Check ──
@app.get("/health")
async def health_check():
    """Liveness probe for Railway / monitoring."""
    redis = await get_redis()
    redis_ok = await redis.ping()
    return {
        "status": "ok",
        "version": "2.1.0",
        "environment": settings.environment,
        "redis": "connected" if redis_ok else "disconnected",
    }


# ── Import & Register Routes (after app creation to avoid circular imports) ──
from src.api import routes  # noqa: E402

routes.register_routes(app)
