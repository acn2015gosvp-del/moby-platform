"""
Grafana 연동 API 엔드포인트

Grafana 데이터 소스 및 대시보드 관리를 위한 API를 제공합니다.
"""

import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from pydantic import BaseModel, Field

from backend.api.core.responses import SuccessResponse, ErrorResponse
from backend.api.core.api_exceptions import BadRequestError, InternalServerError
from backend.api.core.permissions import require_permissions
from backend.api.models.role import Permission
from backend.api.models.user import User
from backend.api.services.grafana_client import get_grafana_client, GrafanaClient
from backend.api.services.schemas.models.core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/grafana", tags=["Grafana"])


# 요청/응답 스키마
class DatasourceCreateRequest(BaseModel):
    """데이터 소스 생성 요청"""
    name: str = Field(..., description="데이터 소스 이름")
    type: str = Field(default="influxdb", description="데이터 소스 타입")
    url: Optional[str] = Field(None, description="InfluxDB URL (선택사항)")
    is_default: bool = Field(default=False, description="기본 데이터 소스로 설정할지 여부")


class DashboardCreateRequest(BaseModel):
    """대시보드 생성 요청"""
    title: str = Field(..., description="대시보드 제목")
    datasource_name: str = Field(default="InfluxDB", description="데이터 소스 이름")


def get_grafana_client_dependency() -> GrafanaClient:
    """
    Grafana 클라이언트 의존성
    
    Returns:
        GrafanaClient 인스턴스
        
    Raises:
        HTTPException: Grafana 클라이언트를 초기화할 수 없는 경우
    """
    client = get_grafana_client()
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Grafana 클라이언트를 초기화할 수 없습니다. GRAFANA_URL과 GRAFANA_API_KEY를 확인하세요."
        )
    return client


@router.get("/health", response_model=SuccessResponse)
async def check_grafana_connection(
    client: GrafanaClient = Depends(get_grafana_client_dependency)
):
    """
    Grafana 연결 상태 확인
    
    Returns:
        연결 상태 정보
    """
    try:
        is_connected = client.test_connection()
        if is_connected:
            return SuccessResponse(
                data={"status": "connected", "url": client.base_url},
                message="Grafana 연결 성공"
            )
        else:
            return SuccessResponse(
                data={"status": "disconnected", "url": client.base_url},
                message="Grafana 연결 실패"
            )
    except Exception as e:
        logger.exception("Grafana 연결 확인 중 오류 발생")
        raise InternalServerError(message=f"Grafana 연결 확인 실패: {str(e)}")


@router.post("/datasources", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED)
async def create_datasource(
    request: DatasourceCreateRequest,
    current_user: User = Depends(require_permissions(Permission.GRAFANA_WRITE)),
    client: GrafanaClient = Depends(get_grafana_client_dependency)
):
    """
    InfluxDB 데이터 소스 생성
    
    Args:
        request: 데이터 소스 생성 요청
        
    Returns:
        생성된 데이터 소스 정보
    """
    try:
        result = client.create_datasource(
            name=request.name,
            type=request.type,
            url=request.url,
            is_default=request.is_default
        )
        
        return SuccessResponse(
            data=result,
            message=f"데이터 소스 '{request.name}' 생성 완료"
        )
    except ValueError as e:
        raise BadRequestError(message=str(e))
    except Exception as e:
        logger.exception("데이터 소스 생성 중 오류 발생")
        raise InternalServerError(message=f"데이터 소스 생성 실패: {str(e)}")


