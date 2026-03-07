from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from src.api.deps import (
    chat_audit_store,
    enforce_rate_limit,
    evaluate_chat_message,
    filter_selected_cases,
    format_cases_for_prompt,
    get_prioritized_client_context,
    get_prioritized_clients,
    get_prioritized_clients_catalog,
    graph,
    invoke_llm_async,
    is_prioritized_client,
    map_state_response,
    normalize_company_name,
    raise_domain_http,
    raise_internal_server_error,
    search_cases_with_sla,
    search_metrics,
    session_funnel_store,
    settings,
    validate_selected_cases_have_url,
)
from src.api.schemas import (
    AgentStateResponse,
    AssignRequest,
    ChatRequest,
    ChatResponse,
    RefineRequest,
    SearchRequest,
    SelectRequest,
    StartRequest,
    TeamResponse,
)
from src.services.errors import BackendDomainError, BusinessRuleError, SessionNotFoundError

router = APIRouter(tags=["agent"])


@router.get("/api/prioritized-clients")
async def prioritized_clients():
    """Lista oficial de clientes priorizados para fase actual."""
    catalog = get_prioritized_clients_catalog()
    return {
        "status": "success",
        "total": len(catalog),
        "clients": get_prioritized_clients(),
        "catalog": catalog,
    }


@router.post("/api/search")
async def api_search(data: SearchRequest):
    """Primitiva de búsqueda semántica stateless."""
    try:
        payload = await search_cases_with_sla(
            problema=data.problema.strip(),
            switch=data.switch,
            limit=6,
            score_threshold=0.50,
        )
        search_metrics.record_success(
            total_ms=payload.get("latencia_ms", 0),
            embedding_ms=payload.get("embedding_ms"),
            qdrant_ms=payload.get("qdrant_ms"),
            cache_hit=payload.get("cache_hit"),
        )
        return payload
    except BackendDomainError as exc:
        search_metrics.record_error(exc.code)
        raise_domain_http(exc)
    except Exception:
        search_metrics.record_error("UNHANDLED_ERROR")
        raise_internal_server_error("Error in /api/search")


@router.post("/agent/start", response_model=AgentStateResponse)
async def start_agent(data: StartRequest):
    """Inicia una nueva sesión de generación de propuesta."""
    enforce_rate_limit(
        "start",
        key=normalize_company_name(data.empresa),
        limit=settings.rate_limit_start_per_window,
    )
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    empresa_normalized = normalize_company_name(data.empresa)
    prioritized = is_prioritized_client(data.empresa)

    inputs = {
        "empresa": empresa_normalized,
        "rubro": data.rubro,
        "area": data.area,
        "problema": data.problema,
        "switch": data.switch,
        "cliente_priorizado_contexto": (
            get_prioritized_client_context(data.empresa) if prioritized else {}
        ),
        "casos_seleccionados_ids": [],
        "propuesta_versiones": [],
        "warning": None
        if prioritized
        else "Cliente fuera del catalogo priorizado. Se ejecuta busqueda abierta centrada en problema.",
    }

    try:
        final_state = await graph.ainvoke(inputs, config=config)
        session_funnel_store.record_start(
            thread_id=thread_id,
            empresa=empresa_normalized,
            area=data.area,
            total_cases=len(final_state.get("casos_encontrados", [])),
        )
        return map_state_response(thread_id, final_state, status="awaiting_selection")
    except BackendDomainError as exc:
        raise_domain_http(exc)
    except Exception:
        raise_internal_server_error("Error starting agent")


