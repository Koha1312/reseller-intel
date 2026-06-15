"""Tests for the deterministic deal-scoring engine."""
from __future__ import annotations

import pandas as pd

from src.analytics.deal_score import (
    SCORE_COLUMNS,
    compute_deal_scores,
    top_opportunities,
)


def _sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            # Cheap, new, authenticated, high demand -> should top the ranking.
            {
                "id": 1, "title": "Nike Air Jordan 1 OG", "brand": "Nike",
                "product_type": "shoes", "condition": "new", "price_value": 90.0,
                "watch_count": 50, "view_count": 800,
                "has_authenticity_proof": True, "has_original_box": True,
                "has_tags": True, "is_vintage": False,
            },
            # Overpriced, worn, no signals, no demand -> should rank low.
            {
                "id": 2, "title": "Nike Air Jordan 1", "brand": "Nike",
                "product_type": "shoes", "condition": "used-fair", "price_value": 220.0,
                "watch_count": 1, "view_count": 10,
                "has_authenticity_proof": False, "has_original_box": False,
                "has_tags": False, "is_vintage": False,
            },
            # Mid-market peer to set the median.
            {
                "id": 3, "title": "Nike Air Jordan 1 Mid", "brand": "Nike",
                "product_type": "shoes", "condition": "used-good", "price_value": 150.0,
                "watch_count": 10, "view_count": 120,
                "has_authenticity_proof": False, "has_original_box": True,
                "has_tags": False, "is_vintage": False,
            },
        ]
    )


def test_score_columns_added_and_bounded():
    scored = compute_deal_scores(_sample_df())
    for col in SCORE_COLUMNS:
        assert col in scored.columns
    assert scored["deal_score"].between(0, 100).all()


def test_cheap_clean_listing_beats_overpriced_worn():
    scored = compute_deal_scores(_sample_df()).set_index("id")
    assert scored.loc[1, "deal_score"] > scored.loc[2, "deal_score"]


def test_top_opportunities_is_sorted():
    scored = compute_deal_scores(_sample_df())
    top = top_opportunities(scored, n=2)
    assert len(top) == 2
    assert top.iloc[0]["deal_score"] >= top.iloc[1]["deal_score"]
    assert top.iloc[0]["id"] == 1  # the underpriced, authenticated, in-demand pair


def test_value_gap_reflects_discount():
    scored = compute_deal_scores(_sample_df()).set_index("id")
    # Listing 1 is priced below the Nike/shoes median -> positive value gap.
    assert scored.loc[1, "value_gap_pct"] > 0
    # Listing 2 is priced above it -> negative value gap.
    assert scored.loc[2, "value_gap_pct"] < 0


def test_sparse_peers_are_not_confident():
    # Two single-item, different-tier "watches" — no real comparables.
    df = pd.DataFrame(
        [
            {
                "id": 1, "title": "Casio G-Shock", "brand": "Casio",
                "product_type": "watch", "condition": "new", "price_value": 85.0,
                "watch_count": 5, "view_count": 50,
                "has_authenticity_proof": False, "has_original_box": True,
                "has_tags": False, "is_vintage": False,
            },
            {
                "id": 2, "title": "Rolex Submariner", "brand": "Rolex",
                "product_type": "watch", "condition": "used-good", "price_value": 12500.0,
                "watch_count": 20, "view_count": 300,
                "has_authenticity_proof": True, "has_original_box": True,
                "has_tags": False, "is_vintage": False,
            },
        ]
    )
    scored = compute_deal_scores(df).set_index("id")
    # Neither has >= MIN_PEERS comparables -> value must stay neutral, not claim a gap.
    assert not scored["value_confident"].any()
    assert scored["value_gap_pct"].isna().all()
    assert (scored["score_value"] == 0.5).all()
    # The key guarantee: with no real comparables we never claim a discount.
    assert "below median" not in scored.loc[1, "deal_reason"]
    assert "above median" not in scored.loc[2, "deal_reason"]


def test_sell_through_column_and_demand_blend():
    # Two Nike-shoes peers sold, one active -> group STR = 2/3.
    df = pd.DataFrame(
        [
            {"id": 1, "title": "Nike AF1", "brand": "Nike", "product_type": "shoes",
             "condition": "new", "price_value": 110.0, "watch_count": 10, "view_count": 100,
             "status": "active", "has_authenticity_proof": False, "has_original_box": True,
             "has_tags": True, "is_vintage": False},
            {"id": 2, "title": "Nike AF1", "brand": "Nike", "product_type": "shoes",
             "condition": "new", "price_value": 115.0, "watch_count": 20, "view_count": 200,
             "status": "sold", "has_authenticity_proof": False, "has_original_box": True,
             "has_tags": True, "is_vintage": False},
            {"id": 3, "title": "Nike AJ1", "brand": "Nike", "product_type": "shoes",
             "condition": "used-good", "price_value": 425.0, "watch_count": 5, "view_count": 60,
             "status": "sold", "has_authenticity_proof": False, "has_original_box": True,
             "has_tags": False, "is_vintage": False},
        ]
    )
    scored = compute_deal_scores(df).set_index("id")
    assert abs(scored.loc[1, "sell_through"] - 2 / 3) < 1e-9
    assert "fast mover" in scored.loc[1, "deal_reason"]


def test_empty_df_is_safe():
    empty = pd.DataFrame(
        columns=["id", "brand", "product_type", "condition", "price_value",
                 "watch_count", "view_count", "has_authenticity_proof",
                 "has_original_box", "has_tags", "is_vintage"]
    )
    scored = compute_deal_scores(empty)
    assert scored.empty
    assert "deal_score" in scored.columns
