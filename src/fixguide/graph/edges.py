"""Conditional edge routing for the repair graph."""

from __future__ import annotations

from fixguide.models.domain import RiskLevel
from fixguide.models.state import GraphState


def route_after_risk(state: GraphState) -> str:
    """Route after risk gate: block or proceed to retrieval."""
    if state.risk_level in (RiskLevel.HIGH_RISK, RiskLevel.BLOCKED):
        return "error"
    return "retrieve"


def route_after_retrieve(state: GraphState) -> str:
    """Route after retrieval: generate if results found, else error."""
    if state.retrieval_results:
        return "generate"
    return "error"


def route_after_generate(state: GraphState) -> str:
    """Route after generation: verify grounding, or reassembly if complete."""
    if state.is_complete:
        return "reassembly"
    return "verify"


def route_after_verify(state: GraphState) -> str:
    """Route after grounding verification: vision check if grounded, else regenerate."""
    is_grounded = bool(state.verification_result and state.verification_result.get("grounded"))
    if is_grounded or state.retry_count >= 1:
        return "vision_check"
    return "generate"


def route_after_vision(state: GraphState) -> str:
    """Route after vision check: next step if matches, else correction loop."""
    if state.vision_result and state.vision_result.get("matches"):
        if state.is_complete:
            return "reassembly"
        return "retrieve"
    return "generate"
