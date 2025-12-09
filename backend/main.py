from fastapi import FastAPI, Request, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

# 로깅 설정 초기화 (가장 먼저 실행 - 다른 임포트 전에)
from backend.api.services.schemas.models.core.logger import setup_logging, get_logger
from backend.api.services.schemas.models.core.config import settings

# 로깅 설정
setup_logging(
    log_level=settings.LOG_LEVEL,
    log_file="logs/moby.log" if settings.is_production() else ("logs/moby-debug.log" if settings.DEBUG else None)
)

logger = get_logger(__name__)

# 필수 서비스만 즉시 임포트 (초기화에 필요)
from backend.api.services.database import init_db  # ✅ 데이터베이스 초기화
from backend.api.services.scheduler import init_scheduler, shutdown_scheduler  # ✅ 스케줄러 초기화
from backend.api.routes_health import set_app_start_time

# 라우터 및 기타 모듈은 지연 로딩 (lifespan이나 app 생성 시 임포트)
# 이렇게 하면 서버 시작 시점의 임포트 시간을 줄일 수 있습니다.

# -------------------------------------------------------------------
# FastAPI Lifespan (애플리케이션 생명주기 관리)
# -------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    서버 시작 및 종료 시 실행할 코드를 정의합니다.
    """
    import time
    startup_start = time.time()
    
    # 1. 서버 시작 (Startup)
    logger.info("Application starting up: Validating configuration...")
    
    # 환경 변수 검증 (프로덕션 환경에서 필수 설정 누락 시 시작 중단)
    try:
        step_start = time.time()
        settings.validate_and_raise()
        step_time = (time.time() - step_start) * 1000
        logger.info(f"✅ Configuration validation passed. ({step_time:.1f}ms)")
    except ValueError as e:
        logger.critical(f"❌ Configuration validation failed: {e}")
        raise  # 애플리케이션 시작 중단
    
    # 필수 초기화 작업 (서버 시작 전 반드시 완료해야 할 작업)
    logger.info("Initializing core services...")
    step_start = time.time()
    set_app_start_time()  # 애플리케이션 시작 시간 설정
    step_time = (time.time() - step_start) * 1000
    logger.debug(f"App start time set ({step_time:.1f}ms)")
    
    # 데이터베이스 초기화 (동기 - 빠른 작업이므로 블로킹 허용)
    step_start = time.time()
    try:
        init_db()  # ✅ 데이터베이스 테이블 생성 (빠른 작업)
        step_time = (time.time() - step_start) * 1000
        logger.info(f"✅ Database initialization completed ({step_time:.1f}ms)")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}", exc_info=True)
        # 데이터베이스 초기화 실패해도 서버는 시작 (나중에 재시도 가능)
    
    # 비동기/백그라운드 초기화 작업 (서버 시작을 블로킹하지 않음)
    import threading
    
    # MQTT 초기화를 백그라운드 스레드로 처리 (블로킹 방지)
    def init_mqtt_async():
        try:
            # 지연 로딩: MQTT 클라이언트는 필요할 때만 임포트
            from backend.api.services.mqtt_client import init_mqtt_client
            init_mqtt_client()  # ✅ MQTT 연결 시도 및 재시도 로직 호출
        except Exception as e:
            logger.warning(f"MQTT 초기화 중 오류 (비동기): {e}")
    
    mqtt_thread = threading.Thread(target=init_mqtt_async, daemon=True, name="MQTT-Init")
    mqtt_thread.start()
    logger.info("✅ MQTT 초기화를 백그라운드에서 시작했습니다.")
    
    # 스케줄러 초기화 (매일 18:00 일일 보고서 생성 및 이메일 발송)
    try:
        step_start = time.time()
        init_scheduler()
        step_time = (time.time() - step_start) * 1000
        logger.info(f"✅ 스케줄러 초기화 완료 ({step_time:.1f}ms)")
    except Exception as e:
        logger.warning(f"스케줄러 초기화 중 오류 발생: {e}")
    
    # 이메일 알림 서비스 초기화를 백그라운드로 이동 (서버 시작 속도 개선)
    def init_email_async():
        try:
            from backend.api.services.email_service import alert_email_manager
            
            # SMTP 설정 확인 (None 체크 포함)
            smtp_configs = [
                settings.SMTP_HOST,
                settings.SMTP_USER,
                settings.SMTP_PASSWORD,
                settings.SMTP_FROM_EMAIL,
                settings.SMTP_TO_EMAILS
            ]
            
            if all(config and str(config).strip() for config in smtp_configs):
                try:
                    # 수신자 이메일 파싱 (쉼표로 구분)
                    to_emails = [email.strip() for email in str(settings.SMTP_TO_EMAILS).split(',') if email.strip()]
                    
                    if not to_emails:
                        logger.warning("⚠️ SMTP_TO_EMAILS에 유효한 이메일 주소가 없습니다.")
                    else:
                        alert_email_manager.initialize(
                            smtp_host=str(settings.SMTP_HOST).strip(),
                            smtp_port=settings.SMTP_PORT,
                            smtp_user=str(settings.SMTP_USER).strip(),
                            smtp_password=str(settings.SMTP_PASSWORD).strip(),
                            from_email=str(settings.SMTP_FROM_EMAIL).strip(),
                            to_emails=to_emails,
                            max_retries=3,
                            throttle_window=60  # 1분으로 단축 (테스트용, 필요시 조정 가능)
                        )
                        logger.info("✅ 이메일 알림 서비스 초기화 완료")
                except Exception as init_error:
                    logger.error(f"❌ 이메일 서비스 초기화 중 오류: {init_error}", exc_info=True)
            else:
                logger.debug("⚠️ 이메일 알림 서비스 설정이 없습니다. SMTP 설정을 추가하면 이메일 알림을 사용할 수 있습니다.")
        except ImportError as e:
            logger.warning(f"이메일 서비스 모듈을 불러올 수 없습니다: {e}")
        except Exception as e:
            logger.error(f"이메일 알림 서비스 초기화 중 예상치 못한 오류 발생: {e}", exc_info=True)
    
    email_thread = threading.Thread(target=init_email_async, daemon=True, name="Email-Init")
    email_thread.start()
    logger.info("✅ 이메일 알림 서비스 초기화를 백그라운드에서 시작했습니다.")
    
    # 서버 IP 주소 설정 (타임아웃 설정으로 빠른 실패 처리)
    import socket
    step_start = time.time()
    FASTAPI_SERVER_IP = "127.0.0.1"  # 기본값 설정
    try:
        # 외부 연결을 시도하여 로컬 IP 확인 (1초 타임아웃 - 빠른 시작)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(1.0)  # 1초 타임아웃 설정 (네트워크가 없을 때 빠른 실패)
        s.connect(("8.8.8.8", 80))
        FASTAPI_SERVER_IP = s.getsockname()[0]
        s.close()
        step_time = (time.time() - step_start) * 1000
        logger.debug(f"IP 주소 자동 감지 완료: {FASTAPI_SERVER_IP} ({step_time:.1f}ms)")
    except (socket.timeout, OSError, Exception):
        # 타임아웃 또는 네트워크 오류 시 localhost 사용 (빠르게 진행)
        FASTAPI_SERVER_IP = "127.0.0.1"
        step_time = (time.time() - step_start) * 1000
        logger.debug(f"IP 주소 자동 감지 실패, localhost 사용 ({step_time:.1f}ms)")
    
    # 전체 시작 시간 로깅
    total_startup_time = (time.time() - startup_start) * 1000
    logger.info(f"⚡ 서버 시작 완료 (총 {total_startup_time:.1f}ms)")
    
    # Grafana Webhook URL 정보 출력 (서버 시작 완료 후)
    GRAFANA_WEBHOOK_IP = FASTAPI_SERVER_IP
    GRAFANA_WEBHOOK_PORT = 8000
    webhook_url = f"http://{GRAFANA_WEBHOOK_IP}:{GRAFANA_WEBHOOK_PORT}/api/webhook/grafana"
    logger.info("")
    logger.info("=" * 70)
    logger.info("✅ Grafana Webhook URL:")
    logger.info(f"   {webhook_url}")
    logger.info("=" * 70)
    logger.info("")
    logger.info("📋 Grafana 관리자(Stark)에게 전달할 정보:")
    logger.info(f"   Webhook URL: {webhook_url}")
    logger.info("   Method: POST")
    logger.info("   Content-Type: application/json")
    logger.info("")
    
    # 2. 애플리케이션 실행 (Yield)
    yield
    
    # 3. 서버 종료 (Shutdown)
    logger.info("Application shutting down: Cleaning up resources...")
    
    # 스케줄러 종료
    try:
        shutdown_scheduler()
    except Exception as e:
        logger.warning(f"스케줄러 종료 중 오류 발생: {e}")
    
    logger.info("Application shutdown complete.")

# -------------------------------------------------------------------

# 라우터 지연 로딩 (app 생성 후 임포트하여 시작 시간 단축)
def _load_routers():
    """라우터를 지연 로딩합니다."""
    from backend.api.routes_sensors import router as sensors_router
    from backend.api.routes_alerts import router as alerts_router
    from backend.api.routes_auth import router as auth_router
    from backend.api.routes_grafana import router as grafana_router
    from backend.api.routes_health import router as health_router
    from backend.api.routes_reports import router as reports_router
    from backend.api.routes_websocket import router as websocket_router
    from backend.api.routes_webhook import router as webhook_router
    from backend.api.routes_grafana_proxy import router as grafana_proxy_router
    
    return {
        'auth': auth_router,
        'grafana': grafana_router,
        'alerts': alerts_router,
        'sensors': sensors_router,
        'reports': reports_router,
        'health': health_router,
        'websocket': websocket_router,
        'webhook': webhook_router,
        'grafana_proxy': grafana_proxy_router,
    }

app = FastAPI(
    # ✅ lifespan 핸들러 등록
    lifespan=lifespan,
    title="MOBY Backend API",
    description="Industrial IoT & Predictive Maintenance Platform",
    version="1.0.0",
)

# ▼▼▼ CORS 미들웨어 추가 (웹소켓 연결 허용) - 필수! ▼▼▼
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 보안상 안 좋지만 테스트니까 모두 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ▲▲▲▲▲▲

# 응답 시간 측정 미들웨어 추가 (가장 먼저 - 다른 미들웨어보다 먼저 실행)
from backend.api.middleware.timing import TimingMiddleware
app.add_middleware(TimingMiddleware)

# Routers (지연 로딩)
import time
router_load_start = time.time()
routers = _load_routers()
router_load_time = (time.time() - router_load_start) * 1000
logger.debug(f"Router loading completed ({router_load_time:.1f}ms)")

app.include_router(routers['auth'], prefix="/auth", tags=["Authentication"])
app.include_router(routers['grafana'], tags=["Grafana"])
app.include_router(routers['alerts'], prefix="/alerts", tags=["Alerts"])
app.include_router(routers['sensors'], prefix="/sensors", tags=["Sensors"])
app.include_router(routers['reports'], tags=["Reports"])
app.include_router(routers['health'], tags=["Health"])
app.include_router(routers['websocket'], tags=["WebSocket"])
app.include_router(routers['webhook'], tags=["Webhook"])
app.include_router(routers['grafana_proxy'], tags=["Grafana Proxy"])

# 미들웨어 및 기타 설정 (지연 로딩 - 서버 시작 속도 개선)
# 미들웨어는 실제 요청 시에만 필요하므로 지연 로딩
def _setup_middleware():
    """미들웨어를 지연 로딩합니다."""
    from backend.api.middleware.rate_limit import RateLimitMiddleware
    from backend.api.middleware.csrf import CSRFMiddleware
    
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

# 미들웨어 설정 (지연 로딩)
_setup_middleware()

# 예외 핸들러 등록 (프론트엔드와의 일관된 에러 형식을 위해 필수)
from backend.api.core.api_exceptions import APIException
from pydantic import ValidationError

@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException):
    """APIException을 ErrorResponse 형식으로 변환"""
    error_response = exc.to_error_response()
    logger.debug(
        f"APIException 처리: {request.method} {request.url.path} -> "
        f"{exc.status_code} {exc.error_code}: {exc.detail}"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump()
    )

# Pydantic ValidationError 핸들러 추가
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Pydantic ValidationError를 ErrorResponse 형식으로 변환"""
    from backend.api.core.responses import ErrorResponse, ErrorDetail
    from datetime import datetime
    
    # ValidationError의 상세 정보 추출
    errors = exc.errors()
    error_messages = []
    for error in errors:
        field = ".".join(str(loc) for loc in error.get("loc", []))
        msg = error.get("msg", "Validation error")
        error_messages.append(f"{field}: {msg}")
    
    error_detail = "; ".join(error_messages) if error_messages else str(exc)
    
    logger.warning(
        f"ValidationError 처리: {request.method} {request.url.path} -> {error_detail}"
    )
    logger.debug(f"ValidationError 상세: {errors}")
    
    error_response = ErrorResponse(
        success=False,
        error=ErrorDetail(
            code="VALIDATION_ERROR",
            message=f"요청 데이터 검증 실패: {error_detail}"
        ),
        timestamp=datetime.utcnow().isoformat() + "Z"
    )
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=error_response.model_dump()
    )

