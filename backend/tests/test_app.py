import sys
import os

import pytest

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import app as app_module


@pytest.fixture
def client():
    app_module.app.config["TESTING"] = True
    return app_module.app.test_client()


def test_portfolio_metrics_rejects_invalid_symbol(client):
    response = client.post(
        "/portfolio/metrics",
        json={"positions": [{"symbol": "AAPL1", "quantity": 1}]},
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "Symbol must contain only letters (A-Z)."


def test_portfolio_metrics_returns_502_when_all_symbols_fail(client, monkeypatch):
    def mock_calculate_portfolio_metrics(_positions):
        return {
            "total_value": 0.0,
            "by_symbol": {},
            "history_by_symbol": {},
            "top_symbol": {"symbol": None, "weight": 0.0},
            "successful_symbols": [],
            "failed_symbols": [{"symbol": "AAPL", "reason": "data_provider_error"}],
            "warnings": ["Could not fetch market data for AAPL."],
        }

    monkeypatch.setattr(app_module, "calculate_portfolio_metrics", mock_calculate_portfolio_metrics)

    response = client.post(
        "/portfolio/metrics",
        json={"positions": [{"symbol": "AAPL", "quantity": 1}]},
    )

    body = response.get_json()
    assert response.status_code == 502
    assert "temporarily unavailable" in body["error"]
    assert body["failed_symbols"] == [{"symbol": "AAPL", "reason": "data_provider_error"}]
