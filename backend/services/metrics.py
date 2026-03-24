from typing import Any, Dict
from .market_data import fetch_price, fetch_price_history, fetch_company_name


def calculate_portfolio_metrics(positions: list[Dict[str, Any]]) -> Dict[str, Any]:
    total_value = 0.0
    values_by_symbol: Dict[str, float] = {}
    history_by_symbol: Dict[str, list[dict]] = {}
    failed_reasons: Dict[str, str] = {}

    # Cache market data per symbol so duplicate positions do not trigger extra network calls.
    price_cache: Dict[str, float] = {}
    history_cache: Dict[str, list[dict]] = {}

    for position in positions:
        symbol = str(position["symbol"]).upper()
        quantity = float(position["quantity"])

        if symbol in failed_reasons:
            continue

        if symbol not in price_cache:
            try:
                price_cache[symbol] = fetch_price(symbol)
                history_cache[symbol] = fetch_price_history(symbol)
            except Exception:
                failed_reasons[symbol] = "data_provider_error"
                continue

        price = price_cache[symbol]
        history_by_symbol[symbol] = history_cache[symbol]
        
        # Fetch company name (gracefully degrade to symbol if it fails)
        try:
            company_name = fetch_company_name(symbol)
        except Exception:
            company_name = symbol
        
        value = quantity * price
        values_by_symbol[symbol] = {
            "value": values_by_symbol.get(symbol, 0.0) + value,
            "name": company_name
        }

        total_value += value

    if total_value > 0:
        top_symbol = max(values_by_symbol, key=lambda s: values_by_symbol[s]["value"])
        top_weight = values_by_symbol[top_symbol]["value"] / total_value
    else:
        top_symbol = None
        top_weight = 0.0

    failed_symbols = [
        {"symbol": symbol, "reason": reason}
        for symbol, reason in failed_reasons.items()
    ]
    warnings = [
        f"Could not fetch market data for {item['symbol']}."
        for item in failed_symbols
    ]

    return {
        "total_value": total_value,
        "by_symbol": values_by_symbol,
        "history_by_symbol": history_by_symbol,
        "top_symbol": {
            "symbol": top_symbol,
            "weight": top_weight,
            "name": values_by_symbol[top_symbol]["name"] if top_symbol else None,
        },
        "successful_symbols": list(values_by_symbol.keys()),
        "failed_symbols": failed_symbols,
        "warnings": warnings,
    }