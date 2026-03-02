from __future__ import annotations

import time
from typing import Callable

from fastapi import APIRouter, Depends, HTTPException

from src.models.human_insight import HumanInsightCreate, StructuredInsightItem
from src.repositories.base import HumanInsightRepository
from src.services.errors import BackendDomainError, IntelStorageError, ValidationDomainError
from src.services.human_insight_parser import parse_sales_insight_text
from src.services.intel_metrics import intel_metrics
from src.services.intel_storage import human_insight_repository
from src.services.prioritized_clients import normalize_company_name

router = APIRouter()


def _raise_domain_http(error: BackendDomainError) -> None:
    raise HTTPException(
        status_code=error.status_code,
        detail={"code": error.code, "message": error.message},
    )


def get_human_insight_repository() -> HumanInsightRepository:
    return human_insight_repository  # type: ignore[return-value]


def get_insight_parser() -> Callable[[str], list[StructuredInsightItem]]:
    return parse_sales_insight_text


@router.post("/company/{company_id}/insights")
async def create_human_insight(
    company_id: str,
    payload: HumanInsightCreate,
    repository: HumanInsightRepository = Depends(get_human_insight_repository),
    parser: Callable[[str], list[StructuredInsightItem]] = Depends(get_insight_parser),
):
    if not hasattr(repository, "save"):  # soporte para invocacion directa en tests
        repository = get_human_insight_repository()
    if not callable(parser):  # soporte para invocacion directa en tests
        parser = get_insight_parser()

    normalized_company = normalize_company_name(company_id)
    if not normalized_company:
        error = ValidationDomainError("company_id invalido")
        intel_metrics.record_error(error.code)
        _raise_domain_http(error)

    parse_start = time.perf_counter()
    try:
        structured = parser(payload.text)
    except BackendDomainError as exc:
        intel_metrics.record_error(exc.code)
        _raise_domain_http(exc)
    except Exception as exc:
        error = IntelStorageError(f"Error parseando insight: {exc}")
        intel_metrics.record_error(error.code)
        _raise_domain_http(error)
    parse_ms = int((time.perf_counter() - parse_start) * 1000)

    store_start = time.perf_counter()
    try:
        saved = repository.save(
            company_id=normalized_company,
            seller_id=payload.seller_id,
            raw_text=payload.text,
            structured_payload=structured,
            source=payload.source,
            parser_version="v1",
        )
    except Exception as exc:
        error = IntelStorageError(f"Error guardando insight: {exc}")
        intel_metrics.record_error(error.code)
        _raise_domain_http(error)
    store_ms = int((time.perf_counter() - store_start) * 1000)
    intel_metrics.record_success(parse_ms=parse_ms, store_ms=store_ms)

    return {
        "status": "success",
        "company_id": saved.company_id,
        "insight_id": saved.id,
        "created_at": saved.created_at,
        "structured_payload": [item.model_dump() for item in saved.structured_payload],
        "metrics": {
            "parse_ms": parse_ms,
            "store_ms": store_ms,
        },
    }
