"""LangGraph builder — compiles the repair assistant state machine."""

from __future__ import annotations

from typing import Any

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from fixguide.graph.edges import (
    route_after_generate,
    route_after_retrieve,
    route_after_risk,
    route_after_verify,
    route_after_vision,
)
from fixguide.graph.nodes import (
    generate_node,
    reassembly_node,
    retrieve_node,
    risk_gate_node,
    verify_node,
    vision_check_node,
)
from fixguide.models.state import GraphState


def build_graph() -> StateGraph:
    """Build and compile the FixGuide repair graph."""
    builder = StateGraph(GraphState)

    # Nodes
    builder.add_node("risk_gate", risk_gate_node)
    builder.add_node("retrieve", retrieve_node)
    builder.add_node("generate", generate_node)
    builder.add_node("verify", verify_node)
    builder.add_node("vision_check", vision_check_node)
    builder.add_node("reassembly", reassembly_node)

    # Edges
    builder.add_edge(START, "risk_gate")
    builder.add_conditional_edges(
        "risk_gate",
        route_after_risk,
        {
            "retrieve": "retrieve",
            "error": END,
        },
    )
    builder.add_conditional_edges(
        "retrieve",
        route_after_retrieve,
        {
            "generate": "generate",
            "error": END,
        },
    )
    builder.add_conditional_edges(
        "generate",
        route_after_generate,
        {
            "verify": "verify",
            "reassembly": "reassembly",
        },
    )
    builder.add_conditional_edges(
        "verify",
        route_after_verify,
        {
            "vision_check": "vision_check",
            "generate": "generate",
        },
    )
    builder.add_conditional_edges(
        "vision_check",
        route_after_vision,
        {
            "retrieve": "retrieve",
            "generate": "generate",
            "reassembly": "reassembly",
        },
    )
    builder.add_edge("reassembly", END)

    # Compile with memory checkpointing and pause before vision verification
    return builder.compile(  # type: ignore[return-value]
        checkpointer=MemorySaver(),
        interrupt_before=["vision_check"],
    )


# Singleton instance
graph: Any = build_graph()
