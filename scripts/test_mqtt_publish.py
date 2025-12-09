"""
MQTT 테스트 메시지 발행 스크립트

센서 데이터를 MQTT 브로커로 발행하여 백엔드가 수신하는지 테스트합니다.
"""

import sys
import os
import json
import time
from pathlib import Path
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("❌ paho-mqtt가 설치되지 않았습니다.")
    print("   설치 명령: pip install paho-mqtt")
    sys.exit(1)

from backend.api.services.schemas.models.core.config import settings

def on_connect(client, userdata, flags, rc, properties=None):
    """연결 콜백"""
    if rc == 0:
        print("✅ MQTT 브로커에 연결되었습니다.")
    else:
        print(f"❌ MQTT 연결 실패. 코드: {rc}")
        sys.exit(1)

def on_publish(client, userdata, mid, properties=None, reason_code=None):
    """발행 완료 콜백"""
    print(f"✅ 메시지 발행 완료 (Message ID: {mid})")

def publish_test_message():
    """테스트 메시지 발행"""
    print("=" * 60)
    print("MQTT 테스트 메시지 발행")
    print("=" * 60)
    print()
    
    # MQTT 설정
    host = settings.MQTT_HOST or "127.0.0.1"
    port = settings.MQTT_PORT or 1883
    
    print(f"📡 MQTT 설정:")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print()
    
    # MQTT 클라이언트 생성
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_publish = on_publish
    
    try:
        # 연결
        print(f"🔄 MQTT 브로커에 연결 중... ({host}:{port})")
        client.connect(host, port, 60)
        client.loop_start()
        
        # 연결 확인을 위해 잠시 대기
        time.sleep(1)
        
        if not client.is_connected():
            print("❌ MQTT 브로커에 연결할 수 없습니다.")
            return False
        
        # 테스트 센서 데이터 생성
        test_device_id = "test-sensor-001"
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        test_messages = [
            {
                "device_id": test_device_id,
                "timestamp": timestamp,
                "temperature": 25.5,
                "humidity": 60.0,
                "vibration": 0.5,
                "sound": 45.0,
            },
            {
                "device_id": test_device_id,
                "timestamp": timestamp,
                "temperature": 26.0,
                "humidity": 61.0,
                "vibration": 0.6,
                "sound": 46.0,
            },
        ]
        
        # 메시지 발행
        topic = f"sensors/{test_device_id}/data"
        print(f"📤 테스트 메시지 발행 중...")
        print(f"   토픽: {topic}")
        print()
        
        for i, message in enumerate(test_messages, 1):
            payload = json.dumps(message)
            result = client.publish(topic, payload, qos=1)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"✅ 메시지 {i} 발행 성공:")
                print(f"   {json.dumps(message, indent=2, ensure_ascii=False)}")
            else:
                print(f"❌ 메시지 {i} 발행 실패. 코드: {result.rc}")
            
            time.sleep(0.5)  # 메시지 간 간격
        
        # 발행 완료 대기
        time.sleep(2)
        
        print()
        print("=" * 60)
        print("요약")
        print("=" * 60)
        print("✅ 테스트 메시지 발행 완료")
        print(f"📊 발행된 메시지 수: {len(test_messages)}")
        print(f"📡 토픽: {topic}")
        print()
        print("💡 다음 단계:")
        print("   1. 백엔드 서버 로그에서 메시지 수신 여부 확인")
        print("   2. InfluxDB에 데이터가 저장되었는지 확인:")
        print("      python scripts/check_influxdb_data.py")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    try:
        publish_test_message()
    except KeyboardInterrupt:
        print("\n\n사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

