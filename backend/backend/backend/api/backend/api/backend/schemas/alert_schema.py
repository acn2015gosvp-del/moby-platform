from pydantic import BaseModel
from typing import Optional

class AlertItem(BaseModel):
    id: str
    level: str
    message: str
    sensor_id: str
    ts: str
    llm_summary: Optional[str] = None
