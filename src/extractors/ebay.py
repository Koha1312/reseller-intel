"""eBay Browse API extractor.

Auth: OAuth2 client credentials flow (App ID + Cert ID → application token).
Docs: https://developer.ebay.com/api-docs/buy/browse/overview.html

Set EBAY_APP_ID and EBAY_CERT_ID in .env to enable.
"""
from __future__ import annotations

import base64
import time
from typing import Any

import httpx
from loguru import logger

from src.config import settings
from src.extractors.base import MarketplaceExtractor
from src.parser.schemas import ListingStatus, Money, RawListing, Seller

_ENV_HOSTS = {
    "PRODUCTION": {
        "api": "https://api.ebay.com",
        "oauth": "https://api.ebay.com/identity/v1/oauth2/token",
    },
    "SANDBOX": {
        "api": "https://api.sandbox.ebay.com",
        "oauth": "https://api.sandbox.ebay.com/identity/v1/oauth2/token",
    },
}

_DEFAULT_SCOPE = "https://api.ebay.com/oauth/api_scope"
_DEFAULT_MARKETPLACE = "EBAY_US"


class EbayExtractor(MarketplaceExtractor):
    """Pulls listings from eBay Browse API using OAuth2 client credentials."""

    def __init__(
        self,
        app_id: str | None = None,
        cert_id: str | None = None,
        environment: str | None = None,
        marketplace_id: str = _DEFAULT_MARKETPLACE,
        timeout: float = 30.0,
    ) -> None:
        self.app_id = app_id or settings.ebay_app_id
        self.cert_id = cert_id or settings.ebay_cert_id
        self.environment = (environment or settings.ebay_environment).upper()
        self.marketplace_id = marketplace_id

        if self.environment not in _ENV_HOSTS:
            raise ValueError(f"Invalid environment: {self.environment}. Must be PRODUCTION or SANDBOX.")

        if not self.app_id or not self.cert_id:
            raise ValueError(
                "Missing eBay credentials. Set EBAY_APP_ID and EBAY_CERT_ID in .env. "
                "Register at https://developer.ebay.com/"
            )

        self._hosts = _ENV_HOSTS[self.environment]
        self._http = httpx.Client(timeout=timeout)
        self._token: str | None = None
        self._token_expires_at: float = 0.0

    @property
    def platform(self) -> str:
        return "ebay"

    # ---- OAuth ----------------------------------------------------------

    def _get_token(self) -> str:
        """Return a valid OAuth token, refreshing if expired or near-expiry."""
        if self._token and time.time() < self._token_expires_at - 60:
            return self._token

        credentials = f"{self.app_id}:{self.cert_id}".encode()
        auth_header = base64.b64encode(credentials).decode()

        response = self._http.post(
            self._hosts["oauth"],
            headers={
                "Authorization": f"Basic {auth_header}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={"grant_type": "client_credentials", "scope": _DEFAULT_SCOPE},
        )
        response.raise_for_status()
        data = response.json()

        self._token = data["access_token"]
        self._token_expires_at = time.time() + int(data.get("expires_in", 7200))
        logger.debug("eBay OAuth token refreshed (expires in {}s)", data.get("expires_in"))
        return self._token

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._get_token()}",
            "X-EBAY-C-MARKETPLACE-ID": self.marketplace_id,
            "Content-Type": "application/json",
        }

    # ---- Public API -----------------------------------------------------

    def search(
        self,
        query: str,
        *,
        limit: int = 50,
        offset: int = 0,
        category_id: str | None = None,
    ) -> list[RawListing]:
        params: dict[str, Any] = {"q": query, "limit": min(limit, 200), "offset": offset}
        if category_id:
            params["category_ids"] = category_id

        url = f"{self._hosts['api']}/buy/browse/v1/item_summary/search"
        response = self._http.get(url, params=params, headers=self._headers())

        if response.status_code == 401:
            self._token = None
            response = self._http.get(url, params=params, headers=self._headers())

        response.raise_for_status()
        payload = response.json()
        return [self._map_summary(item) for item in payload.get("itemSummaries", [])]

    def get_item(self, listing_id: str) -> RawListing:
        url = f"{self._hosts['api']}/buy/browse/v1/item/{listing_id}"
        response = self._http.get(url, headers=self._headers())

        if response.status_code == 401:
            self._token = None
            response = self._http.get(url, headers=self._headers())

        response.raise_for_status()
        return self._map_full_item(response.json())

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> EbayExtractor:
        return self

    def __exit__(self, *exc_info: Any) -> None:
        self.close()

    # ---- Response mapping -----------------------------------------------

    def _map_summary(self, item: dict[str, Any]) -> RawListing:
        """Map an eBay itemSummary entry to our RawListing schema."""
        price = item.get("price", {})
        seller = item.get("seller", {})

        buying_options = item.get("buyingOptions", [])
        category_path = item.get("categories", [{}])
        category = category_path[0] if category_path else {}

        location = item.get("itemLocation", {})

        return RawListing(
            listing_id=item["itemId"],
            platform="ebay",
            title=item.get("title", ""),
            description=item.get("shortDescription"),
            price=Money(
                value=float(price.get("value", 0)),
                currency=price.get("currency", "USD"),
            ),
            seller=Seller(
                username=seller.get("username", "unknown"),
                feedback_percentage=_safe_float(seller.get("feedbackPercentage")),
                feedback_count=seller.get("feedbackScore"),
            ),
            condition_raw=item.get("condition", "Unknown"),
            category_name=category.get("categoryName"),
            category_id=category.get("categoryId"),
            image_url=(item.get("image") or {}).get("imageUrl"),
            item_url=item.get("itemWebUrl", ""),
            buying_options=buying_options,
            location_country=location.get("country"),
            status=ListingStatus.ACTIVE,
            watch_count=item.get("watchCount"),
        )

    def _map_full_item(self, item: dict[str, Any]) -> RawListing:
        """Map a full eBay item detail response to RawListing.

        Full responses include description (HTML) and richer metadata.
        """
        base = self._map_summary(item)

        description = item.get("description")
        if description:
            base = base.model_copy(update={"description": description})

        return base


def _safe_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
