from fastapi import APIRouter
from schemas.sensor_schema import SensorData
from services.mqtt_client import publish_message

router = APIRouter()

@router.post("/publish")
def publish_sensor_data(data: SensorData):
    publish_message("factory/sensor/data", data.dict())
    return {"status": "published", "data": data}
