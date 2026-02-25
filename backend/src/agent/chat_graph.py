import os
from typing import Annotated, Sequence, TypedDict
import operator

from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from src.config import get_settings

class ChatState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    cases_context: str

def format_sys_prompt(context: str) -> str:
    base = """Eres NEO Intelligence Assistant, un experto consultor de estrategia digital con acceso a la base de casos de éxito de NEO Consulting.

Tu rol es ayudar al consultor a:
1. Entender en profundidad los casos encontrados
2. Identificar qué elementos de cada caso son más relevantes para su cliente actual
3. Sugerir cómo adaptar las soluciones al contexto específico del cliente
4. Generar ideas de propuesta de valor basadas en los casos
5. Responder preguntas técnicas sobre las soluciones implementadas

{context}

Responde de manera profesional, concisa y orientada a valor comercial.
Si el consultor menciona el nombre de su cliente o industria, personaliza tu respuesta.
Siempre cita los casos específicos cuando los referencie."""
    return base.replace("{context}", context)

def agent_node(state: ChatState):
    settings = get_settings()
    llm = ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
        temperature=0.3,
        google_api_key=settings.gemini_api_key,
    )
    
    sys_msg = SystemMessage(content=format_sys_prompt(state.get("cases_context", "")))
    
    # Check if the first message is already a system message
    messages_to_send = []
    has_system = False
    for msg in state["messages"]:
        if isinstance(msg, SystemMessage):
            has_system = True
    
    if not has_system:
        messages_to_send.append(sys_msg)
        
    messages_to_send.extend(state["messages"])
    
    try:
        response = llm.invoke(messages_to_send)
        return {"messages": [response]}
    except Exception as e:
        # Fallback graceful response
        error_msg = AIMessage(content=f"Lo siento, ocurrió un error generando la respuesta: {e}. Por favor intenta de nuevo.")
        return {"messages": [error_msg]}

builder = StateGraph(ChatState)
builder.add_node("agent", agent_node)
builder.add_edge(START, "agent")
builder.add_edge("agent", END)

memory = MemorySaver()
chat_graph = builder.compile(checkpointer=memory)
