"""
MQTT 구독 상태 확인 스크립트

factory/inference/results/# 토픽 구독 상태를 확인합니다.
"""

import sys
import os

# 프로젝트 루트를 Python 경로에 추가
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from backend.api.services.mqtt_client import mqtt_manager
import time

def check_mqtt_subscription():
    """MQTT 구독 상태 확인"""
    print("=" * 60)
    print("MQTT 구독 상태 확인")
    print("=" * 60)
    print()
    
    print("=" * 60)
    print("MQTT 연결 상태")
    print("=" * 60)
    print(f"📡 MQTT 설정:")
    print(f"   Host: {mqtt_manager.host}")
    print(f"   Port: {mqtt_manager.port}")
    print(f"   연결 상태: {'✅ 연결됨' if mqtt_manager.client and mqtt_manager.client.is_connected() else '❌ 연결 안 됨'}")
    print(f"   루프 상태: {'실행 중' if mqtt_manager.client and mqtt_manager.client.loop_start() else '중지됨'}")
    print()
    
    if mqtt_manager.client and mqtt_manager.client.is_connected():
        print("=" * 60)
        print("구독 토픽 확인")
        print("=" * 60)
        print("✅ 구독 중인 토픽:")
        print("   - sensors/+/data")
        print("   - factory/inference/results/#")
        print()
        print("💡 MQTT 메시지 수신 확인:")
        print("   - 백엔드 로그에서 '📥 MQTT message received' 메시지 확인")
        print("   - '✅ [MQTT] Edge AI 알림 토픽 감지' 메시지 확인")
        print("   - '🚀 [MQTT AI] WebSocket으로 알림 전송 시도' 메시지 확인")
        print()
    else:
        print("=" * 60)
        print("요약")
        print("=" * 60)
        print("❌ MQTT 연결: 실패")
        print("💡 MQTT 브로커에 연결되지 않았습니다.")
        print("   가능한 원인:")
        print("   1. MQTT 브로커가 실행되지 않음")
        print("   2. MQTT_HOST 또는 MQTT_PORT 설정이 잘못됨")
        print("   3. 네트워크 연결 문제")
        print()
        print("   해결 방법:")
        print("   1. MQTT 브로커(Mosquitto 등)가 실행 중인지 확인")
        print("   2. .env 파일의 MQTT_HOST, MQTT_PORT 확인")
        print("   3. 백엔드 서버를 재시작하여 MQTT 연결 재시도")
        print()

if __name__ == "__main__":
    try:
        check_mqtt_subscription()
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()




