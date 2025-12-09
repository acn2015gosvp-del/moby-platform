"""
센서 데이터 불일치 디버깅 스크립트
알람에는 값이 있는데 통계가 0인 문제 해결
"""

import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.api.services.report_service import get_report_service
from backend.api.services.database import get_db
from backend.api.services.alert_storage import get_latest_alerts

def debug_data_mismatch():
    """알람 데이터와 센서 통계 데이터 불일치 확인"""
    print("=" * 60)
    print("센서 데이터 불일치 디버깅")
    print("=" * 60)
    
    # 리포트 기간 (알람이 있는 기간)
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(days=7)
    
    print(f"\n📅 조회 기간:")
    print(f"   시작: {start_time.isoformat()}")
    print(f"   종료: {end_time.isoformat()}")
    print()
    
    # 1. 알람 데이터 확인 (SQLite)
    print("=" * 60)
    print("1. 알람 데이터 확인 (SQLite)")
    print("=" * 60)
    
    try:
        with next(get_db()) as db:
            alerts = get_latest_alerts(db=db, limit=100)
            
            # 기간 내 알람 필터링
            period_alerts = []
            for alert in alerts:
                alert_time = getattr(alert, 'ts', None) or getattr(alert, 'timestamp', None)
                if alert_time:
                    try:
                        if isinstance(alert_time, str):
                            alert_dt = datetime.fromisoformat(alert_time.replace("Z", "+00:00"))
                        else:
                            alert_dt = alert_time
                            if alert_dt.tzinfo is None:
                                alert_dt = alert_dt.replace(tzinfo=timezone.utc)
                        
                        if start_time <= alert_dt <= end_time:
                            details = getattr(alert, 'details', None)
                            if isinstance(details, dict):
                                value = details.get('value', 0.0)
                                period_alerts.append({
                                    'time': alert_dt,
                                    'value': value,
                                    'sensor': getattr(alert, 'sensor_id', 'unknown')
                                })
                    except:
                        continue
            
            print(f"   기간 내 알람 개수: {len(period_alerts)}")
            if period_alerts:
                print(f"   알람 값 샘플:")
                for alert in period_alerts[:5]:
                    print(f"      {alert['time']}: {alert['value']} (센서: {alert['sensor']})")
            else:
                print("   ⚠️ 기간 내 알람이 없습니다.")
    except Exception as e:
        print(f"   ❌ 알람 조회 실패: {e}")
    
    print()
    
    # 2. InfluxDB 센서 데이터 확인
    print("=" * 60)
    print("2. InfluxDB 센서 데이터 확인")
    print("=" * 60)
    
    report_service = get_report_service()
    
    # 시간 범위를 RFC3339로 변환
    start_rfc3339 = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_rfc3339 = end_time.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    print(f"   조회 기간 (RFC3339): {start_rfc3339} ~ {end_rfc3339}")
    print()
    
    # 각 필드별로 데이터 확인
    fields_to_check = [
        ("fields_temperature_c", "온도"),
        ("fields_humidity_percent", "습도"),
        ("fields_vibration_raw", "진동"),
        ("fields_sound_raw", "소음")
    ]
    
    for field_name, field_desc in fields_to_check:
        print(f"   📊 {field_desc} ({field_name}):")
        try:
            df = report_service._fetch_raw_data_as_dataframe(
                start_rfc3339=start_rfc3339,
                end_rfc3339=end_rfc3339,
                field_name=field_name,
                device_filter=None,  # 필터 없이
                measurement="moby_sensors"
            )
            
            if df is not None and len(df) > 0:
                print(f"      ✅ 데이터 발견: {len(df)}개 포인트")
                print(f"      📈 통계:")
                print(f"         Mean: {df['_value'].mean():.2f}")
                print(f"         Min: {df['_value'].min():.2f}")
                print(f"         Max: {df['_value'].max():.2f}")
                print(f"      📅 시간 범위:")
                print(f"         시작: {df['_time'].min()}")
                print(f"         종료: {df['_time'].max()}")
            else:
                print(f"      ❌ 데이터 없음")
                
                # 필드명이 다른지 확인
                print(f"      🔍 다른 필드명 확인 중...")
                # 가능한 필드명 목록
                possible_fields = [
                    field_name.replace("fields_", ""),
                    field_name.replace("fields_", "field_"),
                    field_name.upper(),
                    field_name.lower(),
                ]
                # 실제로는 InfluxDB에서 필드 목록을 조회해야 하지만, 여기서는 로그만
                print(f"      💡 가능한 필드명: {possible_fields}")
        except Exception as e:
            print(f"      ❌ 오류: {e}")
        print()
    
    # 3. 전체 통계 조회 테스트
    print("=" * 60)
    print("3. 전체 통계 조회 테스트")
    print("=" * 60)
    
    try:
        with next(get_db()) as db:
            report_data = report_service.fetch_report_data(
                start_time=start_time,
                end_time=end_time,
                equipment_id="Conveyor A-01",
                db=db,
                sensor_ids=None
            )
            
            sensor_stats = report_data.get("sensor_stats", {})
            alarms = report_data.get("alarms", [])
            
            print(f"   알람 개수: {len(alarms)}")
            if alarms:
                print(f"   알람 값 샘플:")
                for alarm in alarms[:3]:
                    print(f"      {alarm.get('timestamp', 'N/A')}: {alarm.get('value', 0)}")
            
            print()
            print(f"   센서 통계:")
            for sensor_name, stats in sensor_stats.items():
                if sensor_name == "vibration":
                    print(f"      {sensor_name}:")
                    for axis, axis_stats in stats.items():
                        mean = axis_stats.get('mean', 0)
                        if mean != 0.0:
                            print(f"         {axis}: mean={mean:.2f}")
                        else:
                            print(f"         {axis}: mean=0.0 ⚠️")
                else:
                    mean = stats.get('mean', 0)
                    if mean != 0.0:
                        print(f"      {sensor_name}: mean={mean:.2f}, max={stats.get('max', 0):.2f}")
                    else:
                        print(f"      {sensor_name}: mean=0.0 ⚠️")
            
            # 불일치 확인
            print()
            print("=" * 60)
            print("4. 불일치 분석")
            print("=" * 60)
            
            if len(alarms) > 0 and all(
                stats.get('mean', 0) == 0.0 
                for stats in sensor_stats.values() 
                if isinstance(stats, dict) and 'mean' in stats
            ):
                print("   ⚠️ 불일치 발견!")
                print("   - 알람에는 값이 있음")
                print("   - 통계는 모두 0.0")
                print()
                print("   가능한 원인:")
                print("   1. 타임존 불일치 (알람은 다른 시간대, 통계는 다른 시간대 조회)")
                print("   2. 필드명 불일치 (알람은 다른 필드, 통계는 다른 필드 조회)")
                print("   3. measurement 불일치 (알람은 다른 measurement, 통계는 다른 measurement)")
                print("   4. 집계 쿼리 오류 (데이터는 있지만 집계 결과가 0)")
            else:
                print("   ✅ 데이터 일치 또는 알람이 없음")
                
    except Exception as e:
        print(f"❌ 전체 조회 실패: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    debug_data_mismatch()

