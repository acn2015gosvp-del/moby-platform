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
        # 기간 검증 (여러 날짜 형식 지원)
        def parse_datetime(date_str: str) -> datetime:
            """여러 날짜 형식을 지원하는 파서"""
            # 형식 목록 (우선순위 순)
            formats = [
                "%Y-%m-%d %H:%M:%S",  # YYYY-MM-DD HH:MM:SS
                "%Y-%m-%dT%H:%M:%S",  # YYYY-MM-DDTHH:MM:SS (ISO 형식)
                "%Y-%m-%d %H:%M",     # YYYY-MM-DD HH:MM
                "%Y-%m-%dT%H:%M",     # YYYY-MM-DDTHH:MM
                "%Y-%m-%d %H:%M:%S.%f",  # 마이크로초 포함
                "%Y-%m-%dT%H:%M:%S.%f",  # ISO 형식 + 마이크로초
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            # ISO 형식으로 시도 (fromisoformat)
            try:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except ValueError:
                pass
            
            raise ValueError(f"날짜 형식을 파싱할 수 없습니다: {date_str}")
        
        start_dt = parse_datetime(request.period_start)
        end_dt = parse_datetime(request.period_end)
        
        if end_dt <= start_dt:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="종료 시간이 시작 시간보다 이후여야 합니다."
            )
        
        # 보고서 데이터 수집
        import time
        total_start_time = time.time()
        
        logger.info(f"보고서 데이터 수집 시작. 기간: {request.period_start} ~ {request.period_end}")
        data_collection_start = time.time()
        
        report_data = await _collect_report_data(
            db=db,
            period_start=request.period_start,
            period_end=request.period_end,
            equipment=request.equipment,
            sensor_ids=request.sensor_ids,
            include_mlp_anomalies=request.include_mlp_anomalies,
            include_if_anomalies=request.include_if_anomalies
        )
        
        data_collection_time = time.time() - data_collection_start
        logger.info(f"✅ 데이터 수집 완료 (소요 시간: {data_collection_time:.2f}초)")
        
        # 보고서 생성
        try:
            # 보고서 생성기 인스턴스 리셋 (모델 변경 시 필요)
            from backend.api.services.report_generator import reset_report_generator
            reset_report_generator()
            
            llm_start_time = time.time()
            logger.info("LLM 보고서 생성 시작...")
            
            generator = get_report_generator()
            report_content = generator.generate_report(report_data)
            
            llm_time = time.time() - llm_start_time
            total_time = time.time() - total_start_time
            logger.info(f"✅ LLM 생성 완료 (소요 시간: {llm_time:.2f}초)")
            logger.info(f"📊 전체 보고서 생성 완료 (총 소요 시간: {total_time:.2f}초, 데이터 수집: {data_collection_time:.2f}초, LLM 생성: {llm_time:.2f}초)")
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
    
    # 알람 데이터 수집 (성능 최적화: 제한된 수만 가져오기)
    # 기간 필터링을 위해 알람을 가져온 후 필터링
    # limit을 500으로 줄여서 데이터 수집 시간 단축
    all_alerts = get_latest_alerts(
        db=db,
        limit=500,  # 1000 → 500으로 감소 (성능 개선)
        sensor_id=None if not sensor_ids else sensor_ids[0] if len(sensor_ids) == 1 else None,
        level=None
    )
    
    # 기간 필터링 (parse_datetime 함수 재사용)
    def parse_datetime_for_filter(date_str: str) -> datetime:
        """여러 날짜 형식을 지원하는 파서 (필터링용)"""
        formats = [
            "%Y-%m-%d %H:%M:%S",  # YYYY-MM-DD HH:MM:SS
            "%Y-%m-%dT%H:%M:%S",  # YYYY-MM-DDTHH:MM:SS (ISO 형식)
            "%Y-%m-%d %H:%M",     # YYYY-MM-DD HH:MM
            "%Y-%m-%dT%H:%M",     # YYYY-MM-DDTHH:MM
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        # ISO 형식으로 시도
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except ValueError:
            pass
        
        raise ValueError(f"날짜 형식을 파싱할 수 없습니다: {date_str}")
    
    start_dt = parse_datetime_for_filter(period_start)
    end_dt = parse_datetime_for_filter(period_end)
    
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
        details = alert.get("details", {})
        if not isinstance(details, dict):
            details = {}
        
        # 원본 노트북 형식에 맞춘 alarms 데이터 구조
        # 원본: {"timestamp": "...", "sensor": "...", "value": 52.3, "threshold": 50.0, "level": "WARNING"}
        alarm_data = {
            "timestamp": alert.get("ts", ""),
            "sensor": alert.get("sensor_id", ""),
            "level": alert.get("level", ""),
            "message": alert.get("message", "")
        }
        
        # details에서 value와 threshold 추출 (원본 형식에 맞춤)
        if "value" in details:
            alarm_data["value"] = details.get("value")
        if "threshold" in details:
            alarm_data["threshold"] = details.get("threshold")
        
        alarms.append(alarm_data)
        
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
        
        # Isolation Forest 이상 탐지 확인 (원본 형식에 맞춤)
        if include_if_anomalies and "anomaly_score" in details:
            if_anomaly = {
                "start_time": alert.get("ts", ""),
                "anomaly_score": details.get("anomaly_score", 0.0),
                "threshold": details.get("threshold", -0.15),
                "key_features": details.get("meta", {}) if isinstance(details.get("meta"), dict) else {}
            }
            
            # 원본 노트북 형식에 맞춰 추가 필드 포함
            if "end_time" in details:
                if_anomaly["end_time"] = details.get("end_time")
            if "duration_minutes" in details:
                if_anomaly["duration_minutes"] = details.get("duration_minutes")
            if "mlp_vector_magnitude" in details:
                if_anomaly["mlp_vector_magnitude"] = details.get("mlp_vector_magnitude")
            
            if_anomalies.append(if_anomaly)
    
    # 센서 통계 (예시 데이터 - 실제로는 InfluxDB에서 집계)
    # TODO: InfluxDB에서 실제 센서 통계 수집
    # 원본 노트북 형식에 맞춰 모든 센서 데이터 포함
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
        },
        # 원본 노트북에 있던 추가 센서 데이터
        "accelerometer": {
            "x": {"mean": 0.12, "peak": 2.45, "rms": 0.38, "std": 0.34},
            "y": {"mean": -0.08, "peak": 2.21, "rms": 0.35, "std": 0.32},
            "z": {"mean": 9.81, "peak": 11.23, "rms": 9.85, "std": 0.28}
        },
        "gyroscope": {
            "x": {"mean": 0.03, "peak": 8.92, "rms": 1.24, "std": 1.22},
            "y": {"mean": -0.01, "peak": 7.68, "rms": 1.18, "std": 1.17},
            "z": {"mean": 0.02, "peak": 6.34, "rms": 0.95, "std": 0.94}
        },
        "sound": {
            "mean": 68.3,
            "max": 89.7,
            "p95": 81.5,
            "threshold_violations": len([a for a in alarms if a.get("sensor") == "sound"])
        },
        "pressure": {
            "mean": 1013.2,
            "min": 1008.5,
            "max": 1018.7,
            "trend_note": "주중 기압 완만 하강 (기상 영향)"
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

