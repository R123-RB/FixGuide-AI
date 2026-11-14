"""Vision verification for repair progress photos."""

from __future__ import annotations

import json
from typing import Any, cast

from fixguide.config import get_settings
from fixguide.services.vision import get_vision_client
from fixguide.utils.prompts import render_prompt


class VisionVerifier:
    """Compares user progress photo to expected step state."""

    def __init__(self) -> None:
        """Initialize the vision verifier with settings and vision client."""
        self.settings = get_settings()
        self.client = get_vision_client()

    async def verify(
        self,
        image_base64: str,
        step_number: int,
        expected_state: str,
        components: list[str],
        user_notes: str | None = None,
    ) -> dict[str, Any]:
        """Verify user photo matches expected state."""
        prompt = render_prompt(
            "vision_verifier",
            {
                "step_number": step_number,
                "expected_state": expected_state,
                "components": ", ".join(components),
                "user_notes": user_notes or "None provided",
            },
        )

        response = await self.client.vision_completion(
            prompt["system"],
            prompt["user"],
            image_base64,
        )

        try:
            return cast(dict[str, Any], json.loads(response))
        except json.JSONDecodeError:
            import re

            match = re.search(r"\{.*\}", response, re.DOTALL)
            if match:
                return cast(dict[str, Any], json.loads(match.group()))
            return {
                "matches": False,
                "confidence": 0.0,
                "feedback": "Failed to parse vision verifier output",
                "detected_components": [],
            }


_verifier: VisionVerifier | None = None


def get_vision_verifier() -> VisionVerifier:
    """Get the singleton vision verifier."""
    global _verifier
    if _verifier is None:
        _verifier = VisionVerifier()
    return _verifier
