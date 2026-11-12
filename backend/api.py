"""
FastAPI REST API Server for Stock Price Trend Predictor
Serves real-time stock trend predictions, risk indicators, and technical metrics.
"""

import math
import numbers

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from predict import predict_stock
from risk import calculate_risk_metrics


app = FastAPI(
    title="Stock Price Trend Predictor API",
    description="REST API connecting the Machine Learning trend forecast and risk engine to the frontend.",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Convert NaN and Infinity values into JSON-safe values
def clean_for_json(value):

    if isinstance(value, dict):
        return {
            key: clean_for_json(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [
            clean_for_json(item)
            for item in value
        ]

    # Convert NumPy scalar values into normal Python values
    if hasattr(value, "item") and callable(value.item):
        try:
            value = value.item()
        except (ValueError, TypeError):
            pass

    if isinstance(value, numbers.Real) and not isinstance(value, bool):
        if not math.isfinite(value):
            return None

    return value


@app.get("/")
def root():
    return {
        "status": "online",
        "service": "Stock Price Trend Predictor API",
        "endpoints": {
            "prediction": "/api/predict?ticker=AAPL&mode=binary",
            "documentation": "/docs",
        },
    }


@app.get("/api/predict")
def get_prediction(
    ticker: str = Query(
        ...,
        description="Stock ticker symbol (e.g. AAPL, MSFT, RELIANCE.NS, TCS.NS)"
    ),
    mode: str = Query(
        "binary",
        regex="^(binary|3class)$",
        description="Forecast mode: 'binary' (UP vs DOWN) or '3class' (UP, DOWN, STABLE)",
    ),
):
    """
    Get next trading day trend prediction, confidence scores,
    technical indicators, risk factors, and historical chart records.
    """

    try:
        data = predict_stock(ticker=ticker.strip(), mode=mode)

        if data is None:
            raise HTTPException(
                status_code=404,
                detail=f"Unable to fetch data or generate prediction for ticker '{ticker}'. Please verify the symbol.",
            )

        # Clean all NaN and Infinity values before sending JSON response
        return clean_for_json(data)

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Prediction error: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    print("Starting Stock Trend Predictor API on http://localhost:8000 ...")

    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )