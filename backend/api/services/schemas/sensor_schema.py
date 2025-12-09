from pydantic import BaseModel

class SensorData(BaseModel):
    device_id: str
    temperature: float | None = None
    humidity: float | None = None
    vibration: float | None = None
    sound: float | None = None
