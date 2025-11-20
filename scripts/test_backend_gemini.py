"""
백엔드 서버의 Gemini API 키 사용 확인 스크립트

백엔드 서버가 실제로 사용하는 API 키를 확인합니다.
"""

import requests
import json

# 백엔드 서버 URL
BASE_URL = "http://localhost:8000"

print("="*60)
print("백엔드 서버 Gemini API 키 확인")
print("="*60)

# 1. 서버 상태 확인
try:
    response = requests.get(f"{BASE_URL}/", timeout=5)
    print(f"✅ 서버 연결 성공: {response.json()}")
except Exception as e:
    print(f"❌ 서버 연결 실패: {e}")
    print("   백엔드 서버가 실행 중인지 확인하세요.")
    exit(1)

# 2. 보고서 생성 엔드포인트 테스트 (간단한 요청)
print("\n📋 보고서 생성 엔드포인트 테스트...")
print("   (실제 보고서 생성은 하지 않고, API 키 검증만 확인)")

# 최소한의 테스트 데이터
test_data = {
    "period_start": "2025-01-01 00:00:00",
    "period_end": "2025-01-02 00:00:00",
    "equipment": "test",
    "sensor_ids": None,
    "include_mlp_anomalies": True,
    "include_if_anomalies": True,
}

try:
    # 인증 없이 테스트 (실제로는 인증이 필요할 수 있음)
    response = requests.post(
        f"{BASE_URL}/api/reports/generate",
        json=test_data,
        timeout=10
    )
    
    print(f"   상태 코드: {response.status_code}")
    
    if response.status_code == 401:
        print("   ⚠️  인증이 필요합니다. (정상)")
        print("   ✅ 서버는 실행 중이며, API 키 검증은 보고서 생성 시점에 이루어집니다.")
    elif response.status_code == 400:
        error_detail = response.json().get('detail', '')
        if 'API key not valid' in str(error_detail) or 'API_KEY_INVALID' in str(error_detail):
            print(f"   ❌ API 키 오류 발견: {error_detail[:200]}")
        else:
            print(f"   ⚠️  요청 오류 (예상됨): {error_detail[:200]}")
    elif response.status_code == 200:
        print("   ✅ 보고서 생성 성공!")
    else:
        print(f"   응답: {response.text[:200]}")
        
except requests.exceptions.Timeout:
    print("   ⚠️  요청 시간 초과 (보고서 생성이 오래 걸릴 수 있음)")
except Exception as e:
    print(f"   ⚠️  오류: {e}")

print("\n" + "="*60)
print("💡 팁:")
print("   - 실제 보고서 생성을 테스트하려면 프론트엔드에서 시도하세요.")
print("   - API 키가 유효하지 않으면 'API key not valid' 오류가 발생합니다.")
print("   - 서버를 재시작하면 최신 .env 파일이 로드됩니다.")
print("="*60)

