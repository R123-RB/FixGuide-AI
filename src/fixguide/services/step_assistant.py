"""Interactive assistant service for answering user questions during repair steps."""

from __future__ import annotations

import logging
from typing import Any

from fixguide.graph.builder import graph
from fixguide.services.llm import get_llm_client
from fixguide.services.vision import get_vision_client
from fixguide.utils.prompts import render_prompt

logger = logging.getLogger(__name__)


class StepAssistantService:
    """Answers user questions and troubleshoots issues during an active repair step."""

    def __init__(self) -> None:
        """Initialize the assistant with LLM and Vision clients."""
        self.llm_client = get_llm_client()
        self.vision_client = get_vision_client()

    async def answer_question(
        self,
        session_id: str,
        question: str,
        image_base64: str | None = None,
    ) -> str:
        """Answer a user question within the context of the active repair step."""
        config = {"configurable": {"thread_id": session_id}}

        category = "Electronics"
        device_name = "Device"
        problem = "Repair"
        current_step_num = 1
        instruction = "Proceed with caution."
        tools: list[str] = []
        safety_flags: list[str] = []
        components: list[str] = []
        context_chunks: list[dict[str, Any]] = []

        try:
            state_snapshot = await graph.aget_state(config)
            values = state_snapshot.values or {}

            cat = values.get("category")
            if cat is not None and hasattr(cat, "value"):
                category = str(cat.value)
            elif cat is not None:
                category = str(cat)

            device_name = values.get("product_id") or category.replace("_", " ").title()
            problem = values.get("problem_description", "Hardware issue")
            current_step_num = values.get("current_step", 0) + 1

            step_data = values.get("generation_output") or {}
            instruction = step_data.get("instruction", "Follow the current step.")
            tools = step_data.get("tools_required", [])
            safety_flags = step_data.get("safety_flags", [])
            components = step_data.get("components_involved", [])
            context_chunks = values.get("retrieval_results", [])
        except Exception as e:
            logger.warning(f"Could not load state snapshot for session {session_id}: {e}")

        # Build context string from top chunks
        context_text = "\n".join(
            f"[{c.get('chunk_id', i)}]: {c.get('text', '')}"
            for i, c in enumerate(context_chunks[:3], 1)
        ) or "No additional manual chunks available."

        prompt = render_prompt(
            "step_qa",
            {
                "device_name": device_name,
                "category": category,
                "problem": problem,
                "step_number": current_step_num,
                "step_instruction": instruction,
                "tools": ", ".join(tools) if tools else "None specified",
                "safety_flags": ", ".join(safety_flags) if safety_flags else "Standard safety",
                "components": ", ".join(components) if components else "General casing",
                "context": context_text,
                "question": question,
            },
        )

        try:
            if image_base64:
                return await self.vision_client.vision_completion(
                    system_prompt=prompt["system"],
                    user_prompt=prompt["user"],
                    image_base64=image_base64,
                )

            return await self.llm_client.chat_completion(
                [
                    {"role": "system", "content": prompt["system"]},
                    {"role": "user", "content": prompt["user"]},
                ]
            )
        except Exception as e:
            logger.error(f"Failed to generate answer for step question: {e}")
            return (
                "I apologize, but I encountered an error retrieving an answer. "
                "Please make sure tools and parts are handled gently without forcing."
            )


_assistant_service: StepAssistantService | None = None


def get_step_assistant() -> StepAssistantService:
    """Get the singleton StepAssistantService instance."""
    global _assistant_service
    if _assistant_service is None:
        _assistant_service = StepAssistantService()
    return _assistant_service
