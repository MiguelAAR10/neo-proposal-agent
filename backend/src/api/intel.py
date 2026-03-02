from __future__ import annotations

import time
from typing import Callable

from fastapi import APIRouter, Depends, HTTPException

from src.models.human_insight import HumanInsightCreate, ParsedHumanInsight
from src.repositories.base import CompanyProfileRepository, HumanInsightRepository
from src.services.errors import BackendDomainError, IntelStorageError, ValidationDomainError
from src.services.human_insight_parser import parse_sales_insight_text
from src.services.intel_metrics import intel_metrics
from src.services.intel_storage import company_profile_repository, human_insight_repository
from src.services.prioritized_clients import normalize_company_name

router = APIRouter()


def _raise_domain_http(error: BackendDomainError) -> None:
    raise HTTPException(
        status_code=error.status_code,
        detail={"code": error.code, "message": error.message},
    )


def get_human_insight_repository() -> HumanInsightRepository:
    return human_insight_repository  # type: ignore[return-value]


def get_company_profile_repository() -> CompanyProfileRepository:
    return company_profile_repository  # type: ignore[return-value]


def get_insight_parser() -> Callable[[str], ParsedHumanInsight]:
    return parse_sales_insight_text


@router.post("/company/{company_id}/insights")
async def create_human_insight(
    company_id: str,
    payload: HumanInsightCreate,
    repository: HumanInsightRepository = Depends(get_human_insight_repository),
    parser: Callable[[str], ParsedHumanInsight] = Depends(get_insight_parser),
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
        parsed = parser(payload.text)
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
            author=payload.author,
            department=parsed.department,
            sentiment=parsed.sentiment,
            raw_text=payload.text,
            structured_payload=parsed.structured_payload,
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
        "author": saved.author,
        "department": saved.department,
        "sentiment": saved.sentiment,
        "created_at": saved.created_at,
        "structured_payload": [item.model_dump() for item in saved.structured_payload],
        "metrics": {
            "parse_ms": parse_ms,
            "store_ms": store_ms,
        },
    }


@router.get("/company/{company_id}/profile")
async def get_company_profile(
    company_id: str,
    area: str = "General",
    refresh: bool = True,
    repository: CompanyProfileRepository = Depends(get_company_profile_repository),
):
    if not hasattr(repository, "get_profile"):
        repository = get_company_profile_repository()

    normalized_company = normalize_company_name(company_id)
    normalized_area = (area or "General").strip() or "General"
    if not normalized_company:
        error = ValidationDomainError("company_id invalido")
        intel_metrics.record_error(error.code)
        _raise_domain_http(error)

    refresh_result: dict[str, object] | None = None
    if refresh:
        try:
            from src.agent.nodes import update_summary_node

            state = {
                "empresa": normalized_company,
                "area": normalized_area,
                "perfil_cliente": {"empresa": normalized_company, "area": normalized_area},
                "inteligencia_sector": {
                    "industria": "General",
                    "area": normalized_area,
                    "source": "intel_profile_endpoint",
                    "tendencias": [],
                    "benchmarks": {},
                    "oportunidades": [],
                },
                "error": "",
            }
            result = update_summary_node(state)
            refresh_result = {
                "status": "ok",
                "human_insights_used": len(result.get("human_insights", [])),
            }
        except Exception as exc:
            code = "PROFILE_REFRESH_ERROR"
            intel_metrics.record_error(code)
            refresh_result = {"status": "error", "detail": str(exc)}

    try:
        profile = repository.get_profile(company_id=normalized_company, area=normalized_area)
    except Exception as exc:
        error = IntelStorageError(f"Error leyendo perfil: {exc}")
        intel_metrics.record_error(error.code)
        _raise_domain_http(error)
        return {}

    if profile is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "PROFILE_NOT_FOUND",
                "message": "No existe perfil consolidado para la empresa/area solicitada.",
            },
        )

    return {
        "status": "success",
        "company_id": profile.company_id,
        "area": profile.area,
        "updated_at": profile.updated_at,
        "profile_payload": profile.profile_payload,
        "refresh": refresh_result,
    }
