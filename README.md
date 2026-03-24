# Portfolio Analytics

A small full-stack demo that analyzes a stock portfolio.

- Frontend: React + Vite
- Backend: Flask + yfinance

It calculates:

- Total portfolio value
- Top holding and weight
- Value by symbol
- Recent price trend chart

## Quick Start

### 1) Backend

```bash
cd backend
python -m venv ../.venv
source ../.venv/bin/activate
pip install -r requirements.txt
python app.py
```

Backend runs on http://127.0.0.1:5000.

### 2) Frontend

Open a new terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on http://localhost:5173.

## API

`POST /portfolio/metrics`

Example payload:

```json
{
  "positions": [{ "symbol": "AAPL", "quantity": 10 }]
}
```

## Notes

- Symbols are validated on the backend.
- If market data fails for some symbols, the API returns partial results with warnings.
- If all symbols fail, the API returns `502`.
