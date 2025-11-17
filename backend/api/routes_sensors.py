from fastapi import APIRouter, status, Body
from typing import List, Dict, Any

# 오류 수정: 'schemas' 대신 '.services.schemas' 상대 경로를 사용하여 임포트
from .services.schemas.sensor_schema import SensorData # SensorData 스키마 임포트

router = APIRouter()

# -------------------------------------------------------------------
# 센서 데이터 라우트 (예시)
# -------------------------------------------------------------------

@router.post("/data", status_code=status.HTTP_202_ACCEPTED)
def receive_sensor_data(data: SensorData):
    """
    Edge 장치로부터 센서 데이터를 수신합니다.
    (실제 처리는 별도의 파이프라인으로 전달되어야 함)
    """
    # TODO: MQTT 클라이언트 등을 통해 InfluxDB 파이프라인으로 전달하는 로직 필요
    
    return {
        "status": "received", 
        "sensor_id": data.sensor_id,
        "ts": data.ts
    }


@router.get("/status")
def get_sensor_status():
    """
    전체 센서 연결 상태를 반환합니다.
    """
    return {"status": "ok", "count": 10, "active": 9}