from __future__ import annotations

from fastapi import APIRouter, HTTPException

from src.models.human_insight import HumanInsightCreate
from src.services.human_insight_parser import parse_sales_insight_text
from src.services.intel_storage import human_insight_repository
from src.services.prioritized_clients import normalize_company_name

router = APIRouter()


@router.post("/company/{company_id}/insights")
async def create_human_insight(company_id: str, payload: HumanInsightCreate):
    normalized_company = normalize_company_name(company_id)
    if not normalized_company:
        raise HTTPException(status_code=400, detail={"code": "INVALID_COMPANY", "message": "company_id invalido"})

    structured = parse_sales_insight_text(payload.text)
    saved = human_insight_repository.save(
        company_id=normalized_company,
        seller_id=payload.seller_id.strip(),
        raw_text=payload.text.strip(),
        structured_payload=structured,
        source=payload.source,
        parser_version="v1",
    )

    return {
        "status": "success",
        "company_id": saved.company_id,
        "insight_id": saved.id,
        "created_at": saved.created_at,
        "structured_payload": [item.model_dump() for item in saved.structured_payload],
    }
