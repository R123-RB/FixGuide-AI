"""Pytest configuration and shared fixtures."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add src to path for tests
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from fixguide.models.domain import ProductCategory, RepairChunk, RepairStep
from fixguide.models.state import GraphState


@pytest.fixture
def sample_chunks() -> list[RepairChunk]:
    """Sample repair chunks for testing."""
    return [
        RepairChunk(
            chunk_id="test-chunk-1",
            source="test",
            source_id="test-guide",
            category=ProductCategory.GAME_CONTROLLER,
            title="Test Guide",
            text="This is a test repair step for game controllers.",
            chunk_index=0,
            total_chunks=1,
            images=[],
            metadata={"tools": ["screwdriver"], "difficulty": "beginner"},
        ),
        RepairChunk(
            chunk_id="test-chunk-2",
            source="test",
            source_id="test-guide",
            category=ProductCategory.GAME_CONTROLLER,
            title="Test Guide",
            text="Remove the screws to open the controller shell.",
            chunk_index=1,
            total_chunks=2,
            images=[],
            metadata={"tools": ["screwdriver"], "difficulty": "beginner"},
        ),
    ]


@pytest.fixture
def sample_step() -> RepairStep:
    """Sample repair step for testing."""
    return RepairStep(
        step_number=1,
        instruction="Remove the battery cover screw with a Phillips #00 screwdriver.",
        tools_required=["Phillips #00 screwdriver"],
        safety_flags=["Remove batteries before starting"],
        components_involved=["screws", "battery_cover"],
        expected_visual_state="Battery cover removed, screw visible",
        source_chunks=["test-chunk-1"],
    )


@pytest.fixture
def sample_state() -> GraphState:
    """Sample graph state for testing."""
    return GraphState(
        session_id="test-session",
        category=ProductCategory.GAME_CONTROLLER,
        problem_description="Left joystick drifts up",
        user_skill_level="beginner",
        available_tools=["Phillips #00 screwdriver"],
    )
