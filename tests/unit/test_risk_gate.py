"""Unit tests for risk gate."""

from fixguide.core.risk import RiskGate
from fixguide.models.domain import RiskLevel


def test_risk_gate_initialization() -> None:
    """Verify RiskGate instantiates."""
    gate = RiskGate()
    assert gate is not None


def test_classify_blocked() -> None:
    """Verify microwave is classified as blocked."""
    gate = RiskGate()
    result = gate.classify("microwave", "door won't close", "beginner")
    assert result == RiskLevel.BLOCKED


def test_classify_caution() -> None:
    """Verify lamp is classified as caution."""
    gate = RiskGate()
    result = gate.classify("lamp", "won't turn on", "beginner")
    assert result == RiskLevel.CAUTION


def test_classify_safe() -> None:
    """Verify game controller is classified as safe."""
    gate = RiskGate()
    result = gate.classify("game_controller", "stick drift", "beginner")
    assert result == RiskLevel.SAFE
