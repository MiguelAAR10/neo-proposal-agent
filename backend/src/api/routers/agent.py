from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from src.api.schemas import (
    AgentStateResponse,
    ChatRequest,
    ChatResponse,
    RefineRequest,
    SearchRequest,
    SelectRequest,
    StartRequest,
)
from src.services.errors import BackendDomainError, ExternalDependencyTimeout, SessionNotFoundError, BusinessRuleError

router = APIRouter(tags=["agent"])


def _main():
    from src.api import main as main_module

    return main_module


@router.get("/api/prioritized-clients")
async def prioritized_clients():
    """Lista oficial de clientes priorizados para fase actual."""
    main_module = _main()
    catalog = main_module.get_prioritized_clients_catalog()
    return {
        "status": "success",
        "total": len(catalog),
        "clients": main_module.get_prioritized_clients(),
        "catalog": catalog,
    }


@router.post("/api/search")
async def api_search(data: SearchRequest):
    """
    Primitiva de búsqueda semántica.
    Stateless y reutilizable por orquestadores (/agent/*).
    """
    main_module = _main()
    try:
        payload = await main_module.search_cases_with_sla(
            problema=data.problema.strip(),
            switch=data.switch,
            limit=6,
            score_threshold=0.50,
        )
        main_module.search_metrics.record_success(
            total_ms=payload.get("latencia_ms", 0),
            embedding_ms=payload.get("embedding_ms"),
            qdrant_ms=payload.get("qdrant_ms"),
            cache_hit=payload.get("cache_hit"),
        )
        return payload
    except ExternalDependencyTimeout as exc:
        main_module.search_metrics.record_error(exc.code)
        main_module._raise_domain_http(exc)
    except BackendDomainError as exc:
        main_module.search_metrics.record_error(exc.code)
        main_module._raise_domain_http(exc)
    except Exception:
        main_module.search_metrics.record_error("UNHANDLED_ERROR")
        main_module._raise_internal_server_error("Error in /api/search")


@router.post("/agent/start", response_model=AgentStateResponse)
async def start_agent(data: StartRequest):
    """
    Inicia una nueva sesión de generación de propuesta.
    Ejecuta el grafo hasta el nodo de selección (HITL).
    """
    main_module = _main()
    main_module._enforce_rate_limit(
        "start",
        key=main_module.normalize_company_name(data.empresa),
        limit=main_module.settings.rate_limit_start_per_window,
    )
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    empresa_normalized = main_module.normalize_company_name(data.empresa)
    prioritized = main_module.is_prioritized_client(data.empresa)

    inputs = {
        "empresa": empresa_normalized,
        "rubro": data.rubro,
        "area": data.area,
        "problema": data.problema,
        "switch": data.switch,
        "cliente_priorizado_contexto": (
            main_module.get_prioritized_client_context(data.empresa) if prioritized else {}
        ),
        "casos_seleccionados_ids": [],
        "propuesta_versiones": [],
        "warning": None
        if prioritized
        else ("Cliente fuera del catalogo priorizado. Se ejecuta busqueda abierta centrada en problema."),
    }

    try:
        final_state = await main_module.graph.ainvoke(inputs, config=config)
        main_module.session_funnel_store.record_start(
            thread_id=thread_id,
            empresa=empresa_normalized,
            area=data.area,
            total_cases=len(final_state.get("casos_encontrados", [])),
        )
        return main_module._map_state_response(thread_id, final_state, status="awaiting_selection")
    except BackendDomainError as exc:
        main_module._raise_domain_http(exc)
    except Exception:
        main_module._raise_internal_server_error("Error starting agent")


@router.post("/agent/{thread_id}/select", response_model=AgentStateResponse)
async def select_cases(thread_id: str, data: SelectRequest):
    """
    Recibe la selección de casos del usuario y genera la propuesta final.
    """
    main_module = _main()
    main_module._enforce_rate_limit(
        "select",
        key=thread_id,
        limit=main_module.settings.rate_limit_select_per_window,
    )
    config = {"configurable": {"thread_id": thread_id}}

    current_state = await main_module.graph.aget_state(config)
    if not current_state.values:
        main_module._raise_domain_http(SessionNotFoundError("Sesión no encontrada."))

    try:
        current_values = current_state.values or {}
        all_cases = current_values.get("casos_encontrados", [])
        available_ids = {str(case.get("id")) for case in all_cases}
        invalid_ids = [case_id for case_id in data.case_ids if case_id not in available_ids]
        if invalid_ids:
            main_module._raise_domain_http(
                BusinessRuleError(
                    f"Hay case_ids que no pertenecen a la busqueda actual: {', '.join(invalid_ids)}"
                )
            )

        selected_cases = main_module.filter_selected_cases(all_cases, data.case_ids)
        has_url, missing_url_ids = main_module.validate_selected_cases_have_url(selected_cases)
        warning_message = ""
        if not has_url:
            warning_message = (
                "Se seleccionaron casos sin URL de evidencia: "
                f"{', '.join(missing_url_ids)}. "
                "Se usarán como inspiración y se recomienda validación adicional."
            )

        await main_module.graph.aupdate_state(
            config,
            {
                "casos_seleccionados_ids": data.case_ids,
                "warning": warning_message,
            },
        )

        final_state = await main_module.graph.ainvoke(None, config=config)
        main_module.session_funnel_store.record_select(
            thread_id=thread_id,
            selected_count=len(data.case_ids),
            completed=bool(final_state.get("propuesta_final")),
        )
        return main_module._map_state_response(thread_id, final_state, status="completed")
    except BackendDomainError as exc:
        main_module._raise_domain_http(exc)
    except HTTPException:
        raise
    except Exception:
        main_module._raise_internal_server_error("Error in select_cases")