@router.post("/agent/{thread_id}/select", response_model=AgentStateResponse)
async def select_cases(thread_id: str, data: SelectRequest):
    """Recibe la selección de casos del usuario y genera la propuesta final."""
    enforce_rate_limit("select", key=thread_id, limit=settings.rate_limit_select_per_window)
    config = {"configurable": {"thread_id": thread_id}}

    current_state = await graph.aget_state(config)
    if not current_state.values:
        raise_domain_http(SessionNotFoundError("Sesión no encontrada."))

    try:
        current_values = current_state.values or {}
        all_cases = current_values.get("casos_encontrados", [])
        available_ids = {str(case.get("id")) for case in all_cases}
        invalid_ids = [cid for cid in data.case_ids if cid not in available_ids]
        if invalid_ids:
            raise_domain_http(
                BusinessRuleError(
                    f"Hay case_ids que no pertenecen a la busqueda actual: {', '.join(invalid_ids)}"
                )
            )

        selected_cases = filter_selected_cases(all_cases, data.case_ids)
        has_url, missing_url_ids = validate_selected_cases_have_url(selected_cases)
        warning_message = ""
        if not has_url:
            warning_message = (
                "Se seleccionaron casos sin URL de evidencia: "
                f"{', '.join(missing_url_ids)}. "
                "Se usarán como inspiración y se recomienda validación adicional."
            )

        await graph.aupdate_state(
            config,
            {"casos_seleccionados_ids": data.case_ids, "warning": warning_message},
        )

        final_state = await graph.ainvoke(None, config=config)
        session_funnel_store.record_select(
            thread_id=thread_id,
            selected_count=len(data.case_ids),
            completed=bool(final_state.get("propuesta_final")),
        )
        return map_state_response(thread_id, final_state, status="completed")
    except BackendDomainError as exc:
        raise_domain_http(exc)
    except HTTPException:
        raise
    except Exception:
        raise_internal_server_error("Error in select_cases")


@router.post("/agent/{thread_id}/refine", response_model=AgentStateResponse)
async def refine_proposal(thread_id: str, data: RefineRequest):
    """Refina la propuesta existente manteniendo contexto de sesión."""
    enforce_rate_limit("refine", key=thread_id, limit=settings.rate_limit_refine_per_window)
    config = {"configurable": {"thread_id": thread_id}}
    state = await graph.aget_state(config)
    if not state.values:
        raise_domain_http(SessionNotFoundError("Sesión no encontrada."))

    v = state.values
    if not v.get("propuesta_final"):
        raise_domain_http(BusinessRuleError("No hay propuesta previa para refinar."))

    try:
        selected_cases = filter_selected_cases(
            list(v.get("casos_encontrados", [])),
            list(v.get("casos_seleccionados_ids", [])),
        )
        profile_context = v.get("perfil_cliente") or {}
        client_context = v.get("cliente_priorizado_contexto") or {}
        sector_context = v.get("inteligencia_sector") or {}

        prompt = (
            "# ✏️ NEO Strategy Co-Pilot — Refinamiento de Propuesta\n\n"

            "Eres un **co-consultor senior de estrategia** que refina propuestas comerciales "
            "con la calidad y profundidad de una **Big Four / McKinsey**.\n\n"

            "## 🎯 Instrucciones de Refinamiento\n"
            "- Aplica **estrictamente** la instrucción del usuario manteniendo la estructura profesional\n"
            "- Mejora claridad, impacto y persuasión sin perder precisión técnica\n"
            "- Mantén formato **Markdown rico** con emojis en encabezados\n"
            "- Asegura que cada sección tenga valor ejecutivo medible\n"
            "- Si la instrucción pide expandir, agrega **análisis estratégico y opciones adicionales**\n"
            "- Si pide simplificar, mantén los KPIs y el impacto cuantificable\n\n"

            "## 📋 Contexto del Cliente\n"
            f"**Empresa:** {v.get('empresa', 'N/A')}\n"
            f"**Vertical:** {client_context.get('vertical', 'N/A')}\n"
            f"**Prioridades:** {client_context.get('priorities', [])}\n"
            f"**Restricciones:** {client_context.get('constraints', [])}\n\n"

            "## 👤 Perfil del Cliente\n"
            f"**Objetivos:** {profile_context.get('objetivos', [])}\n"
            f"**Pain points:** {profile_context.get('pain_points', [])}\n"
            f"**Notas:** {profile_context.get('notas', 'N/A')}\n\n"

            "## 🌐 Contexto Sectorial\n"
            f"**Industria:** {sector_context.get('industria', 'N/A')} / **Área:** {sector_context.get('area', 'N/A')}\n"
            f"**Tendencias:** {sector_context.get('tendencias', [])}\n\n"

            "## 📌 Casos Seleccionados como Evidencia\n"
            f"{format_cases_for_prompt(selected_cases)}\n\n"

            "---\n\n"
            f"## ⚡ INSTRUCCIÓN DEL CONSULTOR\n**{data.instruction}**\n\n"

            "## 📄 PROPUESTA ACTUAL A REFINAR\n"
            f"{v['propuesta_final']}\n\n"

            "---\n"
            "**REGLAS:** Mantén formato Markdown con emojis en encabezados. "
            "La propuesta refinada debe conservar las secciones: "
            "🔍 Problema, 💡 Solución, 🏗️ Arquitectura/Proceso, 📊 Impacto Estimado, 🎯 Siguiente Paso. "
            "Si alguna sección falta, créala."
        )
        refined = await invoke_llm_async(prompt)

        versions = list(v.get("propuesta_versiones") or [])
        versions.append(refined)
        await graph.aupdate_state(
            config,
            {"propuesta_final": refined, "propuesta_versiones": versions, "error": ""},
        )

        new_state = await graph.aget_state(config)
        session_funnel_store.record_refine(thread_id)
        return map_state_response(thread_id, new_state.values, status="completed")
    except BackendDomainError as exc:
        raise_domain_http(exc)
    except Exception:
        raise_internal_server_error("Error refining proposal")


