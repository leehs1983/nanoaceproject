from __future__ import annotations

from collections.abc import Iterable

import pandas as pd


def apply_filters(
    frame: pd.DataFrame,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
    facilities: Iterable[str] | None = None,
    facility_units: Iterable[str] | None = None,
    pollutant: str | None = None,
) -> pd.DataFrame:
    """전역 필터를 적용한다."""
    mask = frame["date"].between(pd.Timestamp(start_date), pd.Timestamp(end_date))

    facility_values = list(facilities or [])
    if facility_values:
        mask &= frame["발전기명"].isin(facility_values)

    unit_values = list(facility_units or [])
    if unit_values:
        mask &= frame["facility_unit_key"].isin(unit_values)

    if pollutant:
        mask &= frame["pollutant"].eq(pollutant)

    return frame.loc[mask].copy()


def summary_metrics(frame: pd.DataFrame) -> dict[str, float | int | pd.Timestamp | None]:
    """선택된 단일 오염물질 데이터의 핵심 지표를 계산한다."""
    if frame.empty:
        return {
            "average": None,
            "latest_average": None,
            "latest_date": None,
            "previous_average": None,
            "month_change": None,
            "max_ratio": None,
            "exceed_count": 0,
            "exceed_rate": 0.0,
            "unit_count": 0,
            "facility_count": 0,
            "record_count": 0,
        }

    dates = sorted(frame["date"].dropna().unique())
    latest_date = pd.Timestamp(dates[-1])
    latest_average = float(frame.loc[frame["date"].eq(latest_date), "concentration"].mean())
    previous_average: float | None = None
    month_change: float | None = None
    if len(dates) >= 2:
        previous_date = pd.Timestamp(dates[-2])
        previous_average = float(frame.loc[frame["date"].eq(previous_date), "concentration"].mean())
        month_change = latest_average - previous_average

    exceed_count = int(frame["exceeds_limit"].sum())
    return {
        "average": float(frame["concentration"].mean()),
        "latest_average": latest_average,
        "latest_date": latest_date,
        "previous_average": previous_average,
        "month_change": month_change,
        "max_ratio": float(frame["limit_ratio_pct"].max()),
        "exceed_count": exceed_count,
        "exceed_rate": exceed_count / len(frame) * 100,
        "unit_count": int(frame["facility_unit_key"].nunique()),
        "facility_count": int(frame["발전기명"].nunique()),
        "record_count": int(len(frame)),
    }


def monthly_trend(frame: pd.DataFrame) -> pd.DataFrame:
    """월별 농도와 허용기준의 단순평균을 계산한다."""
    if frame.empty:
        return pd.DataFrame(
            columns=["date", "concentration", "limit", "limit_ratio_pct", "record_count"]
        )
    return (
        frame.groupby("date", as_index=False)
        .agg(
            concentration=("concentration", "mean"),
            limit=("limit", "mean"),
            limit_ratio_pct=("limit_ratio_pct", "mean"),
            record_count=("concentration", "size"),
        )
        .sort_values("date")
    )


def comparison(frame: pd.DataFrame, group_column: str) -> pd.DataFrame:
    """발전기 또는 호기별 비교 지표를 계산한다."""
    if frame.empty:
        return pd.DataFrame()
    return frame.groupby(group_column, as_index=False).agg(
        average_concentration=("concentration", "mean"),
        maximum_concentration=("concentration", "max"),
        average_ratio=("limit_ratio_pct", "mean"),
        maximum_ratio=("limit_ratio_pct", "max"),
        exceed_count=("exceeds_limit", "sum"),
        record_count=("concentration", "size"),
    )


def exceedance_by_month(frame: pd.DataFrame) -> pd.DataFrame:
    """월별 기준 초과 관측 수와 비율을 계산한다."""
    if frame.empty:
        return pd.DataFrame(columns=["date", "exceed_count", "record_count", "exceed_rate"])
    result = (
        frame.groupby("date", as_index=False)
        .agg(
            exceed_count=("exceeds_limit", "sum"),
            record_count=("exceeds_limit", "size"),
        )
        .sort_values("date")
    )
    result["exceed_rate"] = result["exceed_count"] / result["record_count"] * 100
    return result


def pollutant_overview(frame: pd.DataFrame) -> pd.DataFrame:
    """오염물질별 기록 수와 초과 관측 수를 요약한다."""
    if frame.empty:
        return pd.DataFrame()
    result = frame.groupby(["pollutant", "unit"], as_index=False).agg(
        average_concentration=("concentration", "mean"),
        maximum_ratio=("limit_ratio_pct", "max"),
        exceed_count=("exceeds_limit", "sum"),
        record_count=("exceeds_limit", "size"),
    )
    result["exceed_rate"] = result["exceed_count"] / result["record_count"] * 100
    return result
