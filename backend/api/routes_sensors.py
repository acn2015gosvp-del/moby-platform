"""
센서(Sensor) 관련 API 엔드포인트

센서 데이터 수신 및 센서 상태 조회 API를 제공합니다.
"""

from fastapi import APIRouter, status, Depends
from typing import Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from .services.schemas.sensor_schema import SensorData
from .core.responses import SuccessResponse, ErrorResponse
from .core.api_exceptions import BadRequestError, InternalServerError
from .services.schemas.models.core.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


class SensorDataResponse(BaseModel):
    """센서 데이터 수신 응답 모델"""
    status: str = Field(..., description="수신 상태")
    sensor_id: str = Field(..., description="센서 ID")
    timestamp: str = Field(..., description="수신 시각")


class SensorStatusResponse(BaseModel):
    """센서 상태 응답 모델"""
    status: str = Field(..., description="전체 상태")
    count: int = Field(..., description="전체 센서 수")
    active: int = Field(..., description="활성 센서 수")
    inactive: int = Field(..., description="비활성 센서 수")


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
        # TODO: MQTT 클라이언트 등을 통해 InfluxDB 파이프라인으로 전달하는 로직 필요
        # 현재는 수신 확인만 수행
        
        logger.info(
            f"Sensor data received. Device: {data.device_id}, "
            f"Temperature: {data.temperature}, Humidity: {data.humidity}"
        )
        
        return SuccessResponse(
            success=True,
            data=SensorDataResponse(
                status="received",
                sensor_id=data.device_id,
                timestamp=timestamp
            ),
            message=f"Sensor data from {data.device_id} received successfully"
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
        # TODO: 실제 센서 상태를 데이터베이스나 센서 관리 시스템에서 조회
        # 현재는 임시 데이터 반환
        total_count = 10
        active_count = 9
        inactive_count = total_count - active_count
        
        status_str = "ok" if active_count == total_count else "warning"
        
        logger.debug(f"Sensor status requested. Active: {active_count}/{total_count}")
        
        return SuccessResponse(
            success=True,
            data=SensorStatusResponse(
                status=status_str,
                count=total_count,
                active=active_count,
                inactive=inactive_count
            ),
            message="Sensor status retrieved successfully"
        )
        
    except Exception as e:
        logger.exception(f"Unexpected error while retrieving sensor status: {e}")
        raise InternalServerError(
            message="An error occurred while retrieving sensor status"
        )