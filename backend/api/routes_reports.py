"""
보고서 생성 API 엔드포인트

LLM 기반 주간/일일 보고서 생성을 제공합니다.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from backend.api.core.responses import SuccessResponse, ErrorResponse
from backend.api.core.permissions import get_current_user, require_permissions
from backend.api.models.role import Permission
from backend.api.services.schemas.models.core.logger import get_logger
from backend.api.services.report_generator import get_report_generator, MOBYReportGenerator
from backend.api.services.alert_storage import get_latest_alerts
from backend.api.services.database import get_db
from sqlalchemy.orm import Session

logger = get_logger(__name__)
router = APIRouter(prefix="/reports", tags=["Reports"])


class ReportRequest(BaseModel):
    """보고서 생성 요청 모델"""
    period_start: str = Field(..., description="보고 기간 시작 (YYYY-MM-DD HH:MM:SS)")
    period_end: str = Field(..., description="보고 기간 종료 (YYYY-MM-DD HH:MM:SS)")
    equipment: str = Field(..., description="설비명")
    sensor_ids: Optional[list[str]] = Field(None, description="특정 센서 ID 목록 (없으면 전체)")
    include_mlp_anomalies: bool = Field(True, description="MLP 이상 탐지 포함 여부")
    include_if_anomalies: bool = Field(True, description="Isolation Forest 이상 탐지 포함 여부")


class ReportResponse(BaseModel):
    """보고서 생성 응답 모델"""
    report_id: str
    report_content: str
    metadata: Dict[str, Any]
    generated_at: str


@router.post(
    "/generate",
    response_model=SuccessResponse[ReportResponse],
    summary="보고서 생성",
    description="""
    주간 또는 일일 보고서를 자동 생성합니다.
    
    **필요 권한**: `ALERT_READ`, `SENSOR_READ`
    
    **보고서 내용**:
    - 센서별 통계 요약
    - 알람 및 이상 탐지 상세
    - 상관 분석 및 인사이트
    - 권장 사항
    """,
    responses={
        200: {
            "description": "보고서 생성 성공",
            "model": SuccessResponse[ReportResponse]
        },
        400: {
            "description": "잘못된 요청",
            "model": ErrorResponse
        },
        500: {
            "description": "서버 내부 오류",
            "model": ErrorResponse
        }
    }
)
async def generate_report(
    request: ReportRequest,
    current_user = Depends(get_current_user),
    _permissions = Depends(require_permissions(Permission.ALERT_READ, Permission.SENSOR_READ)),
    db: Session = Depends(get_db)
) -> SuccessResponse[ReportResponse]:
    """
    보고서 생성
    
    Args:
        request: 보고서 생성 요청 데이터
        current_user: 현재 사용자 (의존성)
        _permissions: 권한 체크 (의존성)
        
    Returns:
        SuccessResponse[ReportResponse]: 생성된 보고서
    """
    try:
        # 기간 검증
        try:
            start_dt = datetime.strptime(request.period_start, "%Y-%m-%d %H:%M:%S")
            end_dt = datetime.strptime(request.period_end, "%Y-%m-%d %H:%M:%S")
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"날짜 형식이 올바르지 않습니다. YYYY-MM-DD HH:MM:SS 형식을 사용하세요. 오류: {e}"
            )
        
        if end_dt <= start_dt:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="종료 시간이 시작 시간보다 이후여야 합니다."
            )
        
        # 보고서 데이터 수집
        logger.info(f"보고서 데이터 수집 시작. 기간: {request.period_start} ~ {request.period_end}")
        
        report_data = await _collect_report_data(
            db=db,
            period_start=request.period_start,
            period_end=request.period_end,
            equipment=request.equipment,
            sensor_ids=request.sensor_ids,
            include_mlp_anomalies=request.include_mlp_anomalies,
            include_if_anomalies=request.include_if_anomalies
        )
        
        # 보고서 생성
        try:
            generator = get_report_generator()
            report_content = generator.generate_report(report_data)
        except ImportError as e:
            logger.error(f"보고서 생성기 초기화 실패: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="보고서 생성 서비스를 사용할 수 없습니다. GEMINI_API_KEY를 확인하세요."
            )
        except ValueError as e:
            logger.error(f"보고서 생성 실패: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"보고서 생성 실패: {str(e)}"
            )
        except Exception as e:
            logger.exception(f"보고서 생성 중 예상치 못한 오류: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"보고서 생성 중 오류가 발생했습니다: {str(e)}"
            )
        
        # 응답 생성
        report_id = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        response = ReportResponse(
            report_id=report_id,
            report_content=report_content,
            metadata=report_data.get("metadata", {}),
            generated_at=datetime.now().isoformat() + "Z"
        )
        
        logger.info(f"보고서 생성 완료. report_id={report_id}")
        
        return SuccessResponse(
            success=True,
            data=response,
            message="보고서가 성공적으로 생성되었습니다."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"보고서 생성 API 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"보고서 생성 중 오류가 발생했습니다: {str(e)}"
        )


async def _collect_report_data(
    db: Session,
    period_start: str,
    period_end: str,
    equipment: str,
    sensor_ids: Optional[list[str]] = None,
    include_mlp_anomalies: bool = True,
    include_if_anomalies: bool = True
) -> Dict[str, Any]:
    """
    보고서 생성을 위한 데이터 수집
    
    Args:
        period_start: 보고 기간 시작
        period_end: 보고 기간 종료
        equipment: 설비명
        sensor_ids: 특정 센서 ID 목록
        include_mlp_anomalies: MLP 이상 탐지 포함 여부
        include_if_anomalies: Isolation Forest 이상 탐지 포함 여부
        
    Returns:
        보고서 생성에 필요한 데이터 딕셔너리
    """
    # 메타데이터
    metadata = {
        "period_start": period_start,
        "period_end": period_end,
        "equipment": equipment,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # 알람 데이터 수집
    # 기간 필터링을 위해 모든 알람을 가져온 후 필터링
    all_alerts = get_latest_alerts(
        db=db,
        limit=1000,
        sensor_id=None if not sensor_ids else sensor_ids[0] if len(sensor_ids) == 1 else None,
        level=None
    )
    
    # 기간 필터링
    try:
        start_dt = datetime.strptime(period_start, "%Y-%m-%d %H:%M:%S")
        end_dt = datetime.strptime(period_end, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        start_dt = datetime.fromisoformat(period_start.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(period_end.replace('Z', '+00:00'))
    
    alerts = []
    for alert in all_alerts:
        try:
            alert_ts = datetime.fromisoformat(alert.ts.replace('Z', '+00:00'))
            if start_dt <= alert_ts <= end_dt:
                alerts.append({
                    "id": alert.alert_id,
                    "ts": alert.ts,
                    "sensor_id": alert.sensor_id,
                    "level": alert.level,
                    "message": alert.message,
                    "details": alert.details if alert.details else {}
                })
        except (ValueError, AttributeError):
            continue
    
    # 알람 목록 구성
    alarms = []
    mlp_anomalies = []
    if_anomalies = []
    
    for alert in alerts:
        alarm_data = {
            "timestamp": alert.get("ts", ""),
            "sensor": alert.get("sensor_id", ""),
            "level": alert.get("level", ""),
            "message": alert.get("message", "")
        }
        
        details = alert.get("details", {})
        if isinstance(details, dict):
            # MLP 이상 탐지 확인
            if include_mlp_anomalies and "vector" in details:
                mlp_anomalies.append({
                    "timestamp": alert.get("ts", ""),
                    "type": details.get("type", "MLP_composite"),
                    "vector": details.get("vector", []),
                    "vector_magnitude": details.get("norm", 0.0),
                    "threshold": details.get("threshold", 0.5),
                    "component_labels": details.get("meta", {}).get("component_labels", []) if isinstance(details.get("meta"), dict) else []
                })
            
            # Isolation Forest 이상 탐지 확인
            if include_if_anomalies and "anomaly_score" in details:
                if_anomalies.append({
                    "start_time": alert.get("ts", ""),
                    "anomaly_score": details.get("anomaly_score", 0.0),
                    "threshold": details.get("threshold", -0.15),
                    "key_features": details.get("meta", {}) if isinstance(details.get("meta"), dict) else {}
                })
        
        alarms.append(alarm_data)
    
    # 센서 통계 (예시 데이터 - 실제로는 InfluxDB에서 집계)
    # TODO: InfluxDB에서 실제 센서 통계 수집
    sensor_stats = {
        "temperature": {
            "mean": 38.2,
            "min": 22.1,
            "max": 52.3,
            "std": 6.8,
            "p95": 48.5,
            "missing_rate": 0.002,
            "threshold_violations": len([a for a in alarms if a.get("sensor") == "temperature"])
        },
        "humidity": {
            "mean": 62.5,
            "min": 45.2,
            "max": 78.9,
            "std": 8.3,
            "p95": 75.1,
            "missing_rate": 0.002
        },
        "vibration": {
            "x": {"mean": 1.24, "peak": 3.87, "rms": 1.45, "p95": 2.31},
            "y": {"mean": 1.18, "peak": 3.52, "rms": 1.39, "p95": 2.18},
            "z": {"mean": 0.95, "peak": 2.89, "rms": 1.12, "p95": 1.87},
            "trend_note": "X축 진동이 주 후반부 약 15% 증가"
        }
    }
    
    # 상관계수 (예시 데이터 - 실제로는 계산 필요)
    correlations = {
        "temperature_vibration_x": {"value": 0.78, "interpretation": "강한 양의 상관"},
        "vibration_magnitude_sound": {"value": 0.65, "interpretation": "중간 양의 상관"},
        "temperature_humidity": {"value": -0.42, "interpretation": "중간 음의 상관"}
    }
    
    return {
        "metadata": metadata,
        "sensor_stats": sensor_stats,
        "alarms": alarms,
        "mlp_anomalies": mlp_anomalies if include_mlp_anomalies else [],
        "if_anomalies": if_anomalies if include_if_anomalies else [],
        "correlations": correlations
    }