# HTTPException 핸들러 (FastAPI 기본 예외를 ErrorResponse 형식으로 변환)
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTPException을 ErrorResponse 형식으로 변환"""
    from backend.api.core.responses import ErrorResponse, ErrorDetail
    from datetime import datetime
    
    # 에러 코드 결정
    if exc.status_code == 401:
        error_code = "UNAUTHORIZED"
    elif exc.status_code == 403:
        error_code = "FORBIDDEN"
    elif exc.status_code == 404:
        error_code = "NOT_FOUND"
    elif exc.status_code == 422:
        error_code = "VALIDATION_ERROR"
    else:
        error_code = "HTTP_ERROR"
    
    logger.debug(
        f"HTTPException 처리: {request.method} {request.url.path} -> "
        f"{exc.status_code} {error_code}: {exc.detail}"
    )
    
    error_response = ErrorResponse(
        success=False,
        error=ErrorDetail(
            code=error_code,
            message=str(exc.detail)
        ),
        timestamp=datetime.utcnow().isoformat() + "Z"
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump()
    )

# 전역 예외 핸들러: 예상치 못한 예외 처리
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """모든 예상치 못한 예외를 처리하고 로깅"""
    import traceback
    
    # HTTPException과 APIException은 이미 처리되었으므로 건너뜀
    if isinstance(exc, (HTTPException, APIException)):
        raise exc
    
    # 예외 상세 정보 로깅
    logger.error(
        f"❌ Unhandled exception in {request.method} {request.url.path}",
        exc_info=True
    )
    logger.error(f"Exception type: {type(exc).__name__}")
    logger.error(f"Exception message: {str(exc)}")
    logger.error(f"Traceback:\n{traceback.format_exc()}")
    
    # 클라이언트에게는 일반적인 에러 메시지만 반환
    from backend.api.core.responses import ErrorResponse, ErrorDetail
    from datetime import datetime
    
    error_response = ErrorResponse(
        success=False,
        error=ErrorDetail(
            code="INTERNAL_ERROR",
            message="서버 내부 오류가 발생했습니다. 관리자에게 문의하세요."
        ),
        timestamp=datetime.utcnow().isoformat() + "Z"
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump()
    )

# Prometheus 메트릭 수집기 설정 (지연 로딩 - 서버 시작 속도 개선)
def _setup_prometheus():
    """Prometheus 메트릭 수집기를 지연 로딩합니다."""
    from prometheus_fastapi_instrumentator import Instrumentator
    
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

# Prometheus 설정 (지연 로딩)
_setup_prometheus()


@app.get("/")
async def root():
    """루트 엔드포인트 - API 상태 확인"""
    return {"status": "ok", "message": "MOBY backend running"}