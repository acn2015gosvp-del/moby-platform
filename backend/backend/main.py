from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes_alerts import router as alerts_router
from api.routes_sensors import router as sensors_router

app = FastAPI(title="MOBY Platform Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(alerts_router, prefix="/api/alerts", tags=["Alerts"])
app.include_router(sensors_router, prefix="/api/sensors", tags=["Sensors"])

@app.get("/")
def root():
    return {"message": "MOBY Backend Running"}
