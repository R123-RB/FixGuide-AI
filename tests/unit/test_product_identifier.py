"""Unit tests for product identifier and iFixit service."""

from fixguide.services.ifixit import get_ifixit_service
from fixguide.services.product_identifier import get_product_identifier
from fixguide.services.step_assistant import get_step_assistant


def test_product_identifier_instantiation() -> None:
    """Verify ProductIdentifier initializes correctly."""
    identifier = get_product_identifier()
    assert identifier is not None


def test_ifixit_service_instantiation() -> None:
    """Verify IFixitService initializes correctly."""
    service = get_ifixit_service()
    assert service is not None
    assert service.base_url == "https://www.ifixit.com/api/2.0"


def test_step_assistant_instantiation() -> None:
    """Verify StepAssistantService initializes correctly."""
    assistant = get_step_assistant()
    assert assistant is not None
