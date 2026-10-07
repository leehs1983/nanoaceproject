from pathlib import Path

import pandas as pd

from src.data_loader import load_dashboard_data
from src.metrics import apply_filters, monthly_trend, summary_metrics

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "대기오염물질_배출량_2022-2025_결측치보간_병합.csv"


def test_ratio_and_equal_limit_rule():
    frame = pd.DataFrame(
        {
            "date": pd.to_datetime(["2025-01-01", "2025-02-01"]),
            "concentration": [10.0, 11.0],
            "limit": [10.0, 10.0],
            "limit_ratio_pct": [100.0, 110.0],
            "exceeds_limit": [False, True],
            "facility_unit_key": ["A · 1", "A · 1"],
            "발전기명": ["A", "A"],
        }
    )

    metrics = summary_metrics(frame)
    assert metrics["max_ratio"] == 110.0
    assert metrics["exceed_count"] == 1
    assert metrics["exceed_rate"] == 50.0


def test_filters_use_intersection_and_keep_zero_values():
    _, long_data, _ = load_dashboard_data(DATA_PATH)
    filtered = apply_filters(
        long_data,
        pd.Timestamp("2022-01-01"),
        pd.Timestamp("2022-12-01"),
        facilities=["서울"],
        facility_units=["서울 · GT1"],
        pollutant="이산화황",
    )

    assert len(filtered) == 12
    assert filtered["concentration"].eq(0).all()
    assert monthly_trend(filtered)["record_count"].sum() == 12


def test_latest_month_change_uses_previous_available_month():
    frame = pd.DataFrame(
        {
            "date": pd.to_datetime(["2025-01-01", "2025-03-01"]),
            "concentration": [2.0, 5.5],
            "limit": [10.0, 10.0],
            "limit_ratio_pct": [20.0, 55.0],
            "exceeds_limit": [False, False],
            "facility_unit_key": ["A · 1", "A · 1"],
            "발전기명": ["A", "A"],
        }
    )

    metrics = summary_metrics(frame)
    assert metrics["month_change"] == 3.5
    assert metrics["latest_date"] == pd.Timestamp("2025-03-01")
