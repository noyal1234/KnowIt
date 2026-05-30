import logging
from typing import Any

import httpx

from app.providers.errors import ProviderError, ProviderRetryableError

logger = logging.getLogger(__name__)


class OpenFoodFactsProvider:
    name = "open_food_facts"

    async def lookup(self, barcode: str) -> dict[str, Any] | None:
        url = f"https://world.openfoodfacts.org/api/v2/product/{barcode}.json"
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.get(url)
        except httpx.TimeoutException as exc:
            raise ProviderRetryableError("Open Food Facts request timed out") from exc
        except httpx.HTTPError as exc:
            raise ProviderError(f"Open Food Facts request failed: {exc}") from exc

        if resp.status_code == 404:
            return None
        if resp.status_code >= 500:
            raise ProviderRetryableError(f"Open Food Facts error: {resp.status_code}")
        if resp.status_code >= 400:
            raise ProviderError(f"Open Food Facts error: {resp.status_code}")

        data = resp.json()
        if data.get("status") != 1:
            return None
        product = data["product"]
        return {
            "name": product.get("product_name") or product.get("product_name_en") or "Unknown",
            "brand": product.get("brands"),
            "barcode": barcode,
            "ingredients_text": product.get("ingredients_text")
            or product.get("ingredients_text_en")
            or "",
            "image_url": product.get("image_url"),
        }
