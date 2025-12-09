import logging
import json
import time
import threading
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional

import paho.mqtt.client as mqtt

from .schemas.models.core.config import settings

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------
# 메시지 큐 항목
# -------------------------------------------------------------------

@dataclass
class QueuedMessage:
    """큐에 저장된 메시지 정보"""
    topic: str
    payload: Dict[str, Any]
    timestamp: datetime
    retry_count: int = 0
    max_retries: int = 3


# -------------------------------------------------------------------
# MQTT 클라이언트 관리자 (안정성 및 재시도 로직)
# -------------------------------------------------------------------

class MqttClientManager:
    """
    MQTT 클라이언트의 연결 생명주기, 이벤트 처리, 안정적인 메시지 발송을 관리합니다.
    
    주요 기능:
    - Exponential backoff를 사용한 재연결 로직
    - 연결 실패 시 메시지 큐잉
    - 자동 재시도 및 복구
    """
    def __init__(self):
        self.host = settings.MQTT_HOST
        self.port = settings.MQTT_PORT
        
        # 호스트 유효성 검사 및 정규화
        if not self.host or not isinstance(self.host, str) or not self.host.strip():
            logger.warning(
                f"⚠️ MQTT_HOST가 유효하지 않습니다: '{self.host}'. "
                f"MQTT 기능이 비활성화됩니다."
            )
            self.host = None
            self.client = None
            self.message_queue: deque = deque()
            self.queue_lock = threading.Lock()
            self.max_queue_size = 1000
            self.is_connecting = False
            self.connection_lock = threading.Lock()
            self.last_connection_attempt: Optional[datetime] = None
            self.connection_attempt_count = 0
            self.queue_processor_thread = None
            return
        
        # paho-mqtt v2.0+에서는 "localhost"를 "127.0.0.1"로 변환
        # "Invalid host" 오류 방지
        if self.host.strip().lower() == "localhost":
            self.host = "127.0.0.1"
            logger.debug(f"MQTT 호스트 'localhost'를 '127.0.0.1'로 변환했습니다.")
        
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        
        # 메시지 큐 (스레드 안전)
        self.message_queue: deque = deque()
        self.queue_lock = threading.Lock()
        self.max_queue_size = 1000  # 최대 큐 크기
        
        # 재연결 상태 추적
        self.is_connecting = False
        self.connection_lock = threading.Lock()
        self.last_connection_attempt: Optional[datetime] = None
        self.connection_attempt_count = 0
        
        # 이벤트 핸들러 등록
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_publish = self._on_publish
        self.client.on_message = self._on_message
        
        # 백그라운드 루프는 connect() 호출 전에 시작하지 않음
        # loop_start()는 자동 재연결을 시도하므로, 호스트가 유효하지 않으면
        # 백그라운드 스레드에서 "Invalid host" 오류가 발생합니다.
        # 대신 connect() 성공 후에만 loop_start()를 호출합니다.
        self._loop_started = False
        
        # 큐 처리 스레드 시작
        self.queue_processor_thread = threading.Thread(
            target=self._process_message_queue,
            daemon=True,
            name="MQTT-QueueProcessor"
        )
        self.queue_processor_thread.start()

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        """연결 성공/실패 콜백"""
        if not self.host:
            return  # 호스트가 없으면 콜백 처리하지 않음
            
        if rc == 0:
            # paho-mqtt v2.0+에서는 flags가 ConnectFlags 객체입니다 (딕셔너리가 아님)
            session_present = getattr(flags, 'session_present', 0)
            logger.info(
                "✅ MQTT connected successfully. "
                f"Host: {self.host}:{self.port}, "
                f"Session present: {session_present}"
            )
            self.connection_attempt_count = 0
            self.is_connecting = False
            
            # 센서 데이터 토픽 구독
            try:
                # sensors/+/data 패턴으로 모든 센서 데이터 구독
                client.subscribe("sensors/+/data", qos=1)
                logger.info("✅ Subscribed to sensor data topics: sensors/+/data")
                
                # factory/sensor/# 패턴으로 실제 센서 데이터 구독 (실시간 데이터)
                client.subscribe("factory/sensor/#", qos=1)
                logger.info("✅ Subscribed to factory sensor topics: factory/sensor/#")
            except Exception as e:
                logger.error(f"❌ Failed to subscribe to sensor topics: {e}", exc_info=True)
            
            # Edge AI 알림 토픽 구독 (새로운 토픽: factory/inference/results/#)
            try:
                client.subscribe("factory/inference/results/#", qos=1)
                logger.info("✅ Subscribed to Edge AI alert topic: factory/inference/results/#")
            except Exception as e:
                logger.error(f"❌ Failed to subscribe to Edge AI alert topic: {e}", exc_info=True)
            
            # 연결 성공 시 큐에 있는 메시지 처리 시작
            self._notify_queue_processor()
        else:
            error_messages = {
                1: "incorrect protocol version",
                2: "invalid client identifier",
                3: "server unavailable",
                4: "bad username or password",
                5: "not authorized"
            }
            error_msg = error_messages.get(rc, f"unknown error code {rc}")
            logger.error(
                f"❌ MQTT connection failed. "
                f"Result code: {rc} ({error_msg}), "
                f"Host: {self.host}:{self.port}"
            )
            self.is_connecting = False
            
    def _on_disconnect(self, client, userdata, rc, *args, **kwargs):
        """
        연결 끊김 콜백
        
        paho-mqtt v2.0+ 호환성을 위해 *args, **kwargs 사용
        인자: (client, userdata, rc, reason_code=None, properties=None)
        """
        # rc가 0이면 정상 종료
        if rc == 0:
            logger.info("ℹ️ MQTT disconnected normally.")
        else:
            # reason_code 추출 (kwargs 또는 args에서)
            reason_code = kwargs.get('reason_code') or (args[0] if args else None)
            reason_str = f", reason_code: {reason_code}" if reason_code else ""
            
            logger.warning(
                f"⚠️ MQTT disconnected unexpectedly. "
                f"Result code: {rc}{reason_str}, "
                f"Host: {self.host}:{self.port}. "
                f"Attempting reconnect with exponential backoff..."
            )
            # 비정상 끊김 시 재연결 시도
            self._schedule_reconnect()
    
    def _on_publish(self, client, userdata, mid, properties=None, reason_code=None):
        """메시지 발행 완료 콜백"""
        if reason_code and reason_code.is_failure:
            logger.warning(
                f"⚠️ MQTT publish failed. "
                f"Message ID: {mid}, "
                f"Reason code: {reason_code}"
            )
        else:
            logger.debug(f"📤 MQTT message published. Message ID: {mid}")
    
    def _on_message(self, client, userdata, msg):
        """
        MQTT 메시지 수신 콜백
        
        센서 데이터를 받아서 InfluxDB에 저장하고,
        Edge AI 알림을 처리합니다.
        """
        try:
            topic = msg.topic
            payload_str = msg.payload.decode('utf-8')
            payload = json.loads(payload_str)
            
            logger.info(f"📥 MQTT message received. Topic: {topic}, Payload size: {len(msg.payload)} bytes")
            
            # Edge AI 알림 토픽인 경우 처리
            # Edge AI 알림 토픽 처리 (factory/inference/results/#)
            if topic.startswith("factory/inference/results/"):
                logger.info(f"✅ [MQTT] Edge AI 알림 토픽 감지: {topic}")
                from backend.api.services.mqtt_ai_subscriber import process_ai_alert_mqtt
                process_ai_alert_mqtt(topic, msg.payload)
                logger.debug(f"✅ [MQTT] Edge AI 알림 처리 함수 호출 완료: {topic}")
            # factory/sensor/* 토픽인 경우 InfluxDB에 저장 (실시간 센서 데이터)
            elif topic.startswith("factory/sensor/"):
                self._process_factory_sensor_data(topic, payload)
            # 센서 데이터 토픽인 경우 InfluxDB에 저장 (기존 형식)
            elif topic.startswith("sensors/") and topic.endswith("/data"):
                self._process_sensor_data(topic, payload)
            else:
                logger.debug(f"Unhandled topic: {topic}")
                
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse MQTT message. Topic: {msg.topic}, Error: {e}")
        except Exception as e:
            logger.error(
                f"❌ Error processing MQTT message. Topic: {msg.topic}, Error: {e}",
                exc_info=True
            )
    
    def _process_sensor_data(self, topic: str, payload: Dict[str, Any]):
        """
        센서 데이터를 InfluxDB에 저장합니다.
        
        Args:
            topic: MQTT 토픽 (예: sensors/sensor_001/data)
            payload: 센서 데이터 페이로드
        """
        try:
            from backend.api.services.influx_client import influx_manager
            from backend.api.services.schemas.models.core.config import settings
            from datetime import datetime
            
            device_id = payload.get("device_id", "unknown")
            
            # 타임스탬프 파싱
            timestamp_str = payload.get("timestamp")
            if timestamp_str:
                try:
                    # ISO 8601 형식 파싱
                    timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                except:
                    timestamp = datetime.utcnow()
            else:
                timestamp = datetime.utcnow()
            
            # InfluxDB Point 생성 및 저장
            bucket = settings.INFLUX_BUCKET
            measurement = "sensor_data"
            
            # 필드 데이터 준비 (None 값 제외)
            fields = {}
            if payload.get("temperature") is not None:
                fields["temperature"] = float(payload["temperature"])
            if payload.get("humidity") is not None:
                fields["humidity"] = float(payload["humidity"])
            if payload.get("vibration") is not None:
                fields["vibration"] = float(payload["vibration"])
            if payload.get("sound") is not None:
                fields["sound"] = float(payload["sound"])
            
            # 필드가 없으면 저장하지 않음
            if not fields:
                logger.warning(f"No valid fields in sensor data. Device: {device_id}")
                return
            
            # 태그 데이터
            tags = {
                "device_id": device_id,
                "sensor_type": "multi"  # 다중 센서
            }
            
            # InfluxDB에 쓰기
            influx_manager.write_point(
                bucket=bucket,
                measurement=measurement,
                fields=fields,
                tags=tags,
                timestamp=timestamp
            )
            
            logger.info(
                f"✅ Sensor data saved to InfluxDB. "
                f"Device: {device_id}, Fields: {list(fields.keys())}"
            )
            
        except ImportError as e:
            logger.error(f"❌ Failed to import InfluxDB manager: {e}")
        except Exception as e:
            logger.error(
                f"❌ Failed to save sensor data to InfluxDB. "
                f"Topic: {topic}, Device: {device_id}, Error: {e}",
                exc_info=True
            )
    
    def _process_factory_sensor_data(self, topic: str, payload: Dict[str, Any]):
        """
        factory/sensor/* 토픽의 센서 데이터를 InfluxDB에 저장합니다.
        
        moby_sensors measurement 형식으로 저장합니다.
        
        Args:
            topic: MQTT 토픽 (예: factory/sensor/vibration, factory/sensor/temperature)
            payload: 센서 데이터 페이로드 (Telegraf 형식)
        """
        try:
            from backend.api.services.influx_client import influx_manager
            from backend.api.services.schemas.models.core.config import settings
            from datetime import datetime
            
            # 토픽에서 센서 타입 추출 (예: factory/sensor/vibration -> vibration)
            sensor_type = topic.split("/")[-1] if "/" in topic else "unknown"
            
            # payload에서 host 추출 (Telegraf 형식)
            # payload 구조: {"fields": {...}, "tags": {...}, "timestamp": ...}
            host = payload.get("tags", {}).get("host") or payload.get("host") or "unknown"
            
            # 타임스탬프 파싱
            timestamp_str = payload.get("timestamp") or payload.get("time")
            if timestamp_str:
                try:
                    # 나노초 타임스탬프 처리
                    if isinstance(timestamp_str, int):
                        # 나노초를 초로 변환
                        timestamp = datetime.fromtimestamp(timestamp_str / 1_000_000_000)
                    else:
                        timestamp = datetime.fromisoformat(str(timestamp_str).replace("Z", "+00:00"))
                except:
                    timestamp = datetime.utcnow()
            else:
                timestamp = datetime.utcnow()
            
            # InfluxDB Point 생성 및 저장
            bucket = settings.INFLUX_BUCKET
            measurement = "moby_sensors"  # 실제 데이터 형식에 맞춤
            
            # fields 추출 (payload.fields 또는 payload에서 직접)
            fields = payload.get("fields", {})
            if not fields:
                # fields가 없으면 payload에서 직접 추출
                fields = {k: v for k, v in payload.items() 
                         if k not in ["tags", "timestamp", "time", "host", "sensor_type", "sensor_model", "topic"]
                         and isinstance(v, (int, float))}
            
            # 필드가 없으면 저장하지 않음
            if not fields:
                logger.debug(f"No valid fields in factory sensor data. Topic: {topic}, Host: {host}")
                return
            
            # 태그 데이터 (moby_sensors 형식에 맞춤)
            tags = payload.get("tags", {})
            if not tags:
                # tags가 없으면 기본 태그 생성
                tags = {
                    "host": host,
                    "sensor_type": sensor_type,
                    "topic": topic
                }
                # payload에서 추가 태그 추출
                if "sensor_model" in payload:
                    tags["sensor_model"] = payload["sensor_model"]
            else:
                # 기존 tags에 topic 추가
                if "topic" not in tags:
                    tags["topic"] = topic
            
            # InfluxDB에 쓰기
            influx_manager.write_point(
                bucket=bucket,
                measurement=measurement,
                fields=fields,
                tags=tags,
                timestamp=timestamp
            )
            
            logger.info(
                f"✅ Factory sensor data saved to InfluxDB. "
                f"Topic: {topic}, Host: {host}, Fields: {list(fields.keys())[:5]}"
            )
            
        except ImportError as e:
            logger.error(f"❌ Failed to import InfluxDB manager: {e}")
        except Exception as e:
            logger.error(
                f"❌ Failed to save factory sensor data to InfluxDB. "
                f"Topic: {topic}, Error: {e}",
                exc_info=True
            )

    def connect_with_retry(
        self, 
        max_retries: int = 3,  # 5 → 3으로 감소 (빠른 실패)
        initial_delay: float = 0.5,  # 1.0 → 0.5로 감소
        max_delay: float = 10.0,  # 60.0 → 10.0으로 감소
        backoff_factor: float = 2.0
    ) -> bool:
        """
        Exponential backoff를 사용한 재연결 로직을 구현합니다.
        
        Args:
            max_retries: 최대 재시도 횟수
            initial_delay: 초기 재시도 간격 (초)
            max_delay: 최대 재시도 간격 (초)
            backoff_factor: 지수 백오프 배수
            
        Returns:
            연결 성공 여부
        """
        # 호스트가 유효하지 않으면 연결 시도하지 않음
        if not self.host or not self.client:
            logger.info(
                "ℹ️ MQTT 호스트가 설정되지 않았습니다. "
                "MQTT 연결을 건너뜁니다."
            )
            return False
        
        with self.connection_lock:
            if self.is_connecting:
                logger.debug("MQTT connection attempt already in progress, skipping...")
                return False
            
            self.is_connecting = True
        
        delay = initial_delay
        
        for attempt in range(max_retries):
            self.connection_attempt_count = attempt + 1
            self.last_connection_attempt = datetime.now()
            
            try:
                logger.info(
                    f"🔄 MQTT connection attempt {attempt + 1}/{max_retries}. "
                    f"Host: {self.host}:{self.port}"
                )
                
                # 연결 시도 (예외 처리 포함)
                try:
                    # connect() 전에 loop_start() 호출 (연결이 성공하면 _on_connect에서 처리)
                    if not self._loop_started:
                        try:
                            self.client.loop_start()
                            self._loop_started = True
                        except Exception as e:
                            logger.warning(f"⚠️ MQTT loop_start 실패: {e}")
                    
                    # 연결 타임아웃 설정 (3초)
                    try:
                        import socket
                        sock = self.client.socket()
                        if sock:
                            sock.settimeout(3.0)
                    except:
                        pass  # socket 설정 실패해도 계속 진행
                    result = self.client.connect(self.host, self.port, keepalive=60)
                except ValueError as e:
                    # "Invalid host" 오류 처리
                    if "Invalid host" in str(e) or "invalid host" in str(e).lower():
                        logger.warning(
                            f"⚠️ MQTT 호스트 '{self.host}'가 유효하지 않습니다. "
                            f"MQTT 연결을 건너뜁니다."
                        )
                        # loop_stop() 호출하여 백그라운드 스레드 종료
                        try:
                            if self._loop_started:
                                self.client.loop_stop()
                                self._loop_started = False
                        except:
                            pass
                        with self.connection_lock:
                            self.is_connecting = False
                        return False
                    raise  # 다른 ValueError는 다시 발생시킴
                
                if result == 0:
                    # 연결 성공 (실제 연결은 _on_connect에서 확인)
                    logger.info(
                        f"✅ MQTT connection initiated successfully on attempt {attempt + 1}. "
                        f"Waiting for confirmation..."
                    )
                    # 연결 확인을 위해 잠시 대기
                    time.sleep(0.5)
                    if self.client.is_connected():
                        with self.connection_lock:
                            self.is_connecting = False
                        return True
                else:
                    logger.warning(
                        f"⚠️ MQTT connection attempt {attempt + 1} returned code {result}. "
                        f"Will retry with exponential backoff."
                    )
                    
            except Exception as e:
                logger.error(
                    f"❌ MQTT connection attempt {attempt + 1} failed with exception: {e}",
                    exc_info=True
                )
            
            # 마지막 시도가 아니면 exponential backoff로 대기
            if attempt < max_retries - 1:
                logger.info(
                    f"⏳ Waiting {delay:.1f} seconds before next retry "
                    f"(exponential backoff: {initial_delay:.1f}s → {delay:.1f}s)..."
                )
                time.sleep(delay)
                
                # 다음 재시도 간격 계산 (exponential backoff)
                delay = min(delay * backoff_factor, max_delay)
        
        # 모든 재시도 실패
        logger.critical(
            f"❌ FATAL: Failed to establish MQTT connection after {max_retries} attempts. "
            f"Host: {self.host}:{self.port}. "
            f"Messages will be queued for later retry."
        )
        
        with self.connection_lock:
            self.is_connecting = False
        
        return False
    
    def _schedule_reconnect(self):
        """연결 끊김 후 재연결을 스케줄링합니다."""
        if not self.is_connecting:
            threading.Thread(
                target=self.connect_with_retry,
                daemon=True,
                name="MQTT-Reconnect"
            ).start()

    def publish_message(self, topic: str, payload: Dict[str, Any]) -> bool:
        """
        MQTT 메시지를 발행합니다.
        
        Args:
            topic: MQTT 토픽
            payload: 발행할 데이터 (딕셔너리)
            
        Returns:
            bool: 발행 성공 여부
        """
        # 호스트가 유효하지 않으면 큐에만 저장
        if not self.host or not self.client:
            logger.debug(
                f"MQTT 호스트가 설정되지 않아 메시지를 큐에 저장합니다. "
                f"Topic: {topic}"
            )
            self._queue_message(topic, payload)
            return False
        
        # 연결되어 있으면 즉시 발송 시도
        if self.client.is_connected():
            try:
                payload_str = json.dumps(payload)
                result = self.client.publish(topic, payload_str, qos=1)
                
                if result.rc == mqtt.MQTT_ERR_SUCCESS:
                    logger.info(
                        f"✅ MQTT message published successfully. "
                        f"Topic: {topic}, Message ID: {result.mid}"
                    )
                    return True
                else:
                    logger.warning(
                        f"⚠️ MQTT publish returned error code {result.rc}. "
                        f"Topic: {topic}. Queueing message for retry."
                    )
                    # 발송 실패 시 큐에 추가
                    self._queue_message(topic, payload)
                    return True  # 큐에 저장되었으므로 True 반환
                    
            except Exception as e:
                logger.error(
                    f"❌ Exception during MQTT publish. "
                    f"Topic: {topic}, Error: {e}. Queueing message for retry.",
                    exc_info=True
                )
                self._queue_message(topic, payload)
                return True  # 큐에 저장되었으므로 True 반환
        
        # 연결되지 않은 경우 큐에 저장
        logger.warning(
            f"⚠️ MQTT client is disconnected. "
            f"Topic: {topic}. Queueing message for later delivery."
        )
        self._queue_message(topic, payload)
        return True  # 큐에 저장되었으므로 True 반환
    
    def _queue_message(self, topic: str, payload: Dict[str, Any]) -> bool:
        """
        메시지를 큐에 추가합니다.
        
        Args:
            topic: MQTT 토픽
            payload: 메시지 데이터
            
        Returns:
            큐 추가 성공 여부
        """
        with self.queue_lock:
            # 큐 크기 확인
            if len(self.message_queue) >= self.max_queue_size:
                logger.error(
                    f"❌ Message queue is full ({self.max_queue_size} messages). "
                    f"Dropping oldest message. Topic: {topic}"
                )
                # 가장 오래된 메시지 제거
                try:
                    self.message_queue.popleft()
                except IndexError:
                    pass
            
            # 새 메시지 추가
            queued_msg = QueuedMessage(
                topic=topic,
                payload=payload,
                timestamp=datetime.now(),
                retry_count=0,
                max_retries=3
            )
            self.message_queue.append(queued_msg)
            
            logger.debug(
                f"📥 Message queued. Topic: {topic}, "
                f"Queue size: {len(self.message_queue)}/{self.max_queue_size}"
            )
            
            # 큐 처리 스레드에 알림
            self._notify_queue_processor()
        
        return True
    
    def _notify_queue_processor(self):
        """큐 처리 스레드에 알림을 보냅니다."""
        # 큐 처리 스레드는 주기적으로 체크하므로 별도 알림 불필요
        pass
    
    def _process_message_queue(self):
        """
        백그라운드에서 큐에 있는 메시지를 처리하는 스레드 함수.
        연결이 복구되면 자동으로 큐의 메시지를 발송합니다.
        """
        logger.info("🔄 MQTT message queue processor started.")
        
        while True:
            try:
                # 호스트가 없으면 스레드 종료
                if not self.host or not self.client:
                    logger.info("ℹ️ MQTT 호스트가 없어 큐 프로세서를 종료합니다.")
                    break
                
                # 연결되어 있고 큐에 메시지가 있으면 처리
                if self.client.is_connected() and len(self.message_queue) > 0:
                    with self.queue_lock:
                        if len(self.message_queue) == 0:
                            continue
                        
                        # 큐에서 메시지 가져오기 (FIFO)
                        queued_msg = self.message_queue.popleft()
                    
                    # 메시지 재시도
                    success = self._retry_queued_message(queued_msg)
                    
                    if not success:
                        # 재시도 실패 시 다시 큐에 추가 (재시도 횟수 확인)
                        if queued_msg.retry_count < queued_msg.max_retries:
                            queued_msg.retry_count += 1
                            with self.queue_lock:
                                self.message_queue.append(queued_msg)
                            logger.warning(
                                f"⚠️ Queued message retry failed. "
                                f"Topic: {queued_msg.topic}, "
                                f"Retry count: {queued_msg.retry_count}/{queued_msg.max_retries}. "
                                f"Will retry later."
                            )
                        else:
                            logger.error(
                                f"❌ Queued message exceeded max retries. "
                                f"Topic: {queued_msg.topic}, "
                                f"Dropping message."
                            )
                else:
                    # 연결되지 않았거나 큐가 비어있으면 잠시 대기
                    time.sleep(1.0)
                    
            except Exception as e:
                logger.error(
                    f"❌ Error in message queue processor: {e}",
                    exc_info=True
                )
                time.sleep(5.0)  # 에러 발생 시 더 긴 대기
    
    def _retry_queued_message(self, queued_msg: QueuedMessage) -> bool:
        """
        큐에 있는 메시지를 재시도합니다.
        
        Args:
            queued_msg: 재시도할 메시지
            
        Returns:
            발송 성공 여부
        """
        try:
            payload_str = json.dumps(queued_msg.payload)
            result = self.client.publish(queued_msg.topic, payload_str, qos=1)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                age_seconds = (datetime.now() - queued_msg.timestamp).total_seconds()
                logger.info(
                    f"✅ Queued message published successfully. "
                    f"Topic: {queued_msg.topic}, "
                    f"Age: {age_seconds:.1f}s, "
                    f"Retry count: {queued_msg.retry_count}, "
                    f"Message ID: {result.mid}"
                )
                return True
            else:
                logger.warning(
                    f"⚠️ Queued message publish failed. "
                    f"Topic: {queued_msg.topic}, "
                    f"Result code: {result.rc}"
                )
                return False
                
        except Exception as e:
            logger.error(
                f"❌ Exception while retrying queued message. "
                f"Topic: {queued_msg.topic}, Error: {e}",
                exc_info=True
            )
            return False

# 글로벌 클라이언트 인스턴스
mqtt_manager = MqttClientManager()

def init_mqtt_client():
    """애플리케이션 시작 시 MQTT 연결을 시도합니다."""
    logger.info("Initializing MQTT connection manager...")
    # 앱 시작 시 연결을 시도하고 실패하면 재시도 루프에 진입합니다.
    mqtt_manager.connect_with_retry()

def publish_alert(topic: str, payload: Dict[str, Any]):
    """
    Alert Engine에서 호출할 외부 엔트리 포인트.
    """
    return mqtt_manager.publish_message(topic, payload)

# -------------------------------------------------------------------