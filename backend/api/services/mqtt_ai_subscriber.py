"""
MQTT AI 알림 구독 서비스

Edge AI에서 전송한 이상 탐지 결과를 MQTT를 통해 수신합니다.
Topic: factory/inference/results/#

데이터 구조:
{
  "sensor_type": "accel_gyro",
  "model_name": "mlp_classifier",
  "context_payload": {
    "fields": {
      "mlp_s1_prob_normal": 0.05,
      "mlp_s1_prob_yellow": 0.10,
      "mlp_s1_prob_red": 0.85,
      "mlp_s2_prob_normal": 0.98,
      "mlp_s2_prob_yellow": 0.02,
      "mlp_s2_prob_red": 0.00
    }
  }
}
"""

import json
import logging
import threading
from typing import Dict, Any, Tuple, Optional
from datetime import datetime, UTC, timezone

from backend.api.services.schemas.models.core.logger import get_logger
from backend.api.services.alert_state_manager import get_alert_state_manager
from backend.api.services.websocket_notifier import get_websocket_notifier
from backend.api.services.alert_storage import save_alert
from backend.api.services.database import SessionLocal

logger = get_logger(__name__)


def parse_ai_result(data: dict) -> Tuple[str, str, str]:
    """
    AI 결과를 파싱하여 severity, 메시지, 말머리를 반환합니다.
    
    판단 기준:
    - MLP Classifier: S1/S2 확률 확인, Red/Yellow 감지 시 WARNING (주황색)
    - Isolation Forest: iforest_score < 0이면 NOTICE (파란색)
    
    Args:
        data: MQTT에서 수신한 AI 결과 데이터
            - model_name: "mlp_classifier" 또는 "isolation_forest"
            - context_payload.fields: 확률값 또는 점수 딕셔너리
    
    Returns:
        Tuple[level, message, prefix]: 
            - level: "NORMAL", "WARNING", "NOTICE" 중 하나
            - message: 알림 메시지 내용
            - prefix: 메시지 말머리 ("🔧 [AI 진단]" 또는 "❓ [이상 징후]")
    """
    model_name = data.get("model_name", "")
    fields = data.get("context_payload", {}).get("fields", {})
    
    alerts = []
    level = "NORMAL"  # 기본값
    prefix = ""
    
    # --- Case A: MLP Classifier (고장 진단) ---
    if model_name == "mlp_classifier":
        prefix = "🔧 [AI 진단]"
        
        # S1 (속도 변동) 확률값 추출
        s1_probs = {
            "정상": fields.get("mlp_s1_prob_normal", 0),
            "주의": fields.get("mlp_s1_prob_yellow", 0),
            "위험": fields.get("mlp_s1_prob_red", 0)
        }
        
        # S2 (불균형) 확률값 추출
        s2_probs = {
            "정상": fields.get("mlp_s2_prob_normal", 0),
            "주의": fields.get("mlp_s2_prob_yellow", 0),
            "위험": fields.get("mlp_s2_prob_red", 0)
        }
        
        # 상태 판정 (argmax: 가장 높은 확률의 상태 선택)
        s1_status = max(s1_probs, key=s1_probs.get)
        s2_status = max(s2_probs, key=s2_probs.get)
        
        # Red/Yellow 감지 시 WARNING
        if s1_status == "위험":
            prob_value = s1_probs['위험']
            alerts.append(f"속도변동 위험({prob_value:.2f})")
            level = "WARNING"
        elif s1_status == "주의":
            alerts.append("속도변동 주의")
            if level == "NORMAL":
                level = "WARNING"
        
        if s2_status == "위험":
            prob_value = s2_probs['위험']
            alerts.append(f"불균형 위험({prob_value:.2f})")
            level = "WARNING"
        elif s2_status == "주의":
            alerts.append("불균형 주의")
            if level == "NORMAL":
                level = "WARNING"
    
    # --- Case B: Isolation Forest (이상 징후) ---
    elif model_name == "isolation_forest":
        prefix = "❓ [이상 징후]"
        
        score = fields.get("iforest_score", 0)
        if score < 0:
            alerts.append(f"미확인 패턴(Score: {score:.2f})")
            level = "NOTICE"
    
    return level, ", ".join(alerts) if alerts else "정상 상태", prefix


