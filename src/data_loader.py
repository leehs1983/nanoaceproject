from __future__ import annotations

from pathlib import Path

import pandas as pd

KEY_COLUMNS = ["발전기명", "호기명", "배출년월"]

POLLUTANT_CONFIG = {
    "이산화황": {
        "concentration": "이산화황 평균농도(Sox_ppm)",
        "limit": "이산화황 허용기준(Sox_ppm)",
        "unit": "ppm",
    },
    "질소산화물": {
        "concentration": "질소산화물 평균농도(Nox_ppm)",
        "limit": "질소산화물 허용기준(Nox_ppm)",
        "unit": "ppm",
    },
    "먼지": {
        "concentration": "먼지 평균농도(표준세제곱미터당 밀리그램)",
        "limit": "먼지 허용기준(표준세제곱미터당 밀리그램)",
        "unit": "mg/표준m³",
    },
}

REQUIRED_COLUMNS = KEY_COLUMNS + [
    column
    for config in POLLUTANT_CONFIG.values()
    for column in (config["limit"], config["concentration"])
]


class DataValidationError(ValueError):
    """사용자에게 표시할 수 있는 데이터 검증 오류."""


def load_source_data(path: str | Path) -> tuple[pd.DataFrame, list[str]]:
    """CSV를 읽고 스키마를 검증한 뒤 원본 형태의 데이터프레임을 반환한다."""
    csv_path = Path(path)
    if not csv_path.exists():
        raise DataValidationError(f"데이터 파일을 찾을 수 없습니다: {csv_path.name}")

    try:
        frame = pd.read_csv(csv_path, encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise DataValidationError("CSV 파일을 UTF-8로 읽을 수 없습니다.") from exc
    except Exception as exc:
        raise DataValidationError(f"CSV 파일을 읽는 중 오류가 발생했습니다: {exc}") from exc

    missing_columns = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing_columns:
        raise DataValidationError("필수 컬럼이 없습니다: " + ", ".join(missing_columns))

    frame = frame[REQUIRED_COLUMNS].copy()
    warnings: list[str] = []

    if frame[KEY_COLUMNS].isna().any().any():
        raise DataValidationError("발전기명, 호기명 또는 배출년월에 빈 값이 있습니다.")

    frame["발전기명"] = frame["발전기명"].astype(str).str.strip()
    frame["호기명"] = frame["호기명"].astype(str).str.strip()
    frame["배출년월"] = frame["배출년월"].astype(str).str.strip()

    if (frame[["발전기명", "호기명", "배출년월"]] == "").any().any():
        raise DataValidationError("발전기명, 호기명 또는 배출년월에 빈 문자열이 있습니다.")

    duplicate_count = int(frame.duplicated(KEY_COLUMNS, keep=False).sum())
    if duplicate_count:
        raise DataValidationError(
            f"발전기명·호기명·배출년월이 중복된 행이 {duplicate_count}개 있습니다."
        )

    parsed_dates = pd.to_datetime(frame["배출년월"], format="%Y-%m", errors="coerce")
    invalid_dates = int(parsed_dates.isna().sum())
    if invalid_dates:
        raise DataValidationError(
            f"YYYY-MM 형식으로 변환할 수 없는 배출년월이 {invalid_dates}개 있습니다."
        )
    frame["date"] = parsed_dates

    numeric_columns = [column for column in REQUIRED_COLUMNS if column not in KEY_COLUMNS]
    for column in numeric_columns:
        converted = pd.to_numeric(frame[column], errors="coerce")
        invalid_count = int(converted.isna().sum())
        if invalid_count:
            raise DataValidationError(
                f"'{column}'에서 숫자로 변환할 수 없는 값이 {invalid_count}개 있습니다."
            )
        frame[column] = converted.astype(float)

    limit_columns = [config["limit"] for config in POLLUTANT_CONFIG.values()]
    non_positive_limits = int((frame[limit_columns] <= 0).sum().sum())
    if non_positive_limits:
        warnings.append(
            f"0 이하의 허용기준 {non_positive_limits}개는 허용기준 대비 비율을 계산하지 않습니다."
        )

    concentration_columns = [config["concentration"] for config in POLLUTANT_CONFIG.values()]
    negative_concentrations = int((frame[concentration_columns] < 0).sum().sum())
    if negative_concentrations:
        warnings.append(f"음수 평균농도가 {negative_concentrations}개 있습니다.")

    return frame.sort_values(KEY_COLUMNS).reset_index(drop=True), warnings


def to_long_format(source: pd.DataFrame) -> pd.DataFrame:
    """오염물질별 분석이 쉬운 긴 형식으로 변환한다."""
    parts: list[pd.DataFrame] = []

    for pollutant, config in POLLUTANT_CONFIG.items():
        part = source[["발전기명", "호기명", "배출년월", "date"]].copy()
        part["pollutant"] = pollutant
        part["concentration"] = source[config["concentration"]].astype(float)
        part["limit"] = source[config["limit"]].astype(float)
        part["unit"] = config["unit"]
        part["limit_ratio_pct"] = (
            part["concentration"].div(part["limit"].where(part["limit"] > 0)).mul(100)
        )
        part["exceeds_limit"] = (part["limit"] > 0) & (part["concentration"] > part["limit"])
        part["facility_unit_key"] = part["발전기명"] + " · " + part["호기명"]
        parts.append(part)

    return (
        pd.concat(parts, ignore_index=True)
        .sort_values(["date", "발전기명", "호기명", "pollutant"])
        .reset_index(drop=True)
    )


def load_dashboard_data(path: str | Path) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    """원본 및 긴 형식 데이터와 검증 경고를 함께 반환한다."""
    source, warnings = load_source_data(path)
    return source, to_long_format(source), warnings
