"""Unified LLM client for Groq, OpenAI, Anthropic, Vertex."""

from __future__ import annotations

import asyncio
import os
from typing import Any

from fixguide.config import get_settings


class LLMClient:
    """Abstract LLM client supporting multiple providers."""

    def __init__(self) -> None:
        """Initialize the LLM client with settings."""
        self.settings = get_settings()
        self.provider = self.settings.llm.provider
        self.model = self.settings.llm.model
        self._client: Any = None

    def _get_client(self) -> Any:  # noqa: ANN401
        if self._client is None:
            if self.provider == "groq":
                from groq import AsyncGroq

                self._client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
            elif self.provider == "gemini":
                from openai import AsyncOpenAI

                self._client = AsyncOpenAI(
                    api_key=os.getenv("GEMINI_API_KEY"),
                    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                )
            elif self.provider == "openai":
                from openai import AsyncOpenAI

                self._client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            elif self.provider == "anthropic":
                from anthropic import AsyncAnthropic

                self._client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            elif self.provider == "vertex":
                import vertexai  # type: ignore[import-not-found]

                vertexai.init(
                    project=os.getenv("VERTEX_PROJECT"),
                    location=os.getenv("VERTEX_LOCATION"),
                )
                from vertexai.generative_models import (  # type: ignore[import-not-found]
                    GenerativeModel,
                )

                self._client = GenerativeModel(self.model)
            else:
                raise ValueError(f"Unknown provider: {self.provider}")
        return self._client

    async def chat_completion(self, messages: list[dict], **kwargs: Any) -> str:  # noqa: ANN401
        """Generate chat completion with retry handling."""
        client = self._get_client()
        retries = self.settings.llm.max_retries

        for attempt in range(retries + 1):
            try:
                if self.provider in ("groq", "openai", "gemini"):
                    response = await client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        temperature=self.settings.llm.temperature,
                        max_tokens=self.settings.llm.max_tokens,
                        **kwargs,
                    )
                    return str(response.choices[0].message.content)

                if self.provider == "anthropic":
                    system = next((m["content"] for m in messages if m["role"] == "system"), "")
                    user_messages = [m for m in messages if m["role"] != "system"]
                    response = await client.messages.create(
                        model=self.model,
                        system=system,
                        messages=user_messages,
                        temperature=self.settings.llm.temperature,
                        max_tokens=self.settings.llm.max_tokens,
                        **kwargs,
                    )
                    return str(response.content[0].text)

                if self.provider == "vertex":
                    prompt = "\n".join(f"{m['role']}: {m['content']}" for m in messages)
                    response = await client.generate_content_async(prompt)
                    return str(response.text)

                raise ValueError(f"Unsupported provider: {self.provider}")
            except Exception as e:
                err_msg = str(e).lower()
                if attempt < retries and any(
                    k in err_msg for k in ("429", "resource_exhausted", "rate_limit", "quota")
                ):
                    delay = (2**attempt) * 4
                    await asyncio.sleep(delay)
                    continue
                raise
        raise RuntimeError("Failed to generate completion after retries")


_client = None


def get_llm_client() -> LLMClient:
    """Get the singleton LLM client."""
    global _client
    if _client is None:
        _client = LLMClient()
    return _client