def process_ai_alert_mqtt(topic: str, payload: bytes) -> None:
    """
    MQTT에서 수신한 Edge AI 알림을 처리합니다.
    
    우선순위 로직:
    - IS_CRITICAL_ACTIVE가 True면 → 무시 (Pass, 로그만 남김)
    - IS_CRITICAL_ACTIVE가 False면 → 전송 (WARNING/Orange)
    
    Args:
        topic: MQTT 토픽 (예: factory/inference/results/device-001)
        payload: MQTT 페이로드 (JSON 문자열)
    """
    try:
        # JSON 파싱
        data_str = payload.decode('utf-8')
        data = json.loads(data_str)
        
        logger.info(f"📨 Edge AI 알림 수신 (MQTT): topic={topic}")
        logger.debug(f"Payload: {data}")
        
        # 1. 토픽 필터링 (원하는 모델 결과만 처리)
        if not topic.startswith("factory/inference/results"):
            logger.debug(f"토픽이 factory/inference/results로 시작하지 않음: {topic}")
            return
        
        # 2. 데이터 파싱
        ai_level, msg_content, prefix = parse_ai_result(data)
        
        # 3. 정상이면 무시
        if ai_level == "NORMAL":
            logger.debug(f"Edge AI 알림: 정상 상태 (topic={topic})")
            return
        
        # 4. ★ 우선순위 체크: IS_CRITICAL_ACTIVE가 True면 AI 알림 무시
        state_manager = get_alert_state_manager()
        if state_manager.is_critical_active:
            logger.info(
                f"⚠️ AI 알림 무시됨 (CRITICAL 상태 활성): "
                f"topic={topic}, ai_level={ai_level}, message={msg_content}"
            )
            return
        
        # 5. 디바이스 ID 하드코딩 (Demo Setting)
        device_id = "Demo-Conveyor-01"
        
        # 센서 타입 및 모델명 추출
        sensor_type = data.get("sensor_type", "unknown")
        model_name = data.get("model_name", "unknown")
        
        # 6. 메시지 생성 (말머리 포함)
        message = f"{prefix} {device_id}: {msg_content}"
        
        # 7. 색상 매핑
        color_map = {
            "WARNING": "orange",
            "NOTICE": "#2196F3"  # 파란색
        }
        color = color_map.get(ai_level, "gray")
        
        # 8. WebSocket 출력 형식
        websocket_payload = {
            "type": ai_level,  # WARNING 또는 NOTICE
            "message": message,
            "sensor": device_id,
            "color": color,
            "device_id": device_id,
            "sensor_type": sensor_type,
            "model_name": model_name,
            "timestamp": datetime.now().isoformat()
        }
        
        # 데이터베이스 저장 및 전송 (백그라운드)
        def save_and_send():
            db = SessionLocal()
            try:
                # AlertPayloadModel 생성
                from backend.api.services.alert_engine import AlertPayloadModel, AlertDetailsModel
                from backend.api.services.constants import AlertLevel
                from datetime import datetime, UTC, timezone
                
                def _now_iso() -> str:
                    try:
                        return datetime.now(UTC).isoformat()
                    except TypeError:
                        return datetime.now(timezone.utc).isoformat()
                
                # context_payload.fields를 meta에 저장
                fields = data.get("context_payload", {}).get("fields", {})
                
                details = AlertDetailsModel(
                    vector=[],
                    norm=0.0,
                    threshold=None,
                    warning_threshold=None,
                    critical_threshold=None,
                    severity=ai_level.lower(),
                    meta={
                        "edge_ai": True,
                        "model_name": model_name,
                        "sensor_type": sensor_type,
                        "source": "mqtt",
                        "topic": topic,
                        "context_fields": fields
                    }
                )
                
                # AlertLevel 매핑 (ai_level에 따라)
                level_map = {
                    "WARNING": AlertLevel.WARNING.value,
                    "NOTICE": AlertLevel.INFO.value,  # NOTICE는 INFO 레벨로 저장
                }
                alert_level = level_map.get(ai_level, AlertLevel.WARNING.value)
                
                alert_payload = AlertPayloadModel(
                    id=f"edge-ai-{device_id}-{datetime.now().timestamp()}",
                    level=alert_level,
                    message=message,
                    llm_summary=None,
                    sensor_id=device_id,
                    source="edge-ai-mqtt",
                    ts=_now_iso(),
                    details=details
                )
                
                # 데이터베이스 저장
                try:
                    save_alert(db, alert_payload)
                except Exception as e:
                    logger.error(f"Edge AI 알림 저장 실패: {e}", exc_info=True)
                
                # WebSocket 전송 (비동기 함수를 동기 컨텍스트에서 실행)
                import asyncio
                notifier = get_websocket_notifier()
                logger.info(f"🚀 [MQTT AI] WebSocket으로 알림 전송 시도: {websocket_payload}")
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # 이미 실행 중인 이벤트 루프가 있으면 태스크로 실행
                        logger.debug("[MQTT AI] 이벤트 루프 실행 중 - create_task 사용")
                        asyncio.create_task(notifier.send_alert(websocket_payload))
                    else:
                        # 이벤트 루프가 없으면 실행
                        logger.debug("[MQTT AI] 이벤트 루프 없음 - run_until_complete 사용")
                        loop.run_until_complete(notifier.send_alert(websocket_payload))
                except RuntimeError as e:
                    # 이벤트 루프가 없는 경우 새로 생성
                    logger.debug(f"[MQTT AI] RuntimeError 발생 - 새 이벤트 루프 생성: {e}")
                    asyncio.run(notifier.send_alert(websocket_payload))
                except Exception as e:
                    logger.error(f"❌ [MQTT AI] WebSocket 전송 실패: {e}", exc_info=True)
                
                # 이메일 알림 전송 (WARNING만 전송, NOTICE는 제외)
                if ai_level == "WARNING":
                    try:
                        from backend.api.services.email_service import alert_email_manager
                        logger.info(f"📧 [MQTT AI] 이메일 알림 전송 시도: {device_id}")
                        try:
                            loop = asyncio.get_event_loop()
                            if loop.is_running():
                                logger.debug("[MQTT AI] 이메일 - 이벤트 루프 실행 중 - create_task 사용")
                                asyncio.create_task(
                                    alert_email_manager.handle_alert(
                                        alert_type="WARNING",
                                        message=message,
                                        source=device_id,
                                        severity=3  # WARNING은 중간 심각도
                                    )
                                )
                            else:
                                logger.debug("[MQTT AI] 이메일 - 이벤트 루프 없음 - run_until_complete 사용")
                                loop.run_until_complete(
                                    alert_email_manager.handle_alert(
                                        alert_type="WARNING",
                                        message=message,
                                        source=device_id,
                                        severity=3
                                    )
                                )
                        except RuntimeError as e:
                            logger.debug(f"[MQTT AI] 이메일 - RuntimeError 발생 - 새 이벤트 루프 생성: {e}")
                            asyncio.run(
                                alert_email_manager.handle_alert(
                                    alert_type="WARNING",
                                    message=message,
                                    source=device_id,
                                    severity=3
                                )
                            )
                    except Exception as e:
                        logger.warning(f"📧 [MQTT AI] 이메일 알림 전송 중 오류 (무시): {e}")
                
            finally:
                db.close()
        
        # 백그라운드 스레드에서 실행
        thread = threading.Thread(target=save_and_send, daemon=True, name="MQTT-AI-Process")
        thread.start()
        
        logger.info(
            f"✅ Edge AI 알림 처리 및 전송 완료: "
            f"device_id={device_id}, model={model_name}, level={ai_level}, message={msg_content}"
        )
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ MQTT 페이로드 JSON 파싱 실패: {e}, payload={payload}")
    except Exception as e:
        logger.error(
            f"❌ Edge AI MQTT 알림 처리 실패: {e}",
            exc_info=True
        )