@router.post("/agent/{thread_id}/chat", response_model=ChatResponse)
async def contextual_chat(thread_id: str, data: ChatRequest):
    """Chat contextual dedicado por thread."""
    enforce_rate_limit("chat", key=thread_id, limit=settings.rate_limit_chat_per_window)
    config = {"configurable": {"thread_id": thread_id}}
    state = await graph.aget_state(config)
    if not state.values:
        raise_domain_http(SessionNotFoundError("Sesión no encontrada."))

    v = state.values
    all_cases = list(v.get("casos_encontrados", []))
    selected_ids = list(v.get("casos_seleccionados_ids", []))
    selected_cases = filter_selected_cases(all_cases, selected_ids)
    cases_for_chat = selected_cases if selected_cases else all_cases[:3]
    used_case_ids = [str(c.get("id")) for c in cases_for_chat if c.get("id")]

    profile_context = v.get("perfil_cliente") or {}
    client_context = v.get("cliente_priorizado_contexto") or {}
    sector_context = v.get("inteligencia_sector") or {}
    chat_history = list(v.get("chat_messages") or [])
    history_tail = chat_history[-8:]
    history_block = "\n".join(
        f"{item.get('role', 'user').upper()}: {item.get('content', '')}" for item in history_tail
    )
    audit_ts = datetime.now(timezone.utc).isoformat()
    guardrail = evaluate_chat_message(data.message)

    if not guardrail.allowed:
        blocked_answer = (
            "No puedo procesar ese mensaje en el chat contextual por una regla de seguridad. "
            "Reformula tu consulta enfocandola en estrategia, evidencia de casos o propuesta de valor."
        )
        new_history = history_tail + [
            {"role": "user", "content": guardrail.sanitized_message},
            {"role": "assistant", "content": blocked_answer},
        ]
        await graph.aupdate_state(config, {"chat_messages": new_history})
        chat_audit_store.record_event(
            thread_id=thread_id,
            empresa=v.get("empresa"),
            status="guardrail_blocked",
            guardrail_code=guardrail.code,
            used_case_ids=[],
            message=guardrail.sanitized_message,
        )
        session_funnel_store.record_chat(thread_id=thread_id, status="guardrail_blocked")
        return ChatResponse(
            thread_id=thread_id,
            answer=blocked_answer,
            used_case_ids=[],
            used_case_count=0,
            status="guardrail_blocked",
            guardrail_code=guardrail.code,
            audit_ts_utc=audit_ts,
        )

    try:
        prompt = (
            "# 🧠 NEO Strategy Co-Pilot — Chat Contextual de Propuesta\n\n"

            "Eres un **co-consultor senior de estrategia digital** al nivel de McKinsey Digital / BCG Platinion.\n"
            "Tu misión es ayudar al vendedor-consultor a construir la MEJOR propuesta posible para su cliente.\n\n"

            "## 🎯 Cómo Debes Responder\n"
            "- **Piensa como un Partner de consultoría** que asesora al equipo comercial\n"
            "- NO te limites a los casos — **analiza, combina, sugiere nuevas líneas de servicio**\n"
            "- Usa **Markdown rico**: encabezados con emojis, negritas, bullet points, tablas si aplica\n"
            "- Si recomiendas algo, explica el **por qué estratégico** y el **impacto esperado**\n"
            "- Cita casos con formato: `📌 Caso [ID]: [Título]` cuando los referencie\n"
            "- Sé **proactivo**: sugiere ángulos que el consultor no ha considerado\n"
            "- No inventes evidencias — pero SÍ genera hipótesis fundamentadas en tendencias del sector\n\n"

            "## 📊 Estructura de Respuesta\n"
            "Para preguntas sustantivas, organiza tu respuesta en:\n"
            "1. **🔍 Diagnóstico/Contexto** — Qué entiendes del problema o pregunta\n"
            "2. **💡 Análisis y Recomendación** — Tu perspectiva estratégica con evidencia\n"
            "3. **🚀 Opciones o Líneas de Acción** — Propuestas concretas (no solo una)\n"
            "4. **🎯 Siguiente Paso** — Qué debería hacer el consultor ahora\n\n"

            "---\n\n"

            "## 📋 Contexto del Cliente\n"
            f"**Empresa:** {v.get('empresa', 'N/A')}\n"
            f"**Vertical:** {client_context.get('vertical', 'N/A')}\n"
            f"**Prioridades estratégicas:** {client_context.get('priorities', [])}\n"
            f"**Restricciones:** {client_context.get('constraints', [])}\n\n"

            "## 👤 Perfil del Cliente\n"
            f"**Objetivos:** {profile_context.get('objetivos', [])}\n"
            f"**Pain points:** {profile_context.get('pain_points', [])}\n"
            f"**Notas internas:** {profile_context.get('notas', 'N/A')}\n\n"

            "## 🌐 Inteligencia Sectorial\n"
            f"**Industria:** {sector_context.get('industria', 'N/A')} / **Área:** {sector_context.get('area', 'N/A')}\n"
            f"**Tendencias clave:** {sector_context.get('tendencias', [])}\n\n"

            "## 📌 Casos Disponibles como Base\n"
            f"{format_cases_for_prompt(cases_for_chat)}\n\n"

            "## 💬 Historial de Conversación\n"
            f"{history_block or 'Sin historial previo.'}\n\n"

            "---\n\n"
            "## ❓ Mensaje del Consultor\n"
            f"**{guardrail.sanitized_message}**\n\n"

            "---\n"
            "**INSTRUCCIONES FINALES:** Responde en **mínimo 300 palabras** para preguntas sustantivas. "
            "Usa Markdown rico con emojis en encabezados. "
            "Sé creativo, estratégico y de alto valor. "
            "Cierra SIEMPRE con **🎯 Siguiente paso recomendado**. "
            "Cita `📌 Caso [ID]` cuando corresponda."
        )
        answer = await invoke_llm_async(prompt)

        new_history = history_tail + [
            {"role": "user", "content": guardrail.sanitized_message},
            {"role": "assistant", "content": answer},
        ]
        await graph.aupdate_state(config, {"chat_messages": new_history})
        chat_audit_store.record_event(
            thread_id=thread_id,
            empresa=v.get("empresa"),
            status="ok",
            guardrail_code=guardrail.code,
            used_case_ids=used_case_ids,
            message=guardrail.sanitized_message,
        )
        session_funnel_store.record_chat(thread_id=thread_id, status="ok")

        return ChatResponse(
            thread_id=thread_id,
            answer=answer,
            used_case_ids=used_case_ids,
            used_case_count=len(used_case_ids),
            status="ok",
            guardrail_code=guardrail.code,
            audit_ts_utc=audit_ts,
        )
    except BackendDomainError as exc:
        raise_domain_http(exc)
    except Exception:
        raise_internal_server_error("Error in contextual chat")


