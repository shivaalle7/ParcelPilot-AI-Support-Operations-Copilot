from datetime import datetime
import pandas as pd

def calculate_delay(scheduled, actual):
    s = pd.to_datetime(scheduled, errors="coerce")
    a = pd.to_datetime(actual, errors="coerce")
    if pd.isna(s) or pd.isna(a):
        return {"error": "Could not parse scheduled/actual timestamps."}
    hours = (a - s).total_seconds() / 3600
    return {"delay_hours": round(hours, 2), "scheduled": str(s), "actual": str(a)}

def calculate_service_credit(delay_hours: float, threshold_hours: float, credit_percent: float = 0):
    eligible = delay_hours >= threshold_hours
    return {
        "delay_hours": round(float(delay_hours), 2),
        "threshold_hours": float(threshold_hours),
        "eligible": bool(eligible),
        "credit_percent": float(credit_percent) if eligible else 0.0,
    }
