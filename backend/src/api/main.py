"""
main.py — FastAPI MVP V2 Backend entrypoint.

All shared helpers and dependencies live in src.api.deps.
Routers import directly from deps — no circular references.
"""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

import redis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routers import admin_router, agent_router, ops_router
from src.api.intel import router as intel_router
from src.config import get_settings
from src.tools.qdrant_tool import db_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("neo_api_v2")
settings = get_settings()
_HEALTHCHECK_TIMEOUT_SEC = 1.0


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("NEO Proposal Agent API V2 starting up...")
    yield
    logger.info("NEO Proposal Agent API V2 shutting down...")


app = FastAPI(
    title="NEO Proposal Agent API",
    version="2.1.0",
    description="Backend para la generación de propuestas comerciales orientadas a perfiles corporativos.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Health checks ---
async def _check_qdrant_health() -> str:
    if not settings.qdrant_url:
        return "not_configured"
    try:
        client = db_connection._ensure_client()
        await asyncio.wait_for(
            asyncio.to_thread(client.get_collections),
            timeout=_HEALTHCHECK_TIMEOUT_SEC,
        )
        return "connected"
    except Exception as exc:
        logger.warning("Qdrant health check failed: %s", exc)
        return "unavailable"


async def _check_redis_health() -> str:
    if not settings.redis_url:
        return "not_configured"

    def _ping() -> bool:
        client = redis.from_url(
            settings.redis_url,
            socket_timeout=_HEALTHCHECK_TIMEOUT_SEC,
            socket_connect_timeout=_HEALTHCHECK_TIMEOUT_SEC,
            decode_responses=True,
        )
        return bool(client.ping())

    try:
        ok = await asyncio.wait_for(
            asyncio.to_thread(_ping),
            timeout=_HEALTHCHECK_TIMEOUT_SEC,
        )
        return "connected" if ok else "unavailable"
    except Exception as exc:
        logger.warning("Redis health check failed: %s", exc)
        return "unavailable"


@app.get("/health")
async def health():
    """Verifica el estado de los servicios."""
    qdrant_status, redis_status = await asyncio.gather(
        _check_qdrant_health(),
        _check_redis_health(),
    )
    status = "healthy" if (qdrant_status == "connected" and redis_status == "connected") else "degraded"
    return {
        "status": status,
        "version": "2.1.0",
        "environment": settings.app_env,
        "qdrant": qdrant_status,
        "redis_required": settings.is_non_local_env,
    }


# --- Router registration ---
app.include_router(agent_router)
app.include_router(ops_router)
app.include_router(admin_router)
app.include_router(intel_router, prefix="/intel", tags=["intel"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
