from langchain_google_genai import ChatGoogleGenerativeAI

from src.agent.state import ProposalState
from src.config import get_settings
from src.tools.qdrant_tool import db_connection


def intake_node(state: ProposalState) -> ProposalState:
    empresa = (state.get("empresa") or "").strip()
    problema = (state.get("problema") or "").strip()

    if not empresa or not problema:
        state["error"] = "Los campos Empresa y Problema son obligatorios."
        return state

    state["empresa"] = empresa
    state["problema"] = problema
    state["error"] = ""
    return state


def retrieve_node(state: ProposalState) -> ProposalState:
    if state.get("error"):
        return state

    try:
        results = db_connection.search_cases(state["problema"], collection_name="neo_cases_v1", limit=6)
        state["casos_encontrados"] = results
        if not results:
            state["error"] = "No se encontraron casos para el problema ingresado."
    except Exception as exc:
        state["error"] = f"Error consultando Qdrant: {exc}"

    return state


def _format_cases_for_prompt(cases: list[dict]) -> str:
    if not cases:
        return "No hay casos seleccionados."

    blocks: list[str] = []
    for idx, case in enumerate(cases, start=1):
        blocks.append(
            f"Caso {idx}\n"
            f"ID: {case.get('id', 'N/A')}\n"
            f"Titulo: {case.get('titulo', 'Sin titulo')}\n"
            f"Resumen: {case.get('resumen', 'Sin resumen')}"
        )
    return "\n\n".join(blocks)


def draft_node(state: ProposalState) -> ProposalState:
    if state.get("error"):
        return state

    selected_ids = set(state.get("casos_seleccionados_ids", []))
    found_cases = state.get("casos_encontrados", [])

    filtered_cases = [c for c in found_cases if str(c.get("id")) in selected_ids]
    if not filtered_cases:
        state["error"] = "Debes seleccionar al menos un caso antes de generar la propuesta."
        return state

    try:
        settings = get_settings()
        if not settings.gemini_api_key:
            state["error"] = "Falta configurar GEMINI_API_KEY para generar la propuesta."
            return state

        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0.3,
            google_api_key=settings.gemini_api_key,
        )

        prompt = (
            "Eres un consultor comercial senior. Redacta una propuesta de valor clara y accionable "
            "de aproximadamente 400 palabras en espanol.\n\n"
            f"Empresa: {state.get('empresa', '')}\n"
            f"Rubro: {state.get('rubro', '')}\n"
            f"Problema del cliente: {state.get('problema', '')}\n\n"
            "Casos de referencia seleccionados:\n"
            f"{_format_cases_for_prompt(filtered_cases)}\n\n"
            "La propuesta debe incluir: contexto, enfoque recomendado, plan de trabajo resumido, "
            "beneficios esperados y llamado a la accion."
        )

        response = llm.invoke(prompt)
        content = response.content
        if isinstance(content, list):
            text = "\n".join(str(part) for part in content)
        else:
            text = str(content)

        state["propuesta_final"] = text.strip()
        state["error"] = ""
    except Exception as exc:
        state["error"] = f"Error generando propuesta: {exc}"

    return state
