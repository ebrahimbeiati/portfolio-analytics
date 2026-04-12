import { useState } from "react";

const MAX_QUANTITY = 1_000_000;
const MAX_FETCH_ATTEMPTS = 3;
const RETRY_BASE_DELAY_MS = 1200;
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL?.trim();
const METRICS_API_URL = API_BASE_URL
  ? `${API_BASE_URL}/portfolio/metrics`
  : "/api/portfolio/metrics";

const RETRYABLE_STATUS_CODES = new Set([429, 502, 503, 504]);

const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

function App() {
  const [symbol, setSymbol] = useState("");
  const [quantity, setQuantity] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState("");

  const activeSymbol = result?.top_symbol?.symbol;
  const priceHistory = activeSymbol
    ? result?.history_by_symbol?.[activeSymbol] || []
    : [];
  const warnings = result?.warnings || [];
  const failedSymbols = result?.failed_symbols || [];

  const chartWidth = 560;
  const chartHeight = 220;
  const chartPadding = 16;

  const closes = priceHistory.map((point) => Number(point.close));
  const minClose = closes.length ? Math.min(...closes) : 0;
  const maxClose = closes.length ? Math.max(...closes) : 1;
  const closeRange = maxClose - minClose || 1;

  const formatDisplayDate = (dateString) => {
    if (!dateString) {
      return "N/A";
    }

    const date = new Date(`${dateString}T00:00:00`);
    if (Number.isNaN(date.getTime())) {
      return dateString;
    }

    return date.toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  const windowStart = formatDisplayDate(priceHistory[0]?.date);
  const windowEnd = formatDisplayDate(
    priceHistory[priceHistory.length - 1]?.date,
  );

  const linePoints = priceHistory
    .map((point, index) => {
      const x =
        chartPadding +
        (index / Math.max(priceHistory.length - 1, 1)) *
          (chartWidth - chartPadding * 2);
      const y =
        chartHeight -
        chartPadding -
        ((Number(point.close) - minClose) / closeRange) *
          (chartHeight - chartPadding * 2);
      return `${x},${y}`;
    })
    .join(" ");

  const handleQuantityChange = (e) => {
    const nextValue = e.target.value;
    if (nextValue === "") {
      setQuantity("");
      return;
    }

    const parsed = Number(nextValue);
    if (!Number.isFinite(parsed)) {
      return;
    }

    if (parsed > MAX_QUANTITY) {
      return;
    }

    setQuantity(nextValue);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setStatusMessage("");

    try {
      const parsedQuantity = Number(quantity);

      if (!/^[A-Za-z]+$/.test(symbol)) {
        setResult({ error: "Stock symbol must contain only letters (A-Z)." });
        return;
      }

      if (!Number.isFinite(parsedQuantity) || parsedQuantity <= 0) {
        setResult({ error: "Quantity must be a positive number." });
        return;
      }

      if (parsedQuantity > MAX_QUANTITY) {
        setResult({
          error: `Quantity must be less than or equal to ${MAX_QUANTITY.toLocaleString()}.`,
        });
        return;
      }

      let response;
      let data;

      for (let attempt = 1; attempt <= MAX_FETCH_ATTEMPTS; attempt += 1) {
        try {
          response = await fetch(METRICS_API_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              positions: [{ symbol, quantity: parsedQuantity }],
            }),
          });

          const contentType = response.headers.get("content-type") || "";
          const isJson = contentType.includes("application/json");
          data = isJson ? await response.json() : null;

          if (!response.ok) {
            const message =
              data?.error ||
              "Could not reach the metrics API. In Netlify, set VITE_API_BASE_URL to your backend URL.";

            if (
              RETRYABLE_STATUS_CODES.has(response.status) &&
              attempt < MAX_FETCH_ATTEMPTS
            ) {
              setStatusMessage(
                `Server is warming up. Retrying ${attempt + 1}/${MAX_FETCH_ATTEMPTS}...`,
              );
              await delay(RETRY_BASE_DELAY_MS * attempt);
              continue;
            }

            throw new Error(message);
          }

          if (!data) {
            throw new Error("Unexpected response from API. Expected JSON.");
          }

          setStatusMessage("");
          setResult(data);
          return;
        } catch (attemptError) {
          const isNetworkError = attemptError instanceof TypeError;
          if (isNetworkError && attempt < MAX_FETCH_ATTEMPTS) {
            setStatusMessage(
              `Server is warming up. Retrying ${attempt + 1}/${MAX_FETCH_ATTEMPTS}...`,
            );
            await delay(RETRY_BASE_DELAY_MS * attempt);
            continue;
          }

          throw attemptError;
        }
      }
    } catch (error) {
      console.error("Error fetching metrics:", error);
      setStatusMessage("");
      setResult({ error: error.message || "Failed to fetch metrics" });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="portfolio-app">
      <h1>Portfolio Analytics</h1>

      <form onSubmit={handleSubmit} className="portfolio-form">
        <div className="field-row">
          <label htmlFor="symbol">Stock Symbol:</label>
          <input
            id="symbol"
            type="text"
            value={symbol}
            onChange={(e) => setSymbol(e.target.value.toUpperCase())}
            required
            className="symbol-input"
          />
        </div>

        <div className="field-row">
          <label htmlFor="quantity">Quantity:</label>
          <input
            id="quantity"
            type="number"
            value={quantity}
            onChange={handleQuantityChange}
            required
            min="0.000001"
            max={MAX_QUANTITY}
            step="0.000001"
            className="quantity-input"
          />
        </div>

        <button type="submit" disabled={loading} className="submit-button">
          {loading ? "Analyzing..." : "Calculate Metrics"}
        </button>

        {statusMessage && (
          <p className="status-banner" role="status" aria-live="polite">
            {statusMessage}
          </p>
        )}
      </form>

      {result?.error && <div className="error-banner">{result.error}</div>}

      {result && !result.error && (
        <div className="metrics-section">
          <h2>Metrics</h2>

          {warnings.length > 0 && (
            <div className="warning-banner">
              <strong>Partial data:</strong>
              <ul className="warning-list">
                {warnings.map((warning) => (
                  <li key={warning}>{warning}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="metrics-card">
            <p>
              <strong>Total Value:</strong> ${result.total_value.toFixed(2)}
            </p>

            <p>
              <strong>Top Symbol:</strong>{" "}
              {result.top_symbol.symbol
                ? `${result.top_symbol.name} (${result.top_symbol.symbol})`
                : "N/A"}
            </p>

            <p>
              <strong>Top Weight:</strong>{" "}
              {(result.top_symbol.weight * 100).toFixed(2)}%
            </p>

            <h3>Value by Symbol</h3>
            <ul>
              {Object.entries(result.by_symbol).map(([sym, val]) => (
                <li key={sym}>
                  {val.name} ({sym}): ${val.value.toFixed(2)}
                </li>
              ))}
            </ul>

            {failedSymbols.length > 0 && (
              <>
                <h3 className="section-heading">Failed Symbols</h3>
                <ul>
                  {failedSymbols.map((item) => (
                    <li key={item.symbol}>
                      {item.symbol}: {item.reason}
                    </li>
                  ))}
                </ul>
              </>
            )}

            <h3 className="section-heading">
              {activeSymbol ? `Price Trend (${activeSymbol})` : "Price Trend"}
            </h3>
            {priceHistory.length > 1 ? (
              <div>
                <svg
                  viewBox={`0 0 ${chartWidth} ${chartHeight}`}
                  width="100%"
                  aria-labelledby="price-trend-title"
                  className="price-chart"
                >
                  <title id="price-trend-title">
                    {`Recent closing prices for ${activeSymbol}`}
                  </title>
                  <polyline
                    fill="none"
                    stroke="#1f6feb"
                    strokeWidth="3"
                    strokeLinejoin="round"
                    strokeLinecap="round"
                    points={linePoints}
                  />
                </svg>

                <div className="chart-meta-grid">
                  <div className="chart-meta-card">
                    <div className="chart-meta-label">Window</div>
                    <div className="chart-meta-value">
                      {windowStart} to {windowEnd}
                    </div>
                  </div>
                  <div className="chart-meta-card">
                    <div className="chart-meta-label">Price Range</div>
                    <div className="chart-meta-value">
                      ${minClose.toFixed(2)} - ${maxClose.toFixed(2)}
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <p>Not enough history to draw the stock chart.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
