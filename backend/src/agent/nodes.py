from datetime import datetime
import logging
from typing import Any
from langchain_google_genai import ChatGoogleGenerativeAI
from src.agent.state import ProposalState
from src.config import get_settings
from src.services.prioritized_clients import get_prioritized_client_context, is_prioritized_client
from src.services.proposal_context import (
    filter_selected_cases,
    format_cases_for_prompt,
    validate_selected_cases_have_url,
)
from src.services.search_service import search_cases_sync
from src.tools.qdrant_tool import db_connection

logger = logging.getLogger(__name__)


def intake_node(state: ProposalState) -> ProposalState:
    """Valida los inputs iniciales y prepara el estado."""
    empresa = (state.get("empresa") or "").strip()
    problema = (state.get("problema") or "").strip()
    area = (state.get("area") or "General").strip()
    switch = state.get("switch") or "both"

    if not empresa or not problema:
        state["error"] = "Los campos Empresa y Problema son obligatorios."
        return state
    if not is_prioritized_client(empresa):
        state["error"] = (
            "En esta fase solo se permiten clientes priorizados: "
            "BCP, Interbank, BBVA, Alicorp, Rimac, Pacifico, Scotiabank, MiBanco, "
            "Credicorp, Plaza Vea, Falabella y Sodimac."
        )
        return state

    state["empresa"] = empresa
    state["problema"] = problema
    state["area"] = area
    state["switch"] = switch
    state["cliente_priorizado_contexto"] = get_prioritized_client_context(empresa)
    state["error"] = ""
    return state

def retrieve_node(state: ProposalState) -> ProposalState:
    """Busca casos (con switch) y recupera el perfil del cliente (Dummy/Real)."""
    if state.get("error"):
        return state

    try:
        # 1. Buscar casos via primitiva compartida (/api/search)
        search_payload = search_cases_sync(
            problema=state["problema"],
            switch=state["switch"],
            limit=6,
            score_threshold=0.50,
        )
        reranked_all = _rerank_cases_for_client(
            search_payload.get("casos", []),
            empresa=state.get("empresa", ""),
            area=state.get("area", ""),
            rubro=state.get("rubro", ""),
        )
        reranked_neo = _rerank_cases_for_client(
            search_payload.get("neo_cases", []),
            empresa=state.get("empresa", ""),
            area=state.get("area", ""),
            rubro=state.get("rubro", ""),
        )
        reranked_ai = _rerank_cases_for_client(
            search_payload.get("ai_cases", []),
            empresa=state.get("empresa", ""),
            area=state.get("area", ""),
            rubro=state.get("rubro", ""),
        )
        # Para cards seleccionables exigimos evidencia URL.
        filtered_cases = [c for c in reranked_all if c.get("url_slide")]
        filtered_neo = [c for c in reranked_neo if c.get("url_slide")]
        filtered_ai = [c for c in reranked_ai if c.get("url_slide")]

        # Fallback comercial: nunca dejar la UI sin fichas; ampliar búsqueda por rubro/área.
        if not filtered_cases:
            fallback_query = (
                f"Iniciativas de alto impacto para {state.get('rubro', 'negocio')} "
                f"en el área {state.get('area', 'operaciones')} con evidencia verificable"
            )
            fallback_payload = search_cases_sync(
                problema=fallback_query,
                switch="both",
                limit=8,
                score_threshold=0.35,
            )
            fallback_cases = _rerank_cases_for_client(
                fallback_payload.get("casos", []),
                empresa=state.get("empresa", ""),
                area=state.get("area", ""),
                rubro=state.get("rubro", ""),
            )
            fallback_neo = _rerank_cases_for_client(
                fallback_payload.get("neo_cases", []),
                empresa=state.get("empresa", ""),
                area=state.get("area", ""),
                rubro=state.get("rubro", ""),
            )
            fallback_ai = _rerank_cases_for_client(
                fallback_payload.get("ai_cases", []),
                empresa=state.get("empresa", ""),
                area=state.get("area", ""),
                rubro=state.get("rubro", ""),
            )
            filtered_cases = [c for c in fallback_cases if c.get("url_slide")]
            filtered_neo = [c for c in fallback_neo if c.get("url_slide")]
            filtered_ai = [c for c in fallback_ai if c.get("url_slide")]

            # Etiquetar explícitamente como relacionados/inspiracionales para transparencia UX.
            for item in filtered_cases:
                item.setdefault("match_type", "inspiracional")
                item.setdefault("match_reason", "Sugerencia por afinidad de industria/área")
            for item in filtered_neo:
                item.setdefault("match_type", "inspiracional")
            for item in filtered_ai:
                item.setdefault("match_type", "inspiracional")

        state["casos_encontrados"] = filtered_cases
        state["neo_cases"] = filtered_neo
        state["ai_cases"] = filtered_ai

        top_match = search_payload.get("top_match_global")
        if top_match and top_match.get("url_slide"):
            state["top_match_global"] = top_match
            state["top_match_global_reason"] = search_payload.get("top_match_global_reason", "")

        # 2. Buscar perfil del cliente (Insights de negocio)
        perfil = db_connection.get_profile(state["empresa"], state["area"])
        if perfil:
            state["perfil_cliente"] = perfil
            has_objectives = bool(perfil.get("objetivos"))
            has_pains = bool(perfil.get("pain_points"))
            state["profile_status"] = "found" if (has_objectives and has_pains) else "incomplete"
            logger.info("Perfil encontrado para empresa=%s area=%s", state["empresa"], state["area"])
        else:
            # Si no existe, podemos crear un placeholder o dejarlo vacío
            state["perfil_cliente"] = {
                "empresa": state["empresa"],
                "area": state["area"],
                "notas": "Empresa nueva sin historial previo."
            }
            state["profile_status"] = "not_found"

        # 3. Contexto sectorial (placeholder estructurado para el layout lateral)
        state["inteligencia_sector"] = _build_sector_intel(
            rubro=state.get("rubro", ""),
            area=state.get("area", ""),
        )

        if not state["casos_encontrados"]:
            state["error"] = (
                "No se encontraron casos con evidencia suficiente para el problema ingresado. "
                "Intenta reformular en términos de industria/área."
            )
            
    except Exception as exc:
        state["error"] = f"Error en retrieve_node: {exc}"

    return state


