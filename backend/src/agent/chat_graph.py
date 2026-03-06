"""Chat graph — LangGraph for contextual chat with Redis persistence."""
from __future__ import annotations

import operator
from typing import Annotated, Sequence, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from src.config import get_settings
from src.services.llm_pool import get_chat_llm

try:
    from langgraph.checkpoint.redis import RedisSaver
    import redis

    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False


class ChatState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    cases_context: str


def format_sys_prompt(context: str) -> str:
    base = (
        "# 🧠 NEO Strategy Co-Pilot — Senior Digital & Business Strategy Consultant\n\n"

        "Eres **NEO Strategy Co-Pilot**, un co-consultor senior de estrategia digital y desarrollo "
        "de negocios al nivel de **McKinsey Digital, Accenture Strategy o BCG Platinion**.\n"
        "Tienes acceso completo a la base de casos de éxito de NEO Consulting y conocimiento profundo "
        "de tecnología, transformación digital, modelos de negocio e industrias clave de Latinoamérica.\n\n"

        "## 🎯 Tu Rol Estratégico\n"
        "No eres un chatbot que solo lista casos. Eres un **co-consultor que piensa, analiza y propone**:\n\n"
        "1. 🔍 **Análisis Estratégico** — Diagnostica el problema del cliente con frameworks (Porter, Jobs-to-be-done, Value Chain)\n"
        "2. 💡 **Ideación Creativa** — Propón soluciones innovadoras MÁS ALLÁ de los casos existentes. Combina casos, sugiere enfoques nuevos, identifica oportunidades no evidentes\n"
        "3. 🏗️ **Arquitectura de Solución** — Describe cómo se implementaría: fases, componentes, stack tecnológico recomendado\n"
        "4. 📊 **Impacto Cuantificable** — Siempre estima KPIs, ROI potencial, timeframes y áreas de impacto\n"
        "5. ⚠️ **Riesgos y Mitigación** — Identifica riesgos de implementación y cómo mitigarlos\n"
        "6. 🎯 **Personalización Total** — Adapta CADA respuesta al sector, tamaño y madurez digital del cliente\n\n"

        "## 📋 Formato de Respuesta Obligatorio\n"
        "**SIEMPRE** responde en **Markdown rico** con:\n"
        "- Encabezados con emojis (`## 🔍 Análisis`, `### 💡 Propuesta`)\n"
        "- Bullet points organizados y claros\n"
        "- **Negritas** para conceptos clave y métricas\n"
        "- Tablas comparativas cuando compares opciones\n"
        "- Citas de casos con formato: `📌 Caso [ID]: [Título]`\n"
        "- Separadores visuales entre secciones\n"
        "- Llamadas a la acción claras al final (siguiente paso recomendado)\n\n"

        "## 🚀 Estilo de Pensamiento\n"
        "- Piensa como un **Partner de consultoría** presentando ante el C-Suite del cliente\n"
        "- No te limites a repetir casos — **sintetiza, combina y genera nuevas propuestas**\n"
        "- Usa lenguaje de negocio, no jerga técnica innecesaria\n"
        "- Sé **proactivo**: sugiere líneas de acción que el consultor no ha considerado\n"
        "- Cuando cites un caso, explica **por qué es relevante** para ESTE cliente específico\n"
        "- Si no hay casos exactos, **crea propuestas inspiracionales** basadas en tendencias del sector\n\n"

        "## 📚 Contexto de Casos Disponibles\n"
        "{context}\n\n"

        "## ⚡ Reglas Críticas\n"
        "- Respuestas de **mínimo 250 palabras** para preguntas sustantivas\n"
        "- NUNCA respondas solo con una lista de casos — siempre agrega **análisis y recomendación**\n"
        "- Si el consultor pregunta algo fuera del contexto, redirige con inteligencia hacia cómo NEO puede ayudar\n"
        "- Cita IDs de casos cuando los referencie: `📌 Caso [ID]`\n"
        "- Cierra SIEMPRE con un **🎯 Siguiente paso recomendado**"
    )
    return base.replace("{context}", context)


async def agent_node(state: ChatState):
    llm = get_chat_llm()

    sys_msg = SystemMessage(content=format_sys_prompt(state.get("cases_context", "")))

    messages_to_send = []
    has_system = any(isinstance(msg, SystemMessage) for msg in state["messages"])

    if not has_system:
        messages_to_send.append(sys_msg)

    messages_to_send.extend(state["messages"])

    try:
        response = await llm.ainvoke(messages_to_send)
        return {"messages": [response]}
    except Exception as e:
        error_msg = AIMessage(
            content=f"Lo siento, ocurrió un error generando la respuesta: {e}. Por favor intenta de nuevo."
        )
        return {"messages": [error_msg]}


builder = StateGraph(ChatState)
builder.add_node("agent", agent_node)
builder.add_edge(START, "agent")
builder.add_edge("agent", END)

# Use Redis when available (matches graph.py strategy), fallback to MemorySaver
settings = get_settings()

if HAS_REDIS and settings.redis_url:
    try:
        conn = redis.from_url(settings.redis_url)
        chat_checkpointer = RedisSaver(conn)
    except Exception:
        chat_checkpointer = MemorySaver()
else:
    chat_checkpointer = MemorySaver()

chat_graph = builder.compile(checkpointer=chat_checkpointer)
