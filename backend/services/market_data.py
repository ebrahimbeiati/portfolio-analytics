import yfinance as yf


def fetch_company_name(symbol: str) -> str:
    try:
        info = yf.Ticker(symbol).info
        return info.get("longName") or info.get("shortName") or symbol
    except Exception:
        return symbol


def fetch_price(symbol: str) -> float:
    ticker = yf.Ticker(symbol)
    data = ticker.history(period="1d")
    if data.empty:
        raise ValueError(f"No data found for symbol: {symbol}")
    return float(data["Close"].iloc[-1])


def fetch_price_history(symbol: str, period: str = "1mo") -> list[dict]:
    ticker = yf.Ticker(symbol)
    data = ticker.history(period=period, interval="1d")
    if data.empty:
        return []

    history = []
    for idx, row in data.iterrows():
        history.append(
            {
                "date": idx.strftime("%Y-%m-%d"),
                "close": float(row["Close"]),
            }
        )

    return history

