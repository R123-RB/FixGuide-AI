"""iFixit API client for retrieving repair guides and step reference images."""

from __future__ import annotations

import logging
import os
from typing import Any, cast

import httpx

from fixguide.config import get_settings

logger = logging.getLogger(__name__)


class IFixitService:
    """Service to interact with iFixit API 2.0 for guide search and reference media."""

    def __init__(self) -> None:
        """Initialize iFixit service with settings and in-memory caches."""
        self.settings = get_settings()
        self.api_key = os.getenv("IFIXIT_API_KEY", "") or getattr(
            self.settings, "ifixit_api_key", ""
        )
        self.base_url = "https://www.ifixit.com/api/2.0"
        self._guide_cache: dict[int, dict[str, Any]] = {}
        self._search_cache: dict[str, int | None] = {}

    def _get_headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def search_guide(self, query: str) -> int | None:
        """Search for a guide ID matching the device or query."""
        clean_query = query.strip()
        if not clean_query:
            return None

        if clean_query in self._search_cache:
            return self._search_cache[clean_query]

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{self.base_url}/search/{clean_query}",
                    params={"filter": "guide"},
                    headers=self._get_headers(),
                )
                if resp.status_code == 200:
                    data = resp.json()
                    results = data.get("results", [])
                    if results:
                        guide_id = int(results[0].get("guideid", 0))
                        if guide_id:
                            self._search_cache[clean_query] = guide_id
                            return guide_id
        except Exception as e:
            logger.warning(f"Failed to search iFixit guides for '{clean_query}': {e}")

        self._search_cache[clean_query] = None
        return None

    async def get_guide(self, guide_id: int) -> dict[str, Any] | None:
        """Fetch full guide with steps and images."""
        if guide_id in self._guide_cache:
            return self._guide_cache[guide_id]

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    f"{self.base_url}/guides/{guide_id}",
                    headers=self._get_headers(),
                )
                if resp.status_code == 200:
                    guide = cast(dict[str, Any], resp.json())
                    self._guide_cache[guide_id] = guide
                    return guide
        except Exception as e:
            logger.warning(f"Failed to fetch iFixit guide {guide_id}: {e}")

        return None

    async def get_step_images(
        self, device_or_query: str, step_number: int
    ) -> list[str]:
        """Get reference images for a specific repair step from an iFixit guide."""
        guide_id = await self.search_guide(device_or_query)
        if not guide_id:
            return []

        guide = await self.get_guide(guide_id)
        if not guide:
            return []

        steps = guide.get("steps", [])
        if not steps:
            return []

        idx = min(max(0, step_number - 1), len(steps) - 1)
        step = steps[idx]
        media_items = step.get("media", {}).get("data", [])

        images: list[str] = []
        for m in media_items:
            url = m.get("standard") or m.get("medium") or m.get("large")
            if url and url not in images:
                images.append(str(url))

        return images


_ifixit_service: IFixitService | None = None


def get_ifixit_service() -> IFixitService:
    """Get the singleton IFixitService instance."""
    global _ifixit_service
    if _ifixit_service is None:
        _ifixit_service = IFixitService()
    return _ifixit_service
