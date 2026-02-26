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
    perfil_cliente: NotRequired[dict]
    inteligencia_sector: NotRequired[dict]
    
    # Decisiones HITL
    casos_seleccionados_ids: list[str]
    
    # Resultados
    propuesta_final: str
    propuesta_versiones: list[str]  # Para manejar v1, v2, etc.
    
    # Control
    error: NotRequired[str]
    thread_id: NotRequired[str]
    updated_at: NotRequired[str]
