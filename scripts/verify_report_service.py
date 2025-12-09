"""
보고서 서비스 환경 검증 스크립트

실제 환경에서 보고서 서비스가 정상 작동하는지 확인합니다.
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import datetime, timezone, timedelta
from backend.api.services.report_service import get_report_service
from backend.api.services.schemas.models.core.config import settings
from backend.api.services.database import get_db
from backend.api.services.influx_client import influx_manager


def check_environment():
    """환경 변수 설정 확인"""
    print("=" * 60)
    print("환경 변수 확인")
    print("=" * 60)
    
    required_vars = {
        "INFLUX_URL": settings.INFLUX_URL,
        "INFLUX_TOKEN": "설정됨" if settings.INFLUX_TOKEN else "❌ 미설정",
        "INFLUX_ORG": settings.INFLUX_ORG if settings.INFLUX_ORG else "❌ 미설정",
        "INFLUX_BUCKET": settings.INFLUX_BUCKET if settings.INFLUX_BUCKET else "❌ 미설정",
    }
    
    all_ok = True
    for var_name, var_value in required_vars.items():
        status = "✅" if var_value and "❌" not in str(var_value) else "❌"
        print(f"{status} {var_name}: {var_value}")
        if "❌" in str(var_value):
            all_ok = False
    
    print()
    return all_ok


def check_influxdb_connection():
    """InfluxDB 연결 확인"""
    print("=" * 60)
    print("InfluxDB 연결 확인")
    print("=" * 60)
    
    try:
        # 간단한 쿼리로 연결 테스트
        query = f'''
        from(bucket: "{settings.INFLUX_BUCKET}")
          |> range(start: -1h)
          |> limit(n: 1)
        '''
        
        result = influx_manager.query_api.query(
            query=query,
            org=settings.INFLUX_ORG
        )
        
        # 결과가 있는지 확인 (에러가 나지 않으면 연결 성공)
        count = sum(1 for _ in result)
        print(f"✅ InfluxDB 연결 성공")
        print(f"   Bucket: {settings.INFLUX_BUCKET}")
        print(f"   Org: {settings.INFLUX_ORG}")
        print(f"   최근 1시간 데이터 포인트: {count}개")
        print()
        return True
        
    except Exception as e:
        print(f"❌ InfluxDB 연결 실패: {e}")
        print()
        return False


def test_report_service_data_fetch():
    """보고서 서비스 데이터 조회 테스트"""
    print("=" * 60)
    print("보고서 서비스 데이터 조회 테스트")
    print("=" * 60)
    
    try:
        # 보고서 서비스 초기화
        service = get_report_service()
        
        # 테스트 기간 설정 (최근 1일)
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=1)
        
        # 데이터베이스 세션 가져오기
        db = next(get_db())
        
        try:
            # 보고서 데이터 조회
            print(f"기간: {start_time.isoformat()} ~ {end_time.isoformat()}")
            print(f"설비 ID: test_equipment")
            print()
            
            report_data = service.fetch_report_data(
                start_time=start_time,
                end_time=end_time,
                equipment_id="test_equipment",
                db=db
            )
            
            # 결과 확인
            print("✅ 보고서 데이터 조회 성공")
            print()
            print("데이터 구조:")
            print(f"  - 메타데이터: {'✅' if 'metadata' in report_data else '❌'}")
            print(f"  - 센서 통계: {'✅' if 'sensor_stats' in report_data else '❌'}")
            print(f"  - 알람: {'✅' if 'alarms' in report_data else '❌'} ({len(report_data.get('alarms', []))}개)")
            print(f"  - MLP 이상: {'✅' if 'mlp_anomalies' in report_data else '❌'} ({len(report_data.get('mlp_anomalies', []))}개)")
            print(f"  - IF 이상: {'✅' if 'if_anomalies' in report_data else '❌'} ({len(report_data.get('if_anomalies', []))}개)")
            print(f"  - 상관계수: {'✅' if 'correlations' in report_data else '❌'}")
            print()
            
            # 센서 통계 상세
            sensor_stats = report_data.get("sensor_stats", {})
            if sensor_stats:
                print("센서 통계:")
                for sensor_name, stats in sensor_stats.items():
                    if isinstance(stats, dict) and "mean" in stats:
                        print(f"  - {sensor_name}: 평균={stats.get('mean', 'N/A')}, 최대={stats.get('max', 'N/A')}")
                    elif isinstance(stats, dict):
                        print(f"  - {sensor_name}: {len(stats)}개 항목")
            
            print()
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ 보고서 데이터 조회 실패: {e}")
        import traceback
        traceback.print_exc()
        print()
        return False


def main():
    """메인 실행 함수"""
    print("\n" + "=" * 60)
    print("보고서 서비스 환경 검증")
    print("=" * 60 + "\n")
    
    results = []
    
    # 1. 환경 변수 확인
    results.append(("환경 변수", check_environment()))
    
    if not results[-1][1]:
        print("⚠️  환경 변수가 올바르게 설정되지 않았습니다.")
        print("   .env 파일을 확인하세요.\n")
        return
    
    # 2. InfluxDB 연결 확인
    results.append(("InfluxDB 연결", check_influxdb_connection()))
    
    if not results[-1][1]:
        print("⚠️  InfluxDB에 연결할 수 없습니다.")
        print("   연결 정보를 확인하세요.\n")
        return
    
    # 3. 보고서 서비스 테스트
    results.append(("보고서 서비스", test_report_service_data_fetch()))
    
    # 결과 요약
    print("=" * 60)
    print("검증 결과 요약")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ 통과" if passed else "❌ 실패"
        print(f"{status}: {name}")
        if not passed:
            all_passed = False
    
    print()
    
    if all_passed:
        print("✅ 모든 검증을 통과했습니다!")
    else:
        print("❌ 일부 검증에 실패했습니다. 위의 오류 메시지를 확인하세요.")
    
    print()


if __name__ == "__main__":
    main()

