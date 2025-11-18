from fastapi import FastAPI
from backend.api.routes_alerts import router as alerts_router
from backend.api.routes_sensors import router as sensors_router
from backend.api.routes_auth import router as auth_router
from backend.api.routes_grafana import router as grafana_router
from backend.api.routes_health import router as health_router, set_app_start_time
from contextlib import asynccontextmanager
from backend.api.services.mqtt_client import init_mqtt_client # ✅ MQTT 초기화 함수 임포트
from backend.api.services.database import init_db  # ✅ 데이터베이스 초기화

# 로깅 설정 초기화 (가장 먼저 실행)
from backend.api.services.schemas.models.core.logger import setup_logging, get_logger
from backend.api.services.schemas.models.core.config import settings

# Prometheus 메트릭
from prometheus_fastapi_instrumentator import Instrumentator

# Rate Limiting
from backend.api.middleware.rate_limit import RateLimitMiddleware

# CSRF Protection
from backend.api.middleware.csrf import CSRFMiddleware

# 로깅 설정
setup_logging(
    log_level=settings.LOG_LEVEL,
    log_file="logs/moby.log" if settings.is_production() else ("logs/moby-debug.log" if settings.DEBUG else None)
)

logger = get_logger(__name__)

# -------------------------------------------------------------------
# FastAPI Lifespan (애플리케이션 생명주기 관리)
# -------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    서버 시작 및 종료 시 실행할 코드를 정의합니다.
    """
    # 1. 서버 시작 (Startup)
    logger.info("Application starting up: Validating configuration...")
    
    # 환경 변수 검증 (프로덕션 환경에서 필수 설정 누락 시 시작 중단)
    try:
        settings.validate_and_raise()
        logger.info("✅ Configuration validation passed.")
    except ValueError as e:
        logger.critical(f"❌ Configuration validation failed: {e}")
        raise  # 애플리케이션 시작 중단
    
    logger.info("Initializing database and MQTT client...")
    set_app_start_time()  # 애플리케이션 시작 시간 설정
    init_db()  # ✅ 데이터베이스 테이블 생성
    init_mqtt_client()  # ✅ MQTT 연결 시도 및 재시도 로직 호출
    
    # 2. 애플리케이션 실행 (Yield)
    yield
    
    # 3. 서버 종료 (Shutdown)
    logger.info("Application shutting down: No specific MQTT cleanup needed (paho handles it).")

# -------------------------------------------------------------------

app = FastAPI(
    # ✅ lifespan 핸들러 등록
    lifespan=lifespan,
    title="MOBY Backend API",
    description="Industrial IoT & Predictive Maintenance Platform",
    version="1.0.0",
)

# Rate Limiting 미들웨어 추가
app.add_middleware(
    RateLimitMiddleware,
    default_limit=100,  # 기본: 100 requests per minute
    window_seconds=60,
)

# CSRF 방지 미들웨어 추가 (개발 환경에서는 선택적)
if settings.is_production():
    app.add_middleware(
        CSRFMiddleware,
        secret_key=settings.SECRET_KEY,
        cookie_name="csrf_token"
    )

# Routers
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(grafana_router, tags=["Grafana"])
app.include_router(alerts_router, prefix="/alerts", tags=["Alerts"])
app.include_router(sensors_router, prefix="/sensors", tags=["Sensors"])
app.include_router(health_router, tags=["Health"])

# Prometheus 메트릭 수집기 설정
instrumentator = Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=True,
    should_instrument_requests_inprogress=True,
    excluded_handlers=["/metrics", "/health", "/health/liveness", "/health/readiness"],
    inprogress_name="http_requests_inprogress",
    inprogress_labels=True,
)
instrumentator.instrument(app)
instrumentator.expose(app, endpoint="/metrics")


@app.get("/")
async def root():
    """루트 엔드포인트 - API 상태 확인"""
    return {"status": "ok", "message": "MOBY backend running"}