@router.post("/agent/{thread_id}/refine", response_model=AgentStateResponse)
async def refine_proposal(thread_id: str, data: RefineRequest):
    """
    Refina la propuesta existente manteniendo contexto de sesión.
    """
    main_module = _main()
    main_module._enforce_rate_limit(
        "refine",
        key=thread_id,
        limit=main_module.settings.rate_limit_refine_per_window,
    )
    config = {"configurable": {"thread_id": thread_id}}
    state = await main_module.graph.aget_state(config)
    if not state.values:
        main_module._raise_domain_http(SessionNotFoundError("Sesión no encontrada."))

    v = state.values
    if not v.get("propuesta_final"):
        main_module._raise_domain_http(BusinessRuleError("No hay propuesta previa para refinar."))

    try:
        app_settings = main_module.get_settings()
        llm = main_module.ChatGoogleGenerativeAI(
            model=app_settings.gemini_chat_model,
            temperature=0.3,
            google_api_key=app_settings.gemini_api_key,
        )
        selected_cases = main_module.filter_selected_cases(
            list(v.get("casos_encontrados", [])),
            list(v.get("casos_seleccionados_ids", [])),
        )
        profile_context = v.get("perfil_cliente") or {}
        client_context = v.get("cliente_priorizado_contexto") or {}
        sector_context = v.get("inteligencia_sector") or {}

        prompt = (
            "Refina la siguiente propuesta comercial manteniendo precisión y tono ejecutivo.\n"
            "Aplica estrictamente la instrucción del usuario.\n\n"
            "--- CONTEXTO CLIENTE PRIORIZADO ---\n"
            f"Empresa: {v.get('empresa', 'N/A')}\n"
            f"Vertical: {client_context.get('vertical', 'N/A')}\n"
            f"Prioridades: {client_context.get('priorities', [])}\n"
            f"Restricciones: {client_context.get('constraints', [])}\n\n"
            "--- CONTEXTO PERFIL CLIENTE ---\n"
            f"Objetivos: {profile_context.get('objetivos', [])}\n"
            f"Pain points: {profile_context.get('pain_points', [])}\n"
            f"Notas: {profile_context.get('notas', 'N/A')}\n\n"
            "--- CONTEXTO SECTOR ---\n"
            f"Industria: {sector_context.get('industria', 'N/A')} / Area: {sector_context.get('area', 'N/A')}\n"
            f"Tendencias: {sector_context.get('tendencias', [])}\n\n"
            "--- CASOS SELECCIONADOS CON EVIDENCIA ---\n"
            f"{main_module.format_cases_for_prompt(selected_cases)}\n\n"
            f"INSTRUCCION: {data.instruction}\n\n"
            "PROPUESTA ACTUAL:\n"
            f"{v['propuesta_final']}\n"
        )
        refined = await main_module._invoke_llm_async(llm, prompt)

        versions = list(v.get("propuesta_versiones") or [])
        versions.append(refined)
        await main_module.graph.aupdate_state(
            config,
            {
                "propuesta_final": refined,
                "propuesta_versiones": versions,
                "error": "",
            },
        )

        new_state = await main_module.graph.aget_state(config)
        latest = new_state.values
        main_module.session_funnel_store.record_refine(thread_id)
        return main_module._map_state_response(thread_id, latest, status="completed")
    except BackendDomainError as exc:
        main_module._raise_domain_http(exc)
    except Exception:
        main_module._raise_internal_server_error("Error refining proposal")


