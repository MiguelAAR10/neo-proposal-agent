from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from src.intel_pipeline.orchestrator.nodes import (
    collect_signals_node,
    evaluate_triggers_node,
    update_industry_profile_node,
)
from src.intel_pipeline.orchestrator.state import RadarState


def _route_on_error(state: RadarState) -> str:
    return "end" if state.get("error") else "next"


builder = StateGraph(RadarState)
builder.add_node("collect_signals", collect_signals_node)
builder.add_node("evaluate_triggers", evaluate_triggers_node)
builder.add_node("update_industry_profile", update_industry_profile_node)

builder.add_edge(START, "collect_signals")
builder.add_conditional_edges(
    "collect_signals",
    _route_on_error,
    {"end": END, "next": "evaluate_triggers"},
)
builder.add_conditional_edges(
    "evaluate_triggers",
    _route_on_error,
    {"end": END, "next": "update_industry_profile"},
)
builder.add_edge("update_industry_profile", END)

macro_radar_graph = builder.compile()


def run_macro_radar_sync(*, industry_target: str, force_mock_tools: bool = False) -> RadarState:
    initial_state: RadarState = {
        "industry_target": industry_target,
        "raw_signals": [],
        "critical_triggers_found": [],
        "industry_radiography": {},
        "force_mock_tools": force_mock_tools,
    }
    result = macro_radar_graph.invoke(initial_state)
    return result
