from pydantic import BaseModel

class AlertResponse(BaseModel):
    status: str
    message: str
    llm_summary: str | None = None
