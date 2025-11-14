from schemas.alert_schema import AlertResponse
from services.llm_client import summarize_alert

def evaluate_alert():
    dummy = {"anomaly_score": 0.82}
    summary = summarize_alert(dummy)

    return AlertResponse(
        status="warning",
        message="Anomaly detected",
        llm_summary=summary
    )
