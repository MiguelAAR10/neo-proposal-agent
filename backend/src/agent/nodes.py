from datetime import datetime, timezone
import json
import logging
from typing import Any, Literal

from src.agent.state import ProposalState
from src.config import get_settings
from src.services.intel_storage import (
    company_profile_repository,
    human_insight_repository,
    industry_radar_repository,
)
from src.services.llm_pool import get_chat_llm, get_flash_llm
from src.services.prioritized_clients import get_prioritized_client_context, is_prioritized_client
from src.services.proposal_context import (
    filter_selected_cases,
    format_cases_for_prompt,
    validate_selected_cases_have_url,
)
from src.services.search_service import search_cases_sync

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
    prioritized = is_prioritized_client(empresa)

    state["empresa"] = empresa
    state["problema"] = problema
    state["area"] = area
    state["switch"] = switch
    state["cliente_priorizado_contexto"] = get_prioritized_client_context(empresa) if prioritized else {}
    if not prioritized:
        state["warning"] = (
            "Cliente fuera del catalogo priorizado. Se usa busqueda abierta con foco en el problema."
        )
    state["error"] = ""
    return state


def retrieve_node(state: ProposalState) -> ProposalState:
    """Busca casos (con switch) y recupera el perfil del cliente desde repositorio.

    Scoring is fully delegated to search_service._normalize_case (unified scorer).
    No local reranking — cases arrive pre-scored with client-context bonus.
    """
    if state.get("error"):
        return state

    empresa = state.get("empresa", "")
    area = state.get("area", "")
    rubro = state.get("rubro", "")

    try:
        # 1. Search with progressive thresholds — scoring includes client context
        search_payload = _search_with_progressive_thresholds(
            problema=state["problema"],
            switch=state["switch"],
            thresholds=(0.50, 0.40, 0.30, 0.20),
            limit=8,
            client_empresa=empresa,
            client_area=area,
            client_rubro=rubro,
        )
        filtered_cases = _prioritize_cases_with_evidence(search_payload.get("casos", []))
        filtered_neo = _prioritize_cases_with_evidence(search_payload.get("neo_cases", []))
        filtered_ai = _prioritize_cases_with_evidence(search_payload.get("ai_cases", []))

        # Fallback: never leave UI without cards
        if not filtered_cases:
            fallback_query = (
                f"Iniciativas de alto impacto para {rubro or 'negocio'} "
                f"en el área {area or 'operaciones'} con evidencia verificable"
            )
            fallback_payload = _search_with_progressive_thresholds(
                problema=fallback_query,
                switch="both",
                thresholds=(0.40, 0.30, 0.20, 0.0),
                limit=10,
                client_empresa=empresa,
                client_area=area,
                client_rubro=rubro,
            )
            filtered_cases = _prioritize_cases_with_evidence(fallback_payload.get("casos", []))
            filtered_neo = _prioritize_cases_with_evidence(fallback_payload.get("neo_cases", []))
            filtered_ai = _prioritize_cases_with_evidence(fallback_payload.get("ai_cases", []))

            for item in filtered_cases + filtered_neo + filtered_ai:
                item.setdefault("match_type", "inspiracional")
                item.setdefault("match_reason", "Sugerencia por afinidad de industria/área")

        state["casos_encontrados"] = filtered_cases
        state["neo_cases"] = filtered_neo
        state["ai_cases"] = filtered_ai

        top_match = search_payload.get("top_match_global")
        if top_match:
            state["top_match_global"] = top_match
            state["top_match_global_reason"] = search_payload.get("top_match_global_reason", "")

        # 2. Client profile from SQLite
        profile_row = company_profile_repository.get_profile(
            company_id=empresa,
            area=area,
        )
        if profile_row:
            perfil = profile_row.profile_payload
            state["perfil_cliente"] = perfil
            has_objectives = bool(perfil.get("objetivos"))
            has_pains = bool(perfil.get("pain_points"))
            state["profile_status"] = "found" if (has_objectives and has_pains) else "incomplete"
            logger.info("Perfil encontrado para empresa=%s area=%s", empresa, area)
        else:
            state["perfil_cliente"] = {
                "empresa": empresa,
                "area": area,
                "notas": "Empresa nueva sin historial previo.",
            }
            state["profile_status"] = "not_found"

        # 3. Sector intel from real radiography (SQLite), fallback to template
        state["inteligencia_sector"] = _build_sector_intel(rubro=rubro, area=area)

        # 4. Eagerly load human insights so they're available in the initial response
        #    (update_summary_node will re-process them with time-decay after case selection)
        try:
            settings = get_settings()
            recent_insights = human_insight_repository.list_recent(
                company_id=empresa,
                limit=max(1, int(settings.intel_summary_insights_limit)),
            )
            state["human_insights"] = [
                {
                    "id": insight.id,
                    "author": insight.author,
                    "department": insight.department,
                    "sentiment": insight.sentiment,
                    "raw_text": insight.raw_text,
                    "source": insight.source,
                    "created_at": insight.created_at,
                    "created_at_label": _format_insight_age_label(insight.created_at),
                    "structured_payload": [item.model_dump() for item in insight.structured_payload],
                }
                for insight in recent_insights
            ]
        except Exception as exc_insights:
            logger.warning("Failed to load human insights in retrieve_node: %s", exc_insights)
            state.setdefault("human_insights", [])

        if not state["casos_encontrados"]:
            state["error"] = (
                "No se encontraron casos para el problema ingresado. "
                "Intenta reformular en términos de industria/área."
            )

    except Exception as exc:
        state["error"] = f"Error en retrieve_node: {exc}"

    return state


