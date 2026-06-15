"""Tests for the profit-after-fees estimator and sell-through rate."""
from __future__ import annotations

import pandas as pd

from src.analytics.profit import (
    DEFAULT_FEE_PCT,
    PROFIT_COLUMNS,
    estimate_profit,
)
from src.analytics.queries import sell_through_rate


def _df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "id": 1, "platform": "ebay", "brand": "Nike", "product_type": "shoes",
                "price_value": 100.0, "estimated_retail_price_usd": 200.0,
                "ref_price": 180.0, "status": "active",
            },
            {
                "id": 2, "platform": "poshmark", "brand": "Nike", "product_type": "shoes",
                "price_value": 100.0, "estimated_retail_price_usd": None,
                "ref_price": 140.0, "status": "sold",
            },
        ]
    )


def test_profit_columns_added():
    out = estimate_profit(_df())
    for col in PROFIT_COLUMNS:
        assert col in out.columns


def test_platform_fees_are_looked_up():
    out = estimate_profit(_df()).set_index("id")
    assert out.loc[1, "fee_pct"] == 0.1325  # ebay
    assert out.loc[2, "fee_pct"] == 0.20     # poshmark


def test_fee_override_applies_to_all_rows():
    out = estimate_profit(_df(), fee_pct=0.10)
    assert (out["fee_pct"] == 0.10).all()


def test_profit_math_is_correct():
    # Row 1: retail $200 > price $100 -> resell target 200.
    # net = 200 - (200*0.1325) - 8 shipping - 100 buy = 65.5
    out = estimate_profit(_df(), shipping_usd=8.0).set_index("id")
    assert round(out.loc[1, "est_net_profit_usd"], 2) == 65.50
    assert round(out.loc[1, "est_roi_pct"], 4) == 0.6550


def test_resale_target_falls_back_to_market_median():
    # Row 2 has no retail price -> uses ref_price (140) as the resale target.
    out = estimate_profit(_df()).set_index("id")
    assert out.loc[2, "resale_target"] == 140.0


def test_sell_through_rate():
    str_df = sell_through_rate(_df(), by="brand").set_index("brand")
    # Nike: 1 sold of 2 total -> 50%.
    assert str_df.loc["Nike", "sold"] == 1
    assert str_df.loc["Nike", "total"] == 2
    assert str_df.loc["Nike", "sell_through_pct"] == 50.0


def test_default_fee_constant_sane():
    assert 0.0 < DEFAULT_FEE_PCT < 0.30


def test_empty_df_is_safe():
    empty = pd.DataFrame(columns=["platform", "price_value", "ref_price"])
    out = estimate_profit(empty)
    assert out.empty
    assert "est_net_profit_usd" in out.columns