@router.get("/agent/{thread_id}/state", response_model=AgentStateResponse)
async def get_agent_state(thread_id: str):
    """Recupera el estado actual de una sesión."""
    config = {"configurable": {"thread_id": thread_id}}
    state = await graph.aget_state(config)
    if not state.values:
        raise_domain_http(SessionNotFoundError("Sesión no encontrada."))
    return map_state_response(thread_id, state.values)


# ---------------------------------------------------------------------------
# Teams (static catalog for MVP)
# ---------------------------------------------------------------------------

_TEAMS = [
    TeamResponse(
        id="analytics-ml",
        name="Analytics & ML",
        description="Equipo especializado en modelos predictivos, scoring, forecast de demanda y analítica avanzada. Experiencia en TensorFlow, scikit-learn, y plataformas de MLOps.",
        capabilities=["Machine Learning", "Predictive Analytics", "MLOps", "Data Engineering", "Statistical Modeling"],
        icon="brain",
        is_best_match=False,
    ),
    TeamResponse(
        id="ai-lab",
        name="AI Lab",
        description="Laboratorio de inteligencia artificial enfocado en NLP, computer vision, IA generativa y agentes autónomos. Especialistas en LLMs, RAG y soluciones de IA conversacional.",
        capabilities=["NLP", "Computer Vision", "Generative AI", "LLM/RAG", "AI Agents"],
        icon="sparkles",
        is_best_match=False,
    ),
    TeamResponse(
        id="growth-crm",
        name="Growth & CRM",
        description="Equipo de growth marketing, personalización, CRM analytics y optimización de customer journey. Experiencia en Salesforce, HubSpot, y plataformas de CDP.",
        capabilities=["CRM Analytics", "Customer Journey", "Personalization", "Marketing Automation", "CDP"],
        icon="target",
        is_best_match=False,
    ),
    TeamResponse(
        id="operaciones",
        name="Operaciones & RPA",
        description="Equipo de automatización robótica de procesos, BPM, workflow optimization e integración de sistemas. Experiencia en UiPath, Power Automate y procesos bancarios.",
        capabilities=["RPA", "Process Mining", "BPM", "System Integration", "Workflow Automation"],
        icon="cog",
        is_best_match=False,
    ),
]

