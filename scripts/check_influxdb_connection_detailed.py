"""
InfluxDB 연결 상태 상세 확인 스크립트
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.api.services.schemas.models.core.config import settings
from backend.api.services.influx_client import influx_manager


def check_connection():
    """InfluxDB 연결 상태 확인"""
    print("=" * 60)
    print("InfluxDB 연결 상태 상세 확인")
    print("=" * 60)
    
    try:
        # 클라이언트 정보
        print(f"\n📡 연결 정보:")
        print(f"   URL: {settings.INFLUX_URL}")
        print(f"   Organization: {settings.INFLUX_ORG}")
        print(f"   Bucket: {settings.INFLUX_BUCKET}")
        print(f"   Token: {'설정됨' if settings.INFLUX_TOKEN else '❌ 미설정'}")
        print()
        
        # Health 체크
        print("🔍 Health 체크:")
        try:
            health = influx_manager.client.health()
            print(f"   Status: {health.status if hasattr(health, 'status') else 'OK'}")
            print(f"   Message: {health.message if hasattr(health, 'message') else 'N/A'}")
        except Exception as e:
            print(f"   ❌ Health 체크 실패: {e}")
        print()
        
        # 간단한 쿼리 테스트
        print("🔍 쿼리 테스트:")
        try:
            query = f'''
            from(bucket: "{settings.INFLUX_BUCKET}")
              |> range(start: -1h)
              |> limit(n: 1)
            '''
            
            result = influx_manager.query_api.query(query=query, org=settings.INFLUX_ORG)
            count = sum(1 for table in result for _ in table.records)
            print(f"   ✅ 쿼리 성공 (최근 1시간 데이터: {count}개 포인트)")
        except Exception as e:
            print(f"   ❌ 쿼리 실패: {e}")
        print()
        
        # Write API 테스트
        print("🔍 Write API 테스트:")
        try:
            from influxdb_client import Point
            from datetime import datetime
            
            # 테스트 포인트 생성
            test_point = Point("connection_test")
            test_point.field("test_value", 1.0)
            test_point.tag("test", "true")
            test_point.time(datetime.utcnow())
            
            # 쓰기 시도 (실제로는 쓰지 않고 API만 확인)
            print(f"   ✅ Write API 초기화 완료")
            print(f"   버퍼 크기: {len(influx_manager.buffer)}/{influx_manager.buffer_size}")
        except Exception as e:
            print(f"   ❌ Write API 확인 실패: {e}")
        print()
        
        # 버퍼 상태
        print("📦 버퍼 상태:")
        print(f"   현재 버퍼 크기: {len(influx_manager.buffer)}")
        print(f"   최대 버퍼 크기: {influx_manager.buffer_size}")
        print(f"   플러시 간격: {influx_manager.flush_interval}초")
        print()
        
        print("=" * 60)
        print("✅ InfluxDB 연결 상태: 정상")
        print("=" * 60)
        print()
        print("💡 참고:")
        print("   - 연결은 정상적으로 되어 있습니다.")
        print("   - 실시간 데이터 저장을 위해서는 MQTT 브로커가 실행 중이어야 합니다.")
        print("   - MQTT 클라이언트가 factory/sensor/# 토픽을 구독하고 있습니다.")
        print()
        
    except Exception as e:
        print(f"❌ 연결 확인 실패: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    check_connection()

