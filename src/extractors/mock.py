"""Mock extractor with realistic eBay-shaped fixture data.

Lets us build and test the full pipeline (extraction → parsing → storage →
analytics) before real platform credentials are available.

Swap to a real extractor by changing one line in scripts/seed.py.
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

from src.extractors.base import MarketplaceExtractor
from src.parser.schemas import (
    ListingStatus,
    Money,
    RawListing,
    Seller,
)

_NOW = datetime.now(timezone.utc)


def _days_ago(n: float) -> datetime:
    return _NOW - timedelta(days=n)


_FIXTURES: list[RawListing] = [
    RawListing(
        listing_id="mock-ebay-001",
        platform="ebay",
        title="Nike Air Jordan 1 Retro High OG 'Chicago' 2022 Men's 10.5",
        description=(
            "Worn maybe 5 times. OG all (box, extra laces, hangtag). "
            "Minor crease on toe box, no major scuffs. Retail was $180. "
            "Smoke-free home. Ships double-boxed next day."
        ),
        price=Money(value=425.00, currency="USD"),
        seller=Seller(username="sneakerhead_atl", feedback_percentage=99.8, feedback_count=1242),
        condition_raw="Pre-Owned",
        category_name="Athletic Shoes",
        category_id="15709",
        image_url="https://i.ebayimg.com/images/mock/aj1-chicago.jpg",
        item_url="https://www.ebay.com/itm/mock-ebay-001",
        buying_options=["FIXED_PRICE", "BEST_OFFER"],
        location_country="US",
        listing_date=_days_ago(3),
        status=ListingStatus.ACTIVE,
        watch_count=37,
        view_count=412,
    ),
    RawListing(
        listing_id="mock-ebay-002",
        platform="ebay",
        title="BRAND NEW Nike Air Force 1 '07 Triple White Mens 11 DS",
        description="DEADSTOCK. Never worn. 100% authentic. Tags + box included. Fast shipping!",
        price=Money(value=110.00, currency="USD"),
        seller=Seller(username="freshkicks_nyc", feedback_percentage=100.0, feedback_count=580),
        condition_raw="New with box",
        category_name="Athletic Shoes",
        category_id="15709",
        image_url="https://i.ebayimg.com/images/mock/af1-white.jpg",
        item_url="https://www.ebay.com/itm/mock-ebay-002",
        buying_options=["FIXED_PRICE"],
        location_country="US",
        listing_date=_days_ago(1),
        status=ListingStatus.ACTIVE,
        watch_count=12,
        view_count=88,
    ),
    RawListing(
        listing_id="mock-ebay-003",
        platform="ebay",
        title="Louis Vuitton Speedy 25 Monogram Canvas Handbag - Authentic",
        description=(
            "Beautiful pre-owned Speedy 25 in classic monogram canvas. "
            "Date code SP0073 (France, 2003). Some patina on the leather handles "
            "consistent with age. Interior clean. Comes with dust bag. "
            "Authenticated by Entrupy — certificate included. No box."
        ),
        price=Money(value=895.00, currency="USD"),
        seller=Seller(username="luxe_resale_co", feedback_percentage=99.5, feedback_count=4210),
        condition_raw="Pre-Owned",
        category_name="Women's Handbags",
        category_id="169291",
        image_url="https://i.ebayimg.com/images/mock/lv-speedy.jpg",
        item_url="https://www.ebay.com/itm/mock-ebay-003",
        buying_options=["FIXED_PRICE", "BEST_OFFER"],
        location_country="US",
        listing_date=_days_ago(7),
        status=ListingStatus.ACTIVE,
        watch_count=64,
        view_count=901,
    ),
    RawListing(
        listing_id="mock-ebay-004",
        platform="ebay",
        title="Rolex Submariner Date 116610LN Black 40mm 2019 Full Set",
        description=(
            "2019 Rolex Submariner 116610LN. Full set: original box, papers, "
            "warranty card dated 03/2019, hangtag, polishing cloth. "
            "Serviced by Rolex AD May 2024. Excellent condition, very light "
            "desk-diving marks on clasp only. Bezel mint. Movement runs +1s/day."
        ),
        price=Money(value=12500.00, currency="USD"),
        seller=Seller(username="watchworks_intl", feedback_percentage=100.0, feedback_count=87),
        condition_raw="Pre-Owned",
        category_name="Wristwatches",
        category_id="31387",
        image_url="https://i.ebayimg.com/images/mock/rolex-sub.jpg",
        item_url="https://www.ebay.com/itm/mock-ebay-004",
        buying_options=["FIXED_PRICE", "BEST_OFFER"],
        location_country="CH",
        listing_date=_days_ago(12),
        status=ListingStatus.ACTIVE,
        watch_count=210,
        view_count=3812,
    ),
    RawListing(
        listing_id="mock-ebay-005",
        platform="ebay",
        title="Vintage Levi's 501 Big E Redline Selvedge Denim Jacket 70s Type III",
        description=(
            "Authentic vintage Levi's Type III trucker, BIG E tab, redline "
            "selvedge interior, single stitch. Tagged size 42 fits like modern L. "
            "Honest wear, perfect fades, no holes or repairs. Made in USA."
        ),
        price=Money(value=340.00, currency="USD"),
        seller=Seller(username="dustbowl_vintage", feedback_percentage=99.2, feedback_count=2103),
        condition_raw="Pre-Owned",
        category_name="Men's Coats & Jackets",
        category_id="57988",
        image_url="https://i.ebayimg.com/images/mock/levis-bigE.jpg",
        item_url="https://www.ebay.com/itm/mock-ebay-005",
        buying_options=["FIXED_PRICE", "AUCTION"],
        location_country="US",
        listing_date=_days_ago(2),
        status=ListingStatus.ACTIVE,
        watch_count=19,
        view_count=287,
        bid_count=4,
    ),
    RawListing(
        listing_id="mock-ebay-006",
        platform="ebay",
        title="Supreme Box Logo Hoodie FW21 Black Size Large BOGO NEW WITH TAGS",
        description="NWT. 100% authentic, bought from Supreme NYC. Receipt included.",
        price=Money(value=620.00, currency="USD"),
        seller=Seller(username="hypebeast_supply", feedback_percentage=98.7, feedback_count=312),
        condition_raw="New with tags",
        category_name="Men's Hoodies & Sweatshirts",
        category_id="155183",
        image_url="https://i.ebayimg.com/images/mock/supreme-bogo.jpg",
        item_url="https://www.ebay.com/itm/mock-ebay-006",
        buying_options=["FIXED_PRICE"],
        location_country="US",
        listing_date=_days_ago(5),
        status=ListingStatus.ACTIVE,
        watch_count=44,
        view_count=620,
    ),
    RawListing(
        listing_id="mock-ebay-007",
        platform="ebay",
        title="adidas Yeezy Boost 350 V2 Zebra CP9654 Sz 9 USED",
        description=(
            "Worn quite a bit, sole has wear (see pics), boost still bouncy. "
            "No box. Insoles original. Honest pricing — these are beaters but "
            "still fire."
        ),
        price=Money(value=145.00, currency="USD"),
        seller=Seller(username="kicksforcheap", feedback_percentage=97.4, feedback_count=1809),
        condition_raw="Pre-Owned",
        category_name="Athletic Shoes",
        category_id="15709",
        image_url="https://i.ebayimg.com/images/mock/yeezy-zebra.jpg",
        item_url="https://www.ebay.com/itm/mock-ebay-007",
        buying_options=["FIXED_PRICE", "BEST_OFFER"],
        location_country="US",
        listing_date=_days_ago(9),
        status=ListingStatus.ACTIVE,
        watch_count=8,
        view_count=143,
    ),
    RawListing(
        listing_id="mock-ebay-008",
        platform="ebay",
        title="Hermes Twilly Silk Scarf 'Della Cavalleria' Rose Pink NEW IN BOX",
        description=(
            "Brand new, never worn. Original orange box, ribbon, and care card. "
            "Purchased from Hermes boutique London. 100% silk twill, made in France."
        ),
        price=Money(value=255.00, currency="EUR"),
        seller=Seller(username="parisienne_lux", feedback_percentage=100.0, feedback_count=156),
        condition_raw="New with tags",
        category_name="Women's Scarves & Wraps",
        category_id="45238",
        image_url="https://i.ebayimg.com/images/mock/hermes-twilly.jpg",
        item_url="https://www.ebay.com/itm/mock-ebay-008",
        buying_options=["FIXED_PRICE"],
        location_country="FR",
        listing_date=_days_ago(4),
        status=ListingStatus.ACTIVE,
        watch_count=22,
        view_count=341,
    ),
    RawListing(
        listing_id="mock-ebay-009",
        platform="ebay",
        title="Goyard Saint Louis PM Tote Black Tan Authentic w/ Dust Bag",
        description=(
            "Pre-owned, light interior wear. Exterior chevron print vibrant. "
            "Comes with original dust bag and pouch. No card. Authenticated."
        ),
        price=Money(value=1180.00, currency="USD"),
        seller=Seller(username="bagcollector_99", feedback_percentage=99.9, feedback_count=8001),
        condition_raw="Pre-Owned",
        category_name="Women's Handbags",
        category_id="169291",
        image_url="https://i.ebayimg.com/images/mock/goyard-stlouis.jpg",
        item_url="https://www.ebay.com/itm/mock-ebay-009",
        buying_options=["FIXED_PRICE", "BEST_OFFER"],
        location_country="US",
        listing_date=_days_ago(6),
        status=ListingStatus.ACTIVE,
        watch_count=51,
        view_count=771,
    ),
    RawListing(
        listing_id="mock-ebay-010",
        platform="ebay",
        title="Casio G-Shock GA-2100-1A1 Casioak Black New",
        description="Brand new in box. 200m water resist. MSRP $99.",
        price=Money(value=85.00, currency="USD"),
        seller=Seller(username="watch_basics", feedback_percentage=99.1, feedback_count=2200),
        condition_raw="New with box",
        category_name="Wristwatches",
        category_id="31387",
        image_url="https://i.ebayimg.com/images/mock/casioak.jpg",
        item_url="https://www.ebay.com/itm/mock-ebay-010",
        buying_options=["FIXED_PRICE"],
        location_country="US",
        listing_date=_days_ago(0.5),
        status=ListingStatus.ACTIVE,
        watch_count=3,
        view_count=29,
    ),
    RawListing(
        listing_id="mock-ebay-011",
        platform="ebay",
        title="Off-White x Nike Air Jordan 1 'UNC' Size 9.5 WORN",
        description=(
            "OG Off-White Jordan 1 UNC colorway. Worn a handful of times — "
            "the famous orange tag is intact but slightly curled. Box has some "
            "shelf wear. No receipt. 1000% authentic, will provide additional pics."
        ),
        price=Money(value=2850.00, currency="USD"),
        seller=Seller(username="grail_market", feedback_percentage=98.9, feedback_count=412),
        condition_raw="Pre-Owned",
        category_name="Athletic Shoes",
        category_id="15709",
        image_url="https://i.ebayimg.com/images/mock/ow-jordan-unc.jpg",
        item_url="https://www.ebay.com/itm/mock-ebay-011",
        buying_options=["FIXED_PRICE", "BEST_OFFER"],
        location_country="US",
        listing_date=_days_ago(10),
        status=ListingStatus.ACTIVE,
        watch_count=98,
        view_count=2104,
    ),
    RawListing(
        listing_id="mock-ebay-012",
        platform="ebay",
        title="Coach Bifold Wallet Brown Leather Mens — Used",
        description="Used coach wallet, brown leather, holds 6 cards plus billfold. Some wear on edges.",
        price=Money(value=28.00, currency="USD"),
        seller=Seller(username="moms_attic_finds", feedback_percentage=96.5, feedback_count=44),
        condition_raw="Pre-Owned",
        category_name="Men's Wallets",
        category_id="2996",
        image_url="https://i.ebayimg.com/images/mock/coach-wallet.jpg",
        item_url="https://www.ebay.com/itm/mock-ebay-012",
        buying_options=["FIXED_PRICE", "BEST_OFFER"],
        location_country="US",
        listing_date=_days_ago(14),
        status=ListingStatus.ACTIVE,
        watch_count=2,
        view_count=38,
    ),
    # --- Recently SOLD comps (give sell-through rate real signal per segment) ---
    RawListing(
        listing_id="mock-ebay-101",
        platform="ebay",
        title="Nike Air Force 1 '07 Triple White Mens 11 New",
        description="Brand new, never worn. Box + tags included. 100% authentic.",
        price=Money(value=115.00, currency="USD"),
        seller=Seller(username="freshkicks_nyc", feedback_percentage=100.0, feedback_count=585),
        condition_raw="New with box",
        category_name="Athletic Shoes",
        category_id="15709",
        item_url="https://www.ebay.com/itm/mock-ebay-101",
        buying_options=["FIXED_PRICE"],
        location_country="US",
        listing_date=_days_ago(11),
        end_date=_days_ago(3),
        status=ListingStatus.SOLD,
        watch_count=21,
        view_count=240,
    ),
    RawListing(
        listing_id="mock-ebay-102",
        platform="ebay",
        title="Nike Air Jordan 1 Retro High OG 'Chicago' 2022 Mens 10",
        description="OG all, box and laces. Worn twice, near deadstock. Authentic.",
        price=Money(value=440.00, currency="USD"),
        seller=Seller(username="sneakerhead_atl", feedback_percentage=99.8, feedback_count=1250),
        condition_raw="Pre-Owned",
        category_name="Athletic Shoes",
        category_id="15709",
        item_url="https://www.ebay.com/itm/mock-ebay-102",
        buying_options=["FIXED_PRICE", "BEST_OFFER"],
        location_country="US",
        listing_date=_days_ago(15),
        end_date=_days_ago(5),
        status=ListingStatus.SOLD,
        watch_count=44,
        view_count=520,
    ),
    RawListing(
        listing_id="mock-ebay-103",
        platform="ebay",
        title="Louis Vuitton Speedy 25 Monogram Canvas Handbag Authentic",
        description="Pre-owned Speedy 25, monogram canvas, light patina. Dust bag. Authenticated.",
        price=Money(value=920.00, currency="USD"),
        seller=Seller(username="luxe_resale_co", feedback_percentage=99.5, feedback_count=4220),
        condition_raw="Pre-Owned",
        category_name="Women's Handbags",
        category_id="169291",
        item_url="https://www.ebay.com/itm/mock-ebay-103",
        buying_options=["FIXED_PRICE", "BEST_OFFER"],
        location_country="US",
        listing_date=_days_ago(20),
        end_date=_days_ago(8),
        status=ListingStatus.SOLD,
        watch_count=70,
        view_count=980,
    ),
    RawListing(
        listing_id="mock-ebay-104",
        platform="ebay",
        title="Casio G-Shock GA-2100-1A1 Casioak Black New In Box",
        description="Brand new in box. 200m water resist. MSRP $99.",
        price=Money(value=92.00, currency="USD"),
        seller=Seller(username="watch_basics", feedback_percentage=99.1, feedback_count=2210),
        condition_raw="New with box",
        category_name="Wristwatches",
        category_id="31387",
        item_url="https://www.ebay.com/itm/mock-ebay-104",
        buying_options=["FIXED_PRICE"],
        location_country="US",
        listing_date=_days_ago(9),
        end_date=_days_ago(2),
        status=ListingStatus.SOLD,
        watch_count=9,
        view_count=110,
    ),
    RawListing(
        listing_id="mock-ebay-105",
        platform="ebay",
        title="Supreme Box Logo Hoodie FW21 Black Size Large NEW WITH TAGS",
        description="NWT. 100% authentic from Supreme NYC. Receipt included.",
        price=Money(value=650.00, currency="USD"),
        seller=Seller(username="hypebeast_supply", feedback_percentage=98.7, feedback_count=320),
        condition_raw="New with tags",
        category_name="Men's Hoodies & Sweatshirts",
        category_id="155183",
        item_url="https://www.ebay.com/itm/mock-ebay-105",
        buying_options=["FIXED_PRICE"],
        location_country="US",
        listing_date=_days_ago(13),
        end_date=_days_ago(4),
        status=ListingStatus.SOLD,
        watch_count=52,
        view_count=700,
    ),
    RawListing(
        listing_id="mock-ebay-106",
        platform="ebay",
        title="adidas Yeezy Boost 350 V2 Zebra CP9654 Sz 9 Pre-Owned",
        description="Worn a few times, boost intact, minor sole wear. No box.",
        price=Money(value=160.00, currency="USD"),
        seller=Seller(username="kicksforcheap", feedback_percentage=97.4, feedback_count=1820),
        condition_raw="Pre-Owned",
        category_name="Athletic Shoes",
        category_id="15709",
        item_url="https://www.ebay.com/itm/mock-ebay-106",
        buying_options=["FIXED_PRICE", "BEST_OFFER"],
        location_country="US",
        listing_date=_days_ago(16),
        end_date=_days_ago(6),
        status=ListingStatus.SOLD,
        watch_count=14,
        view_count=205,
    ),
]


class MockExtractor(MarketplaceExtractor):
    """Returns fixture data shaped like eBay Browse API responses."""

    @property
    def platform(self) -> str:
        return "ebay"

    def search(
        self,
        query: str,
        *,
        limit: int = 50,
        offset: int = 0,
        category_id: str | None = None,
    ) -> list[RawListing]:
        results = _FIXTURES

        if query and query.strip():
            q = query.lower().strip()
            results = [r for r in results if q in r.title.lower() or q in (r.description or "").lower()]

        if category_id:
            results = [r for r in results if r.category_id == category_id]

        return results[offset : offset + limit]

    def get_item(self, listing_id: str) -> RawListing:
        for r in _FIXTURES:
            if r.listing_id == listing_id:
                return r
        raise ValueError(f"Listing not found in fixtures: {listing_id}")

    def sample(self, n: int = 10, *, seed: int | None = None) -> list[RawListing]:
        """Test helper: return n random fixtures."""
        rng = random.Random(seed)
        return rng.sample(_FIXTURES, min(n, len(_FIXTURES)))