_BEST_MATCH_RULES: dict[str, str] = {
    "rpa": "operaciones",
    "automatizacion": "operaciones",
    "proceso": "operaciones",
    "conciliacion": "operaciones",
    "backoffice": "operaciones",
    "scoring": "analytics-ml",
    "forecast": "analytics-ml",
    "prediccion": "analytics-ml",
    "predictivo": "analytics-ml",
    "ml": "analytics-ml",
    "demanda": "analytics-ml",
    "nlp": "ai-lab",
    "chatbot": "ai-lab",
    "generativa": "ai-lab",
    "vision": "ai-lab",
    "fraude": "analytics-ml",
    "marketing": "growth-crm",
    "crm": "growth-crm",
    "personalizacion": "growth-crm",
    "pricing": "analytics-ml",
    "siniestro": "operaciones",
}


def _suggest_best_match(state_values: dict) -> str:
    """Simple keyword-based best match suggestion."""
    text_pool = " ".join([
        str(state_values.get("problema", "")),
        str(state_values.get("area", "")),
        str(state_values.get("propuesta_final", "")),
    ]).lower()
    scores: dict[str, int] = {}
    for keyword, team_id in _BEST_MATCH_RULES.items():
        if keyword in text_pool:
            scores[team_id] = scores.get(team_id, 0) + 1
    if scores:
        return max(scores, key=scores.get)  # type: ignore[arg-type]
    return "analytics-ml"


@router.get("/teams", response_model=list[TeamResponse])
async def list_teams(thread_id: str | None = None):
    """Lista de equipos disponibles con sugerencia de best match."""
    best_match_id = "analytics-ml"
    if thread_id:
        config = {"configurable": {"thread_id": thread_id}}
        try:
            state = await graph.aget_state(config)
            if state.values:
                best_match_id = _suggest_best_match(state.values)
        except Exception:
            pass

    teams = []
    for t in _TEAMS:
        copy = t.model_copy()
        copy.is_best_match = (copy.id == best_match_id)
        teams.append(copy)
    return teams


@router.post("/agent/{thread_id}/assign")
async def assign_team(thread_id: str, data: AssignRequest):
    """Asigna un equipo a la propuesta (MVP: registro en estado)."""
    config = {"configurable": {"thread_id": thread_id}}
    state = await graph.aget_state(config)
    if not state.values:
        raise_domain_http(SessionNotFoundError("Sesión no encontrada."))

    team = next((t for t in _TEAMS if t.id == data.team_id), None)
    if not team:
        raise HTTPException(status_code=400, detail={"code": "INVALID_TEAM", "message": f"Team '{data.team_id}' no existe."})

    return {
        "status": "assigned",
        "thread_id": thread_id,
        "team_id": data.team_id,
        "team_name": team.name,
        "notes": data.notes,
        "proposal_id": f"prop-{thread_id[:8]}",
    }
