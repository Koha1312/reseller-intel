"""SQLAlchemy ORM models. One flat `listings` table holds raw + parsed fields."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Listing(Base):
    __tablename__ = "listings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    listing_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    platform: Mapped[str] = mapped_column(String(32), index=True)

    title: Mapped[str] = mapped_column(String(512))
    description: Mapped[str | None] = mapped_column(Text, default=None)

    price_value: Mapped[float]
    price_currency: Mapped[str] = mapped_column(String(8), default="USD")

    seller_username: Mapped[str] = mapped_column(String(128))
    seller_feedback_pct: Mapped[float | None] = mapped_column(default=None)
    seller_feedback_count: Mapped[int | None] = mapped_column(default=None)

    condition_raw: Mapped[str] = mapped_column(String(64), default="Unknown")
    category_name: Mapped[str | None] = mapped_column(String(128), default=None)
    category_id: Mapped[str | None] = mapped_column(String(64), default=None, index=True)
    image_url: Mapped[str | None] = mapped_column(String(512), default=None)
    item_url: Mapped[str] = mapped_column(String(512))
    buying_options: Mapped[list | None] = mapped_column(JSON, default=None)
    location_country: Mapped[str | None] = mapped_column(String(8), default=None)

    listing_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    status: Mapped[str] = mapped_column(String(16), default="active", index=True)

    watch_count: Mapped[int | None] = mapped_column(default=None)
    view_count: Mapped[int | None] = mapped_column(default=None)
    bid_count: Mapped[int | None] = mapped_column(default=None)

    brand: Mapped[str | None] = mapped_column(String(64), default=None, index=True)
    product_type: Mapped[str | None] = mapped_column(String(64), default=None, index=True)
    model_name: Mapped[str | None] = mapped_column(String(128), default=None)
    condition: Mapped[str | None] = mapped_column(String(16), default=None, index=True)
    size: Mapped[str | None] = mapped_column(String(32), default=None)
    color: Mapped[str | None] = mapped_column(String(64), default=None)
    material: Mapped[str | None] = mapped_column(String(64), default=None)
    year: Mapped[int | None] = mapped_column(default=None)
    estimated_retail_price_usd: Mapped[float | None] = mapped_column(default=None)

    has_original_box: Mapped[bool] = mapped_column(default=False)
    has_tags: Mapped[bool] = mapped_column(default=False)
    has_authenticity_proof: Mapped[bool] = mapped_column(default=False)
    is_vintage: Mapped[bool] = mapped_column(default=False)
    key_features: Mapped[list | None] = mapped_column(JSON, default=None)

    parsed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    parser_model: Mapped[str | None] = mapped_column(String(64), default=None)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    def __repr__(self) -> str:
        return f"<Listing {self.platform}:{self.listing_id} {self.title[:40]!r}>"
