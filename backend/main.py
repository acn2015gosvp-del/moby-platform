from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # 1. CORS 모듈 import
# 오류 수정: 'api.'를 'backend.api.'로 변경하여 Python 경로 문제를 해결
from backend.api.routes_alerts import router as alerts_router
from backend.api.routes_sensors import router as sensors_router

app = FastAPI(
    title="MOBY Backend API",
    description="Industrial IoT & Predictive Maintenance Platform",
    version="1.0.0",
)

# 2. Frontend 포트(5173) 및 모든 출처(*)를 허용하는 CORS 설정 추가
origins = [
    "http://localhost:5173",  # Frontend 개발 서버 포트
    "http://127.0.0.1:5173",
    "*"                       # 임시로 모든 출처를 허용 (개발 단계에서 필요)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,  # 쿠키, 인증 헤더 허용
    allow_methods=["*"],     # 모든 HTTP 메소드 허용 (GET, POST 등)
    allow_headers=["*"],     # 모든 헤더 허용
)

# Routers
app.include_router(alerts_router, prefix="/api/v1/alerts", tags=["Alerts"]) # ⚠️ prefix 수정
app.include_router(sensors_router, prefix="/api/v1/sensors", tags=["Sensors"]) # ⚠️ prefix 수정


@app.get("/")
def root():
    return {"status": "ok", "message": "MOBY backend running"}