def _rerank_cases_for_client(
    cases: list[dict[str, Any]],
    empresa: str,
    area: str,
    rubro: str,
) -> list[dict[str, Any]]:
    empresa_norm = (empresa or "").strip().lower()
    area_norm = (area or "").strip().lower()
    rubro_norm = (rubro or "").strip().lower()

    rescored: list[dict[str, Any]] = []
    for case in cases:
        score_raw = float(case.get("score_raw", case.get("score", 0.0)))
        bonus = 0.0

        case_empresa = str(case.get("empresa") or "").strip().lower()
        case_area = str(case.get("area") or "").strip().lower()
        case_industria = str(case.get("industria") or "").strip().lower()

        if empresa_norm and case_empresa and (empresa_norm in case_empresa or case_empresa in empresa_norm):
            bonus += 0.12
        if area_norm and case_area and (area_norm == case_area):
            bonus += 0.05
        if rubro_norm and case_industria and (rubro_norm in case_industria or case_industria in rubro_norm):
            bonus += 0.03

        rescored_case = dict(case)
        rescored_case["score_client_fit"] = round(min(1.0, score_raw + bonus), 4)
        if bonus >= 0.12:
            rescored_case["match_type"] = "exacto"
            rescored_case["match_reason"] = "Coincidencia directa con empresa/área objetivo"
        elif bonus > 0:
            rescored_case["match_type"] = "relacionado"
            rescored_case["match_reason"] = "Coincidencia parcial por industria/área"
        else:
            rescored_case["match_type"] = "inspiracional"
            rescored_case["match_reason"] = "Referencia útil por similitud de problema"
        rescored.append(rescored_case)

    rescored.sort(key=lambda c: c.get("score_client_fit", c.get("score_raw", 0.0)), reverse=True)
    return rescored


def _build_sector_intel(rubro: str, area: str) -> dict:
    rubro_norm = (rubro or "General").strip()
    area_norm = (area or "General").strip()
    return {
        "industria": rubro_norm,
        "area": area_norm,
        "tendencias": [
            f"Automatización inteligente aplicada a {area_norm}",
            f"Uso de IA generativa para productividad en {rubro_norm}",
            "Gobierno de datos y trazabilidad como ventaja competitiva",
        ],
        "benchmarks": {
            "ahorro_potencial": "15-30% en eficiencias operativas",
            "time_to_value": "8-16 semanas para pilotos controlados",
        },
        "oportunidades": [
            "Priorización de quick wins con casos comparables",
            "Escalado modular por unidades de negocio",
        ],
        "source": "placeholder_v2",
    }

