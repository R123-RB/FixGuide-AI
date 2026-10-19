"""Vision model client for image analysis."""

from __future__ import annotations

import asyncio
import os
from typing import Any

from fixguide.config import get_settings


class VisionClient:
    """Vision model client for image understanding."""

    def __init__(self) -> None:
        """Initialize the vision client with settings."""
        self.settings = get_settings()
        self.provider = self.settings.vision.provider
        self.model = self.settings.vision.model
        self._client: Any = None

    def _get_client(self) -> Any:  # noqa: ANN401
        if self._client is None:
            if self.provider in ("groq", "openai", "gemini"):
                if self.provider == "groq":
                    from groq import AsyncGroq

                    self._client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
                elif self.provider == "gemini":
                    from openai import AsyncOpenAI

                    self._client = AsyncOpenAI(
                        api_key=os.getenv("GEMINI_API_KEY"),
                        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                    )
                else:
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
                raise ValueError(f"Unknown vision provider: {self.provider}")
        return self._client

    async def vision_completion(
        self, system_prompt: str, user_prompt: str, image_base64: str
    ) -> str:
        """Generate completion with image input and retry handling."""
        client = self._get_client()
        retries = 3

        for attempt in range(retries + 1):
            try:
                if self.provider in ("groq", "openai", "gemini"):
                    response = await client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": user_prompt},
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/jpeg;base64,{image_base64}"
                                        },
                                    },
                                ],
                            },
                        ],
                        max_tokens=self.settings.vision.max_tokens,
                    )
                    return str(response.choices[0].message.content)

                if self.provider == "anthropic":
                    response = await client.messages.create(
                        model=self.model,
                        system=system_prompt,
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": user_prompt},
                                    {
                                        "type": "image",
                                        "source": {
                                            "type": "base64",
                                            "media_type": "image/jpeg",
                                            "data": image_base64,
                                        },
                                    },
                                ],
                            }
                        ],
                        max_tokens=self.settings.vision.max_tokens,
                    )
                    return str(response.content[0].text)

                if self.provider == "vertex":
                    from vertexai.generative_models import (  # type: ignore[import-not-found]
                        Part,
                    )

                    image_part = Part.from_data(image_base64, mime_type="image/jpeg")
                    prompt = f"{system_prompt}\n\n{user_prompt}"
                    response = await client.generate_content_async([prompt, image_part])
                    return str(response.text)

                raise ValueError(f"Unsupported vision provider: {self.provider}")
            except Exception as e:
                err_msg = str(e).lower()
                if attempt < retries and any(
                    k in err_msg for k in ("429", "resource_exhausted", "rate_limit", "quota")
                ):
                    delay = (2**attempt) * 4
                    await asyncio.sleep(delay)
                    continue
                raise
        raise RuntimeError("Failed to generate vision completion after retries")


_client = None


def get_vision_client() -> VisionClient:
    """Get the singleton vision client."""
    global _client
    if _client is None:
        _client = VisionClient()
    return _client
