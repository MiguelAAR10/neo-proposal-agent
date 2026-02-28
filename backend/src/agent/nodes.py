from datetime import datetime
from typing import Any
from langchain_google_genai import ChatGoogleGenerativeAI
from src.agent.state import ProposalState
from src.config import get_settings
from src.services.search_service import search_cases_sync
from src.tools.qdrant_tool import db_connection

def intake_node(state: ProposalState) -> ProposalState:
    """Valida los inputs iniciales y prepara el estado."""
    empresa = (state.get("empresa") or "").strip()
    problema = (state.get("problema") or "").strip()
    area = (state.get("area") or "General").strip()
    switch = state.get("switch") or "both"

    if not empresa or not problema:
        state["error"] = "Los campos Empresa y Problema son obligatorios."
        return state

    state["empresa"] = empresa
    state["problema"] = problema
    state["area"] = area
    state["switch"] = switch
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
        state["casos_encontrados"] = search_payload.get("casos", [])
        state["neo_cases"] = search_payload.get("neo_cases", [])
        state["ai_cases"] = search_payload.get("ai_cases", [])
        if search_payload.get("top_match_global"):
            state["top_match_global"] = search_payload["top_match_global"]
            state["top_match_global_reason"] = search_payload.get("top_match_global_reason", "")

        # 2. Buscar perfil del cliente (Insights de negocio)
        perfil = db_connection.get_profile(state["empresa"], state["area"])
        if perfil:
            state["perfil_cliente"] = perfil
            print(f"✅ Perfil encontrado para {state['empresa']}")
        else:
            # Si no existe, podemos crear un placeholder o dejarlo vacío
            state["perfil_cliente"] = {
                "empresa": state["empresa"],
                "area": state["area"],
                "notas": "Empresa nueva sin historial previo."
            }

        if not state["casos_encontrados"]:
            state["error"] = "No se encontraron casos para el problema ingresado."
            
    except Exception as exc:
        state["error"] = f"Error en retrieve_node: {exc}"

    return state

def _format_cases_for_prompt(cases: list[dict]) -> str:
    if not cases:
        return "No hay casos seleccionados."

    blocks: list[str] = []
    for idx, case in enumerate(cases, start=1):
        blocks.append(
            f"--- CASO {idx} ---\n"
            f"TITULO: {case.get('titulo', 'Sin titulo')}\n"
            f"PROBLEMA: {case.get('resumen', case.get('problema', 'N/A'))}\n"
            f"SOLUCION: {case.get('solucion', 'Ver slide original')}\n"
            f"BENEFICIOS: {case.get('beneficios', 'N/A')}"
        )
    return "\n\n".join(blocks)

def _format_profile_for_prompt(perfil: dict | None) -> str:
    if not perfil or not perfil.get("empresa"):
        return "No hay información previa del cliente."
    
    return (
        f"Información sobre {perfil.get('empresa')}:\n"
        f"- Objetivos: {perfil.get('objetivos', 'N/A')}\n"
        f"- Pain Points: {perfil.get('pain_points', 'N/A')}\n"
        f"- Estilo/Cultura: {perfil.get('notas', 'N/A')}"
    )

def draft_node(state: ProposalState) -> ProposalState:
    """Genera la propuesta final usando los casos y el perfil del cliente."""
    print(f"DEBUG: Entrando a draft_node para {state.get('empresa')}")
    if state.get("error"):
        print(f"DEBUG: draft_node saltado por error previo: {state.get('error')}")
        return state

    selected_ids = set(state.get("casos_seleccionados_ids", []))
    found_cases = state.get("casos_encontrados", [])

    filtered_cases = [c for c in found_cases if str(c.get("id")) in selected_ids]
    if not filtered_cases:
        print("DEBUG: draft_node - No hay casos filtrados")
        state["error"] = "Debes seleccionar al menos un caso antes de generar la propuesta."
        return state

    try:
        print(f"DEBUG: draft_node - Llamando a Gemini con {len(filtered_cases)} casos...")
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
            
            "--- CASOS DE ÉXITO SELECCIONADOS (BASE TECNOLÓGICA) ---\n"
            f"{_format_cases_for_prompt(filtered_cases)}\n\n"
            
            "INSTRUCCIONES DE REDACCIÓN:\n"
            "1. Usa el 'Enfoque Propuesto' basado en los casos de éxito, pero ADÁPTALO a los objetivos del cliente.\n"
            "2. Si el cliente es adverso al riesgo (ver perfil), propón una implementación modular.\n"
            "3. Resalta el IMPACTO de negocio, no solo la tecnología.\n"
            "4. Mantén un tono ejecutivo, profesional y persuasivo.\n"
            "5. Máximo 500 palabras."
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