def _format_profile_for_prompt(perfil: dict | None) -> str:
    if not perfil or not perfil.get("empresa"):
        return "No hay información previa del cliente."
    
    return (
        f"Información sobre {perfil.get('empresa')}:\n"
        f"- Objetivos: {perfil.get('objetivos', 'N/A')}\n"
        f"- Pain Points: {perfil.get('pain_points', 'N/A')}\n"
        f"- Estilo/Cultura: {perfil.get('notas', 'N/A')}"
    )


def _format_sector_for_prompt(sector: dict | None) -> str:
    if not sector:
        return "No hay inteligencia sectorial disponible."
    return (
        f"Sector: {sector.get('industria', 'N/A')} / Área: {sector.get('area', 'N/A')}\n"
        f"- Tendencias: {sector.get('tendencias', [])}\n"
        f"- Benchmarks: {sector.get('benchmarks', {})}\n"
        f"- Oportunidades: {sector.get('oportunidades', [])}"
    )


def _format_prioritized_client_context(context: dict | None) -> str:
    if not context:
        return "No hay contexto estrategico del cliente priorizado."

    return (
        f"Vertical: {context.get('vertical', 'N/A')}\n"
        f"- Prioridades: {context.get('priorities', [])}\n"
        f"- Restricciones: {context.get('constraints', [])}\n"
        f"- Fuente: {context.get('source', 'N/A')}"
    )


def draft_node(state: ProposalState) -> ProposalState:
    """Genera la propuesta final usando los casos y el perfil del cliente."""
    logger.info("Entrando a draft_node empresa=%s", state.get("empresa"))
    if state.get("error"):
        logger.warning("draft_node omitido por error previo: %s", state.get("error"))
        return state

    selected_ids = list(state.get("casos_seleccionados_ids", []))
    found_cases = state.get("casos_encontrados", [])
    filtered_cases = filter_selected_cases(found_cases, selected_ids)
    if not filtered_cases:
        logger.warning("draft_node sin casos filtrados para selected_case_ids=%s", selected_ids)
        state["error"] = "Debes seleccionar al menos un caso antes de generar la propuesta."
        return state

    has_url, missing_url_ids = validate_selected_cases_have_url(filtered_cases)
    if not has_url:
        state["error"] = (
            "Todos los casos seleccionados deben incluir URL de evidencia. "
            f"Faltan URL en: {', '.join(missing_url_ids)}"
        )
        return state

    try:
        logger.info("draft_node llamando a Gemini con %s casos", len(filtered_cases))
        settings = get_settings()
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0.3,
            google_api_key=settings.gemini_api_key,
        )

        prompt = (
            "Eres un consultor comercial senior experto en estrategia de negocios.\n"
            "Tu objetivo es redactar una PROPUESTA DE VALOR que resuelva un problema técnico "
            "pero que hable el lenguaje de negocio del cliente.\n\n"
            
            "--- CONTEXTO DEL CLIENTE ---\n"
            f"Empresa: {state['empresa']}\n"
            f"Área: {state['area']}\n"
            f"Problema actual: {state['problema']}\n"
            f"{_format_profile_for_prompt(state.get('perfil_cliente'))}\n\n"

            "--- CONTEXTO CLIENTE PRIORIZADO ---\n"
            f"{_format_prioritized_client_context(state.get('cliente_priorizado_contexto'))}\n\n"

            "--- INTELIGENCIA DE MERCADO / SECTOR ---\n"
            f"{_format_sector_for_prompt(state.get('inteligencia_sector'))}\n\n"
            
            "--- CASOS DE ÉXITO SELECCIONADOS (BASE TECNOLÓGICA) ---\n"
            f"{format_cases_for_prompt(filtered_cases)}\n\n"
            
            "INSTRUCCIONES DE REDACCIÓN:\n"
            "1. Usa el 'Enfoque Propuesto' basado en los casos de éxito, pero ADÁPTALO a los objetivos del cliente.\n"
            "2. Si el cliente es adverso al riesgo (ver perfil), propón una implementación modular.\n"
            "3. Resalta el IMPACTO de negocio, no solo la tecnología.\n"
            "4. Incluye al menos 2 KPI/impactos cuantificables cuando la evidencia lo permita.\n"
            "5. Mantén un tono ejecutivo, profesional y persuasivo.\n"
            "6. Máximo 500 palabras."
        )

        response = llm.invoke(prompt)
        text = str(response.content)

        state["propuesta_final"] = text.strip()
        state["propuesta_versiones"] = [text.strip()]
        state["updated_at"] = datetime.now().isoformat()
        state["error"] = ""
    except Exception as exc:
        state["error"] = f"Error generando propuesta: {exc}"

    return state
