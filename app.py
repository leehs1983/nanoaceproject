from __future__ import annotations

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from src.charts import (
    comparison_chart,
    distribution_chart,
    exceedance_chart,
    trend_chart,
)
from src.data_loader import DataValidationError, load_dashboard_data
from src.metrics import (
    apply_filters,
    comparison,
    exceedance_by_month,
    monthly_trend,
    pollutant_overview,
    summary_metrics,
)
from src.ui import apply_page_style, format_number, section_header

APP_DIR = Path(__file__).resolve().parent
DATA_PATH = APP_DIR / "대기오염물질_배출량_2022-2025_결측치보간_병합.csv"
POLLUTANTS = ["이산화황", "질소산화물", "먼지"]


st.set_page_config(
    page_title="대기오염 평균농도 대시보드",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed",
)
apply_page_style()


@st.cache_data(show_spinner="데이터를 불러오는 중입니다…")
def get_data(path: str, modified_time: float):
    del modified_time
    return load_dashboard_data(path)


def reset_filters() -> None:
    for key in (
        "period_filter",
        "facility_filter",
        "unit_filter",
        "pollutant_filter",
        "exceed_only",
    ):
        st.session_state.pop(key, None)


def reset_unit_filter() -> None:
    st.session_state["unit_filter"] = []


