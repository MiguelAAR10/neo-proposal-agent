from typing import NotRequired, TypedDict, Literal


class ProposalState(TypedDict):
    # Inputs iniciales
    empresa: str
    rubro: str
    area: str
    problema: str
    switch: Literal["neo", "ai", "both"]
    
    # Contexto recuperado
    casos_encontrados: list[dict]
    neo_cases: NotRequired[list[dict]]
    ai_cases: NotRequired[list[dict]]
    top_match_global: NotRequired[dict]
    top_match_global_reason: NotRequired[str]
    perfil_cliente: NotRequired[dict]
    profile_status: NotRequired[Literal["found", "not_found", "incomplete"]]
    cliente_priorizado_contexto: NotRequired[dict]
    inteligencia_sector: NotRequired[dict]
    
    # Decisiones HITL
    casos_seleccionados_ids: list[str]
    
    # Resultados
    propuesta_final: str
    propuesta_versiones: list[str]  # Para manejar v1, v2, etc.
    chat_messages: NotRequired[list[dict[str, str]]]
    
    # Control
    warning: NotRequired[str]
    error: NotRequired[str]
    thread_id: NotRequired[str]
    updated_at: NotRequired[str]
