from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi import APIRouter, Header, HTTPException

from src.api.deps import db_connection, raise_internal_server_error, require_admin_access
from src.api.schemas import IngestRequest

router = APIRouter(tags=["admin"])


@router.post("/api/ingest")
async def ingest_cases(data: IngestRequest, authorization: str | None = Header(default=None)):
    """Endpoint administrativo de ingesta de casos hacia Qdrant."""
    require_admin_access(authorization)

    base = Path(__file__).resolve().parents[4] / "data"
    csv_paths = [str(base / name) for name in data.csv_files]
    missing = [p for p in csv_paths if not Path(p).exists()]
    if missing:
        raise HTTPException(status_code=400, detail=f"CSV no encontrados: {missing}")

    try:
        if data.force_rebuild:
            await asyncio.to_thread(db_connection.reset_cases_collection, "neo_cases_v1")
        ingest_summary = await asyncio.to_thread(
            db_connection.load_csv_files, csv_paths, "neo_cases_v1"
        )
    except Exception:
        raise_internal_server_error("Error en /api/ingest")

    return {
        "status": "success",
        "summary": {
            "csv_files": data.csv_files,
            "inserted": ingest_summary.get("valid", 0),
            "rejected": ingest_summary.get("rejected", 0),
            "with_url": ingest_summary.get("with_url", 0),
            "missing_url": ingest_summary.get("missing_url", 0),
            "source_stats": ingest_summary.get("source_stats", {}),
            "collection": "neo_cases_v1",
        },
    }
