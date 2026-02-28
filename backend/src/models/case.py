from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator

VALID_INDUSTRIAS = {
    "Banca",
    "Salud",
    "Tech",
    "Retail",
    "Seguros",
    "Consumo Masivo",
    "Otro",
}

VALID_AREAS = {
    "Operaciones",
    "Marketing",
    "TI",
    "Finanzas",
    "Ventas",
    "RRHH",
    "Innovacion",
    "Innovación",
    "Customer Experience",
    "Otro",
}


class CaseInput(BaseModel):
    """Normalized case schema validated during ingestion."""

    case_id: str = Field(..., min_length=2)
    tipo: Literal["AI", "NEO"]
    titulo: str = Field(..., min_length=5, max_length=200)
    problema: str = Field(..., min_length=8, max_length=1000)
    solucion: str = Field(..., min_length=8, max_length=1000)
    url_slide: str

    empresa: str | None = None
    industria: str | None = None
    area: str | None = None
    beneficios: list[str] = Field(default_factory=list)
    stack: list[str] = Field(default_factory=list)
    kpi_impacto: str | None = None
    origen: str | None = None

    @field_validator("case_id")
    @classmethod
    def _validate_case_id(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("case_id no puede estar vacio")
        return cleaned

    @field_validator("url_slide")
    @classmethod
    def _validate_url(cls, value: str) -> str:
        raw = (value or "").strip()
        parsed = urlparse(raw)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("url_slide debe ser HTTP/HTTPS valida")
        return raw

    @field_validator("industria")
    @classmethod
    def _validate_industria(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        cleaned = value.strip()
        if cleaned not in VALID_INDUSTRIAS:
            return "Otro"
        return cleaned

    @field_validator("area")
    @classmethod
    def _validate_area(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        cleaned = value.strip()
        if cleaned not in VALID_AREAS:
            return "Otro"
        return cleaned


class CaseQdrant(BaseModel):
    """Qdrant payload with fallback fields already computed."""

    case_id: str
    tipo: Literal["AI", "NEO"]
    titulo: str
    problema: str
    solucion: str
    url_slide: str

    empresa: str | None = None
    industria: str | None = None
    area: str | None = None
    beneficios: list[str] = Field(default_factory=list)
    stack: list[str] = Field(default_factory=list)
    kpi_impacto: str | None = None

    confianza_fuente: float
    origen: str
    data_quality_score: float
    semantic_quality: str
    fecha_ingesta: str

    @classmethod
    def from_input(cls, case: CaseInput) -> "CaseQdrant":
        has_problem_verb = any(
            token in case.problema.lower()
            for token in ("automat", "mejor", "optim", "reduc", "analiz", "predict", "detec")
        )
        has_solution_signal = any(
            token in case.solucion.lower()
            for token in ("ia", "ai", "ml", "llm", "rpa", "dashboard", "modelo", "agente")
        )
        semantic_quality = "good" if has_problem_verb or has_solution_signal else "basic"

        quality = 0.0
        if case.url_slide:
            quality += 0.25
        if case.kpi_impacto or case.beneficios:
            quality += 0.25
        if case.stack:
            quality += 0.2
        if case.empresa:
            quality += 0.15
        if semantic_quality == "good":
            quality += 0.15

        return cls(
            case_id=case.case_id,
            tipo=case.tipo,
            titulo=case.titulo,
            problema=case.problema,
            solucion=case.solucion,
            url_slide=case.url_slide,
            empresa=case.empresa,
            industria=case.industria,
            area=case.area,
            beneficios=case.beneficios,
            stack=case.stack,
            kpi_impacto=case.kpi_impacto,
            confianza_fuente=1.0 if case.tipo == "NEO" else 0.85,
            origen=case.origen or "unknown",
            data_quality_score=round(min(1.0, quality), 3),
            semantic_quality=semantic_quality,
            fecha_ingesta=datetime.now(timezone.utc).isoformat(),
        )
