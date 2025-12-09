"""
알림 엔진 서비스 모듈 (최종 리팩토링 버전)

역할:
- anomaly_vector_service를 이용해 벡터 기반 이상 여부 및 심각도 평가
- alerts_summary 서비스를 통해 LLM 요약 생성 (옵션)
- 프론트/백엔드에서 공통으로 사용하는 알람 페이로드(dict) 생성

주의:
- 이 모듈은 "알람 평가 및 페이로드 생성"까지만 담당합니다.
- 실제 슬랙/이메일/WebSocket 전송은 notifier 등 상위 레이어에서 처리하세요.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, UTC, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

from backend.api.core.exceptions import (
    AlertEngineError,
    AlertValidationError,
    AlertProcessingError,
    LLMSummaryError,
    AnomalyVectorError,
)
from .anomaly_vector_service import (
    evaluate_anomaly_vector,
    evaluate_anomaly_vector_with_severity,
)
from .alerts_summary import generate_alert_summary
from . import constants

logger = logging.getLogger(__name__)


# -------------------------------------------------------------------
# 타입 정의 (Pydantic Models)
# -------------------------------------------------------------------


class AlertInputModel(BaseModel):
    """Pydantic 모델: 알람 처리를 위한 입력 데이터 검증"""

    id: Optional[str] = None
    sensor_id: str = constants.Defaults.SENSOR_ID
    source: str = constants.Defaults.SOURCE
    ts: Optional[str] = None
    vector: List[float]
    threshold: Optional[float] = None
    warning_threshold: Optional[float] = None
    critical_threshold: Optional[float] = None
    message: str = constants.Defaults.MESSAGE
    enable_llm_summary: bool = True
    meta: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("vector")
    @classmethod
    def vector_must_not_be_empty(cls, v: List[float]) -> List[float]:
        if not v:
            raise ValueError(constants.ValidationMessages.VECTOR_EMPTY)
        return v

    @model_validator(mode='after')
    def check_thresholds(self) -> 'AlertInputModel':
        """'threshold' 또는 'warning_threshold'/'critical_threshold' 쌍의 존재 여부를 확인합니다."""
        if (
            self.threshold is None
            and (self.warning_threshold is None or self.critical_threshold is None)
        ):
            raise ValueError(constants.ValidationMessages.MISSING_THRESHOLDS)
        return self


class AlertDetailsModel(BaseModel):
    """Pydantic 모델: 알람 페이로드의 'details' 필드 구조"""

    vector: List[float]
    norm: float
    threshold: Optional[float]
    warning_threshold: Optional[float]
    critical_threshold: Optional[float]
    severity: str
    meta: Dict[str, Any] = Field(default_factory=dict)


class AlertPayloadModel(BaseModel):
    """Pydantic 모델: 최종적으로 생성되는 알람 페이로드 구조"""

    id: str
    level: str
    message: str
    llm_summary: Optional[str] = None
    sensor_id: str
    source: str
    ts: str
    details: AlertDetailsModel


# -------------------------------------------------------------------
# 내부 유틸
# -------------------------------------------------------------------


def _now_iso() -> str:
    """UTC 기준 ISO8601 타임스탬프 문자열을 반환합니다."""
    # Python 3.11+에서 UTC 사용, 그 이하는 timezone.utc 사용
    try:
        return datetime.now(UTC).isoformat()
    except TypeError:
        # Python 3.9, 3.10 호환성
        return datetime.now(timezone.utc).isoformat()


def _normalize_level(severity: constants.Severity) -> constants.AlertLevel:
    """
    severity 열거형을 UI에서 쓰기 쉬운 level 열거형으로 매핑합니다.
    """
    return constants.SEVERITY_TO_LEVEL_MAP.get(
        severity, constants.AlertLevel.INFO
    )


# -------------------------------------------------------------------
# 공개 엔트리 포인트 (기존 호환용)
# -------------------------------------------------------------------


def evaluate_alert(alert_data: Dict[str, Any]) -> Optional[AlertPayloadModel]:
    """
    기존 코드와의 호환을 위한 엔트리 포인트.
    내부적으로 Pydantic 모델을 사용하여 데이터를 검증하고 처리합니다.
    """
    return process_alert(alert_data)


# -------------------------------------------------------------------
# 핵심 처리 함수
# -------------------------------------------------------------------


def process_alert(alert_data: Dict[str, Any]) -> Optional[AlertPayloadModel]:
    """
    알람 평가 및 페이로드 생성의 핵심 로직.
    Pydantic 모델을 사용하여 입력 데이터를 검증합니다.
    """
    # --------------------------------------------------------------
    # 1) 입력 검증 (Pydantic)
    # --------------------------------------------------------------
    try:
        alert_input = AlertInputModel(**alert_data)
    except ValidationError as exc:
        logger.warning(
            "process_alert: 입력 데이터 검증 실패. data=%s, error=%s", alert_data, exc
        )
        return None

    # --------------------------------------------------------------
    # 2) 벡터 기반 이상 평가 (심각도 포함/미포함 자동 선택)
    # --------------------------------------------------------------
    try:
        if (
            alert_input.warning_threshold is not None
            and alert_input.critical_threshold is not None
        ):
            norm, is_anomaly, severity_str = evaluate_anomaly_vector_with_severity(
                vector=alert_input.vector,
                warning_threshold=alert_input.warning_threshold,
                critical_threshold=alert_input.critical_threshold,
            )
            # severity_str는 문자열이므로 enum으로 변환
            severity = constants.Severity(severity_str)
        else:
            # Pydantic validator가 threshold 존재를 보장함
            norm, is_anomaly = evaluate_anomaly_vector(
                vector=alert_input.vector,
                threshold=alert_input.threshold,  # type: ignore
            )
            # severity_str는 이미 enum 값이므로 바로 할당
            severity = (
                constants.Severity.CRITICAL
                if is_anomaly
                else constants.Severity.NORMAL
            )

    except (ValueError, TypeError) as exc:
        error = AnomalyVectorError(
            message=f"벡터 평가 중 데이터 타입 또는 값 오류: {exc}",
            vector=alert_input.vector,
            threshold=alert_input.threshold
        )
        logger.error(
            f"process_alert: {error.message} "
            f"(sensor_id={alert_input.sensor_id}, vector={alert_input.vector})"
        )
        return None
    except Exception as exc:  # noqa: BLE001
        error = AlertProcessingError(
            message=f"벡터 평가 중 예상치 못한 예외: {exc}",
            sensor_id=alert_input.sensor_id
        )
        logger.exception(
            f"process_alert: {error.message} (sensor_id={alert_input.sensor_id})"
        )
        return None

    # --------------------------------------------------------------
    # 3) 이상이 아니라면 알람 생성하지 않음
    # --------------------------------------------------------------
    if not is_anomaly or severity == constants.Severity.NORMAL:
        logger.info(
            "process_alert: 이상 아님 (sensor_id=%s, norm=%.4f, severity=%s)",
            alert_input.sensor_id,
            norm,
            severity.value,
        )
        return None

    # --------------------------------------------------------------
    # 4) 기본 알람 페이로드 구성
    # --------------------------------------------------------------
    level = _normalize_level(severity)
    # UUID를 사용하여 고유한 알람 ID 생성
    alert_id = alert_input.id or f"{constants.Defaults.ALERT_ID_PREFIX}{uuid.uuid4().hex[:8]}"
    ts = alert_input.ts or _now_iso()
    message = f"{alert_input.message} (severity={severity.value}, norm={norm:.3f})"

    details = AlertDetailsModel(
        vector=alert_input.vector,
        norm=norm,
        threshold=alert_input.threshold,
        warning_threshold=alert_input.warning_threshold,
        critical_threshold=alert_input.critical_threshold,
        severity=severity.value,
        meta=alert_input.meta,
    )

    payload = AlertPayloadModel(
        id=alert_id,
        level=level.value,
        message=message,
        llm_summary=None,
        sensor_id=alert_input.sensor_id,
        source=alert_input.source,
        ts=ts,
        details=details,
    )

    # --------------------------------------------------------------
    # 5) LLM 요약 (옵션) - 동기 처리 (성능 최적화: 비동기 버전은 별도 제공)
    # --------------------------------------------------------------
    # 참고: LLM 요약은 I/O 작업이지만, 현재는 동기적으로 처리합니다.
    # 비동기 처리가 필요한 경우 process_alert_async()를 사용하세요.
    if alert_input.enable_llm_summary:
        try:
            # Pydantic 모델을 dict로 변환하여 전달
            summary = generate_alert_summary(payload.model_dump())
            if summary:
                payload.llm_summary = summary
            else:
                # LLM 요약 실패 시 fallback 메시지
                payload.llm_summary = (
                    f"Alert detected: {payload.message}. "
                    f"Severity: {severity.value}, Norm: {norm:.3f}. "
                    f"LLM summary generation was unavailable."
                )
                logger.warning(
                    "process_alert: LLM 요약이 None을 반환했습니다. "
                    "Fallback 메시지를 사용합니다. "
                    f"(alert_id={payload.id}, sensor_id={payload.sensor_id})"
                )
        except LLMSummaryError as exc:
            # LLM 관련 커스텀 예외 처리
            payload.llm_summary = (
                f"Alert detected: {payload.message}. "
                f"Severity: {severity.value}, Norm: {norm:.3f}. "
                f"LLM summary generation failed: {exc.message}"
            )
            logger.warning(
                f"process_alert: LLM 요약 생성 실패 (LLMSummaryError). "
                f"alert_id={payload.id}, sensor_id={payload.sensor_id}, "
                f"error={exc.message}. Fallback 메시지를 사용합니다."
            )
        except Exception as exc:  # noqa: BLE001
            # 기타 예외 처리
            payload.llm_summary = (
                f"Alert detected: {payload.message}. "
                f"Severity: {severity.value}, Norm: {norm:.3f}. "
                f"LLM summary generation encountered an error."
            )
            logger.exception(
                f"process_alert: LLM 요약 생성 중 예상치 못한 예외 발생. "
                f"alert_id={payload.id}, sensor_id={payload.sensor_id}, "
                f"error={exc}. Fallback 메시지를 사용합니다."
            )

    logger.info(
        "process_alert: 알람 생성 완료 (alert_id=%s, sensor_id=%s, level=%s, norm=%.4f)",
        payload.id,
        payload.sensor_id,
        payload.level,
        norm,
    )
    return payload


__all__ = [
    "evaluate_alert",
    "process_alert",
    "AlertInputModel",
    "AlertPayloadModel",
]
