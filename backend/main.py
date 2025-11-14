from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from api.routes_auth import router as auth_router
from api.routes_facilities import router as facilities_router
from api.routes_alerts import router as alerts_router
from api.routes_reports import router as reports_router
from api.routes_health import router as health_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="MOBY Industrial IoT & PdM API",
        version="0.1.0",
        description="MOBY Industrial IoT & Predictive Maintenance Platform Backend (FastAPI)",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 라우터 등록
    app.include_router(auth_router, prefix="/auth", tags=["auth"])
    app.include_router(facilities_router, prefix="/facilities", tags=["facilities"])
    app.include_router(alerts_router, prefix="/alerts", tags=["alerts"])
    app.include_router(reports_router, prefix="/reports", tags=["reports"])
    app.include_router(health_router, tags=["health"])

    return app


app = create_app()

