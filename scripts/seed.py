"""Seed the database with mock listings parsed by the local LLM.

Run from project root:
    uv run python scripts/seed.py

This exercises the full pipeline:
    MockExtractor -> ListingParser (qwen3:4b) -> SQLite storage
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from loguru import logger

from src.extractors.mock import MockExtractor
from src.parser.llm_parser import ListingParser
from src.storage.db import get_session, init_db, upsert_listing


def main() -> None:
    logger.info("Initializing database")
    init_db()

    logger.info("Extracting listings from mock source")
    extractor = MockExtractor()
    raws = extractor.search(query="", limit=100)
    logger.info("Extracted {} listings", len(raws))

    logger.info("Parsing listings with LLM")
    parser = ListingParser()
    enriched = parser.parse_many(raws)

    logger.info("Persisting to database")
    parsed_ok = 0
    parsed_failed = 0
    with get_session() as session:
        for record in enriched:
            upsert_listing(session, record)
            if record.parsed is not None:
                parsed_ok += 1
            else:
                parsed_failed += 1

    logger.info("Done: {} parsed, {} failed", parsed_ok, parsed_failed)
    _print_summary()


def _print_summary() -> None:
    from sqlalchemy import select, func
    from src.storage.db import SessionLocal
    from src.storage.models import Listing

    with SessionLocal() as session:
        total = session.execute(select(func.count()).select_from(Listing)).scalar_one()

        by_brand = session.execute(
            select(Listing.brand, func.count(), func.avg(Listing.price_value))
            .group_by(Listing.brand)
            .order_by(func.count().desc())
        ).all()

        by_condition = session.execute(
            select(Listing.condition, func.count()).group_by(Listing.condition)
        ).all()

        print()
        print("=" * 70)
        print(f"  DATABASE SUMMARY  —  total listings: {total}")
        print("=" * 70)

        print("\n  By brand:")
        print(f"  {'brand':<25} {'count':>6} {'avg price':>12}")
        print(f"  {'-' * 25} {'-' * 6} {'-' * 12}")
        for brand, count, avg in by_brand:
            print(f"  {(brand or '(unknown)'):<25} {count:>6} {avg:>11.2f}")

        print("\n  By condition:")
        for cond, count in by_condition:
            print(f"  {(cond or '(unparsed)'):<15} {count:>3}")
        print()


if __name__ == "__main__":
    main()
