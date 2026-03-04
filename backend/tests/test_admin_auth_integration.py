from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from httpx import ASGITransport, AsyncClient

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.api import main


def _force_admin_token(monkeypatch, token: str = "test-admin-token") -> str:
    monkeypatch.setattr(main.settings, "admin_token", token)
    monkeypatch.setattr(main.settings, "app_env", "development")
    return token


def test_ops_metrics_requires_token(monkeypatch) -> None:
    token = _force_admin_token(monkeypatch)
    async def _run():
        transport = ASGITransport(app=main.app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            missing = await client.get("/ops/metrics")
            invalid = await client.get("/ops/metrics", headers={"Authorization": "Bearer wrong-token"})
            ok = await client.get("/ops/metrics", headers={"Authorization": f"Bearer {token}"})
            return missing, invalid, ok

    missing, invalid, ok = asyncio.run(_run())
    assert missing.status_code in {401, 403}
    assert invalid.status_code in {401, 403}
    assert ok.status_code == 200
    body = ok.json()
    assert body["status"] == "ok"
    assert "search" in body
    assert "intel" in body


def test_ops_funnel_requires_token(monkeypatch) -> None:
    token = _force_admin_token(monkeypatch)
    async def _run():
        transport = ASGITransport(app=main.app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            missing = await client.get("/ops/funnel")
            invalid = await client.get("/ops/funnel", headers={"Authorization": "Bearer invalid"})
            ok = await client.get("/ops/funnel", headers={"Authorization": f"Bearer {token}"})
            return missing, invalid, ok

    missing, invalid, ok = asyncio.run(_run())
    assert missing.status_code in {401, 403}
    assert invalid.status_code in {401, 403}
    assert ok.status_code == 200
    assert ok.json()["status"] == "ok"


def test_ingest_requires_token_and_allows_valid_token(monkeypatch) -> None:
    token = _force_admin_token(monkeypatch)
    payload = {"csv_files": ["missing_fixture.csv"], "force_rebuild": False}

    async def _run():
        transport = ASGITransport(app=main.app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            missing = await client.post("/api/ingest", json=payload)
            invalid = await client.post(
                "/api/ingest",
                json=payload,
                headers={"Authorization": "Bearer invalid"},
            )
            ok = await client.post(
                "/api/ingest",
                json=payload,
                headers={"Authorization": f"Bearer {token}"},
            )
            return missing, invalid, ok

    missing, invalid, ok = asyncio.run(_run())
    assert missing.status_code in {401, 403}
    assert invalid.status_code in {401, 403}
    assert ok.status_code == 400
    assert "CSV no encontrados" in ok.json()["detail"]
