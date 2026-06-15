"""Profit-after-fees estimator.

Borrows the core idea from Vendoo / Underpriced AI: a listing's headline price
is not what you keep. This estimates the take-home profit of *flipping* a listing
— buy at its price, resell at a realistic target, minus marketplace fees and
shipping — and the return on that buy (ROI).
"""
from __future__ import annotations

import pandas as pd

# Marketplace final-value fee rates (approximate, 2026). Override per call as needed.
PLATFORM_FEE_PCT = {
    "ebay": 0.1325,
    "poshmark": 0.20,
    "mercari": 0.10,
    "depop": 0.10,
    "etsy": 0.065,
}
DEFAULT_FEE_PCT = 0.13
DEFAULT_SHIPPING_USD = 8.0

PROFIT_COLUMNS = [
    "resale_target",
    "fee_pct",
    "est_fee_usd",
    "est_net_profit_usd",
    "est_roi_pct",
]


def _resale_target(df: pd.DataFrame) -> pd.Series:
    """Best estimate of resale value: parsed retail price if it beats the asking
    price, else the comparable market median (`ref_price`), else the price itself.
    """
    price = df["price_value"]
    target = df.get("estimated_retail_price_usd")
    if target is None:
        target = pd.Series(pd.NA, index=df.index, dtype="float64")

    fallback = df["ref_price"] if "ref_price" in df.columns else price
    # Use retail only when it's present and actually above the asking price.
    target = target.where(target.notna() & (target > price), fallback)
    return target.fillna(price)


def estimate_profit(
    df: pd.DataFrame,
    *,
    fee_pct: float | None = None,
    shipping_usd: float = DEFAULT_SHIPPING_USD,
) -> pd.DataFrame:
    """Append profit columns (see PROFIT_COLUMNS) to a copy of `df`.

    fee_pct: override the marketplace fee for every row; if None, look it up per
    listing from `platform` (falling back to DEFAULT_FEE_PCT).
    """
    if df.empty:
        return df.assign(**{col: pd.Series(dtype="float64") for col in PROFIT_COLUMNS})

    out = df.copy()

    if fee_pct is not None:
        out["fee_pct"] = float(fee_pct)
    else:
        out["fee_pct"] = (
            out["platform"].astype(str).str.lower().map(PLATFORM_FEE_PCT).fillna(DEFAULT_FEE_PCT)
        )

    out["resale_target"] = _resale_target(out)
    out["est_fee_usd"] = out["resale_target"] * out["fee_pct"]
    out["est_net_profit_usd"] = (
        out["resale_target"] - out["est_fee_usd"] - shipping_usd - out["price_value"]
    )
    out["est_roi_pct"] = out["est_net_profit_usd"] / out["price_value"].replace(0, pd.NA)
    return out
