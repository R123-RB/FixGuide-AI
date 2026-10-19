"""Integration tests for graph flow."""

import pytest

from fixguide.graph.builder import graph
from fixguide.models.domain import ProductCategory, RiskLevel
from fixguide.models.state import GraphState


@pytest.mark.asyncio
async def test_graph_risk_gate_blocks_microwave() -> None:
    """Verify risk gate blocks high-risk products like microwaves."""
    state = GraphState(
        session_id="test",
        category=ProductCategory.GAME_CONTROLLER,
        problem_description="microwave door won't close",
        user_skill_level="beginner",
    )
    config = {"configurable": {"thread_id": "test"}}
    result = await graph.ainvoke(state, config=config)
    assert result["risk_level"] in (RiskLevel.HIGH_RISK, RiskLevel.BLOCKED)


@pytest.mark.asyncio
async def test_graph_safe_product_proceeds() -> None:
    """Verify safe products proceed past the risk gate."""
    state = GraphState(
        session_id="test2",
        category=ProductCategory.GAME_CONTROLLER,
        problem_description="stick drift on left joystick",
        user_skill_level="beginner",
    )
    config = {"configurable": {"thread_id": "test2"}}
    try:
        result = await graph.ainvoke(state, config=config)
        assert result["risk_level"] == RiskLevel.SAFE
        assert result["next_action"] in (
            "retrieve",
            "generate",
            "verify",
            "vision_check",
            "reassembly",
            "complete",
        )
    except Exception as e:
        # Skip if no API key or model not available
        err = str(e).lower()
        if any(
            k in err
            for k in [
                "api_key",
                "auth",
                "401",
                "404",
                "429",
                "rate_limit",
                "quota",
                "resource_exhausted",
                "model_not_found",
                "not_found",
            ]
        ):
            pytest.skip("Requires valid API key, model access, and active quota")
        raise
