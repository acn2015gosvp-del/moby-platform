"""
센서(Sensor) 관련 API 엔드포인트

센서 데이터 수신 및 센서 상태 조회 API를 제공합니다.
"""

from fastapi import APIRouter, status, Depends
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from .services.schemas.sensor_schema import SensorData
from .core.responses import SuccessResponse, ErrorResponse
from .core.api_exceptions import BadRequestError, InternalServerError
from .services.schemas.models.core.logger import get_logger
from backend.api.services.mqtt_client import mqtt_manager
from backend.api.services.influx_client import query_sensor_status, influx_manager
from backend.api.services.schemas.models.core.config import settings
from backend.api.services.cache import get_cache, cache_key

router = APIRouter()
logger = get_logger(__name__)


class SensorDataResponse(BaseModel):
    """센서 데이터 수신 응답 모델"""
    status: str = Field(..., description="수신 상태")
    sensor_id: str = Field(..., description="센서 ID")
    timestamp: str = Field(..., description="수신 시각")


class DeviceSummary(BaseModel):
    """설비 요약 정보"""
    device_id: str = Field(..., description="설비 ID")
    name: str = Field(..., description="설비 이름")
    category: Optional[str] = Field(None, description="설비 카테고리")
    dashboardUID: str = Field(..., description="Grafana 대시보드 UID")
    status: str = Field(..., description="상태 (정상, 경고, 긴급, 오프라인)")
    sensorCount: Optional[int] = Field(None, description="센서 수")
    alertCount: Optional[int] = Field(None, description="알림 수")
    operationRate: Optional[float] = Field(None, description="가동률 (%)")
    lastUpdated: Optional[str] = Field(None, description="마지막 업데이트 시간")


class SensorStatusResponse(BaseModel):
    """센서 상태 응답 모델"""
    status: str = Field(..., description="전체 상태")
    count: int = Field(..., description="전체 센서 수")
    active: int = Field(..., description="활성 센서 수")
    inactive: int = Field(..., description="비활성 센서 수")
    devices: List[DeviceSummary] = Field(default_factory=list, description="설비 목록")


def get_current_timestamp() -> str:
    """현재 타임스탬프를 ISO 8601 형식으로 반환하는 의존성"""
    return datetime.utcnow().isoformat() + "Z"


