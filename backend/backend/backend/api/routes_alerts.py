from fastapi import APIRouter
from schemas.alert_schema import AlertItem

router = APIRouter()

fake_alerts = []

@router.get("/")
def get_alerts():
    return {"alerts": fake_alerts}

@router.post("/")
def create_alert(alert: AlertItem):
    fake_alerts.append(alert.dict())
    return {"status": "ok", "alert": alert}
