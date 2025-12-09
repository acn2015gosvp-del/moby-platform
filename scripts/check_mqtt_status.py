"""
MQTT 연결 및 데이터 수신 상태 확인 스크립트
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.api.services.schemas.models.core.config import settings
from backend.api.services.mqtt_client import mqtt_manager

def check_mqtt_status():
    """MQTT 연결 상태 확인"""
    print("=" * 60)
    print("MQTT 연결 상태 확인")
    print("=" * 60)
    
    if not mqtt_manager.host:
        print("❌ MQTT 호스트가 설정되지 않았습니다.")
        print(f"   MQTT_HOST: {settings.MQTT_HOST}")
        return False
    
    print(f"📡 MQTT 설정:")
    print(f"   Host: {mqtt_manager.host}")
    print(f"   Port: {mqtt_manager.port}")
    print(f"   연결 상태: {'✅ 연결됨' if mqtt_manager.client and mqtt_manager.client.is_connected() else '❌ 연결 안 됨'}")
    
    if mqtt_manager.client:
        print(f"   루프 상태: {'실행 중' if mqtt_manager._loop_started else '중지됨'}")
        print(f"   큐 크기: {len(mqtt_manager.message_queue)}/{mqtt_manager.max_queue_size}")
    
    return mqtt_manager.client and mqtt_manager.client.is_connected()

def main():
    """메인 함수"""
    print("\n" + "=" * 60)
    print("MQTT 상태 확인")
    print("=" * 60)
    print()
    
    is_connected = check_mqtt_status()
    
    print("\n" + "=" * 60)
    print("요약")
    print("=" * 60)
    
    if is_connected:
        print("✅ MQTT 연결: 성공")
        print("💡 MQTT 브로커에 연결되어 있습니다.")
        print("   센서 데이터가 MQTT 토픽 'sensors/+/data'로 전송되면")
        print("   자동으로 InfluxDB에 저장됩니다.")
    else:
        print("❌ MQTT 연결: 실패")
        print("💡 MQTT 브로커에 연결되지 않았습니다.")
        print("   가능한 원인:")
        print("   1. MQTT 브로커가 실행되지 않음")
        print("   2. MQTT_HOST 또는 MQTT_PORT 설정이 잘못됨")
        print("   3. 네트워크 연결 문제")
        print("\n   해결 방법:")
        print("   1. MQTT 브로커(Mosquitto 등)가 실행 중인지 확인")
        print("   2. .env 파일의 MQTT_HOST, MQTT_PORT 확인")
        print("   3. 백엔드 서버를 재시작하여 MQTT 연결 재시도")
    
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

