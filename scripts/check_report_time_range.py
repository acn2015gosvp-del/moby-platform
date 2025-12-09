"""
보고서 생성 시 사용된 시간 범위와 실제 데이터 시간 범위 비교 스크립트
"""

import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.api.services.report_service import get_report_service
from backend.api.services.database import get_db

def check_time_range():
    """보고서 생성 시 사용된 시간 범위 확인"""
    print("=" * 80)
    print("보고서 시간 범위 확인")
    print("=" * 80)
    print()
    
    # 콘솔 로그에서 확인된 시간 범위
    # period_start: "2025-11-30 21:14:00" (UTC)
    # period_end: "2025-12-07 21:14:00" (UTC)
    
    start_time = datetime(2025, 11, 30, 21, 14, 0, tzinfo=timezone.utc)
    end_time = datetime(2025, 12, 7, 21, 14, 0, tzinfo=timezone.utc)
    
    print(f"📅 보고서 요청 시간 범위:")
    print(f"   시작: {start_time.isoformat()}")
    print(f"   종료: {end_time.isoformat()}")
    print(f"   기간: {(end_time - start_time).total_seconds() / 3600:.2f}시간")
    print()
    
    # InfluxDB에서 실제 데이터 확인
    report_service = get_report_service()
    
    start_rfc3339 = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_rfc3339 = end_time.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    print(f"📊 InfluxDB 조회 시간 범위 (RFC3339):")
    print(f"   시작: {start_rfc3339}")
    print(f"   종료: {end_rfc3339}")
    print()
    
    # 각 필드별로 데이터 확인
    fields_to_check = [
        ("fields_temperature_c", "온도"),
        ("fields_humidity_percent", "습도"),
        ("fields_vibration_raw", "진동"),
        ("fields_sound_raw", "소음")
    ]
    
    print("=" * 80)
    print("데이터 조회 테스트")
    print("=" * 80)
    print()
    
    for field_name, field_desc in fields_to_check:
        print(f"📊 {field_desc} ({field_name}):")
        try:
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
                print(f"   📅 시간 범위:")
                print(f"      시작: {df['_time'].min()}")
                print(f"      종료: {df['_time'].max()}")
            else:
                print(f"   ❌ 데이터 없음")
                
                # 시간 범위를 넓혀서 확인
                print(f"   🔍 시간 범위 확장하여 재시도...")
                extended_start = start_time - timedelta(days=1)
                extended_end = end_time + timedelta(days=1)
                extended_start_rfc = extended_start.strftime("%Y-%m-%dT%H:%M:%SZ")
                extended_end_rfc = extended_end.strftime("%Y-%m-%dT%H:%M:%SZ")
                
                df_extended = report_service._fetch_raw_data_as_dataframe(
                    start_rfc3339=extended_start_rfc,
                    end_rfc3339=extended_end_rfc,
                    field_name=field_name,
                    device_filter=None,
                    measurement="moby_sensors"
                )
                
                if df_extended is not None and len(df_extended) > 0:
                    print(f"   ⚠️ 확장된 범위에서는 데이터 발견: {len(df_extended)}개")
                    print(f"      데이터 시간 범위: {df_extended['_time'].min()} ~ {df_extended['_time'].max()}")
                    print(f"      → 요청 시간 범위와 실제 데이터 시간 범위가 다릅니다!")
                else:
                    print(f"   ❌ 확장된 범위에서도 데이터 없음")
        except Exception as e:
            print(f"   ❌ 오류: {e}")
        print()
    
    # 알람 데이터 확인
    print("=" * 80)
    print("알람 데이터 확인")
    print("=" * 80)
    print()
    
    try:
        with next(get_db()) as db:
            from backend.api.services.alert_storage import get_latest_alerts
            alerts = get_latest_alerts(db=db, limit=100)
            
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
                            period_alerts.append({
                                'time': alert_dt,
                                'sensor': getattr(alert, 'sensor_id', 'unknown')
                            })
                    except:
                        continue
            
            print(f"   기간 내 알람 개수: {len(period_alerts)}")
            if period_alerts:
                print(f"   알람 시간 범위:")
                alarm_times = [a['time'] for a in period_alerts]
                print(f"      시작: {min(alarm_times)}")
                print(f"      종료: {max(alarm_times)}")
            else:
                print("   ⚠️ 기간 내 알람이 없습니다.")
    except Exception as e:
        print(f"   ❌ 알람 조회 실패: {e}")


if __name__ == "__main__":
    check_time_range()

