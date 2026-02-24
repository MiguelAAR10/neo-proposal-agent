from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from src.agent.nodes import draft_node, intake_node, retrieve_node
from src.agent.state import ProposalState


def _route_on_error(state: ProposalState) -> str:
    return "end" if state.get("error") else "next"


builder = StateGraph(ProposalState)
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
        "next": "draft_node",
    },
)
builder.add_edge("draft_node", END)

checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer, interrupt_before=["draft_node"])
