from fastapi import APIRouter
from schemas.sensor_schema import SensorData

router = APIRouter()

fake_sensors = []

@router.get("/")
def get_sensor_data():
    return {"sensors": fake_sensors}

@router.post("/")
def add_sensor_data(data: SensorData):
    fake_sensors.append(data.dict())
    return {"status": "ok", "data": data}
