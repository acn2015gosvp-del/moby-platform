"""
센서 데이터 조회 디버깅 스크립트
실제로 InfluxDB에서 데이터가 조회되는지 확인
"""

import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.api.services.report_service import get_report_service
from backend.api.services.database import get_db

def test_sensor_data_query():
    """센서 데이터 조회 테스트"""
    print("=" * 60)
    print("센서 데이터 조회 디버깅")
    print("=" * 60)
    
    # 테스트 기간 설정 (최근 7일)
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(days=7)
    
    print(f"\n📅 조회 기간:")
    print(f"   시작: {start_time.isoformat()}")
    print(f"   종료: {end_time.isoformat()}")
    print()
    
    # ReportDataService 인스턴스 가져오기
    report_service = get_report_service()
    
    # 각 필드별로 직접 조회 테스트
    fields_to_test = [
        "fields_temperature_c",
        "fields_humidity_percent",
        "fields_accel_x",
        "fields_accel_y",
        "fields_accel_z",
        "fields_sound_raw"
    ]
    
    print("🔍 필드별 데이터 조회 테스트:")
    print()
    
    for field_name in fields_to_test:
        print(f"📊 {field_name}:")
        try:
            start_rfc3339 = start_time.strftime('%Y-%m-%dT%H:%M:%SZ')
            end_rfc3339 = end_time.strftime('%Y-%m-%dT%H:%M:%SZ')
            
            df = report_service._fetch_raw_data_as_dataframe(
                start_rfc3339=start_rfc3339,
                end_rfc3339=end_rfc3339,
                field_name=field_name,
                device_filter=None,
                measurement="moby_sensors"
            )
            
            if df is not None and len(df) > 0:
                print(f"   ✅ 데이터 발견: {len(df)}개 포인트")
                print(f"   📈 통계:")
                print(f"      Mean: {df['_value'].mean():.2f}")
                print(f"      Min: {df['_value'].min():.2f}")
                print(f"      Max: {df['_value'].max():.2f}")
                print(f"      Std: {df['_value'].std():.2f}")
                if len(df) > 0:
                    print(f"      P95: {df['_value'].quantile(0.95):.2f}")
            else:
                print(f"   ❌ 데이터 없음")
        except Exception as e:
            print(f"   ❌ 오류: {e}")
            import traceback
            traceback.print_exc()
        print()
    
    # 전체 센서 통계 조회 테스트
    print("=" * 60)
    print("전체 센서 통계 조회 테스트")
    print("=" * 60)
    print()
    
    try:
        with next(get_db()) as db:
            report_data = report_service.fetch_report_data(
                start_time=start_time,
                end_time=end_time,
                equipment_id="Conveyor A-01",
                db=db,
                sensor_ids=None
            )
            
            print("📊 센서 통계 결과:")
            sensor_stats = report_data.get("sensor_stats", {})
            
            # 온도
            temp = sensor_stats.get("temperature", {})
            print(f"   온도: mean={temp.get('mean', 0):.2f}, max={temp.get('max', 0):.2f}")
            
            # 습도
            humidity = sensor_stats.get("humidity", {})
            print(f"   습도: mean={humidity.get('mean', 0):.2f}, max={humidity.get('max', 0):.2f}")
            
            # 진동
            vibration = sensor_stats.get("vibration", {})
            print(f"   진동 X: mean={vibration.get('x', {}).get('mean', 0):.2f}, peak={vibration.get('x', {}).get('peak', 0):.2f}")
            print(f"   진동 Y: mean={vibration.get('y', {}).get('mean', 0):.2f}, peak={vibration.get('y', {}).get('peak', 0):.2f}")
            print(f"   진동 Z: mean={vibration.get('z', {}).get('mean', 0):.2f}, peak={vibration.get('z', {}).get('peak', 0):.2f}")
            
            # 사운드
            sound = sensor_stats.get("sound", {})
            print(f"   사운드: mean={sound.get('mean', 0):.2f}, max={sound.get('max', 0):.2f}")
            
    except Exception as e:
        print(f"❌ 전체 조회 실패: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_sensor_data_query()

