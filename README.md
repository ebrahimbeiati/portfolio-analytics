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

## Netlify Deployment

If you deploy only the frontend to Netlify, the app still needs a live backend API URL.

- In Netlify Site settings, add environment variable `VITE_API_BASE_URL`.
- Set it to your deployed Flask backend URL (for example: `https://your-backend.example.com`).
- Redeploy after setting the variable.

Without this, requests can return HTML (404 page), which causes the browser error: `Unexpected token '<' ... is not valid JSON`.

### Backend CORS (Required)

This project enables CORS in Flask so your Netlify frontend can call the API.

- Install backend dependencies (includes `Flask-Cors`).
- Redeploy the backend after pulling latest changes.

## Free Backend Deploy (Render)

This repo includes [render.yaml](render.yaml), so you can deploy backend without buying a domain.

1. Push this repo to GitHub.
2. In Render, create a new Blueprint from this repo.
3. Deploy the `portfolio-analytics-api` service.
4. Copy the generated URL (example: `https://portfolio-analytics-api.onrender.com`).

Then in Netlify:

1. Site configuration > Environment variables.
2. Set `VITE_API_BASE_URL` to your Render URL (no trailing slash).
3. Redeploy Netlify.
