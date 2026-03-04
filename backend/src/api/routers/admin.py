from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Header, HTTPException

from src.api.schemas import IngestRequest

router = APIRouter(tags=["admin"])


def _main():
    from src.api import main as main_module

    return main_module


@router.post("/api/ingest")
async def ingest_cases(data: IngestRequest, authorization: str | None = Header(default=None)):
    """
    Endpoint administrativo de ingesta de casos hacia Qdrant.
    Si ADMIN_TOKEN está configurado, exige header Authorization Bearer.
    """
    main_module = _main()
    main_module._require_admin_access(authorization)

    base = Path(__file__).resolve().parents[4] / "data"
    csv_paths = [str(base / name) for name in data.csv_files]
    missing = [p for p in csv_paths if not Path(p).exists()]
    if missing:
        raise HTTPException(status_code=400, detail=f"CSV no encontrados: {missing}")

    try:
        if data.force_rebuild:
            await main_module.asyncio.to_thread(main_module.db_connection.reset_cases_collection, "neo_cases_v1")
        ingest_summary = await main_module.asyncio.to_thread(
            main_module.db_connection.load_csv_files, csv_paths, "neo_cases_v1"
        )
    except Exception:
        main_module._raise_internal_server_error("Error en /api/ingest")

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
