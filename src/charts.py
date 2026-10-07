from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

POLLUTANT_COLORS = {
    "이산화황": "#5B6CFF",
    "질소산화물": "#FF7A45",
    "먼지": "#13A085",
}
LIMIT_COLOR = "#667085"
WARNING_COLOR = "#D92D20"


def _base_layout(fig: go.Figure, y_title: str) -> go.Figure:
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=16, r=16, t=22, b=16),
        height=390,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        hovermode="x unified",
        xaxis_title=None,
        yaxis_title=y_title,
        font=dict(family="Pretendard, Noto Sans KR, sans-serif", color="#263238"),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#E9EDF2", rangemode="tozero")
    return fig


def trend_chart(
    trend: pd.DataFrame, pollutant: str, unit: str, ratio_view: bool = False
) -> go.Figure:
    color = POLLUTANT_COLORS.get(pollutant, "#5B6CFF")
    fig = go.Figure()
    if ratio_view:
        fig.add_trace(
            go.Scatter(
                x=trend["date"],
                y=trend["limit_ratio_pct"],
                mode="lines+markers",
                name="허용기준 대비 비율",
                line=dict(color=color, width=3),
                marker=dict(size=6),
                customdata=trend[["record_count"]],
                hovertemplate=(
                    "%{x|%Y-%m}<br>%{y:.1f}%<br>포함 기록 %{customdata[0]}건<extra></extra>"
                ),
            )
        )
        fig.add_hline(
            y=100,
            line_dash="dash",
            line_color=WARNING_COLOR,
            annotation_text="허용기준 100%",
            annotation_position="top left",
        )
        return _base_layout(fig, "허용기준 대비 비율 (%)")

    fig.add_trace(
        go.Scatter(
            x=trend["date"],
            y=trend["concentration"],
            mode="lines+markers",
            name="평균농도",
            line=dict(color=color, width=3),
            marker=dict(size=6),
            customdata=trend[["record_count", "limit_ratio_pct"]],
            hovertemplate=(
                "%{x|%Y-%m}<br>평균농도 %{y:.2f}<br>"
                "평균 비율 %{customdata[1]:.1f}%<br>포함 기록 %{customdata[0]}건<extra></extra>"
            ),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=trend["date"],
            y=trend["limit"],
            mode="lines",
            name="허용기준",
            line=dict(color=LIMIT_COLOR, width=2, dash="dash"),
            hovertemplate="%{x|%Y-%m}<br>허용기준 %{y:.2f}<extra></extra>",
        )
    )
    return _base_layout(fig, unit)


def comparison_chart(
    data: pd.DataFrame,
    category_column: str,
    metric_column: str,
    metric_label: str,
    pollutant: str,
    suffix: str = "",
) -> go.Figure:
    ordered = data.sort_values(metric_column, ascending=True)
    fig = px.bar(
        ordered,
        x=metric_column,
        y=category_column,
        orientation="h",
        color_discrete_sequence=[POLLUTANT_COLORS.get(pollutant, "#5B6CFF")],
        custom_data=["record_count", "exceed_count"],
    )
    fig.update_traces(
        hovertemplate=(
            f"%{{y}}<br>{metric_label} %{{x:.2f}}{suffix}"
            "<br>기록 %{customdata[0]}건<br>초과 관측 %{customdata[1]}건<extra></extra>"
        )
    )
    fig.update_layout(
        template="plotly_white",
        height=max(360, 38 * len(ordered)),
        margin=dict(l=16, r=16, t=22, b=16),
        xaxis_title=f"{metric_label}{f' ({suffix})' if suffix else ''}",
        yaxis_title=None,
        showlegend=False,
        font=dict(family="Pretendard, Noto Sans KR, sans-serif", color="#263238"),
    )
    fig.update_xaxes(gridcolor="#E9EDF2", rangemode="tozero")
    fig.update_yaxes(showgrid=False)
    return fig


def exceedance_chart(data: pd.DataFrame) -> go.Figure:
    colors = [WARNING_COLOR if value > 0 else "#D0D5DD" for value in data["exceed_count"]]
    fig = go.Figure(
        go.Bar(
            x=data["date"],
            y=data["exceed_count"],
            marker_color=colors,
            customdata=data[["record_count", "exceed_rate"]],
            hovertemplate=(
                "%{x|%Y-%m}<br>초과 관측 %{y}건"
                "<br>전체 %{customdata[0]}건<br>비율 %{customdata[1]:.1f}%<extra></extra>"
            ),
        )
    )
    return _base_layout(fig, "기준 초과 관측 수")


def distribution_chart(frame: pd.DataFrame, pollutant: str) -> go.Figure:
    fig = px.histogram(
        frame,
        x="limit_ratio_pct",
        nbins=30,
        color_discrete_sequence=[POLLUTANT_COLORS.get(pollutant, "#5B6CFF")],
        labels={"limit_ratio_pct": "허용기준 대비 비율 (%)", "count": "기록 수"},
    )
    fig.add_vline(
        x=100,
        line_dash="dash",
        line_color=WARNING_COLOR,
        annotation_text="100%",
        annotation_position="top right",
    )
    fig.update_traces(hovertemplate="비율 %{x:.1f}%<br>기록 %{y}건<extra></extra>")
    fig.update_layout(
        template="plotly_white",
        height=390,
        margin=dict(l=16, r=16, t=22, b=16),
        showlegend=False,
        xaxis_title="허용기준 대비 비율 (%)",
        yaxis_title="기록 수",
        font=dict(family="Pretendard, Noto Sans KR, sans-serif", color="#263238"),
    )
    fig.update_xaxes(gridcolor="#E9EDF2")
    fig.update_yaxes(gridcolor="#E9EDF2", rangemode="tozero")
    return fig
