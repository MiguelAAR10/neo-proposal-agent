from datetime import datetime, timezone
import logging
from typing import Any, Literal
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
from src.services.intel_storage import company_profile_repository, human_insight_repository

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
    """Busca casos (con switch) y recupera el perfil del cliente desde repositorio."""
    if state.get("error"):
        return state

    try:
        # 1. Buscar casos via primitiva compartida (/api/search)
        search_payload = _search_with_progressive_thresholds(
            problema=state["problema"],
            switch=state["switch"],
            thresholds=(0.50, 0.40, 0.30, 0.20),
            limit=8,
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
        filtered_cases = _prioritize_cases_with_evidence(reranked_all)
        filtered_neo = _prioritize_cases_with_evidence(reranked_neo)
        filtered_ai = _prioritize_cases_with_evidence(reranked_ai)

        # Fallback comercial: nunca dejar la UI sin fichas; ampliar búsqueda por rubro/área.
        if not filtered_cases:
            fallback_query = (
                f"Iniciativas de alto impacto para {state.get('rubro', 'negocio')} "
                f"en el área {state.get('area', 'operaciones')} con evidencia verificable"
            )
            fallback_payload = _search_with_progressive_thresholds(
                problema=fallback_query,
                switch="both",
                thresholds=(0.40, 0.30, 0.20, 0.0),
                limit=10,
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
            filtered_cases = _prioritize_cases_with_evidence(fallback_cases)
            filtered_neo = _prioritize_cases_with_evidence(fallback_neo)
            filtered_ai = _prioritize_cases_with_evidence(fallback_ai)

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
        if top_match:
            state["top_match_global"] = top_match
            state["top_match_global_reason"] = search_payload.get("top_match_global_reason", "")

        # 2. Buscar perfil del cliente desde SQLite Repository
        profile_row = company_profile_repository.get_profile(
            company_id=state["empresa"],
            area=state["area"],
        )
        if profile_row:
            perfil = profile_row.profile_payload
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
                "notas": "Empresa nueva sin historial previo.",
            }
            state["profile_status"] = "not_found"

        # 3. Contexto sectorial (placeholder estructurado para el layout lateral)
        state["inteligencia_sector"] = _build_sector_intel(
            rubro=state.get("rubro", ""),
            area=state.get("area", ""),
        )

        if not state["casos_encontrados"]:
            state["error"] = (
                "No se encontraron casos para el problema ingresado. "
                "Intenta reformular en términos de industria/área."
            )
            
    except Exception as exc:
        state["error"] = f"Error en retrieve_node: {exc}"

    return state


def update_summary_node(state: ProposalState) -> ProposalState:
    """
    Consolida perfil empresa usando:
    - data web/sectorial ya recuperada en retrieve_node
    - ultimos HumanInsights de ventas (SQLite)
    """
    if state.get("error"):
        return state

    settings = get_settings()
    company_id = str(state.get("empresa") or "").strip()
    area = str(state.get("area") or "General").strip()
    if not company_id:
        return state

    try:
        recent_insights = human_insight_repository.list_recent(
            company_id=company_id,
            limit=max(1, int(settings.intel_summary_insights_limit)),
        )
        state["human_insights"] = [
            {
                "id": insight.id,
                "author": insight.author,
                "department": insight.department,
                "sentiment": insight.sentiment,
                "source": insight.source,
                "created_at": insight.created_at,
                "created_at_label": _format_insight_age_label(insight.created_at),
                "structured_payload": [item.model_dump() for item in insight.structured_payload],
            }
            for insight in recent_insights
        ]

        merged_profile = _merge_profile_with_human_insights(
            company_id=company_id,
            area=area,
            base_profile=state.get("perfil_cliente") or {},
            sector_context=state.get("inteligencia_sector") or {},
            recent_insights=state["human_insights"],
        )
        merged_profile["resumen_departamentos"] = _generate_departmental_time_decay_summary(
            company_id=company_id,
            area=area,
            sector_context=state.get("inteligencia_sector") or {},
            recent_insights=state["human_insights"],
            settings=settings,
        )
        state["perfil_cliente"] = merged_profile
        company_profile_repository.upsert_profile(
            company_id=company_id,
            area=area,
            profile_payload=merged_profile,
        )
    except Exception as exc:
        logger.exception("update_summary_node fallo para empresa=%s: %s", company_id, exc)
        state.setdefault("human_insights", [])

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


def _prioritize_cases_with_evidence(cases: list[dict[str, Any]], limit: int = 10) -> list[dict[str, Any]]:
    """Prioriza casos con URL, pero nunca deja fuera casos útiles sin evidencia."""
    with_url = [c for c in cases if c.get("url_slide")]
    without_url = [c for c in cases if not c.get("url_slide")]
    ordered = with_url + without_url
    return ordered[:limit]


def _search_with_progressive_thresholds(
    problema: str,
    switch: Literal["neo", "ai", "both"],
    thresholds: tuple[float, ...] = (0.40, 0.30, 0.20, 0.0),
    limit: int = 10,
) -> dict[str, Any]:
    """
    Ejecuta búsqueda con umbrales decrecientes hasta obtener resultados.
    Evita estado vacío cuando el problema es demasiado específico.
    """
    last_payload: dict[str, Any] = {"casos": [], "neo_cases": [], "ai_cases": []}
    for threshold in thresholds:
        payload = search_cases_sync(
            problema=problema,
            switch=switch,
            limit=limit,
            score_threshold=threshold,
        )
        last_payload = payload
        if payload.get("casos"):
            return payload
    return last_payload


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


def _merge_profile_with_human_insights(
    *,
    company_id: str,
    area: str,
    base_profile: dict[str, Any],
    sector_context: dict[str, Any],
    recent_insights: list[dict[str, Any]],
) -> dict[str, Any]:
    profile = dict(base_profile or {})
    profile.setdefault("empresa", company_id)
    profile.setdefault("area", area)

    pain_points: list[str] = []
    decision_makers: list[str] = []
    sentiments: list[str] = []
    departments: list[str] = []
    for insight in recent_insights:
        department = str(insight.get("department") or "").strip()
        if department:
            departments.append(department)
        top_sentiment = str(insight.get("sentiment") or "").strip()
        if top_sentiment:
            sentiments.append(top_sentiment)
        structured = insight.get("structured_payload") or []
        for item in structured:
            category = str(item.get("category") or "").strip().lower()
            value = str(item.get("value") or "").strip()
            if not value:
                continue
            if category == "pain_points":
                pain_points.append(value)
            elif category == "decision_makers":
                decision_makers.append(value)
            elif category == "sentiment":
                sentiments.append(value)

    existing_pains = profile.get("pain_points") or []
    if isinstance(existing_pains, str):
        existing_pains = [existing_pains]
    merged_pains = list(dict.fromkeys([*existing_pains, *pain_points]))
    if merged_pains:
        profile["pain_points"] = merged_pains[:10]

    if decision_makers:
        profile["decision_makers"] = list(dict.fromkeys(decision_makers))[:10]
    if sentiments:
        profile["sentimiento_comercial"] = sentiments[0]
    if departments:
        profile["departamentos_activos"] = list(dict.fromkeys(departments))[:10]

    profile["intel_sources"] = {
        "sector_source": sector_context.get("source", "unknown"),
        "human_insights_count": len(recent_insights),
    }
    return profile


def _format_insight_age_label(created_at: str) -> str:
    try:
        ts = datetime.fromisoformat(created_at)
    except Exception:
        return f"Fecha: {created_at}"
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    delta = now - ts.astimezone(timezone.utc)
    days = max(0, delta.days)
    formatted_date = ts.strftime("%d-%b-%Y")
    if days == 0:
        age = "Hoy"
    elif days == 1:
        age = "Hace 1 día"
    elif days < 30:
        age = f"Hace {days} días"
    else:
        months = max(1, days // 30)
        age = f"Hace {months} meses"
    return f"Fecha: {formatted_date} ({age})"


def _format_insights_for_summary_prompt(recent_insights: list[dict[str, Any]]) -> str:
    if not recent_insights:
        return "Sin insights humanos recientes."
    lines: list[str] = []
    for idx, insight in enumerate(recent_insights, start=1):
        items = insight.get("structured_payload") or []
        pain_values = [str(i.get("value") or "").strip() for i in items if str(i.get("category") or "") == "pain_points"]
        decisor_values = [
            str(i.get("value") or "").strip() for i in items if str(i.get("category") or "") == "decision_makers"
        ]
        lines.append(
            (
                f"[Insight {idx}] {insight.get('created_at_label', insight.get('created_at', 'N/A'))}\n"
                f"- Autor: {insight.get('author', 'N/A')}\n"
                f"- Departamento: {insight.get('department', 'General')}\n"
                f"- Sentimiento: {insight.get('sentiment', 'Neutral')}\n"
                f"- Pain points: {pain_values[:3]}\n"
                f"- Decisores: {decisor_values[:3]}"
            )
        )
    return "\n\n".join(lines)


def _generate_departmental_time_decay_summary(
    *,
    company_id: str,
    area: str,
    sector_context: dict[str, Any],
    recent_insights: list[dict[str, Any]],
    settings,
) -> dict[str, Any]:
    if not recent_insights:
        return {
            "departments": [],
            "historical_evolution": "Sin historial suficiente de insights humanos.",
            "source": "no_human_insights",
        }

    insights_block = _format_insights_for_summary_prompt(recent_insights)
    if not settings.gemini_api_key:
        grouped: dict[str, list[str]] = {}
        for insight in recent_insights:
            dept = str(insight.get("department") or "General")
            grouped.setdefault(dept, []).append(str(insight.get("sentiment") or "Neutral"))
        return {
            "departments": [
                {
                    "department": dept,
                    "current_state": f"Señales recientes: {signals[:3]}",
                }
                for dept, signals in grouped.items()
            ],
            "historical_evolution": (
                "Resumen generado en fallback local. "
                "Priorizar insights de últimos 30 días para el estado actual."
            ),
            "source": "fallback_local_time_decay",
        }

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0.2,
        google_api_key=settings.gemini_api_key,
    )
    prompt = (
        "Eres un analista comercial senior. Genera un resumen JSON segmentado por departamentos.\n"
        "Regla estricta de Time-Decay:\n"
        "1) Da PESO ALTISIMO a insights de los últimos 30 días para definir el estado actual.\n"
        "2) Insights antiguos tienen peso menor y sirven solo para evolución histórica.\n"
        "3) No mezcles departamentos; separa TI, Finanzas, Marketing, Operaciones, Comercial o General.\n"
        "4) Responde SOLO JSON con schema:\n"
        "{\"departments\":[{\"department\":\"...\",\"current_state\":\"...\",\"priority_signals_recent\":[\"...\"],\"historical_notes\":\"...\"}],"
        "\"historical_evolution\":\"...\"}\n\n"
        f"EMPRESA: {company_id}\n"
        f"AREA PRINCIPAL: {area}\n"
        f"CONTEXTO SECTORIAL: {sector_context}\n\n"
        f"INSIGHTS HUMANOS (ordenados por recencia):\n{insights_block}\n"
    )
    try:
        response = llm.invoke(prompt)
        text = str(response.content).strip()
        if text.startswith("```"):
            text = text.replace("```json", "").replace("```", "").strip()
        import json

        parsed = json.loads(text)
        if not isinstance(parsed, dict):
            raise ValueError("Formato JSON inválido")
        parsed.setdefault("source", "llm_time_decay_v1")
        return parsed
    except Exception as exc:
        logger.warning("Fallo resumen time-decay LLM para %s: %s", company_id, exc)
        return {
            "departments": [],
            "historical_evolution": "No se pudo generar resumen por LLM; usar señales directas de insights.",
            "source": "llm_error_fallback",
        }

def _format_profile_for_prompt(perfil: dict | None) -> str:
    if not perfil or not perfil.get("empresa"):
        return "No hay información previa del cliente."
    
    return (
        f"Información sobre {perfil.get('empresa')}:\n"
        f"- Objetivos: {perfil.get('objetivos', 'N/A')}\n"
        f"- Pain Points: {perfil.get('pain_points', 'N/A')}\n"
        f"- Decisores: {perfil.get('decision_makers', 'N/A')}\n"
        f"- Sentimiento comercial: {perfil.get('sentimiento_comercial', 'N/A')}\n"
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
        state["warning"] = (
            "Se detectaron casos sin URL de evidencia en la selección: "
            f"{', '.join(missing_url_ids)}. "
            "La propuesta se generará con enfoque inspiracional para esos casos."
        )

    try:
        logger.info("draft_node llamando a Gemini con %s casos", len(filtered_cases))
        settings = get_settings()
        llm = ChatGoogleGenerativeAI(
            model=settings.gemini_chat_model,
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
