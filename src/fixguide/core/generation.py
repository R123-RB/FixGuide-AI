"""Step generation and grounding verification."""

from __future__ import annotations

import json
from typing import Any, cast

from fixguide.config import get_settings
from fixguide.services.llm import get_llm_client
from fixguide.utils.prompts import render_prompt


class StepGenerator:
    """Generates repair steps using LLM with RAG context."""

    def __init__(self) -> None:
        """Initialize the step generator with settings and LLM client."""
        self.settings = get_settings()
        self.client = get_llm_client()

    async def generate(
        self,
        category: str,
        product_id: str | None,
        problem: str,
        skill_level: str,
        tools: list[str],
        current_step: int,
        chunks: list[Any],
    ) -> dict[str, Any]:
        """Generate next repair step."""
        prompt = render_prompt(
            "step_generator",
            {
                "category": category,
                "product_id": product_id or "unknown",
                "problem": problem,
                "skill_level": skill_level,
                "tools": ", ".join(tools) if tools else "none specified",
                "current_step": current_step,
                "chunks": chunks,
            },
        )

        response = await self.client.chat_completion(
            [
                {"role": "system", "content": prompt["system"]},
                {"role": "user", "content": prompt["user"]},
            ]
        )

        try:
            return cast(dict[str, Any], json.loads(response))
        except json.JSONDecodeError:
            # Fallback: extract JSON from response
            import re

            match = re.search(r"\{.*\}", response, re.DOTALL)
            if match:
                return cast(dict[str, Any], json.loads(match.group()))
            raise


class GroundingVerifier:
    """Verifies every claim in a generated step traces to source chunks."""

    def __init__(self) -> None:
        """Initialize the grounding verifier with settings and LLM client."""
        self.settings = get_settings()
        self.client = get_llm_client()

    async def verify(self, step: dict[str, Any], chunks: list[Any]) -> dict[str, Any]:
        """Check grounding of generated step."""
        prompt = render_prompt(
            "grounding_verifier",
            {
                "step": json.dumps(step, indent=2),
                "chunks": chunks,
            },
        )

        response = await self.client.chat_completion(
            [
                {"role": "system", "content": prompt["system"]},
                {"role": "user", "content": prompt["user"]},
            ]
        )

        try:
            return cast(dict[str, Any], json.loads(response))
        except json.JSONDecodeError:
            import re

            match = re.search(r"\{.*\}", response, re.DOTALL)
            if match:
                return cast(dict[str, Any], json.loads(match.group()))
            return {
                "grounded": False,
                "unsupported_claims": ["parse error"],
                "citation_coverage": 0.0,
                "feedback": "Failed to parse verifier output",
            }


# Singletons
_generator: StepGenerator | None = None
_verifier: GroundingVerifier | None = None


def get_generator() -> StepGenerator:
    """Get the singleton step generator."""
    global _generator
    if _generator is None:
        _generator = StepGenerator()
    return _generator


def get_verifier() -> GroundingVerifier:
    """Get the singleton grounding verifier."""
    global _verifier
    if _verifier is None:
        _verifier = GroundingVerifier()
    return _verifier
