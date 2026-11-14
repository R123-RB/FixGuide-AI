"""Risk gate classifier for product safety."""

from __future__ import annotations

from fixguide.config import get_settings
from fixguide.models.domain import RiskLevel
from fixguide.services.llm import get_llm_client
from fixguide.utils.prompts import render_prompt


class RiskGate:
    """Classifies product risk level before any repair guidance."""

    def __init__(self) -> None:
        """Initialize the risk gate with settings and LLM client."""
        self.settings = get_settings()
        self.client = get_llm_client()
        self.blocked = set(self.settings.risk_gate.blocked_categories)
        self.caution_keywords = set(self.settings.risk_gate.caution_keywords)

    def classify(self, category: str, problem: str, skill_level: str) -> RiskLevel:
        """Fast rule-based classification."""
        cat_lower = category.lower()
        prob_lower = problem.lower()

        # Check blocked categories
        for blocked in self.blocked:
            if blocked in cat_lower or blocked in prob_lower:
                return RiskLevel.BLOCKED

        # Check caution keywords
        for keyword in self.caution_keywords:
            if keyword in prob_lower:
                return RiskLevel.CAUTION

        # Category-based defaults
        caution_categories = {"lamp", "table_fan"}
        if cat_lower in caution_categories:
            return RiskLevel.CAUTION

        return RiskLevel.SAFE

    async def classify_with_llm(self, category: str, problem: str, skill_level: str) -> RiskLevel:
        """LLM-based classification for edge cases."""
        prompt = render_prompt(
            "risk_gate",
            {
                "category": category,
                "problem": problem,
                "skill_level": skill_level,
            },
        )

        response = await self.client.chat_completion(
            [
                {"role": "system", "content": prompt["system"]},
                {"role": "user", "content": prompt["user"]},
            ]
        )

        import json

        try:
            result = json.loads(response)
            return RiskLevel(result.get("risk_level", "safe"))
        except Exception:
            return self.classify(category, problem, skill_level)


_gate = None


def get_risk_gate() -> RiskGate:
    """Get the singleton risk gate."""
    global _gate
    if _gate is None:
        _gate = RiskGate()
    return _gate
