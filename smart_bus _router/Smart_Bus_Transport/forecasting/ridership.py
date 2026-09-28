"""Ridership forecasting using Machine Learning Regression and statistical time series."""

from datetime import datetime, timedelta
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures


def moving_average(values: list[float], window: int = 3) -> float:
    """Return the average of the most recent values."""
    if window <= 0:
        raise ValueError("window must be greater than zero")
    if not values:
        return 0.0

    recent_values = values[-window:]
    return sum(recent_values) / len(recent_values)


def forecast_ridership_regression(
    date_strings: list[str],
    passenger_counts: list[int],
    future_days: int = 7,
    poly_degree: int = 1
) -> dict:
    """
    Train Linear / Polynomial Regression model on historical ridership dates and counts.
    Returns:
      - historical_fitted: list of dicts {date, actual, predicted}
      - future_forecast: list of dicts {date, predicted}
      - r2_score: float coefficient of determination
      - slope: trend slope (passengers per day)
    """
    if not date_strings or len(date_strings) < 2:
        return {
            "status": "error",
            "message": "At least 2 historical data points are required for regression forecasting.",
            "historical_fitted": [],
            "future_forecast": [],
            "r2_score": 0.0,
            "slope": 0.0
        }

    # Convert date strings to datetime objects and ordinals
    dates = [datetime.strptime(d, "%Y-%m-%d") for d in date_strings]
    base_date = min(dates)
    
    # Feature X: days since base_date
    X_days = np.array([(d - base_date).days for d in dates]).reshape(-1, 1)
    y = np.array(passenger_counts)

    if poly_degree > 1:
        poly = PolynomialFeatures(degree=poly_degree)
        X_poly = poly.fit_transform(X_days)
        model = LinearRegression()
        model.fit(X_poly, y)
        fitted_y = model.predict(X_poly)
        r2 = model.score(X_poly, y)
        slope = (fitted_y[-1] - fitted_y[0]) / max(1, (X_days[-1][0] - X_days[0][0]))
    else:
        model = LinearRegression()
        model.fit(X_days, y)
        fitted_y = model.predict(X_days)
        r2 = model.score(X_days, y)
        slope = float(model.coef_[0])

    historical_fitted = []
    for d_str, actual, pred in zip(date_strings, passenger_counts, fitted_y):
        historical_fitted.append({
            "date": d_str,
            "actual": int(actual),
            "predicted": round(float(pred), 1)
        })

    # Predict future days
    last_day_idx = max(X_days.flatten())
    future_forecast = []
    
    for i in range(1, future_days + 1):
        future_day_idx = last_day_idx + i
        future_dt = base_date + timedelta(days=int(future_day_idx))
        
        if poly_degree > 1:
            future_X = poly.transform(np.array([[future_day_idx]]))
            pred_val = float(model.predict(future_X)[0])
        else:
            pred_val = float(model.predict(np.array([[future_day_idx]]))[0])
            
        future_forecast.append({
            "date": future_dt.strftime("%Y-%m-%d"),
            "predicted": max(0, round(pred_val, 1))
        })

    return {
        "status": "success",
        "historical_fitted": historical_fitted,
        "future_forecast": future_forecast,
        "r2_score": max(0.0, float(r2)),
        "slope": round(float(slope), 2),
        "model_type": "Polynomial Regression" if poly_degree > 1 else "Linear Regression"
    }