def to_download_frame(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame[
        [
            "배출년월",
            "발전기명",
            "호기명",
            "pollutant",
            "concentration",
            "limit",
            "unit",
            "limit_ratio_pct",
            "exceeds_limit",
        ]
    ].copy()
    result.columns = [
        "배출년월",
        "발전기명",
        "호기명",
        "오염물질",
        "평균농도",
        "허용기준",
        "단위",
        "허용기준 대비 비율(%)",
        "기준 초과 관측",
    ]
    result["기준 초과 관측"] = result["기준 초과 관측"].map({True: "예", False: "아니오"})
    return result.sort_values(["배출년월", "발전기명", "호기명"])


try:
    source_data, long_data, data_warnings = get_data(
        str(DATA_PATH), DATA_PATH.stat().st_mtime if DATA_PATH.exists() else 0
    )
except DataValidationError as exc:
    st.error(str(exc), icon="🚨")
    st.info("CSV 파일의 위치와 컬럼 구성을 확인한 뒤 앱을 다시 실행해 주세요.")
    st.stop()
except Exception as exc:
    st.error(f"대시보드를 시작할 수 없습니다: {exc}", icon="🚨")
    st.stop()


minimum_date = pd.Timestamp(source_data["date"].min())
maximum_date = pd.Timestamp(source_data["date"].max())
month_options = list(pd.date_range(minimum_date, maximum_date, freq="MS"))

st.markdown(
    '<div class="dashboard-kicker">ENVIRONMENTAL DATA MONITOR</div>', unsafe_allow_html=True
)
st.markdown(
    '<h1 class="dashboard-title">대기오염 평균농도 대시보드</h1>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="dashboard-subtitle">'
    "발전기·호기별 월평균 농도와 허용기준 대비 수준을 한눈에 살펴보세요."
    "</div>",
    unsafe_allow_html=True,
)
facility_unit_count = source_data[["발전기명", "호기명"]].drop_duplicates().shape[0]
st.markdown(
    f'<span class="status-chip">{minimum_date:%Y-%m} — {maximum_date:%Y-%m}</span>'
    f'<span class="status-chip">발전기 {source_data["발전기명"].nunique()}곳</span>'
    f'<span class="status-chip">호기 {facility_unit_count}개</span>',
    unsafe_allow_html=True,
)

with st.expander("데이터 해석 안내", expanded=False):
    st.markdown(
        """
        - 이 데이터는 **총배출량이 아닌 월평균 농도**와 허용기준을 담고 있습니다.
        - 여러 호기의 평균은 유량이나 가동 시간을 반영하지 않은 단순평균입니다.
        - 평균농도 0은 원자료의 유효한 수치로 유지하며, 미가동·미측정 여부는 구분할 수 없습니다.
        - ‘기준 초과 관측’은 같은 행의 월평균 농도가 허용기준보다 큰 경우입니다.
          법적 위반 판정을 뜻하지 않습니다.
        - 파일명은 결측치 보간을 시사하지만 원 관측값과 보간값을 구분하는 정보는 없습니다.
        """
    )
    for warning in data_warnings:
        st.warning(warning)

st.write("")
section_header("조회 조건", "기간과 대상을 선택하면 아래의 모든 지표와 차트가 함께 갱신됩니다.")

with st.container(border=True):
    filter_top = st.columns([2.1, 2.2, 2.2, 1.4, 0.9], gap="medium")

    with filter_top[0]:
        selected_period = st.select_slider(
            "조회 기간",
            options=month_options,
            value=(minimum_date, maximum_date),
            format_func=lambda value: value.strftime("%Y-%m"),
            key="period_filter",
        )

    facility_options = sorted(source_data["발전기명"].unique().tolist())
    with filter_top[1]:
        selected_facilities = st.multiselect(
            "발전기명",
            facility_options,
            placeholder="전체 발전기",
            key="facility_filter",
            on_change=reset_unit_filter,
        )

    available_units = long_data
    if selected_facilities:
        available_units = available_units[available_units["발전기명"].isin(selected_facilities)]
    unit_options = sorted(available_units["facility_unit_key"].unique().tolist())
    with filter_top[2]:
        selected_units = st.multiselect(
            "호기",
            unit_options,
            placeholder="전체 호기",
            key="unit_filter",
        )

    with filter_top[3]:
        selected_pollutant = st.selectbox(
            "오염물질",
            POLLUTANTS,
            index=1,
            key="pollutant_filter",
        )

    with filter_top[4]:
        st.write("")
        st.write("")
        st.button("필터 초기화", width="stretch", on_click=reset_filters)

    exceed_only = st.toggle(
        "상세 분석과 표에서 기준 초과 관측만 보기",
        value=False,
        key="exceed_only",
        help="핵심 지표와 전체 추이에는 영향을 주지 않습니다.",
    )


start_date, end_date = selected_period
scope_all_pollutants = apply_filters(
    long_data,
    start_date,
    end_date,
    selected_facilities,
    selected_units,
)
selected_data = scope_all_pollutants[
    scope_all_pollutants["pollutant"].eq(selected_pollutant)
].copy()

if selected_data.empty:
    st.warning("선택한 조건에 해당하는 데이터가 없습니다. 필터를 변경하거나 초기화해 주세요.")
    st.stop()

selected_unit = str(selected_data["unit"].iloc[0])
metrics = summary_metrics(selected_data)

st.write("")
section_header(
    f"{selected_pollutant} 핵심 지표",
    f"선택 범위 {metrics['record_count']:,}건 · "
    f"{metrics['facility_count']}개 발전기 · {metrics['unit_count']}개 호기",
)

metric_columns = st.columns(5, gap="medium")
metric_columns[0].metric(
    "선택 범위 평균농도",
    f"{format_number(metrics['average'])} {selected_unit}",
    help="선택된 모든 행의 단순 산술평균입니다.",
)
latest_label = (
    pd.Timestamp(metrics["latest_date"]).strftime("%Y-%m")
    if metrics["latest_date"] is not None
    else "최신월"
)
latest_delta = (
    f"{metrics['month_change']:+.2f} {selected_unit}"
    if metrics["month_change"] is not None
    else None
)
metric_columns[1].metric(
    f"최신월 평균 · {latest_label}",
    f"{format_number(metrics['latest_average'])} {selected_unit}",
    delta=latest_delta,
    delta_color="inverse",
    help="선택 범위의 직전 데이터 월과 비교합니다.",
)
metric_columns[2].metric(
    "최대 허용기준 대비 비율",
    f"{format_number(metrics['max_ratio'], 1)}%",
)
metric_columns[3].metric(
    "기준 초과 관측",
    f"{metrics['exceed_count']:,}건",
    delta=f"전체의 {metrics['exceed_rate']:.1f}%",
    delta_color="inverse",
    help="월평균 농도가 같은 행의 허용기준보다 큰 기록입니다.",
)
metric_columns[4].metric(
    "선택 대상",
    f"{metrics['unit_count']}개 호기",
    delta=f"{metrics['facility_count']}개 발전기",
    delta_color="off",
)

st.write("")
section_header(
    "월별 추이",
    "여러 호기가 선택된 경우 월별 농도와 허용기준은 포함된 행의 단순평균입니다.",
)
trend_mode = st.segmented_control(
    "추이 표시 방식",
    options=["평균농도", "허용기준 대비 비율"],
    default="평균농도",
    label_visibility="collapsed",
)
trend_data = monthly_trend(selected_data)
st.plotly_chart(
    trend_chart(
        trend_data,
        selected_pollutant,
        selected_unit,
        ratio_view=trend_mode == "허용기준 대비 비율",
    ),
    width="stretch",
    config={"displaylogo": False, "scrollZoom": False},
)

st.write("")
section_header("발전기·호기 비교", "현재 선택한 오염물질과 조회 기간을 기준으로 비교합니다.")
compare_controls = st.columns([1.2, 1.7, 3.1], gap="medium")
with compare_controls[0]:
    comparison_level = st.radio(
        "비교 단위",
        ["발전기명", "호기"],
        horizontal=True,
    )
with compare_controls[1]:
    metric_choice = st.selectbox(
        "정렬 지표",
        ["평균 허용기준 대비 비율", "최대 허용기준 대비 비율", "평균농도", "최대농도"],
    )

group_column = "발전기명" if comparison_level == "발전기명" else "facility_unit_key"
metric_mapping = {
    "평균 허용기준 대비 비율": ("average_ratio", "%"),
    "최대 허용기준 대비 비율": ("maximum_ratio", "%"),
    "평균농도": ("average_concentration", selected_unit),
    "최대농도": ("maximum_concentration", selected_unit),
}
metric_column, metric_suffix = metric_mapping[metric_choice]
comparison_data = comparison(selected_data, group_column)
st.plotly_chart(
    comparison_chart(
        comparison_data,
        group_column,
        metric_column,
        metric_choice,
        selected_pollutant,
        metric_suffix,
    ),
    width="stretch",
    config={"displaylogo": False},
)

st.write("")
section_header(
    "기준 초과와 분포",
    "100%는 파일에 기록된 허용기준과 같은 수준을 뜻합니다. 법적 위반 판정으로 해석하지 않습니다.",
)
analysis_data = (
    selected_data[selected_data["exceeds_limit"]].copy() if exceed_only else selected_data
)
chart_columns = st.columns(2, gap="large")
with chart_columns[0]:
    st.markdown("**월별 기준 초과 관측**")
    st.plotly_chart(
        exceedance_chart(exceedance_by_month(selected_data)),
        width="stretch",
        config={"displaylogo": False},
    )
with chart_columns[1]:
    st.markdown("**허용기준 대비 비율 분포**")
    if analysis_data.empty:
        st.info("현재 범위에는 기준 초과 관측이 없습니다.")
    else:
        st.plotly_chart(
            distribution_chart(analysis_data, selected_pollutant),
            width="stretch",
            config={"displaylogo": False},
        )

overview = pollutant_overview(scope_all_pollutants)
if not overview.empty:
    with st.expander("세 물질의 기준 초과 관측 요약", expanded=False):
        overview_display = overview[
            [
                "pollutant",
                "average_concentration",
                "unit",
                "maximum_ratio",
                "exceed_count",
                "record_count",
                "exceed_rate",
            ]
        ].copy()
        overview_display.columns = [
            "오염물질",
            "평균농도",
            "단위",
            "최대 기준 대비 비율(%)",
            "초과 관측 수",
            "전체 기록 수",
            "초과 관측 비율(%)",
        ]
        st.dataframe(
            overview_display,
            hide_index=True,
            width="stretch",
            column_config={
                "평균농도": st.column_config.NumberColumn(format="%.2f"),
                "최대 기준 대비 비율(%)": st.column_config.NumberColumn(format="%.1f%%"),
                "초과 관측 비율(%)": st.column_config.NumberColumn(format="%.1f%%"),
            },
        )

st.write("")
section_header(
    "상세 데이터",
    "화면 표는 읽기 쉽게 반올림하며, 다운로드 파일에는 원래 수치 정밀도를 유지합니다.",
)
table_data = to_download_frame(analysis_data)
if table_data.empty:
    st.info("표시할 기준 초과 관측이 없습니다.")
else:
    search_term = st.text_input(
        "발전기명 또는 호기 검색",
        placeholder="예: 보령, GT1",
    ).strip()
    displayed_table = table_data
    if search_term:
        search_mask = displayed_table["발전기명"].str.contains(
            search_term, case=False, na=False, regex=False
        ) | displayed_table["호기명"].str.contains(search_term, case=False, na=False, regex=False)
        displayed_table = displayed_table.loc[search_mask]

    st.caption(f"{len(displayed_table):,}건 표시")
    st.dataframe(
        displayed_table,
        hide_index=True,
        width="stretch",
        height=460,
        column_config={
            "평균농도": st.column_config.NumberColumn(format="%.2f"),
            "허용기준": st.column_config.NumberColumn(format="%.2f"),
            "허용기준 대비 비율(%)": st.column_config.ProgressColumn(
                format="%.1f%%",
                min_value=0,
                max_value=max(100.0, float(displayed_table["허용기준 대비 비율(%)"].max())),
            ),
            "기준 초과 관측": st.column_config.TextColumn(),
        },
    )

    now_kst = datetime.now(ZoneInfo("Asia/Seoul"))
    download_name = f"대기오염_{selected_pollutant}_{now_kst:%Y%m%d}.csv"
    st.download_button(
        "필터 결과 CSV 다운로드",
        data=displayed_table.to_csv(index=False).encode("utf-8-sig"),
        file_name=download_name,
        mime="text/csv",
        type="primary",
    )

st.divider()
st.caption(
    f"데이터 기준: {minimum_date:%Y-%m} ~ {maximum_date:%Y-%m} · "
    "본 화면의 기준 초과 관측은 데이터 점검을 위한 비교이며 법적 판단 자료가 아닙니다."
)