def update_summary_node(state: ProposalState) -> ProposalState:
    """Consolida perfil empresa usando HumanInsights + time-decay."""
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
                "raw_text": insight.raw_text,
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


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _prioritize_cases_with_evidence(cases: list[dict[str, Any]], limit: int = 10) -> list[dict[str, Any]]:
    """Prioritize cases with URL evidence, but never drop useful cases without it."""
    with_url = [c for c in cases if c.get("url_slide")]
    without_url = [c for c in cases if not c.get("url_slide")]
    ordered = with_url + without_url
    return ordered[:limit]


def _search_with_progressive_thresholds(
    problema: str,
    switch: Literal["neo", "ai", "both"],
    thresholds: tuple[float, ...] = (0.40, 0.30, 0.20, 0.0),
    limit: int = 10,
    *,
    client_empresa: str = "",
    client_area: str = "",
    client_rubro: str = "",
) -> dict[str, Any]:
    """Search with decreasing thresholds until results are found."""
    last_payload: dict[str, Any] = {"casos": [], "neo_cases": [], "ai_cases": []}
    for threshold in thresholds:
        payload = search_cases_sync(
            problema=problema,
            switch=switch,
            limit=limit,
            score_threshold=threshold,
            client_empresa=client_empresa,
            client_area=client_area,
            client_rubro=client_rubro,
        )
        last_payload = payload
        if payload.get("casos"):
            return payload
    return last_payload