@router.get("/datasources/{name}", response_model=SuccessResponse)
async def get_datasource(
    name: str,
    current_user: User = Depends(require_permissions(Permission.GRAFANA_READ)),
    client: GrafanaClient = Depends(get_grafana_client_dependency)
):
    """
    데이터 소스 조회
    
    Args:
        name: 데이터 소스 이름
        
    Returns:
        데이터 소스 정보
    """
    try:
        datasource = client.get_datasource_by_name(name)
        if datasource is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"데이터 소스를 찾을 수 없습니다: {name}"
            )
        
        return SuccessResponse(
            data=datasource,
            message=f"데이터 소스 '{name}' 조회 완료"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("데이터 소스 조회 중 오류 발생")
        raise InternalServerError(message=f"데이터 소스 조회 실패: {str(e)}")


@router.post("/dashboards", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED)
async def create_dashboard(
    request: DashboardCreateRequest,
    current_user: User = Depends(require_permissions(Permission.GRAFANA_WRITE)),
    client: GrafanaClient = Depends(get_grafana_client_dependency)
):
    """
    센서 데이터 대시보드 생성
    
    Args:
        request: 대시보드 생성 요청
        
    Returns:
        생성된 대시보드 정보
    """
    try:
        result = client.create_sensor_dashboard(
            dashboard_title=request.title,
            datasource_name=request.datasource_name
        )
        
        return SuccessResponse(
            data=result,
            message=f"대시보드 '{request.title}' 생성 완료"
        )
    except ValueError as e:
        raise BadRequestError(message=str(e))
    except Exception as e:
        logger.exception("대시보드 생성 중 오류 발생")
        raise InternalServerError(message=f"대시보드 생성 실패: {str(e)}")


# Grafana Webhook 엔드포인트 (Track A)
# 명세서에 따라 /api/webhook/grafana 엔드포인트도 지원
@router.post("/webhook/alert", response_model=SuccessResponse, status_code=status.HTTP_200_OK)
@router.post("/webhook/grafana", response_model=SuccessResponse, status_code=status.HTTP_200_OK)
async def receive_grafana_webhook(
    webhook_data: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """
    Grafana Webhook을 받아서 알림을 처리합니다. (Track A)
    
    명세서 요구사항:
    - Grafana Alerting 수신: is_critical_active = True 설정 → 즉시 전송(CRITICAL/Red)
    - Grafana OK 수신: is_critical_active = False 설정 → 해제 전송(RESOLVED/Green)
    
    Args:
        webhook_data: Grafana에서 전송한 웹훅 데이터
        background_tasks: 백그라운드 작업 처리
        
    Returns:
        처리 결과
    """
    from backend.api.services.alert_state_manager import get_alert_state_manager
    from backend.api.services.websocket_notifier import get_websocket_notifier
    from backend.api.services.alert_storage import save_alert
    from backend.api.services.database import SessionLocal
    from backend.api.services.alert_priority_service import process_grafana_alert
    from datetime import datetime
    
    try:
        # ============================================================
        # 1. Robust JSON Parsing
        # ============================================================
        logger.info("📩 [Webhook Received] Grafana Webhook 수신")
        print(f"📩 Raw Payload: {webhook_data}")  # 디버깅용 전체 페이로드 출력
        logger.debug(f"Webhook 데이터: {webhook_data}")
        
        # Grafana 알림 배열 확인
        alerts = webhook_data.get("alerts", [])
        if not alerts:
            logger.warning("⚠️ Grafana Webhook에 alerts가 없습니다.")
            print("⚠️ No alerts found in payload")
            return SuccessResponse(
                success=True,
                data={"processed": False, "reason": "알림 데이터 없음"},
                message="Grafana 알림 처리 완료"
            )
        
        # 첫 번째 알림에서 정보 추출
        first_alert = alerts[0]
        
        # State 확인 (payload의 최상위 또는 alert 내부)
        state = webhook_data.get("state", "").lower() or first_alert.get("state", "").lower()
        
        # Labels 추출 (중첩 구조 탐색)
        labels = first_alert.get("labels", {})
        
        print(f"📋 Parsed Labels: {labels}")
        print(f"📋 State: {state}")
        
        # ============================================================
        # 2. Sensor Name Extraction (우선순위: host > instance > device > device_id)
        # ============================================================
        sensor_name = (
            labels.get("host") or 
            labels.get("instance") or 
            labels.get("device") or 
            labels.get("device_id") or 
            "Unknown Device"
        )
        
        # Alert Title 추출
        alert_name = labels.get("alertname", "System Alert")
        
        # RUL Alert 감지 (alertname에 "RUL" 또는 "Remaining Useful Life" 포함 여부 확인)
        is_rul_alert = (
            "rul" in alert_name.lower() or 
            "remaining useful life" in alert_name.lower() or
            "remaining_useful_life" in alert_name.lower() or
            labels.get("alert_type", "").lower() == "rul"
        )
        
        print(f"✅ Extracted sensor_name: {sensor_name}")
        print(f"✅ Extracted alert_name: {alert_name}")
        print(f"✅ Is RUL Alert: {is_rul_alert}")
        
        # ============================================================
        # 3. State Machine: Broadcast Logic
        # ============================================================
        state_manager = get_alert_state_manager()
        notifier = get_websocket_notifier()
        
        # RUL Alert 처리 (우선순위: RUL Alert가 일반 alerting보다 먼저 처리)
        if state == "alerting" and is_rul_alert:
            # ============================================================
            # Case RUL: RUL Alert → RUL_ALERT 타입으로 전송
            # ============================================================
            
            # Annotations에서 메시지 추출 (Grafana가 보내는 형식)
            annotations = first_alert.get("annotations", {})
            rul_message = (
                annotations.get("description") or 
                annotations.get("summary") or 
                "⚠️ Critical: Equipment RUL is below 5 hours!"
            )
            
            # WebSocket 전송 데이터 구성
            websocket_payload = {
                "type": "RUL_ALERT",
                "message": rul_message,
                "color": "orange",
                "sensor": sensor_name,
                "device_id": sensor_name,
                "alert_name": alert_name,
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"🚀 Broadcasting (RUL_ALERT): {websocket_payload}")
            logger.info(f"🚀 [Broadcasting] WebSocket으로 RUL_ALERT 알림 전송: {websocket_payload}")
            
            # WebSocket으로 브로드캐스트
            try:
                websocket_success = await notifier.send_all(websocket_payload)
                if websocket_success:
                    logger.info(
                        f"✅ RUL Alert 처리 완료. "
                        f"Device: {sensor_name}, Message: {rul_message}"
                    )
                else:
                    logger.warning(f"⚠️ WebSocket 전송 실패: 연결된 클라이언트가 없습니다.")
            except Exception as e:
                logger.error(f"❌ WebSocket 전송 실패 (RUL Alert): {e}", exc_info=True)
            
            # 이메일 알림 전송 (RUL Alert는 WARNING 레벨로 처리)
            try:
                from backend.api.services.email_service import alert_email_manager
                email_success = await alert_email_manager.handle_alert(
                    alert_type="WARNING",
                    message=rul_message,
                    source=sensor_name,
                    severity=4  # RUL Alert는 높은 심각도
                )
                if email_success:
                    logger.info(f"✅ RUL Alert 이메일 전송 완료: {sensor_name}")
            except Exception as e:
                logger.warning(f"📧 RUL Alert 이메일 전송 중 오류 (무시): {e}", exc_info=True)
            
            # 데이터베이스에 저장
            try:
                db = SessionLocal()
                try:
                    alert_id = f"rul-{sensor_name}-{int(datetime.now().timestamp())}"
                    save_alert(
                        db=db,
                        alert_id=alert_id,
                        sensor_id=sensor_name,
                        level="warning",  # RUL Alert는 warning 레벨
                        message=rul_message,
                        source="grafana-rul-webhook",
                        details={
                            "alert_name": alert_name,
                            "alert_type": "RUL",
                            "labels": labels,
                            "annotations": annotations
                        }
                    )
                    logger.info(f"✅ RUL Alert 저장 완료: {alert_id}")
                finally:
                    db.close()
            except Exception as e:
                logger.warning(f"RUL Alert 저장 중 오류 (무시): {e}", exc_info=True)
            
            return SuccessResponse(
                success=True,
                data={
                    "processed": True,
                    "alert_type": "RUL_ALERT",
                    "device": sensor_name,
                    "message": rul_message
                },
                message="RUL Alert 처리 완료"
            )
        
        elif state == "alerting":
            # ============================================================
            # Case A: state == "alerting" → CRITICAL
            # ============================================================
            
            # IS_CRITICAL = True 설정 (전역 상태 업데이트)
            state_manager.set_critical_active(device_id=sensor_name)
            
            # 메시지 구성
            alert_message = f"🚨 [{alert_name}] {sensor_name} 임계치 초과!"
            
            # WebSocket 전송 데이터 구성
            websocket_payload = {
                "type": "CRITICAL",
                "message": alert_message,
                "color": "red",
                "sensor": sensor_name,
                "device_id": sensor_name,
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"🚀 Broadcasting (CRITICAL): {websocket_payload}")
            logger.info(f"🚀 [Broadcasting] WebSocket으로 CRITICAL 알림 전송: {websocket_payload}")
            
            # WebSocket으로 브로드캐스트
            try:
                websocket_success = await notifier.send_all(websocket_payload)
                if websocket_success:
                    logger.info(
                        f"✅ Grafana Alerting 처리 완료 (IS_CRITICAL=True). "
                        f"Device: {sensor_name}, Message: {alert_message}"
                    )
                else:
                    logger.warning(f"⚠️ WebSocket 전송 실패: 연결된 클라이언트가 없습니다.")
            except Exception as e:
                logger.error(f"❌ WebSocket 전송 실패 (Critical): {e}", exc_info=True)
            
            # 메신저 알림 전송 (Slack, Telegram) - 백그라운드에서 비동기 처리
            try:
                from backend.api.services.messenger_service import send_messenger_notifications
                messenger_results = await send_messenger_notifications(
                    message=alert_message,
                    alert_type="CRITICAL",
                    device_id=sensor_name
                )
                logger.info(f"📱 메신저 알림 전송 결과: Slack={messenger_results.get('slack', False)}, Telegram={messenger_results.get('telegram', False)}")
            except Exception as e:
                logger.warning(f"메신저 알림 전송 중 오류 (무시): {e}")
            
            # 이메일 알림 전송 - 백그라운드에서 비동기 처리
            try:
                from backend.api.services.email_service import alert_email_manager
                email_success = await alert_email_manager.handle_alert(
                    alert_type="CRITICAL",
                    message=alert_message,
                    source=sensor_name,
                    severity=5  # CRITICAL은 최고 심각도
                )
                if email_success:
                    logger.info(f"📧 이메일 알림 전송 성공: {sensor_name}")
                else:
                    logger.warning(f"📧 이메일 알림 전송 실패 또는 Throttle: {sensor_name}")
            except Exception as e:
                logger.warning(f"이메일 알림 전송 중 오류 (무시): {e}")
            
            # 백그라운드에서 DB 저장 (WebSocket 전송과 분리)
            def store_alert():
                db = SessionLocal()
                try:
                    grafana_alert = process_grafana_alert(webhook_data, sensor_id=sensor_name)
                    if grafana_alert:
                        save_alert(db, grafana_alert)
                        logger.debug(f"✅ Critical 알림 저장 완료: {sensor_name}")
                except Exception as e:
                    logger.error(f"Critical 알림 저장 실패: {e}", exc_info=True)
                finally:
                    db.close()
            
            background_tasks.add_task(store_alert)
            
        elif state == "ok":
            # ============================================================
            # Case B: state == "ok" → RESOLVED
            # ============================================================
            
            # IS_CRITICAL = False 설정 (전역 상태 업데이트)
            state_manager.set_critical_inactive()
            
            # 메시지 구성
            alert_message = f"✅ [{alert_name}] {sensor_name} 정상화."
            
            # WebSocket 전송 데이터 구성
            websocket_payload = {
                "type": "RESOLVED",
                "message": alert_message,
                "color": "green",
                "sensor": sensor_name,
                "device_id": sensor_name,
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"🚀 Broadcasting (RESOLVED): {websocket_payload}")
            logger.info(f"🚀 [Broadcasting] WebSocket으로 RESOLVED 알림 전송: {websocket_payload}")
            
            # WebSocket으로 브로드캐스트
            try:
                websocket_success = await notifier.send_all(websocket_payload)
                if websocket_success:
                    logger.info(
                        f"✅ Grafana OK 처리 완료 (IS_CRITICAL=False). "
                        f"Device: {sensor_name}, Message: {alert_message}"
                    )
                else:
                    logger.warning(f"⚠️ WebSocket 전송 실패: 연결된 클라이언트가 없습니다.")
            except Exception as e:
                logger.error(f"❌ WebSocket 전송 실패 (Resolved): {e}", exc_info=True)
            
            # 메신저 알림 전송 (Slack, Telegram) - 백그라운드에서 비동기 처리
            try:
                from backend.api.services.messenger_service import send_messenger_notifications
                messenger_results = await send_messenger_notifications(
                    message=alert_message,
                    alert_type="RESOLVED",
                    device_id=sensor_name
                )
                logger.info(f"📱 메신저 알림 전송 결과: Slack={messenger_results.get('slack', False)}, Telegram={messenger_results.get('telegram', False)}")
            except Exception as e:
                logger.warning(f"메신저 알림 전송 중 오류 (무시): {e}")
            
            # 이메일 알림 전송 (RESOLVED는 이메일 발송 안함 - 정상화 알림이므로)
            # 필요시 아래 주석을 해제하여 RESOLVED도 이메일로 발송할 수 있습니다.
            # try:
            #     from backend.api.services.email_service import alert_email_manager
            #     email_success = await alert_email_manager.handle_alert(
            #         alert_type="RESOLVED",
            #         message=alert_message,
            #         source=sensor_name,
            #         severity=1  # RESOLVED는 낮은 심각도
            #     )
            #     if email_success:
            #         logger.info(f"📧 이메일 알림 전송 성공: {sensor_name}")
            # except Exception as e:
            #     logger.warning(f"이메일 알림 전송 중 오류 (무시): {e}")
        elif state == "pending":
            # ============================================================
            # Case C: state == "pending" → WARNING
            # ============================================================
            
            # 메시지 구성
            alert_message = f"⚠️ [{alert_name}] {sensor_name} 임계치 초과 (대기 중)"
            
            # WebSocket 전송 데이터 구성
            websocket_payload = {
                "type": "WARNING",
                "message": alert_message,
                "color": "orange",
                "sensor": sensor_name,
                "device_id": sensor_name,
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"🚀 Broadcasting (WARNING - Pending): {websocket_payload}")
            logger.info(f"🚀 [Broadcasting] WebSocket으로 WARNING 알림 전송 (Pending): {websocket_payload}")
            
            # WebSocket으로 브로드캐스트
            try:
                websocket_success = await notifier.send_all(websocket_payload)
                if websocket_success:
                    logger.info(
                        f"✅ Grafana Pending 처리 완료 (WARNING). "
                        f"Device: {sensor_name}, Message: {alert_message}"
                    )
                else:
                    logger.warning(f"⚠️ WebSocket 전송 실패: 연결된 클라이언트가 없습니다.")
            except Exception as e:
                logger.error(f"❌ WebSocket 전송 실패 (Warning - Pending): {e}", exc_info=True)
            
            # 백그라운드에서 DB 저장 (WebSocket 전송과 분리)
            def store_alert():
                db = SessionLocal()
                try:
                    grafana_alert = process_grafana_alert(webhook_data, sensor_id=sensor_name)
                    if grafana_alert:
                        save_alert(db, grafana_alert)
                        logger.debug(f"✅ Warning (Pending) 알림 저장 완료: {sensor_name}")
                except Exception as e:
                    logger.error(f"Warning (Pending) 알림 저장 실패: {e}", exc_info=True)
                finally:
                    db.close()
            
            background_tasks.add_task(store_alert)
        else:
            logger.debug(f"Grafana 알림 상태 처리 불필요: state={state}")
        
        return SuccessResponse(
            success=True,
            data={
                "state": state,
                "processed": True
            },
            message="Grafana 알림 처리 완료"
        )
        
    except Exception as e:
        logger.exception(f"Grafana Webhook 처리 중 오류 발생: {e}")
        raise InternalServerError(
            message=f"Grafana Webhook 처리 실패: {str(e)}"
        )
