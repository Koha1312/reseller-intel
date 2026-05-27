"""Database engine, session factory, and upsert helpers."""
from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from loguru import logger
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from src.config import settings
from src.parser.schemas import EnrichedListing
from src.storage.models import Base, Listing


def _ensure_sqlite_dir(url: str) -> None:
    """Make sure parent dir for SQLite file exists."""
    if url.startswith("sqlite:///") and not url.startswith("sqlite:////"):
        relative = url.removeprefix("sqlite:///")
        Path(relative).parent.mkdir(parents=True, exist_ok=True)


_ensure_sqlite_dir(settings.database_url)

engine = create_engine(settings.database_url, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def init_db() -> None:
    """Create tables if they don't yet exist."""
    Base.metadata.create_all(bind=engine)
    logger.info("Initialized DB at {}", settings.database_url)


@contextmanager
def get_session() -> Iterator[Session]:
    """Yields a session that commits on success and rolls back on exception."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def upsert_listing(session: Session, enriched: EnrichedListing) -> Listing:
    """Insert listing or update existing row matched on (platform, listing_id)."""
    raw = enriched.raw
    parsed = enriched.parsed

    stmt = select(Listing).where(
        Listing.platform == raw.platform,
        Listing.listing_id == raw.listing_id,
    )
    row = session.execute(stmt).scalar_one_or_none()

    fields = _flatten(enriched)

    if row is None:
        row = Listing(**fields)
        session.add(row)
    else:
        for key, value in fields.items():
            setattr(row, key, value)

    return row


def _flatten(enriched: EnrichedListing) -> dict:
    """Flatten EnrichedListing into kwargs for the Listing model."""
    raw = enriched.raw
    parsed = enriched.parsed

    data: dict = {
        "listing_id": raw.listing_id,
        "platform": raw.platform,
        "title": raw.title,
        "description": raw.description,
        "price_value": raw.price.value,
        "price_currency": raw.price.currency,
        "seller_username": raw.seller.username,
        "seller_feedback_pct": raw.seller.feedback_percentage,
        "seller_feedback_count": raw.seller.feedback_count,
        "condition_raw": raw.condition_raw,
        "category_name": raw.category_name,
        "category_id": raw.category_id,
        "image_url": raw.image_url,
        "item_url": raw.item_url,
        "buying_options": raw.buying_options or None,
        "location_country": raw.location_country,
        "listing_date": raw.listing_date,
        "end_date": raw.end_date,
        "status": raw.status.value,
        "watch_count": raw.watch_count,
        "view_count": raw.view_count,
        "bid_count": raw.bid_count,
        "parsed_at": enriched.parsed_at,
        "parser_model": enriched.parser_model,
    }

    if parsed is not None:
        data.update(
            {
                "brand": parsed.brand,
                "product_type": parsed.product_type,
                "model_name": parsed.model_name,
                "condition": parsed.condition.value,
                "size": parsed.size,
                "color": parsed.color,
                "material": parsed.material,
                "year": parsed.year,
                "estimated_retail_price_usd": parsed.estimated_retail_price_usd,
                "has_original_box": parsed.has_original_box,
                "has_tags": parsed.has_tags,
                "has_authenticity_proof": parsed.has_authenticity_proof,
                "is_vintage": parsed.is_vintage,
                "key_features": parsed.key_features or None,
            }
        )

    return data