@router.post(
    "/data",
    response_model=SuccessResponse[SensorDataResponse],
    status_code=status.HTTP_202_ACCEPTED,
    summary="센서 데이터 수신",
    description="""
    Edge 장치로부터 센서 데이터를 수신합니다.
    
    **주요 기능:**
    - 센서 데이터 수신 및 검증
    - 데이터 파이프라인으로 전달 (MQTT/InfluxDB)
    - 비동기 처리 (202 Accepted 응답)
    
    **입력 파라미터:**
    - `device_id`: 센서 장치 ID (필수)
    - `temperature`: 온도 데이터 (선택)
    - `humidity`: 습도 데이터 (선택)
    - `vibration`: 진동 데이터 (선택)
    - `sound`: 소리 데이터 (선택)
    
    **응답:**
    - `202 Accepted`: 데이터가 성공적으로 수신됨 (비동기 처리)
    - `400 Bad Request`: 잘못된 요청 데이터
    - `422 Unprocessable Entity`: 입력 데이터 검증 실패
    - `500 Internal Server Error`: 서버 내부 오류
    
    **참고:**
    - 실제 데이터 처리는 별도의 파이프라인(MQTT/InfluxDB)으로 전달됩니다.
    - 이 엔드포인트는 데이터 수신 확인만 담당합니다.
    
    **예시:**
    ```json
    {
        "device_id": "sensor_001",
        "temperature": 25.5,
        "humidity": 60.0,
        "vibration": 0.5,
        "sound": 45.2
    }
    ```
    """,
    responses={
        202: {
            "description": "데이터가 성공적으로 수신됨",
            "model": SuccessResponse[SensorDataResponse]
        },
        400: {
            "description": "잘못된 요청",
            "model": ErrorResponse
        },
        422: {
            "description": "입력 데이터 검증 실패",
            "model": ErrorResponse
        },
        500: {
            "description": "서버 내부 오류",
            "model": ErrorResponse
        }
    }
)
async def receive_sensor_data(
    data: SensorData,
    timestamp: str = Depends(get_current_timestamp)
) -> SuccessResponse[SensorDataResponse]:
    """
    Edge 장치로부터 센서 데이터를 수신합니다.
    
    실제 처리는 별도의 파이프라인(MQTT/InfluxDB)으로 전달되어야 합니다.
    
    Args:
        data: 센서 데이터
        timestamp: 현재 타임스탬프 (의존성 주입)
        
    Returns:
        SuccessResponse[SensorDataResponse]: 수신 확인 응답
        
    Raises:
        BadRequestError: 잘못된 요청 데이터
        InternalServerError: 데이터 처리 중 내부 오류
    """
    try:
        # 센서 데이터를 MQTT로 발행
        sensor_payload = {
            "device_id": data.device_id,
            "temperature": data.temperature,
            "humidity": data.humidity,
            "vibration": data.vibration,
            "sound": data.sound,
            "timestamp": timestamp
        }
        
        # MQTT 토픽: sensors/{device_id}/data
        mqtt_topic = f"sensors/{data.device_id}/data"
        
        # MQTT로 발행 (비동기 처리)
        publish_success = mqtt_manager.publish_message(mqtt_topic, sensor_payload)
        
        if publish_success:
            logger.info(
                f"Sensor data received and published to MQTT. "
                f"Device: {data.device_id}, Topic: {mqtt_topic}, "
                f"Temperature: {data.temperature}, Humidity: {data.humidity}"
            )
        else:
            logger.warning(
                f"Sensor data received but MQTT publish failed (queued for retry). "
                f"Device: {data.device_id}, Topic: {mqtt_topic}"
            )
            # MQTT 발행 실패해도 큐에 저장되어 있으므로 202 응답 유지
        
        return SuccessResponse(
            success=True,
            data=SensorDataResponse(
                status="received",
                sensor_id=data.device_id,
                timestamp=timestamp
            ),
            message=f"Sensor data from {data.device_id} received and queued for processing"
        )
        
    except ValueError as e:
        logger.warning(f"Invalid sensor data: {e}")
        raise BadRequestError(
            message=f"Invalid sensor data: {str(e)}",
            field="data"
        )
    except Exception as e:
        logger.exception(f"Unexpected error while receiving sensor data: {e}")
        raise InternalServerError(
            message="An error occurred while processing the sensor data"
        )