@router.post("/agent/{thread_id}/chat", response_model=ChatResponse)
async def contextual_chat(thread_id: str, data: ChatRequest):
    """
    Chat contextual dedicado por thread.
    Usa contexto de cliente priorizado, perfil, sector y casos para responder con valor comercial.
    """
    main_module = _main()
    main_module._enforce_rate_limit(
        "chat",
        key=thread_id,
        limit=main_module.settings.rate_limit_chat_per_window,
    )
    config = {"configurable": {"thread_id": thread_id}}
    state = await main_module.graph.aget_state(config)
    if not state.values:
        main_module._raise_domain_http(SessionNotFoundError("Sesión no encontrada."))

    v = state.values
    all_cases = list(v.get("casos_encontrados", []))
    selected_ids = list(v.get("casos_seleccionados_ids", []))
    selected_cases = main_module.filter_selected_cases(all_cases, selected_ids)
    cases_for_chat = selected_cases if selected_cases else all_cases[:3]
    used_case_ids = [str(c.get("id")) for c in cases_for_chat if c.get("id")]

    profile_context = v.get("perfil_cliente") or {}
    client_context = v.get("cliente_priorizado_contexto") or {}
    sector_context = v.get("inteligencia_sector") or {}
    chat_history = list(v.get("chat_messages") or [])
    history_tail = chat_history[-8:]
    history_block = "\n".join(f"{item.get('role', 'user').upper()}: {item.get('content', '')}" for item in history_tail)
    audit_ts = datetime.now(timezone.utc).isoformat()
    guardrail = main_module.evaluate_chat_message(data.message)

    if not guardrail.allowed:
        blocked_answer = (
            "No puedo procesar ese mensaje en el chat contextual por una regla de seguridad. "
            "Reformula tu consulta enfocandola en estrategia, evidencia de casos o propuesta de valor."
        )
        new_history = history_tail + [
            {"role": "user", "content": guardrail.sanitized_message},
            {"role": "assistant", "content": blocked_answer},
        ]
        await main_module.graph.aupdate_state(config, {"chat_messages": new_history})
        main_module.chat_audit_store.record_event(
            thread_id=thread_id,
            empresa=v.get("empresa"),
            status="guardrail_blocked",
            guardrail_code=guardrail.code,
            used_case_ids=[],
            message=guardrail.sanitized_message,
        )
        main_module.session_funnel_store.record_chat(thread_id=thread_id, status="guardrail_blocked")
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
        app_settings = main_module.get_settings()
        llm = main_module.ChatGoogleGenerativeAI(
            model=app_settings.gemini_chat_model,
            temperature=0.3,
            google_api_key=app_settings.gemini_api_key,
        )
        prompt = (
            "Eres el asistente contextual de propuestas NEO.\n"
            "Responde con foco comercial, claridad ejecutiva y trazabilidad a casos.\n"
            "Si recomiendas una linea de propuesta, indica por que aporta valor al cliente.\n"
            "No inventes evidencias; usa solo el contexto provisto.\n\n"
            "--- CONTEXTO CLIENTE PRIORIZADO ---\n"
            f"Empresa: {v.get('empresa', 'N/A')}\n"
            f"Vertical: {client_context.get('vertical', 'N/A')}\n"
            f"Prioridades: {client_context.get('priorities', [])}\n"
            f"Restricciones: {client_context.get('constraints', [])}\n\n"
            "--- PERFIL CLIENTE ---\n"
            f"Objetivos: {profile_context.get('objetivos', [])}\n"
            f"Pain points: {profile_context.get('pain_points', [])}\n"
            f"Notas: {profile_context.get('notas', 'N/A')}\n\n"
            "--- CONTEXTO SECTOR ---\n"
            f"Industria: {sector_context.get('industria', 'N/A')} / Area: {sector_context.get('area', 'N/A')}\n"
            f"Tendencias: {sector_context.get('tendencias', [])}\n\n"
            "--- CASOS DISPONIBLES PARA RESPONDER ---\n"
            f"{main_module.format_cases_for_prompt(cases_for_chat)}\n\n"
            "--- HISTORIAL RECIENTE ---\n"
            f"{history_block or 'Sin historial previo.'}\n\n"
            "--- MENSAJE DEL CONSULTOR ---\n"
            f"{guardrail.sanitized_message}\n\n"
            "Responde en maximo 180 palabras y cita IDs de casos cuando corresponda."
        )
        answer = await main_module._invoke_llm_async(llm, prompt)

        new_history = history_tail + [
            {"role": "user", "content": guardrail.sanitized_message},
            {"role": "assistant", "content": answer},
        ]
        await main_module.graph.aupdate_state(config, {"chat_messages": new_history})
        main_module.chat_audit_store.record_event(
            thread_id=thread_id,
            empresa=v.get("empresa"),
            status="ok",
            guardrail_code=guardrail.code,
            used_case_ids=used_case_ids,
            message=guardrail.sanitized_message,
        )
        main_module.session_funnel_store.record_chat(thread_id=thread_id, status="ok")

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
        main_module._raise_domain_http(exc)
    except Exception:
        main_module._raise_internal_server_error("Error in contextual chat")


@router.get("/agent/{thread_id}/state", response_model=AgentStateResponse)
async def get_agent_state(thread_id: str):
    """Recupera el estado actual de una sesión."""
    main_module = _main()
    config = {"configurable": {"thread_id": thread_id}}
    state = await main_module.graph.aget_state(config)

    if not state.values:
        main_module._raise_domain_http(SessionNotFoundError("Sesión no encontrada."))

    return main_module._map_state_response(thread_id, state.values)
