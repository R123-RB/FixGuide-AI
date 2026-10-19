"""Unit tests for verification."""

from fixguide.core.verification import VisionVerifier


def test_vision_verifier_initialization() -> None:
    """Verify VisionVerifier instantiates."""
    verifier = VisionVerifier()
    assert verifier is not None