@router.get(
    "/status",
    response_model=SuccessResponse[SensorStatusResponse],
    summary="센서 상태 조회",
    description="""
    전체 센서의 연결 상태를 조회합니다.
    
    **응답:**
    - `200 OK`: 센서 상태 조회 성공
    - `500 Internal Server Error`: 서버 내부 오류
    
    **응답 필드:**
    - `status`: 전체 상태 (ok, warning, error)
    - `count`: 전체 센서 수
    - `active`: 활성 센서 수
    - `inactive`: 비활성 센서 수
    
    **참고:**
    - 현재는 임시 데이터를 반환합니다.
    - 실제 구현 시 데이터베이스나 센서 관리 시스템에서 조회해야 합니다.
    """,
    responses={
        200: {
            "description": "센서 상태 조회 성공",
            "model": SuccessResponse[SensorStatusResponse]
        },
        500: {
            "description": "서버 내부 오류",
            "model": ErrorResponse
        }
    }
)
async def get_sensor_status() -> SuccessResponse[SensorStatusResponse]:
    """
    전체 센서 연결 상태를 반환합니다.
    
    Returns:
        SuccessResponse[SensorStatusResponse]: 센서 상태 정보
        
    Raises:
        InternalServerError: 상태 조회 중 내부 오류
        
    Note:
        현재는 임시 데이터를 반환합니다.
        실제 구현 시 데이터베이스나 센서 관리 시스템에서 조회해야 합니다.
    """
    try:
        # 캐시 키 생성
        cache = get_cache()
        cache_key_str = cache_key("sensor_status", bucket=settings.INFLUX_BUCKET)
        
        # 캐시에서 조회 (TTL: 30초)
        cached_result = cache.get(cache_key_str)
        if cached_result is not None:
            logger.debug("Sensor status retrieved from cache")
            return cached_result
        
        # InfluxDB에서 센서 상태 조회
        # 최근 5분 내 데이터가 있는 센서를 활성으로 간주
        sensor_status = query_sensor_status(
            bucket=settings.INFLUX_BUCKET,
            inactive_threshold_minutes=5
        )
        
        total_count = sensor_status["total_count"]
        active_count = sensor_status["active_count"]
        inactive_count = sensor_status["inactive_count"]
        device_ids = sensor_status.get("devices", [])
        
        # 상태 결정
        if total_count == 0:
            status_str = "error"  # 센서가 없음
        elif active_count == total_count:
            status_str = "ok"  # 모든 센서 활성
        elif active_count > 0:
            status_str = "warning"  # 일부 센서 비활성
        else:
            status_str = "error"  # 활성 센서 없음
        
        # 설비 목록 생성 (InfluxDB와 알림 DB에서 실제 데이터 조회)
        devices: List[DeviceSummary] = []
        
        # 알림 데이터베이스에서 각 device별 알림 수 조회
        from backend.api.services.alert_storage import get_latest_alerts
        from backend.api.services.database import SessionLocal
        
        db = SessionLocal()
        try:
            # 각 device별 알림 수 계산
            device_alert_counts: Dict[str, int] = {}
            device_alert_counts_warning: Dict[str, int] = {}
            device_alert_counts_critical: Dict[str, int] = {}
            
            # 최근 24시간 알림 조회
            all_alerts = get_latest_alerts(db=db, limit=1000, sensor_id=None, level=None)
            for alert in all_alerts:
                sensor_id = alert.sensor_id
                # device_id 추출 (sensor_id가 device_id를 포함하는 경우)
                device_id = sensor_id.split('_')[0] if '_' in sensor_id else sensor_id
                
                if device_id in device_ids:
                    device_alert_counts[device_id] = device_alert_counts.get(device_id, 0) + 1
                    if alert.level == "warning":
                        device_alert_counts_warning[device_id] = device_alert_counts_warning.get(device_id, 0) + 1
                    elif alert.level == "critical":
                        device_alert_counts_critical[device_id] = device_alert_counts_critical.get(device_id, 0) + 1
        finally:
            db.close()
        
        # InfluxDB에서 각 device별 상세 정보 조회
        from datetime import timedelta
        
        for device_id in device_ids:
            try:
                # InfluxDB에서 device별 센서 필드 수 계산 (최근 1시간)
                sensor_count = 0
                last_updated = None
                operation_rate = None
                
                try:
                    # 최근 1시간 내 데이터 조회하여 센서 필드 수 계산
                    query = f'''
                    from(bucket: "{settings.INFLUX_BUCKET}")
                      |> range(start: -1h)
                      |> filter(fn: (r) => r["_measurement"] == "sensor_data")
                      |> filter(fn: (r) => r["device_id"] == "{device_id}")
                      |> group(columns: ["_field"])
                      |> distinct(column: "_field")
                    '''
                    
                    result = influx_manager.query_api.query(query=query, org=settings.INFLUX_ORG)
                    sensor_fields = set()
                    for table in result:
                        for record in table.records:
                            # _field 컬럼에서 필드 이름 가져오기
                            field_name = record.values.get("_field")
                            if field_name:
                                sensor_fields.add(field_name)
                    sensor_count = len(sensor_fields) if sensor_fields else 0
                    
                    # 최근 데이터 타임스탬프 조회
                    query_last = f'''
                    from(bucket: "{settings.INFLUX_BUCKET}")
                      |> range(start: -24h)
                      |> filter(fn: (r) => r["_measurement"] == "sensor_data")
                      |> filter(fn: (r) => r["device_id"] == "{device_id}")
                      |> last()
                    '''
                    
                    result_last = influx_manager.query_api.query(query=query_last, org=settings.INFLUX_ORG)
                    for table in result_last:
                        for record in table.records:
                            if record.get_time():
                                last_updated = record.get_time().isoformat()
                                break
                    
                    # 가동률 계산 (최근 24시간 중 데이터가 있는 시간 비율)
                    query_operation = f'''
                    from(bucket: "{settings.INFLUX_BUCKET}")
                      |> range(start: -24h)
                      |> filter(fn: (r) => r["_measurement"] == "sensor_data")
                      |> filter(fn: (r) => r["device_id"] == "{device_id}")
                      |> aggregateWindow(every: 1h, fn: count, createEmpty: false)
                      |> count()
                    '''
                    
                    result_op = influx_manager.query_api.query(query=query_operation, org=settings.INFLUX_ORG)
                    hours_with_data = 0
                    for table in result_op:
                        for record in table.records:
                            hours_with_data = record.get_value() or 0
                            break
                    
                    if hours_with_data > 0:
                        operation_rate = round((hours_with_data / 24) * 100, 1)
                    
                except Exception as e:
                    logger.warning(f"Failed to query device details for {device_id}: {e}")
                
                # 상태 결정 (알림 수 기반)
                alert_count = device_alert_counts.get(device_id, 0)
                warning_count = device_alert_counts_warning.get(device_id, 0)
                critical_count = device_alert_counts_critical.get(device_id, 0)
                
                if critical_count > 0:
                    device_status = "긴급"
                elif warning_count > 0:
                    device_status = "경고"
                elif device_id in device_ids:
                    device_status = "정상"
                else:
                    device_status = "오프라인"
                
                # 설비 이름 및 카테고리 매핑 (향후 데이터베이스에서 조회)
                device_name_mapping = {
                    "sensor": "센서 시스템",
                    "device": "디바이스",
                    "equipment": "설비",
                }
                
                # device_id에서 이름 추출
                device_name = device_id.replace('_', ' ').title()
                if any(keyword in device_id.lower() for keyword in ['conveyor', 'belt']):
                    device_name = f"컨베이어 벨트 {device_id.split('_')[-1] if '_' in device_id else ''}"
                    device_category = "운송 시스템"
                elif any(keyword in device_id.lower() for keyword in ['cnc', 'machine']):
                    device_name = f"CNC 머신 {device_id.split('_')[-1] if '_' in device_id else ''}"
                    device_category = "가공 장비"
                elif any(keyword in device_id.lower() for keyword in ['robot', 'arm']):
                    device_name = f"로봇 팔 {device_id.split('_')[-1] if '_' in device_id else ''}"
                    device_category = "자동화 설비"
                else:
                    device_category = "산업 설비"
                
                devices.append(DeviceSummary(
                    device_id=device_id,
                    name=device_name,
                    category=device_category,
                    dashboardUID=device_id,  # 기본값: device_id를 dashboardUID로 사용
                    status=device_status,
                    sensorCount=sensor_count if sensor_count > 0 else None,
                    alertCount=alert_count if alert_count > 0 else 0,
                    operationRate=operation_rate,
                    lastUpdated=last_updated,
                ))
                
            except Exception as e:
                logger.warning(f"Failed to process device {device_id}: {e}")
                # 기본 정보라도 추가
                devices.append(DeviceSummary(
                    device_id=device_id,
                    name=f"설비 {device_id}",
                    category="산업 설비",
                    dashboardUID=device_id,
                    status="정상",
                    sensorCount=None,
                    alertCount=device_alert_counts.get(device_id, 0),
                    operationRate=None,
                    lastUpdated=None,
                ))
        
        logger.info(
            f"Sensor status retrieved from InfluxDB. "
            f"Total: {total_count}, Active: {active_count}, Inactive: {inactive_count}, "
            f"Devices: {len(devices)}"
        )
        
        response = SuccessResponse(
            success=True,
            data=SensorStatusResponse(
                status=status_str,
                count=total_count,
                active=active_count,
                inactive=inactive_count,
                devices=devices
            ),
            message="Sensor status retrieved successfully"
        )
        
        # 캐시에 저장 (TTL: 30초)
        cache.set(cache_key_str, response, ttl=30.0)
        
        return response
        
    except Exception as e:
        logger.exception(f"Unexpected error while retrieving sensor status: {e}")
        raise InternalServerError(
            message="An error occurred while retrieving sensor status"
        )