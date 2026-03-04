from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class StartRequest(BaseModel):
    empresa: str = Field(..., example="BCP")
    rubro: str = Field(..., example="Banca")
    area: str = Field(..., example="Operaciones")
    problema: str = Field(..., min_length=20, example="Automatización de conciliaciones bancarias...")
    switch: Literal["neo", "ai", "both"] = "both"

    @field_validator("switch", mode="before")
    @classmethod
    def normalize_switch(cls, value: str) -> str:
        return str(value).strip().lower()


class SelectRequest(BaseModel):
    case_ids: List[str] = Field(..., min_items=1)


class SearchRequest(BaseModel):
    problema: str = Field(..., min_length=10, example="Mejorar decisiones en credit scoring con IA")
    switch: Literal["neo", "ai", "both"] = "both"

    @field_validator("switch", mode="before")
    @classmethod
    def normalize_switch(cls, value: str) -> str:
        return str(value).strip().lower()


class RefineRequest(BaseModel):
    instruction: str = Field(..., min_length=5, example="Hazla más corta y enfatiza ROI")


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=2, example="Que caso aplica mejor para este cliente y por que?")


class ChatResponse(BaseModel):
    thread_id: str
    answer: str
    used_case_ids: List[str] = Field(default_factory=list)
    used_case_count: int
    status: str
    guardrail_code: Optional[str] = None
    audit_ts_utc: Optional[str] = None


class IngestRequest(BaseModel):
    csv_files: List[str] = Field(default_factory=lambda: ["ai_cases.csv", "neo_legacy.csv"])
    force_rebuild: bool = False


class AgentStateResponse(BaseModel):
    thread_id: str
    empresa: str
    area: str
    problema: str
    casos_encontrados: List[dict]
    neo_cases: List[dict] = Field(default_factory=list)
    ai_cases: List[dict] = Field(default_factory=list)
    top_match_global: Optional[dict] = None
    top_match_global_reason: Optional[str] = None
    casos_seleccionados_ids: List[str]
    perfil_cliente: Optional[dict] = None
    profile_status: Optional[Literal["found", "not_found", "incomplete"]] = None
    cliente_priorizado_contexto: Optional[dict] = None
    inteligencia_sector: Optional[dict] = None
    human_insights: List[dict] = Field(default_factory=list)
    propuesta_final: Optional[str] = None
    status: str
    warning: Optional[str] = None
    error: Optional[str] = None
