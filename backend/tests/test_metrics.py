import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import services.metrics as metrics


def test_calculate_portfolio_metrics_success(monkeypatch):
    def mock_fetch_price(symbol: str) -> float:
        return {"AAPL": 100.0, "MSFT": 200.0}[symbol]

    def mock_fetch_price_history(symbol: str) -> list[dict]:
        return [{"date": "2026-01-01", "close": mock_fetch_price(symbol)}]

    monkeypatch.setattr(metrics, "fetch_price", mock_fetch_price)
    monkeypatch.setattr(metrics, "fetch_price_history", mock_fetch_price_history)

    positions = [
        {"symbol": "AAPL", "quantity": 10},
        {"symbol": "MSFT", "quantity": 5},
    ]

    results = metrics.calculate_portfolio_metrics(positions)

    assert "total_value" in results
    assert "by_symbol" in results
    assert "top_symbol" in results
    assert "failed_symbols" in results
    assert "warnings" in results

    assert isinstance(results["total_value"], float)
    assert isinstance(results["by_symbol"], dict)
    assert isinstance(results["top_symbol"], dict)

    assert results["top_symbol"]["symbol"] in ["AAPL", "MSFT"]
    assert 0 <= results["top_symbol"]["weight"] <= 1
    assert results["total_value"] == 2000.0
    assert results["failed_symbols"] == []
    assert results["warnings"] == []


def test_calculate_portfolio_metrics_partial_failure(monkeypatch):
    def mock_fetch_price(symbol: str) -> float:
        if symbol == "MSFT":
            raise ValueError("No data")
        return 150.0

    def mock_fetch_price_history(symbol: str) -> list[dict]:
        return [{"date": "2026-01-01", "close": 150.0}]

    monkeypatch.setattr(metrics, "fetch_price", mock_fetch_price)
    monkeypatch.setattr(metrics, "fetch_price_history", mock_fetch_price_history)

    positions = [
        {"symbol": "AAPL", "quantity": 2},
        {"symbol": "MSFT", "quantity": 3},
    ]

    results = metrics.calculate_portfolio_metrics(positions)

    assert results["total_value"] == 300.0
    assert results["successful_symbols"] == ["AAPL"]
    assert results["failed_symbols"] == [
        {"symbol": "MSFT", "reason": "data_provider_error"}
    ]
    assert results["warnings"] == ["Could not fetch market data for MSFT."]