def _build_sector_intel(rubro: str, area: str) -> dict:
    """Look up real radiography from SQLite; fallback to structured template.

    Handles two possible schemas in profile_payload:
    - Seed schema: industria, executive_summary, tendencias, benchmarks, oportunidades
    - Radar pipeline schema: industry_target, executive_summary, critical_triggers,
      recommendations, sources_checked
    """
    rubro_norm = (rubro or "General").strip()
    area_norm = (area or "General").strip()

    radiography = industry_radar_repository.get_radiography(industry_target=rubro_norm)
    if radiography:
        profile = radiography.profile_payload or {}
        triggers = radiography.triggers_payload or []

        # Handle both seed schema (tendencias) and radar pipeline schema (critical_triggers)
        tendencias = profile.get("tendencias", profile.get("trends", []))
        oportunidades = profile.get("oportunidades", profile.get("opportunities", []))
        benchmarks = profile.get("benchmarks", {})

        # If radar pipeline schema, map recommendations -> oportunidades fallback
        if not tendencias and not oportunidades:
            oportunidades = profile.get("recommendations", [])

        return {
            "industria": rubro_norm,
            "area": area_norm,
            "executive_summary": profile.get("executive_summary", ""),
            "tendencias": tendencias,
            "benchmarks": benchmarks,
            "oportunidades": oportunidades,
            "triggers": triggers,
            "updated_at": radiography.updated_at,
            "source": "industry_radiography_sqlite",
        }

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
        "source": "fallback_template",
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

    llm = get_flash_llm()
    prompt = (
        "Eres un analista comercial senior. Genera un resumen JSON segmentado por departamentos.\n"
        "Regla estricta de Time-Decay:\n"
        "1) Da PESO ALTISIMO a insights de los últimos 30 días para definir el estado actual.\n"
        "2) Insights antiguos tienen peso menor y sirven solo para evolución histórica.\n"
        "3) No mezcles departamentos; separa TI, Finanzas, Marketing, Operaciones, Comercial o General.\n"
        '4) Responde SOLO JSON con schema:\n'
        '{"departments":[{"department":"...","current_state":"...","priority_signals_recent":["..."],"historical_notes":"..."}],'
        '"historical_evolution":"..."}\n\n'
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
        return "ℹ️ No hay información previa del cliente — propuesta se genera con enfoque genérico de industria."

    return (
        f"### 👤 Perfil de {perfil.get('empresa')}\n"
        f"- **Objetivos estratégicos:** {perfil.get('objetivos', 'No disponible')}\n"
        f"- **Pain Points identificados:** {perfil.get('pain_points', 'No disponible')}\n"
        f"- **Decisores clave:** {perfil.get('decision_makers', 'No identificados')}\n"
        f"- **Sentimiento comercial:** {perfil.get('sentimiento_comercial', 'Neutral')}\n"
        f"- **Cultura/Estilo organizacional:** {perfil.get('notas', 'No disponible')}"
    )


def _format_sector_for_prompt(sector: dict | None) -> str:
    if not sector:
        return "ℹ️ No hay inteligencia sectorial disponible — se usarán tendencias generales del mercado."
    triggers = sector.get("triggers", [])
    triggers_txt = ""
    if triggers:
        trigger_lines = []
        for t in triggers[:5]:
            if isinstance(t, dict):
                trigger_lines.append(
                    f"  - **{t.get('trigger_type', 'signal')}:** {t.get('title', 'N/A')} "
                    f"(Severidad: {t.get('severity', 'N/A')})"
                )
        if trigger_lines:
            triggers_txt = "\n- **🚨 Triggers activos:**\n" + "\n".join(trigger_lines)
    return (
        f"**Sector:** {sector.get('industria', 'N/A')} / **Área:** {sector.get('area', 'N/A')}\n"
        f"- **📈 Tendencias clave:** {sector.get('tendencias', [])}\n"
        f"- **📊 Benchmarks:** {sector.get('benchmarks', {})}\n"
        f"- **🎯 Oportunidades:** {sector.get('oportunidades', [])}"
        f"{triggers_txt}"
    )


def _format_prioritized_client_context(context: dict | None) -> str:
    if not context:
        return "ℹ️ Cliente no priorizado — se genera propuesta con enfoque abierto basado en el problema."

    return (
        f"**Vertical:** {context.get('vertical', 'N/A')}\n"
        f"- **🎯 Prioridades estratégicas:** {context.get('priorities', [])}\n"
        f"- **⚠️ Restricciones conocidas:** {context.get('constraints', [])}\n"
        f"- **📋 Fuente de contexto:** {context.get('source', 'N/A')}"
    )


def _format_chat_context_for_prompt(chat_messages: list[str] | None) -> str:
    """Formatea los mensajes del chat seleccionados como contexto para la propuesta."""
    if not chat_messages:
        return ""

    formatted_messages = "\n".join([f"- {msg[:500]}..." if len(msg) > 500 else f"- {msg}" for msg in chat_messages])
    return (
        "## 💬 ACUERDOS PREVIOS EN EL CHAT\n"
        "El consultor seleccionó los siguientes mensajes como contexto relevante para esta propuesta:\n\n"
        f"{formatted_messages}\n\n"
        "**INSTRUCCIÓN:** La propuesta DEBE reflejar y alinearse con estos acuerdos/discusiones previas.\n\n"
    )


def _filter_and_format_selected_insights(
    all_insights: list[dict], selected_ids: list[str] | None
) -> str:
    """Filtra insights por IDs seleccionados y los formatea para el prompt."""
    if not selected_ids or not all_insights:
        return ""

    selected_ids_set = set(selected_ids)
    filtered = [ins for ins in all_insights if ins.get("id") in selected_ids_set]

    if not filtered:
        return ""

    formatted_insights = []
    for ins in filtered:
        dept = ins.get("department", "General")
        sentiment = ins.get("sentiment", "Neutral")
        raw_text = ins.get("raw_text", "")[:400]
        age_label = ins.get("created_at_label", "")
        structured = ins.get("structured_payload", [])

        # Extract key points from structured payload
        key_points = []
        for item in structured[:5]:  # Limit to 5 items
            if isinstance(item, dict):
                key_points.append(f"  - {item.get('label', 'Info')}: {item.get('value', 'N/A')}")

        formatted_insights.append(
            f"**📌 Insight ({dept} | {sentiment})**\n"
            f"{raw_text}\n"
            f"{''.join(key_points)}\n"
            f"_{age_label}_"
        )

    return (
        "## 🎯 REQUERIMIENTOS EXPLÍCITOS DEL CLIENTE (PRIORIDAD MÁXIMA)\n"
        "El consultor priorizó los siguientes insights del cliente para esta propuesta:\n\n"
        f"{chr(10).join(formatted_insights)}\n\n"
        "**INSTRUCCIÓN OBLIGATORIA:** La propuesta DEBE abordar directamente cada uno de estos puntos. "
        "Son requisitos explícitos del equipo comercial.\n\n"
    )


def _format_optional_cases_section(filtered_cases: list[dict]) -> str:
    """Formatea la sección de casos de éxito (opcional). Si no hay casos, indica que es propuesta original."""
    if not filtered_cases:
        return (
            "## 📌 EVIDENCIA DE CASOS\n"
            "No se seleccionaron casos de referencia. Esta propuesta se genera como **solución original** "
            "basada en las capacidades de NEO y el contexto del cliente.\n\n"
            "**INSTRUCCIÓN:** Genera una propuesta innovadora sin depender de casos previos. "
            "Enfócate en las capacidades de NEO para resolver el problema específico del cliente.\n\n"
        )

    return (
        "## 📌 CASOS DE ÉXITO (EVIDENCIA DE APOYO OPCIONAL)\n"
        "El consultor seleccionó los siguientes casos como referencia de experiencia previa:\n\n"
        f"{format_cases_for_prompt(filtered_cases)}\n\n"
        "**INSTRUCCIÓN:** Usa estos casos como evidencia de que NEO ya resolvió problemas similares. "
        "Son apoyo, no el foco principal de la propuesta.\n\n"
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

    # Los casos son opcionales - sirven como evidencia de apoyo, no como requisito
    has_cases = bool(filtered_cases)
    if has_cases:
        has_url, missing_url_ids = validate_selected_cases_have_url(filtered_cases)
        if not has_url:
            state["warning"] = (
                "Se detectaron casos sin URL de evidencia en la selección: "
                f"{', '.join(missing_url_ids)}. "
                "La propuesta se generará con enfoque inspiracional para esos casos."
            )

    try:
        logger.info("draft_node llamando a Gemini con %s casos", len(filtered_cases))
        llm = get_chat_llm()

        prompt = (
            "# 🧠 NEO Strategy Co-Pilot — Generación de Propuesta de Valor\n\n"

            "Eres un **consultor estratégico senior** de una firma de consultoría global "
            "(nivel McKinsey, BCG, Accenture Strategy). Tu misión es generar una **propuesta de valor "
            "de clase mundial** que combine evidencia de casos reales con visión estratégica innovadora.\n\n"

            "---\n\n"

            "## 📋 CONTEXTO DEL CLIENTE\n"
            f"**🏢 Empresa:** {state['empresa']}\n"
            f"**🎯 Área:** {state['area']}\n"
            f"**⚠️ Problema/Necesidad:** {state['problema']}\n"
            f"{_format_profile_for_prompt(state.get('perfil_cliente'))}\n\n"

            "## 🏆 CONTEXTO CLIENTE PRIORIZADO\n"
            f"{_format_prioritized_client_context(state.get('cliente_priorizado_contexto'))}\n\n"

            "## 🌐 INTELIGENCIA DE MERCADO / SECTOR\n"
            f"{_format_sector_for_prompt(state.get('inteligencia_sector'))}\n\n"

            # Casos de éxito (opcionales - como evidencia de apoyo)
            f"{_format_optional_cases_section(filtered_cases)}"

            # Contexto adicional seleccionado por el usuario (si existe)
            f"{_format_chat_context_for_prompt(state.get('chat_context_messages'))}"
            f"{_filter_and_format_selected_insights(state.get('human_insights', []), state.get('selected_insight_ids'))}"

            "---\n\n"

            "## ✍️ INSTRUCCIONES DE GENERACIÓN DE PROPUESTA\n\n"

            "Genera la propuesta con **EXACTAMENTE** estas 6 secciones en **Markdown rico**.\n"
            "**IMPORTANTE:** Cada sección DEBE iniciar con su header exacto (incluyendo emoji).\n\n"

            "### 🔍 DIAGNÓSTICO\n"
            "- Reformula el problema en lenguaje ejecutivo (máx 3 bullets concisos)\n"
            "- Identifica impacto cuantificable: costos, eficiencia, riesgo competitivo\n"
            "- Conecta con urgencia de mercado\n\n"

            "### 💡 SOLUCIÓN PROPUESTA\n"
            "- Describe la solución en términos de valor de negocio (no solo tecnología)\n"
            "- Máximo 4 bullets con beneficios claros\n"
            "- Si hay opciones, presenta trade-offs en lista\n\n"

            "### 🏗️ ARQUITECTURA Y STACK\n"
            "- Lista componentes clave en bullets\n"
            "- Stack tecnológico como tags: `[Python]` `[LangChain]` `[PostgreSQL]`\n"
            "- Fases: Quick Win → Escala → Optimización\n\n"

            "### 📊 IMPACTO Y KPIs\n"
            "- KPIs cuantificables en formato: **Métrica:** Valor esperado\n"
            "- Máximo 4-5 KPIs relevantes\n"
            "- Usa benchmarks de casos si aplica\n\n"

            "### 🗓️ ROADMAP\n"
            "- **Fase 1 (Quick Win):** Entregable en X semanas\n"
            "- **Fase 2 (Consolidación):** Siguiente milestone\n"
            "- **Fase 3 (Optimización):** Visión a largo plazo\n\n"

            "### 🎯 SIGUIENTE PASO\n"
            "- Una acción concreta e inmediata\n"
            "- Qué necesitas del cliente para avanzar\n\n"

            "---\n\n"
            "## ⚡ REGLAS DE CALIDAD\n"
            "1. **Formato ejecutivo** — Bullets concisos, no párrafos largos\n"
            "2. **Tags tecnológicos** — Siempre usar formato `[Tecnología]` en sección de stack\n"
            "3. **Tono C-Suite** — Habla como Partner de consultoría estratégica\n"
            "4. **300-500 palabras total** — Profundo pero conciso, tipo PPT ejecutivo\n"
            "5. Si hay casos, cítalos como evidencia: `📌 [ID]`\n"
            "6. NUNCA omitas ninguna de las 6 secciones"
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
