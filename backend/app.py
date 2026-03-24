from flask import Flask, jsonify, request
from flask_cors import CORS
import math
import re
from typing import Any
from services.metrics import calculate_portfolio_metrics


app = Flask(__name__)
MAX_QUANTITY = 1_000_000
SYMBOL_PATTERN = re.compile(r"^[A-Za-z]+$")
# Keep deployment simple: allow frontend calls from any origin for this demo.
CORS(app)


def _get_positions(payload: dict[str, Any] | None):
    if not payload:
        return None, (jsonify({"error": "Invalid JSON payload."}), 400)

    # Accept both names to remain compatible with existing frontend clients.
    positions = payload.get("positions") or payload.get("holdings")
    if not isinstance(positions, list) or not positions:
        return None, (jsonify({"error": "Invalid input, provide a non-empty 'positions' list."}), 400)

    return positions, None


def _normalize_position(position: dict[str, Any]):
    if "symbol" not in position or "quantity" not in position:
        return jsonify({"error": "Each position must include 'symbol' and 'quantity'."}), 400

    symbol = str(position["symbol"]).strip().upper()
    if not SYMBOL_PATTERN.fullmatch(symbol):
        return jsonify({"error": "Symbol must contain only letters (A-Z)."}), 400

    try:
        quantity = float(position["quantity"])
    except (TypeError, ValueError):
        return jsonify({"error": "Quantity must be a valid number."}), 400

    if not math.isfinite(quantity):
        return jsonify({"error": "Quantity must be a finite number."}), 400

    if quantity <= 0:
        return jsonify({"error": "Quantity must be a positive number."}), 400

    if quantity > MAX_QUANTITY:
        return jsonify({"error": f"Quantity must be less than or equal to {MAX_QUANTITY:,}."}), 400

    # Normalize values so downstream code receives validated input.
    position["symbol"] = symbol
    position["quantity"] = quantity
    return None


def _all_symbols_failed_response(results: dict[str, Any]):
    return jsonify({
        "error": "Market data provider is temporarily unavailable for all requested symbols.",
        "failed_symbols": results.get("failed_symbols", []),
        "warnings": results.get("warnings", []),
    }), 502

@app.route("/portfolio/metrics", methods=["GET", "POST"])
def portfolio_metrics():
    if request.method == "GET":
        return jsonify(
            {
                "message": "Use POST to calculate portfolio metrics.",
                "example_payload": {
                    "positions": [{"symbol": "AAPL", "quantity": 10}],
                },
            }
        )

    positions, error_response = _get_positions(request.get_json(silent=True))
    if error_response:
        return error_response

    for position in positions:
        position_error = _normalize_position(position)
        if position_error:
            return position_error

    try:
        results = calculate_portfolio_metrics(positions)

        if not results.get("successful_symbols"):
            return _all_symbols_failed_response(results)

        return jsonify(results)
    except Exception:
        return jsonify({"error": "Internal server error while calculating portfolio metrics."}), 500

if __name__ == "__main__":
    app.run(debug=True)