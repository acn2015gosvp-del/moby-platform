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
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from .anomaly_vector_service import (
    evaluate_anomaly_vector,
    evaluate_anomaly_vector_with_severity,
)
from .alerts_summary import generate_alert_summary

logger = logging.getLogger(__name__)


# -------------------------------------------------------------------
# 내부 유틸
# -------------------------------------------------------------------


def _now_iso() -> str:
    """UTC 기준 ISO8601 타임스탬프 문자열을 반환합니다."""
    return datetime.utcnow().isoformat()


def _normalize_level(severity: str) -> str:
    """
    severity 문자열을 UI에서 쓰기 쉬운 level로 매핑합니다.

    severity:
        - "normal"   → "info"
        - "warning"  → "warning"
        - "critical" → "critical"
    """
    mapping = {
        "normal": "info",
        "warning": "warning",
        "critical": "critical",
    }
    return mapping.get(severity, "info")


# -------------------------------------------------------------------
# 공개 엔트리 포인트 (기존 호환용)
# -------------------------------------------------------------------


def evaluate_alert(alert_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    기존 코드와의 호환을 위한 엔트리 포인트.

    입력된 alert_data(dict)를 기반으로:
    - 벡터(norm) 계산
    - threshold/경고/심각도 평가
    - 이상이 아닐 경우 None 반환
    - 이상일 경우 통합 알람 페이로드(dict) 반환

    실제 전송은 상위 레이어에서 처리합니다.
    """
    return process_alert(alert_data)


# -------------------------------------------------------------------
# 핵심 처리 함수
# -------------------------------------------------------------------


def process_alert(alert_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    알람 평가 및 페이로드 생성의 핵심 로직.

    alert_data 예시(필요시 확장 가능):

        {
            "sensor_id": "motor_01",
            "source": "anomaly-worker",
            "ts": "2025-11-15T03:10:00Z",

            # 벡터 및 임계값
            "vector": [0.4, 0.33],
            "threshold": 0.5,                     # 단일 임계값 (옵션)
            "warning_threshold": 0.5,             # 경고 임계값 (옵션)
            "critical_threshold": 0.7,            # 심각 임계값 (옵션)

            # 메시지 및 LLM 요약 제어
            "message": "MLP 이상 탐지 결과",
            "enable_llm_summary": True,           # 기본값 True

            # 추가 메타데이터
            "meta": {...}
        }

    Returns:
        dict | None:
            - 이상이 아니면 None
            - 이상이면 알람 페이로드(dict)
    """
    # --------------------------------------------------------------
    # 1) 입력 검증
    # --------------------------------------------------------------
    vector = alert_data.get("vector")
    if not isinstance(vector, list) or not vector:
        logger.warning("process_alert: 'vector'가 유효하지 않아서 처리하지 않습니다. data=%s", alert_data)
        return None

    threshold = alert_data.get("threshold")
    warning_threshold = alert_data.get("warning_threshold")
    critical_threshold = alert_data.get("critical_threshold")

    sensor_id = alert_data.get("sensor_id", "unknown_sensor")

    # --------------------------------------------------------------
    # 2) 벡터 기반 이상 평가 (심각도 포함/미포함 자동 선택)
    # --------------------------------------------------------------
    try:
        if warning_threshold is not None and critical_threshold is not None:
            # 경고/심각 임계값이 모두 존재하는 경우
            norm, is_anomaly, severity = evaluate_anomaly_vector_with_severity(
                vector=vector,
                warning_threshold=float(warning_threshold),
                critical_threshold=float(critical_threshold),
            )
        else:
            # 단일 threshold로만 평가
            if threshold is None:
                raise ValueError(
                    "Either 'threshold' or both 'warning_threshold' and "
                    "'critical_threshold' must be provided."
                )
            norm, is_anomaly = evaluate_anomaly_vector(
                vector=vector,
                threshold=float(threshold),
            )
            severity = "critical" if is_anomaly else "normal"

    except Exception as exc:  # noqa: BLE001
        logger.exception("process_alert: 벡터 평가 중 예외 발생 (sensor_id=%s): %s", sensor_id, exc)
        return None

    # --------------------------------------------------------------
    # 3) 이상이 아니라면 알람 생성하지 않음
    # --------------------------------------------------------------
    if not is_anomaly or severity == "normal":
        logger.info(
            "process_alert: 이상 아님 (sensor_id=%s, norm=%.4f, severity=%s)",
            sensor_id,
            norm,
            severity,
        )
        return None

    # --------------------------------------------------------------
    # 4) 기본 알람 페이로드 구성
    # --------------------------------------------------------------
    level = _normalize_level(severity)

    alert_id = alert_data.get("id") or f"anomaly-{_now_iso()}"
    ts = alert_data.get("ts") or _now_iso()
    source = alert_data.get("source", "alert-engine")
    base_message = alert_data.get("message") or "Anomaly detected"

    message = f"{base_message} (severity={severity}, norm={norm:.3f})"

    payload: Dict[str, Any] = {
        "id": alert_id,
        "level": level,
        "message": message,
        "llm_summary": None,
        "sensor_id": sensor_id,
        "source": source,
        "ts": ts,
        "details": {
            "vector": vector,
            "norm": norm,
            "threshold": threshold,
            "warning_threshold": warning_threshold,
            "critical_threshold": critical_threshold,
            "severity": severity,
            "meta": alert_data.get("meta") or {},
        },
    }

    # --------------------------------------------------------------
    # 5) LLM 요약 (옵션)
    # --------------------------------------------------------------
    enable_llm_summary = alert_data.get("enable_llm_summary", True)

    if enable_llm_summary:
        try:
            summary = generate_alert_summary(payload)
            payload["llm_summary"] = summary
        except Exception as exc:  # noqa: BLE001
            # 요약 실패해도 알람 자체는 그대로 사용
            logger.exception(
                "process_alert: LLM 요약 생성 실패 (alert_id=%s, sensor_id=%s): %s",
                alert_id,
                sensor_id,
                exc,
            )

    logger.info(
        "process_alert: 알람 생성 완료 (alert_id=%s, sensor_id=%s, level=%s, norm=%.4f)",
        alert_id,
        sensor_id,
        level,
        norm,
    )
    return payload


__all__ = [
    "evaluate_alert",
    "process_alert",
]
