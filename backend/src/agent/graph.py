from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

# Para V2, prepararemos el RedisSaver pero mantendremos MemorySaver como fallback local
try:
    from langgraph.checkpoint.redis import RedisSaver
    import redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False

from src.agent.nodes import draft_node, intake_node, retrieve_node
from src.agent.state import ProposalState
from src.config import get_settings

def _route_on_error(state: ProposalState) -> str:
    return "end" if state.get("error") else "next"

builder = StateGraph(ProposalState)

# Nodos del MVP V2
builder.add_node("intake_node", intake_node)
builder.add_node("retrieve_node", retrieve_node)
builder.add_node("draft_node", draft_node)

builder.add_edge(START, "intake_node")

builder.add_conditional_edges(
    "intake_node",
    _route_on_error,
    {
        "end": END,
        "next": "retrieve_node",
    },
)

builder.add_conditional_edges(
    "retrieve_node",
    _route_on_error,
    {
        "end": END,
        "next": "draft_node", # El interrupt ocurre aquí
    },
)

builder.add_edge("draft_node", END)

# Configuración del Checkpointer (Persistencia)
settings = get_settings()
is_non_local_env = settings.is_non_local_env

if HAS_REDIS and settings.redis_url:
    try:
        # Intentamos conectar a Redis para persistencia real de V2
        conn = redis.from_url(settings.redis_url)
        checkpointer = RedisSaver(conn)
        print(f"🚀 Persistencia V2 activada: Usando Redis en {settings.redis_url}")
    except Exception as e:
        if is_non_local_env:
            raise RuntimeError(
                f"Redis obligatorio en entorno '{settings.app_env}' y no disponible: {e}"
            ) from e
        print(f"⚠️ Error conectando a Redis, usando memoria temporal: {e}")
        checkpointer = MemorySaver()
else:
    if is_non_local_env:
        raise RuntimeError(
            f"Redis obligatorio en entorno '{settings.app_env}' para persistencia de sesiones."
        )
    print("ℹ️ Redis no configurado o no instalado. Usando MemorySaver (Sesiones no persistentes).")
    checkpointer = MemorySaver()

# Compilación del Grafo
# Interrumpimos antes de draft_node para que el usuario pueda seleccionar los casos (HITL)
graph = builder.compile(
    checkpointer=checkpointer, 
    interrupt_before=["draft_node"]
)
