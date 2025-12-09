"""
Grafana iframe 임베딩 설정 확인 스크립트

Grafana 서버의 allow_embedding 설정을 확인하고 안내합니다.
"""

import sys
import os
import requests
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def check_grafana_embedding():
    """Grafana iframe 임베딩 설정 확인"""
    print("=" * 60)
    print("Grafana iframe 임베딩 설정 확인")
    print("=" * 60)
    print()
    
    grafana_url = "http://192.168.80.183:8080"
    
    # 1. Grafana 서버 연결 확인
    print("1. Grafana 서버 연결 확인")
    print("-" * 60)
    try:
        response = requests.get(f"{grafana_url}/api/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ Grafana 서버 연결 성공: {grafana_url}")
            health_data = response.json()
            print(f"   버전: {health_data.get('version', 'N/A')}")
        else:
            print(f"❌ Grafana 서버 응답 오류: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Grafana 서버 연결 실패: {e}")
        print(f"   URL: {grafana_url}")
        print()
        print("💡 Grafana 서버가 실행 중인지 확인하세요.")
        return False
    
    print()
    
    # 2. X-Frame-Options 헤더 확인
    print("2. X-Frame-Options 헤더 확인")
    print("-" * 60)
    try:
        response = requests.get(
            f"{grafana_url}/d/adrvc2v/repair?orgId=1&kiosk=&theme=light",
            timeout=5,
            allow_redirects=True
        )
        
        x_frame_options = response.headers.get('X-Frame-Options', '없음')
        content_security_policy = response.headers.get('Content-Security-Policy', '없음')
        
        print(f"   X-Frame-Options: {x_frame_options}")
        print(f"   Content-Security-Policy: {content_security_policy[:100] if content_security_policy != '없음' else '없음'}")
        
        if x_frame_options and x_frame_options.upper() in ['DENY', 'SAMEORIGIN']:
            print("   ⚠️ X-Frame-Options가 설정되어 있어 iframe 임베딩이 차단될 수 있습니다.")
        elif x_frame_options == '없음':
            print("   ✅ X-Frame-Options 헤더가 없습니다 (임베딩 가능)")
        else:
            print(f"   ⚠️ X-Frame-Options: {x_frame_options}")
    except requests.exceptions.RequestException as e:
        print(f"   ⚠️ 헤더 확인 실패: {e}")
    
    print()
    
    # 3. 직접 접속 테스트
    print("3. 직접 접속 테스트")
    print("-" * 60)
    test_url = f"{grafana_url}/d/adrvc2v/repair?orgId=1&kiosk=&theme=light"
    try:
        response = requests.get(test_url, timeout=5)
        if response.status_code == 200:
            print(f"✅ 직접 접속 성공")
            print(f"   URL: {test_url}")
            print(f"   응답 크기: {len(response.content)} bytes")
        else:
            print(f"❌ 직접 접속 실패: HTTP {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ 직접 접속 실패: {e}")
    
    print()
    
    # 4. 해결 방법 안내
    print("=" * 60)
    print("해결 방법")
    print("=" * 60)
    print()
    print("Grafana 서버에서 iframe 임베딩을 허용하려면:")
    print()
    print("1. Grafana 설정 파일 수정:")
    print("   - Windows: C:\\Program Files\\GrafanaLabs\\grafana\\conf\\grafana.ini")
    print("   - Linux: /etc/grafana/grafana.ini")
    print("   - Docker: 환경 변수로 설정 가능")
    print()
    print("2. 다음 설정 추가:")
    print("   [security]")
    print("   allow_embedding = true")
    print()
    print("3. Grafana 서버 재시작:")
    print("   - Windows: 서비스 재시작")
    print("   - Linux: sudo systemctl restart grafana-server")
    print("   - Docker: docker restart grafana")
    print()
    print("4. 재시작 후 확인:")
    print("   - 브라우저 캐시 삭제 (Ctrl+Shift+Delete)")
    print("   - 페이지 새로고침 (F5)")
    print()
    print("5. 직접 URL 접속 테스트:")
    print(f"   {test_url}")
    print()

if __name__ == "__main__":
    try:
        check_grafana_embedding()
    except KeyboardInterrupt:
        print("\n\n사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

