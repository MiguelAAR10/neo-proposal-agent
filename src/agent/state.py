from typing import NotRequired, TypedDict


class ProposalState(TypedDict):
    empresa: str
    rubro: str
    problema: str
    casos_encontrados: list[dict]
    casos_seleccionados_ids: list[str]
    propuesta_final: str
    error: NotRequired[str]
