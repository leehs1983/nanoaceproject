from pathlib import Path

import pandas as pd
import pytest

from src.data_loader import DataValidationError, load_dashboard_data, load_source_data

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "대기오염물질_배출량_2022-2025_결측치보간_병합.csv"


def test_current_csv_shape_and_range():
    source, long_data, warnings = load_dashboard_data(DATA_PATH)

    assert source.shape[0] == 1488
    assert source["발전기명"].nunique() == 7
    assert source[["발전기명", "호기명"]].drop_duplicates().shape[0] == 31
    assert source["date"].min() == pd.Timestamp("2022-01-01")
    assert source["date"].max() == pd.Timestamp("2025-12-01")
    assert len(long_data) == 1488 * 3
    assert warnings == []


def test_current_csv_has_expected_exceedance_counts():
    _, long_data, _ = load_dashboard_data(DATA_PATH)
    counts = long_data.groupby("pollutant")["exceeds_limit"].sum().to_dict()

    assert counts == {"먼지": 1, "이산화황": 0, "질소산화물": 68}


def test_duplicate_keys_raise_clear_error(tmp_path):
    source, _ = load_source_data(DATA_PATH)
    duplicated = pd.concat([source.iloc[:1], source.iloc[:1]], ignore_index=True)
    test_path = tmp_path / "duplicate.csv"
    duplicated.drop(columns=["date"]).to_csv(test_path, index=False, encoding="utf-8")

    with pytest.raises(DataValidationError, match="중복"):
        load_source_data(test_path)
