"""Analytics helpers: pull listings from DB into pandas DataFrames + aggregations."""
from __future__ import annotations

import pandas as pd
from sqlalchemy import select

from src.storage.db import SessionLocal
from src.storage.models import Listing


_COLUMNS = [
    "id",
    "listing_id",
    "platform",
    "title",
    "price_value",
    "price_currency",
    "seller_username",
    "seller_feedback_pct",
    "condition_raw",
    "category_name",
    "item_url",
    "image_url",
    "buying_options",
    "location_country",
    "status",
    "listing_date",
    "watch_count",
    "view_count",
    "brand",
    "product_type",
    "model_name",
    "condition",
    "size",
    "color",
    "year",
    "estimated_retail_price_usd",
    "has_original_box",
    "has_tags",
    "has_authenticity_proof",
    "is_vintage",
    "key_features",
]


def load_listings_df() -> pd.DataFrame:
    """Return all listings as a pandas DataFrame."""
    with SessionLocal() as session:
        rows = session.execute(select(Listing)).scalars().all()
        records = [{col: getattr(row, col) for col in _COLUMNS} for row in rows]
    return pd.DataFrame(records, columns=_COLUMNS)


def brand_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Per-brand counts, avg + median price, total inventory value."""
    if df.empty:
        return pd.DataFrame(columns=["brand", "count", "avg_price", "median_price", "total_value"])

    grouped = (
        df.groupby(df["brand"].fillna("(unknown)"))
        .agg(
            count=("id", "size"),
            avg_price=("price_value", "mean"),
            median_price=("price_value", "median"),
            total_value=("price_value", "sum"),
        )
        .reset_index()
        .rename(columns={"brand": "brand"})
        .sort_values("count", ascending=False)
    )
    grouped["brand"] = grouped["brand"].astype(str)
    return grouped


def condition_distribution(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["condition", "count"])
    counts = df["condition"].fillna("(unparsed)").value_counts().reset_index()
    counts.columns = ["condition", "count"]
    return counts


def product_type_distribution(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["product_type", "count"])
    counts = df["product_type"].fillna("(unparsed)").value_counts().reset_index()
    counts.columns = ["product_type", "count"]
    return counts


def quality_signals_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Count how many listings advertise each quality signal."""
    signals = ["has_original_box", "has_tags", "has_authenticity_proof", "is_vintage"]
    rows = [{"signal": s, "count": int(df[s].fillna(False).sum())} for s in signals if s in df.columns]
    return pd.DataFrame(rows)


def sell_through_rate(df: pd.DataFrame, by: str = "brand") -> pd.DataFrame:
    """Sell-through rate (the reseller's #1 metric) grouped by `by`.

    STR = sold listings / total listings. A high rate means the segment moves
    fast — i.e. demand is strong relative to supply.
    """
    cols = [by, "sold", "total", "sell_through_pct"]
    if df.empty or "status" not in df.columns:
        return pd.DataFrame(columns=cols)

    work = df.copy()
    work["_sold"] = work["status"].fillna("").eq("sold")
    grouped = (
        work.groupby(work[by].fillna("(unknown)"))
        .agg(sold=("_sold", "sum"), total=("_sold", "size"))
        .reset_index()
    )
    grouped[by] = grouped[by].astype(str)
    grouped["sell_through_pct"] = (grouped["sold"] / grouped["total"] * 100).round(1)
    return grouped.sort_values("sell_through_pct", ascending=False)[cols]


def price_stats(df: pd.DataFrame) -> dict:
    if df.empty:
        return {"count": 0, "mean": 0.0, "median": 0.0, "min": 0.0, "max": 0.0, "total": 0.0}
    series = df["price_value"]
    return {
        "count": int(series.count()),
        "mean": float(series.mean()),
        "median": float(series.median()),
        "min": float(series.min()),
        "max": float(series.max()),
        "total": float(series.sum()),
    }
