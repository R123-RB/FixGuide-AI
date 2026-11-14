"""Product identification from images."""

from __future__ import annotations

import json
from typing import Any, cast

from fixguide.config import get_settings
from fixguide.models.domain import ProductCategory
from fixguide.services.vision import get_vision_client
from fixguide.utils.prompts import render_prompt


class ProductIdentifier:
    """Identifies product category, brand, model from image."""

    def __init__(self) -> None:
        """Initialize the product identifier with settings and vision client."""
        self.settings = get_settings()
        self.client = get_vision_client()
        self.confidence_threshold = self.settings.product_id.confidence_threshold

    async def identify(self, image_base64: str) -> dict[str, Any]:
        """Identify product from image."""
        prompt = render_prompt("product_id", {})

        response = await self.client.vision_completion(
            prompt["system"],
            prompt["user"],
            image_base64,
        )

        try:
            result = cast(dict[str, Any], json.loads(response))
            # Validate category
            cat = result.get("category")
            if cat and cat in [c.value for c in ProductCategory]:
                result["category"] = ProductCategory(cat)
            else:
                result["category"] = ProductCategory.GAME_CONTROLLER  # default
            return result
        except Exception:
            return {
                "category": ProductCategory.GAME_CONTROLLER,
                "brand": None,
                "model": None,
                "confidence": 0.5,
                "reasoning": "Default fallback",
            }


_identifier: ProductIdentifier | None = None


def get_product_identifier() -> ProductIdentifier:
    """Get the singleton product identifier."""
    global _identifier
    if _identifier is None:
        _identifier = ProductIdentifier()
    return _identifier
