import pytest
from pathlib import Path
from streamlit.testing.v1 import AppTest

def test_app_landing_page_rendering():
    """Valida renderização inicial do app principal sem exceções."""
    app_file = Path(__file__).resolve().parents[2] / "app.py"
    at = AppTest.from_file(str(app_file))
    at.run(timeout=15)
    assert not at.exception
