# backend/api/services/mqtt_client.py (수정된 내용)

import paho.mqtt.client as mqtt
from backend.core.config import settings


# 테스트 파일이 import하는 클래스를 정의합니다.
class MQTTClient:
    # 테스트 Fixture가 요구하는 __init__ 메소드를 구현합니다.
    def __init__(self, 
        host=settings.MQTT_HOST, # settings 사용
        port=settings.MQTT_PORT, # settings 사용
        topics=None, 
        alert_callback=None):
        self.host = host
        self.port = port
        self.topics = topics
        self.alert_callback = alert_callback
        
        # paho-mqtt 클라이언트 인스턴스 생성
        self.client = mqtt.Client()

    # 테스트 파일이 호출하는 연결 메소드를 구현합니다. (Dev A Task 포함)
    def connect_with_retry(self):
        print(f"MQTT: Connecting to {self.host}:{self.port}...")
        # TODO: Dev A는 여기에 지수 백오프(exponential backoff) 재연결 로직을 구현해야 함
        try:
            # 실제 연결 시도
            self.client.connect(self.host, self.port, 60) 
            self.client.loop_start() # 연결 후 백그라운드 루프 시작
            print("MQTT: Connection successful.")
            return True
        except Exception as e:
            print(f"MQTT: Connection failed: {e}")
            return False

    # 기존의 publish_message 함수를 클래스 메소드로 통합
    def publish_message(self, topic: str, payload: dict):
        # 이미 연결되었다고 가정하고 메시지를 보냅니다.
        self.client.publish(topic, str(payload))

# 참고: settings.MQTT_HOST를 사용하도록 초기화 로직을 추가해야 할 수도 있습니다.
# (예: main.py 파일에서 MQTTClient(settings.MQTT_HOST, ...) 형태로 호출)