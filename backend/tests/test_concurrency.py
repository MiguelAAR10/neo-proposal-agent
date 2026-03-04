from __future__ import annotations

import asyncio
import time
import uuid
import sys
from collections import Counter
from pathlib import Path

from httpx import ASGITransport, AsyncClient

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.api import main
from src.services.rate_limit import rate_limiter
from src.services.session_funnel import session_funnel_store


def _prepare_in_memory_runtime(monkeypatch) -> None:
    monkeypatch.setattr(rate_limiter, "_redis_client", None, raising=False)
    monkeypatch.setattr(rate_limiter, "_redis_unavailable", True, raising=False)
    monkeypatch.setattr(session_funnel_store, "_redis_client", None, raising=False)
    monkeypatch.setattr(session_funnel_store, "_redis_unavailable", True, raising=False)
    rate_limiter._buckets.clear()
    session_funnel_store._items.clear()


def test_concurrent_agent_start_respects_rate_limit(monkeypatch) -> None:
    _prepare_in_memory_runtime(monkeypatch)

    company = f"LOADTEST-{uuid.uuid4().hex[:8]}"
    limit = 12
    total_requests = 50

    monkeypatch.setattr(main.settings, "rate_limit_start_per_window", limit, raising=False)
    monkeypatch.setattr(main.settings, "rate_limit_window_sec", 60, raising=False)

    async def fake_ainvoke(inputs: dict, config: dict | None = None) -> dict:
        await asyncio.sleep(0.01)
        return {
            "empresa": inputs["empresa"],
            "area": inputs["area"],
            "problema": inputs["problema"],
            "casos_encontrados": [{"id": "CASE-STRESS-1", "tipo": "AI"}],
            "neo_cases": [],
            "ai_cases": [{"id": "CASE-STRESS-1", "tipo": "AI"}],
            "casos_seleccionados_ids": [],
            "warning": None,
            "error": "",
        }

    monkeypatch.setattr(main.graph, "ainvoke", fake_ainvoke)

    async def _run() -> tuple[Counter, float]:
        transport = ASGITransport(app=main.app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            payload = {
                "empresa": company,
                "rubro": "Banca",
                "area": "Operaciones",
                "problema": "Necesitamos automatizar conciliaciones y mejorar trazabilidad operativa en el banco.",
                "switch": "both",
            }

            async def fire_one() -> int:
                resp = await client.post("/agent/start", json=payload)
                return resp.status_code

            t0 = time.perf_counter()
            statuses = await asyncio.gather(*[fire_one() for _ in range(total_requests)])
            elapsed = time.perf_counter() - t0
        return Counter(statuses), elapsed

    counts, elapsed = asyncio.run(_run())
    assert counts[200] == limit
    assert counts[429] == total_requests - limit
    assert elapsed < 5.0

    summary = session_funnel_store.summary(company=company)
    assert summary["window_sessions"] == limit
    assert summary["sessions_with_cases"] == limit
