from flask import Flask, jsonify, request
import math
import re
from services.metrics import calculate_portfolio_metrics


app = Flask(__name__)
MAX_QUANTITY = 1_000_000
SYMBOL_PATTERN = re.compile(r"^[A-Za-z]+$")

@app.route("/portfolio/metrics", methods=["POST"])
@app.route("/metrics", methods=["POST"])
def portfolio_metrics():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Invalid JSON payload."}), 400

    # Accept both names to remain compatible with existing frontend clients.
    positions = data.get("positions") or data.get("holdings")
    if not isinstance(positions, list) or not positions:
        return jsonify({"error": "Invalid input, provide a non-empty 'positions' list."}), 400

    #validate each position
    for position in positions:
        if "symbol" not in position or "quantity" not in position:
            return jsonify({"error": "Each position must include 'symbol' and 'quantity'."}), 400

        symbol = str(position["symbol"]).strip().upper()
        if not SYMBOL_PATTERN.fullmatch(symbol):
            return jsonify({"error": "Symbol must contain only letters (A-Z)."}), 400

        position["symbol"] = symbol

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

        # Normalize quantity so downstream metrics code receives validated numeric input.
        position["quantity"] = quantity
    
    try:
        results = calculate_portfolio_metrics(positions)

        if not results.get("successful_symbols"):
            return jsonify({
                "error": "Market data provider is temporarily unavailable for all requested symbols.",
                "failed_symbols": results.get("failed_symbols", []),
                "warnings": results.get("warnings", []),
            }), 502

        return jsonify(results)
    except Exception:
        return jsonify({"error": "Internal server error while calculating portfolio metrics."}), 500

if __name__ == "__main__":
    app.run(debug=True)