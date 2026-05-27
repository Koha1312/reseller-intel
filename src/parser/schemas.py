"""Pydantic schemas for raw API data, LLM-parsed fields, and the combined enriched listing."""
from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class Condition(str, Enum):
    NEW = "new"
    LIKE_NEW = "like-new"
    USED_GOOD = "used-good"
    USED_FAIR = "used-fair"
    FOR_PARTS = "for-parts"
    UNKNOWN = "unknown"


class ListingStatus(str, Enum):
    ACTIVE = "active"
    SOLD = "sold"
    ENDED = "ended"
    UNKNOWN = "unknown"


class Money(BaseModel):
    value: float
    currency: str = "USD"


class Seller(BaseModel):
    username: str
    feedback_percentage: float | None = None
    feedback_count: int | None = None


class RawListing(BaseModel):
    """Raw listing record from a marketplace API.

    Shape mirrors eBay Browse API output so swapping mock → real API is a no-op
    for downstream consumers (parser, storage).
    """

    listing_id: str
    platform: str = Field(description="e.g. 'ebay', 'poshmark'")
    title: str
    description: str | None = None
    price: Money
    seller: Seller
    condition_raw: str = Field(default="Unknown", description="Platform's own condition label")
    category_name: str | None = None
    category_id: str | None = None
    image_url: str | None = None
    item_url: str
    buying_options: list[str] = Field(default_factory=list)
    location_country: str | None = None
    listing_date: datetime | None = None
    end_date: datetime | None = None
    status: ListingStatus = ListingStatus.ACTIVE

    # Engagement signals (when available)
    watch_count: int | None = None
    view_count: int | None = None
    bid_count: int | None = None


class ParsedListing(BaseModel):
    """Structured fields the LLM extracts from RawListing.title + description.

    Field descriptions double as prompt hints — keep them precise and actionable.
    """

    brand: str | None = Field(
        default=None,
        description="Brand name exactly as it appears (e.g. 'Nike', 'Louis Vuitton'). Null if generic/unbranded.",
    )
    product_type: str = Field(
        description="Short product category in lowercase singular form (e.g. 'shoes', 'jacket', 'watch', 'handbag').",
    )
    model_name: str | None = Field(
        default=None,
        description="Specific model/line, excluding brand (e.g. 'Air Jordan 1 Retro High OG', 'Speedy 25').",
    )
    condition: Condition = Field(
        description="Map listing condition to one of: new, like-new, used-good, used-fair, for-parts, unknown.",
    )
    size: str | None = Field(
        default=None,
        description="Size if applicable, kept as written (e.g. '10.5', 'M', '32x30').",
    )
    color: str | None = Field(default=None, description="Primary color(s), comma-separated if multiple.")
    material: str | None = Field(default=None, description="Primary material if explicitly mentioned.")
    year: int | None = Field(default=None, description="Year of release/manufacture if mentioned.")
    estimated_retail_price_usd: float | None = Field(
        default=None,
        description="Original MSRP in USD if mentioned or strongly implied. Null if unknown.",
    )

    has_original_box: bool = Field(
        default=False,
        description="True if listing mentions original packaging/box included.",
    )
    has_tags: bool = Field(
        default=False, description="True if listing mentions tags still attached / NWT / deadstock."
    )
    has_authenticity_proof: bool = Field(
        default=False,
        description="True if mentions COA, authentication, receipt, serial number verified, etc.",
    )
    is_vintage: bool = Field(
        default=False, description="True if listing is described as vintage, retro, or pre-2000."
    )

    key_features: list[str] = Field(
        default_factory=list,
        description="Up to 5 short notable attribute phrases (e.g. 'limited edition', 'sample sale').",
    )


class EnrichedListing(BaseModel):
    """Full listing record: raw API data + LLM-parsed fields + parsing metadata."""

    raw: RawListing
    parsed: ParsedListing | None = None
    parsed_at: datetime | None = None
    parser_model: str | None = None
