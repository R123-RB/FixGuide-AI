"""Unit tests for generation."""

from fixguide.core.generation import GroundingVerifier, StepGenerator


def test_generator_initialization() -> None:
    """Verify StepGenerator instantiates."""
    gen = StepGenerator()
    assert gen is not None


def test_verifier_initialization() -> None:
    """Verify GroundingVerifier instantiates."""
    verifier = GroundingVerifier()
    assert verifier is not None
