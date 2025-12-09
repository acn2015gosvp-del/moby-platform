"""
InfluxDB 스키마 및 데이터 디버깅 스크립트

InfluxDB의 Measurement, Field, 데이터 타입 및 샘플 값을 확인합니다.
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Set
from collections import defaultdict

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from influxdb_client import InfluxDBClient
    from influxdb_client.client.query_api import QueryApi
except ImportError:
    print("❌ influxdb-client가 설치되지 않았습니다.")
    print("   설치 방법: pip install influxdb-client")
    sys.exit(1)


def load_env_vars() -> Dict[str, str]:
    """환경 변수에서 InfluxDB 연결 정보 로드"""
    env_file = project_root / ".env"
    
    env_vars = {}
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip().strip('"').strip("'")
    
    # 환경 변수에서 직접 가져오기 (우선순위 높음)
    config = {
        'url': os.getenv('INFLUXDB_URL') or env_vars.get('INFLUXDB_URL', ''),
        'token': os.getenv('INFLUXDB_TOKEN') or env_vars.get('INFLUXDB_TOKEN', ''),
        'org': os.getenv('INFLUXDB_ORG') or env_vars.get('INFLUXDB_ORG', ''),
        'bucket': os.getenv('INFLUXDB_BUCKET') or env_vars.get('INFLUXDB_BUCKET', ''),
    }
    
    # 필수 값 확인
    missing = [k for k, v in config.items() if not v]
    if missing:
        print(f"❌ 필수 환경 변수가 없습니다: {', '.join(missing)}")
        print("\n필요한 환경 변수:")
        print("  - INFLUXDB_URL")
        print("  - INFLUXDB_TOKEN")
        print("  - INFLUXDB_ORG")
        print("  - INFLUXDB_BUCKET")
        sys.exit(1)
    
    return config


def get_python_type(value: Any) -> str:
    """값의 Python 타입을 문자열로 반환"""
    if value is None:
        return "None"
    
    py_type = type(value).__name__
    
    # 숫자 타입 구분
    if py_type == 'float':
        if value != value:  # NaN 체크
            return "float (NaN)"
        if abs(value) == float('inf'):
            return "float (Infinity)"
        return "float"
    elif py_type == 'int':
        return "int"
    elif py_type == 'str':
        return "str"
    elif py_type == 'bool':
        return "bool"
    else:
        return f"{py_type}"


def analyze_influxdb_schema(client: InfluxDBClient, query_api: QueryApi, bucket: str, org: str):
    """InfluxDB 스키마 및 데이터 분석"""
    
    print("=" * 80)
    print("InfluxDB 스키마 및 데이터 분석")
    print("=" * 80)
    print()
    
    # 최근 7일의 시간 범위 계산 (데이터가 없을 수 있으므로 넓은 범위)
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(days=7)
    
    start_rfc3339 = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_rfc3339 = end_time.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    print(f"📅 조회 기간: {start_rfc3339} ~ {end_rfc3339}")
    print(f"   (최근 7일)")
    print()
    
    # Raw 데이터 조회 (집계 없이)
    # 최대 10000개 레코드로 제한하여 성능 확보
    query = f'''
    from(bucket: "{bucket}")
      |> range(start: {start_rfc3339}, stop: {end_rfc3339})
      |> limit(n: 10000)
      |> sort(columns: ["_time"], desc: true)
    '''
    
    print("🔍 Raw 데이터 조회 중... (집계 없이)")
    print()
    
    try:
        result = query_api.query(query=query, org=org)
        
        # Measurement별로 데이터 구조화
        measurements: Dict[str, Dict[str, List[Any]]] = defaultdict(lambda: defaultdict(list))
        measurement_fields: Dict[str, Set[str]] = defaultdict(set)
        total_records = 0
        
        for table in result:
            for record in table.records:
                total_records += 1
                measurement = record.get_measurement()
                field = record.get_field()
                value = record.get_value()
                
                # Measurement와 Field 저장
                measurement_fields[measurement].add(field)
                
                # 값 샘플 저장 (최대 5개)
                if len(measurements[measurement][field]) < 5:
                    measurements[measurement][field].append({
                        'value': value,
                        'time': record.get_time(),
                        'type': get_python_type(value)
                    })
        
        print(f"✅ 총 {total_records}개의 레코드를 조회했습니다.")
        print()
        
        if total_records == 0:
            print("⚠️ 조회된 데이터가 없습니다.")
            print("   가능한 원인:")
            print("   1. 해당 기간에 데이터가 없음")
            print("   2. 시간 범위를 늘려서 다시 시도해보세요")
            return
        
        # Measurement별로 출력
        print("=" * 80)
        print("📊 Measurement (테이블) 목록")
        print("=" * 80)
        print()
        
        for measurement in sorted(measurement_fields.keys()):
            print(f"📋 Measurement: {measurement}")
            print(f"   Field 개수: {len(measurement_fields[measurement])}")
            print()
            
            # Field별 상세 정보
            for field in sorted(measurement_fields[measurement]):
                samples = measurements[measurement][field]
                if samples:
                    # 데이터 타입 확인 (모든 샘플의 타입이 같은지 확인)
                    types = set(s['type'] for s in samples)
                    primary_type = samples[0]['type']
                    
                    print(f"   🔹 Field: {field}")
                    print(f"      데이터 타입: {primary_type}")
                    
                    if len(types) > 1:
                        print(f"      ⚠️ 주의: 여러 타입이 섞여있습니다: {types}")
                    
                    print(f"      샘플 값 (최대 5개):")
                    for i, sample in enumerate(samples, 1):
                        time_str = sample['time'].isoformat() if hasattr(sample['time'], 'isoformat') else str(sample['time'])
                        value_str = str(sample['value'])
                        
                        # 값이 너무 길면 잘라서 표시
                        if len(value_str) > 50:
                            value_str = value_str[:47] + "..."
                        
                        print(f"         {i}. [{time_str}] {value_str} (타입: {sample['type']})")
                    
                    # 숫자 타입인 경우 통계 정보 추가
                    if primary_type in ['float', 'int']:
                        try:
                            numeric_values = [float(s['value']) for s in samples if s['value'] is not None]
                            if numeric_values:
                                print(f"      숫자 통계 (샘플 기준):")
                                print(f"         최소: {min(numeric_values)}")
                                print(f"         최대: {max(numeric_values)}")
                                print(f"         평균: {sum(numeric_values) / len(numeric_values):.2f}")
                        except (ValueError, TypeError):
                            pass
                    
                    print()
            
            print("-" * 80)
            print()
        
        # 보고서에서 사용하는 필드명과 비교
        print("=" * 80)
        print("🔍 보고서 필드명 매칭 확인")
        print("=" * 80)
        print()
        
        report_fields = {
            'fields_temperature_c': '온도',
            'fields_humidity_percent': '습도',
            'fields_vibration_raw': '진동',
            'fields_sound_raw': '소음',
        }
        
        all_fields = set()
        for fields in measurement_fields.values():
            all_fields.update(fields)
        
        for report_field, description in report_fields.items():
            if report_field in all_fields:
                # 어떤 measurement에 있는지 찾기
                found_in = [m for m, fields in measurement_fields.items() if report_field in fields]
                print(f"✅ {report_field} ({description}): 발견됨")
                print(f"   Measurement: {', '.join(found_in)}")
            else:
                print(f"❌ {report_field} ({description}): 발견되지 않음")
                
                # 유사한 필드명 찾기
                similar = [f for f in all_fields if report_field.split('_')[-1] in f or f.split('_')[-1] in report_field.split('_')[-1]]
                if similar:
                    print(f"   💡 유사한 필드명: {', '.join(similar[:5])}")
            print()
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


def main():
    """메인 함수"""
    print("=" * 80)
    print("InfluxDB 스키마 디버깅 스크립트")
    print("=" * 80)
    print()
    
    # 환경 변수 로드
    print("📝 환경 변수 로드 중...")
    config = load_env_vars()
    
    print(f"✅ 연결 정보:")
    print(f"   URL: {config['url']}")
    print(f"   Org: {config['org']}")
    print(f"   Bucket: {config['bucket']}")
    print(f"   Token: {'*' * 20} (보안상 숨김)")
    print()
    
    # InfluxDB 클라이언트 생성
    try:
        client = InfluxDBClient(
            url=config['url'],
            token=config['token'],
            org=config['org']
        )
        query_api = client.query_api()
        
        print("✅ InfluxDB 연결 성공")
        print()
        
        # 스키마 분석
        analyze_influxdb_schema(client, query_api, config['bucket'], config['org'])
        
    except Exception as e:
        print(f"❌ InfluxDB 연결 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        if 'client' in locals():
            client.close()


if __name__ == "__main__":
    main()

