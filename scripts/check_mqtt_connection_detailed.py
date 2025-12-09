"""
MQTT 연결 상세 확인 스크립트

백엔드 서버의 MQTT 연결 상태를 상세히 확인합니다.
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.api.services.schemas.models.core.config import settings
from backend.api.services.mqtt_client import mqtt_manager

def check_mqtt_detailed():
    """MQTT 연결 상세 확인"""
    print("=" * 60)
    print("MQTT 연결 상세 확인")
    print("=" * 60)
    print()
    
    if not mqtt_manager.host:
        print("❌ MQTT 호스트가 설정되지 않았습니다.")
        print(f"   MQTT_HOST: {settings.MQTT_HOST}")
        return False
    
    print(f"📡 MQTT 설정:")
    print(f"   Host: {mqtt_manager.host}")
    print(f"   Port: {mqtt_manager.port}")
    print()
    
    if not mqtt_manager.client:
        print("❌ MQTT 클라이언트가 초기화되지 않았습니다.")
        return False
    
    print(f"🔌 MQTT 클라이언트 상태:")
    print(f"   클라이언트 존재: ✅")
    print(f"   연결 상태: {'✅ 연결됨' if mqtt_manager.client.is_connected() else '❌ 연결 안 됨'}")
    print(f"   루프 상태: {'실행 중' if mqtt_manager._loop_started else '중지됨'}")
    print(f"   연결 시도 중: {mqtt_manager.is_connecting}")
    print(f"   연결 시도 횟수: {mqtt_manager.connection_attempt_count}")
    print(f"   큐 크기: {len(mqtt_manager.message_queue)}/{mqtt_manager.max_queue_size}")
    print()
    
    # 연결 재시도
    if not mqtt_manager.client.is_connected():
        print("🔄 MQTT 연결 재시도 중...")
        result = mqtt_manager.connect_with_retry(max_retries=3, initial_delay=1.0)
        if result:
            print("✅ MQTT 연결 성공!")
        else:
            print("❌ MQTT 연결 실패")
        print()
    
    # 구독된 토픽 확인
    if mqtt_manager.client.is_connected():
        print("📋 구독된 토픽:")
        print("   - sensors/+/data (센서 데이터)")
        print("   - factory/inference/results/# (Edge AI 알림)")
        print()
    
    return mqtt_manager.client.is_connected()

def main():
    """메인 함수"""
    print("\n" + "=" * 60)
    print("MQTT 연결 상세 확인")
    print("=" * 60)
    print()
    
    is_connected = check_mqtt_detailed()
    
    print("=" * 60)
    print("요약")
    print("=" * 60)
    
    if is_connected:
        print("✅ MQTT 연결: 성공")
        print("💡 백엔드가 MQTT 메시지를 수신할 준비가 되었습니다.")
    else:
        print("❌ MQTT 연결: 실패")
        print("💡 백엔드 서버를 재시작하면 MQTT 연결이 자동으로 재시도됩니다.")
        print()
        print("   해결 방법:")
        print("   1. 백엔드 서버가 실행 중인지 확인")
        print("   2. 백엔드 서버를 재시작")
        print("   3. 로그 파일 확인: logs/moby-debug.log")
    
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

