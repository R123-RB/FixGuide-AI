#!/usr/bin/env python
"""Validation script to run after dependencies are installed."""
from __future__ import annotations

import sys


def test_config():
    from fixguide.config import get_settings
    settings = get_settings()
    assert settings.app_name == "fixguide-ai"
    assert settings.api_port == 8000
    print("✓ Config loads correctly")


def test_models():
    from fixguide.models.domain import ProductCategory, RiskLevel, RepairChunk, RepairStep
    from fixguide.models.state import GraphState
    from fixguide.models.api import StartRepairRequest, StartRepairResponse
    
    cat = ProductCategory.GAME_CONTROLLER
    risk = RiskLevel.SAFE
    chunk = RepairChunk(
        chunk_id="test1", source="test", source_id="1", category=cat,
        title="Test", text="Test chunk", chunk_index=0, total_chunks=1
    )
    step = RepairStep(step_number=1, instruction="Test step")
    state = GraphState(
        session_id="test", category=cat, problem_description="test",
        user_skill_level="beginner"
    )
    req = StartRepairRequest(category=cat, problem_description="test problem")
    print("✓ Models work correctly")


def test_risk_gate():
    from fixguide.core.risk import RiskGate, get_risk_gate
    from fixguide.models.domain import RiskLevel
    
    gate = RiskGate()
    assert gate.classify("microwave", "door broken", "beginner") == RiskLevel.BLOCKED
    assert gate.classify("lamp", "won't turn on", "beginner") == RiskLevel.CAUTION
    assert gate.classify("game_controller", "stick drift", "beginner") == RiskLevel.SAFE
    print("✓ Risk gate classification works")


def test_graph_build():
    from fixguide.graph.builder import graph
    # Just verify it compiles
    assert graph is not None
    print("✓ Graph compiles successfully")


def test_prompt_rendering():
    from fixguide.utils.prompts import render_prompt
    result = render_prompt("product_id", {})
    assert "system" in result and "user" in result
    print("✓ Prompt rendering works")


def test_cli():
    from fixguide.cli import app
    assert app is not None
    print("✓ CLI loads correctly")


if __name__ == "__main__":
    tests = [
        test_config,
        test_models,
        test_risk_gate,
        test_graph_build,
        test_prompt_rendering,
        test_cli,
    ]
    
    failed = []
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed.append(test.__name__)
    
    if failed:
        print(f"\n{len(failed)} test(s) failed: {failed}")
        sys.exit(1)
    else:
        print("\n✓ All validation tests passed!")
        sys.exit(0)