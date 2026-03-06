from __future__ import annotations

import asyncio
import uuid
import sys
from types import SimpleNamespace
from pathlib import Path

from httpx import ASGITransport, AsyncClient

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.api import deps
from src.api.main import app
from src.services.rate_limit import rate_limiter
from src.services.session_funnel import session_funnel_store


def _disable_redis_runtime() -> None:
    rate_limiter._redis_client = None
    rate_limiter._redis_unavailable = True
    rate_limiter._buckets.clear()
    session_funnel_store._redis_client = None
    session_funnel_store._redis_unavailable = True
    session_funnel_store._items.clear()


def test_agent_start_http_integration(monkeypatch) -> None:
    _disable_redis_runtime()

    async def fake_ainvoke(inputs: dict, config: dict | None = None) -> dict:
        return {
            "empresa": inputs["empresa"],
            "area": inputs["area"],
            "problema": inputs["problema"],
            "casos_encontrados": [{"id": "CASE-1", "tipo": "NEO"}],
            "neo_cases": [{"id": "CASE-1", "tipo": "NEO"}],
            "ai_cases": [],
            "casos_seleccionados_ids": [],
            "warning": None,
            "error": "",
        }

    monkeypatch.setattr(deps.graph, "ainvoke", fake_ainvoke)
    company = f"ACME-{uuid.uuid4().hex[:8]}"
    payload = {
        "empresa": company,
        "rubro": "Banca",
        "area": "Operaciones",
        "problema": "Necesitamos mejorar trazabilidad y reducir errores en conciliaciones bancarias.",
        "switch": "both",
    }

    async def _run():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            return await client.post("/agent/start", json=payload)

    resp = asyncio.run(_run())
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/json")
    body = resp.json()
    assert isinstance(body.get("thread_id"), str) and body["thread_id"]
    assert body["empresa"] == company.upper()
    assert body["status"] == "awaiting_selection"
    assert len(body["casos_encontrados"]) == 1
    assert body["casos_encontrados"][0]["id"] == "CASE-1"


def test_agent_chat_http_integration(monkeypatch) -> None:
    _disable_redis_runtime()
    thread_id = f"thread-{uuid.uuid4().hex[:8]}"
    state = {
        "empresa": "BCP",
        "casos_encontrados": [
            {
                "id": "CASE-NEO-1",
                "tipo": "NEO",
                "titulo": "Caso Banca",
                "problema": "Demora en conciliaciones",
                "solucion": "Automatizacion IA",
                "url_slide": "https://example.com/case",
            }
        ],
        "casos_seleccionados_ids": ["CASE-NEO-1"],
        "perfil_cliente": {"objetivos": ["eficiencia"]},
        "cliente_priorizado_contexto": {"vertical": "Banca"},
        "inteligencia_sector": {"industria": "Banca", "area": "Operaciones"},
        "chat_messages": [],
    }

    async def fake_aget_state(config: dict) -> SimpleNamespace:
        assert config["configurable"]["thread_id"] == thread_id
        return SimpleNamespace(values=state.copy())

    async def fake_aupdate_state(config: dict, update: dict) -> None:
        if "chat_messages" in update:
            state["chat_messages"] = update["chat_messages"]

    class _FakeLLM:
        async def ainvoke(self, prompt: str) -> SimpleNamespace:
            assert "Casos Disponibles como Base" in prompt
            return SimpleNamespace(content="Recomiendo CASE-NEO-1 por afinidad y evidencia.")

    monkeypatch.setattr(deps.graph, "aget_state", fake_aget_state)
    monkeypatch.setattr(deps.graph, "aupdate_state", fake_aupdate_state)
    monkeypatch.setattr(deps, "get_chat_llm", lambda: _FakeLLM())
    async def _run():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            return await client.post(f"/agent/{thread_id}/chat", json={"message": "Que caso recomiendas?"})

    resp = asyncio.run(_run())
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/json")
    body = resp.json()
    assert body["thread_id"] == thread_id
    assert body["status"] == "ok"
    assert body["used_case_ids"] == ["CASE-NEO-1"]
    assert body["used_case_count"] == 1
    assert "CASE-NEO-1" in body["answer"]
