from fastapi import FastAPI
from api.routes_alerts import router as alerts_router
from api.routes_sensors import router as sensors_router

app = FastAPI(
    title="MOBY Backend API",
    description="Industrial IoT & Predictive Maintenance Platform",
    version="1.0.0",
)

app.include_router(alerts_router, prefix="/alerts", tags=["Alerts"])
app.include_router(sensors_router, prefix="/sensors", tags=["Sensors"])

@app.get("/")
def root():
    return {"status": "ok", "msg": "MOBY Backend Running"}
