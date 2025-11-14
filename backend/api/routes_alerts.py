from fastapi import APIRouter
from schemas.alert_schema import AlertResponse
from services.alert_engine import evaluate_alert

router = APIRouter()

@router.get("/latest", response_model=AlertResponse)
def get_latest_alert():
    return evaluate_alert()
