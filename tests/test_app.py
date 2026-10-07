from pathlib import Path

from streamlit.testing.v1 import AppTest

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_dashboard_initial_view_renders_without_exceptions():
    app = AppTest.from_file(PROJECT_ROOT / "app.py", default_timeout=20).run()

    assert len(app.exception) == 0
    assert len(app.metric) == 5
    assert len(app.dataframe) == 2
    assert app.metric[0].label == "선택 범위 평균농도"
    assert "ppm" in app.metric[0].value
