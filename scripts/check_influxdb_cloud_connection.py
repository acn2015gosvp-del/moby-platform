"""InfluxDB 클라우드 연결 확인"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.api.services.influx_client import influx_manager
from backend.api.services.schemas.models.core.config import settings

print("=" * 60)
print("InfluxDB 클라우드 연결 확인")
print("=" * 60)
print()

print(f"📡 연결 정보:")
print(f"   URL: {settings.INFLUX_URL}")
print(f"   Organization: {settings.INFLUX_ORG}")
print(f"   Bucket: {settings.INFLUX_BUCKET}")
print()

# URL이 클라우드인지 확인
if "cloud" in settings.INFLUX_URL.lower() or "influxdata.com" in settings.INFLUX_URL:
    print("✅ InfluxDB 클라우드 URL 확인됨")
else:
    print("⚠️ 로컬 InfluxDB URL로 보입니다")
print()

# 실제 쿼리 테스트
print("🔍 실제 쿼리 테스트:")
try:
    query = f'''
    from(bucket: "{settings.INFLUX_BUCKET}")
      |> range(start: -1h)
      |> limit(n: 1)
    '''
    
    result = influx_manager.query_api.query(query=query, org=settings.INFLUX_ORG)
    count = sum(1 for table in result for _ in table.records)
    
    if count >= 0:  # 쿼리가 성공하면 (데이터가 없어도 성공)
        print(f"   ✅ InfluxDB 클라우드 연결 성공!")
        print(f"   최근 1시간 데이터: {count}개 포인트")
        print()
        print("=" * 60)
        print("결론: InfluxDB 클라우드에 정상적으로 연결되어 있습니다!")
        print("=" * 60)
    else:
        print("   ⚠️ 쿼리는 성공했지만 데이터가 없습니다")
        
except Exception as e:
    print(f"   ❌ 연결 실패: {e}")
    print()
    print("=" * 60)
    print("결론: InfluxDB 클라우드 연결에 문제가 있습니다.")
    print("=" * 60)

