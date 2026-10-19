"""Product and brand identification service using multimodal vision."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from fixguide.models.domain import ProductCategory
from fixguide.services.vision import get_vision_client

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert electronics and hardware diagnostic specialist.
Analyze the user's uploaded image of a hardware product or electronic device that needs repair.

Your task is to identify:
1. category: The product category. MUST be exactly one of:
   - "game_controller" (Xbox, PlayStation, Nintendo, Switch, JoyCon, etc.)
   - "wired_headphones" (over-ear headphones, earphones, headsets, etc.)
   - "lamp" (table lamps, desk lights, LED lamps)
   - "remote_control" (TV, AC, audio remotes)
   - "table_fan" (desk fans, cooling fans)
   - "keyboard" (mechanical, membrane, or laptop keyboards)
2. brand: Brand name (e.g. "Sony", "Logitech", "Microsoft", "Razer", "Apple", "Unknown")
3. model: Specific model name if recognizable (e.g. "PlayStation 5 DualSense", "Unknown")
4. device_name: Full descriptive device name (e.g. "Sony PS5 DualSense Controller")
5. confidence: Float between 0.0 and 1.0 representing identification confidence
6. visual_condition: Brief note on visible condition (e.g. "Worn thumbstick", "Cracked housing")

Return JSON strictly matching this schema:
{
  "category": "game_controller",
  "brand": "Sony",
  "model": "PlayStation 5 DualSense",
  "device_name": "Sony PlayStation 5 DualSense Controller",
  "confidence": 0.95,
  "visual_condition": "Front shell visible with worn thumbstick"
}
"""


class ProductIdentifier:
    """Identifies product brand, model, and category from a photo."""

    def __init__(self) -> None:
        """Initialize the product identifier with vision client."""
        self.vision_client = get_vision_client()

    async def identify_product(self, image_base64: str) -> dict[str, Any]:
        """Identify product details from base64 encoded photo."""
        try:
            response = await self.vision_client.vision_completion(
                system_prompt=SYSTEM_PROMPT,
                user_prompt="Analyze photo and identify device brand, model, and condition.",
                image_base64=image_base64,
            )

            parsed: dict[str, Any] = {}
            try:
                parsed = json.loads(response)
            except json.JSONDecodeError:
                match = re.search(r"\{.*\}", response, re.DOTALL)
                if match:
                    parsed = json.loads(match.group())

            # Normalize category to ProductCategory enum
            raw_cat = str(parsed.get("category", "")).lower().strip()
            cat_map = {
                "controller": ProductCategory.GAME_CONTROLLER,
                "game_controller": ProductCategory.GAME_CONTROLLER,
                "gamepad": ProductCategory.GAME_CONTROLLER,
                "headphones": ProductCategory.WIRED_HEADPHONES,
                "wired_headphones": ProductCategory.WIRED_HEADPHONES,
                "headset": ProductCategory.WIRED_HEADPHONES,
                "lamp": ProductCategory.LAMP,
                "table_lamp": ProductCategory.LAMP,
                "desk_lamp": ProductCategory.LAMP,
                "remote": ProductCategory.REMOTE_CONTROL,
                "remote_control": ProductCategory.REMOTE_CONTROL,
                "fan": ProductCategory.TABLE_FAN,
                "table_fan": ProductCategory.TABLE_FAN,
                "desk_fan": ProductCategory.TABLE_FAN,
                "keyboard": ProductCategory.KEYBOARD,
            }

            matched_category = cat_map.get(raw_cat, ProductCategory.GAME_CONTROLLER)

            device_name = str(parsed.get("device_name", "")).strip()
            if not device_name or device_name.lower() in ("unknown", "none"):
                brand = str(parsed.get("brand", "")).strip()
                model = str(parsed.get("model", "")).strip()
                if brand and brand.lower() != "unknown" and model and model.lower() != "unknown":
                    device_name = f"{brand} {model}"
                elif brand and brand.lower() != "unknown":
                    device_name = f"{brand} {matched_category.value.replace('_', ' ').title()}"
                else:
                    device_name = matched_category.value.replace("_", " ").title()

            return {
                "category": matched_category,
                "device_name": device_name,
                "brand": parsed.get("brand", "Unknown"),
                "model": parsed.get("model", "Unknown"),
                "confidence": float(parsed.get("confidence", 0.8)),
                "visual_condition": parsed.get("visual_condition"),
            }
        except Exception as e:
            logger.error(f"Error identifying product from photo: {e}")
            return {
                "category": ProductCategory.GAME_CONTROLLER,
                "device_name": "Game Controller",
                "brand": "Unknown",
                "model": "Unknown",
                "confidence": 0.5,
                "visual_condition": None,
            }


_identifier: ProductIdentifier | None = None


def get_product_identifier() -> ProductIdentifier:
    """Get the singleton ProductIdentifier instance."""
    global _identifier
    if _identifier is None:
        _identifier = ProductIdentifier()
    return _identifier
