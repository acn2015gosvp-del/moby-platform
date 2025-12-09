"""
이메일 설정 업데이트 스크립트

khu5405@gmail.com에서 w5597129@gmail.com으로 이메일을 발송하도록 설정을 변경합니다.
"""

import sys
import os
import re
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

def update_env_file():
    """.env 파일의 이메일 설정을 업데이트합니다."""
    env_file = Path(project_root) / '.env'
    
    if not env_file.exists():
        print(f"❌ .env 파일을 찾을 수 없습니다: {env_file}")
        return False
    
    print("=" * 60)
    print("이메일 설정 업데이트")
    print("=" * 60)
    print()
    print("변경 사항:")
    print("  발신자: w5597129@gmail.com → khu5405@gmail.com")
    print("  수신자: khu5405@gmail.com → w5597129@gmail.com")
    print()
    
    # .env 파일 읽기
    try:
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ .env 파일 읽기 실패: {e}")
        return False
    
    # 변경할 설정
    updates = {
        'SMTP_USER': 'khu5405@gmail.com',
        'SMTP_FROM_EMAIL': 'khu5405@gmail.com',
        'SMTP_TO_EMAILS': 'w5597129@gmail.com'
    }
    
    # 각 설정 업데이트
    updated = False
    for key, new_value in updates.items():
        # 기존 설정 찾기 (주석 제외)
        pattern = rf'^{key}\s*=\s*.*$'
        replacement = f'{key}={new_value}'
        
        if re.search(pattern, content, re.MULTILINE):
            # 기존 설정이 있으면 교체
            content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
            print(f"✅ {key} 업데이트: {new_value}")
            updated = True
        else:
            # 기존 설정이 없으면 추가
            # 이메일 설정 섹션 찾기
            email_section_pattern = r'(# 이메일 알림 설정.*?)(?=\n# |$)'
            match = re.search(email_section_pattern, content, re.DOTALL)
            
            if match:
                # 이메일 설정 섹션 뒤에 추가
                section_end = match.end()
                content = content[:section_end] + f'\n{replacement}\n' + content[section_end:]
                print(f"✅ {key} 추가: {new_value}")
                updated = True
            else:
                # 파일 끝에 추가
                content += f'\n{replacement}\n'
                print(f"✅ {key} 추가 (파일 끝): {new_value}")
                updated = True
    
    if not updated:
        print("⚠️ 변경할 설정이 없습니다.")
        return False
    
    # 백업 생성
    backup_file = env_file.with_suffix('.env.backup')
    try:
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"\n📦 백업 생성: {backup_file.name}")
    except Exception as e:
        print(f"⚠️ 백업 생성 실패: {e}")
    
    # .env 파일 저장
    try:
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ .env 파일 업데이트 완료")
        print()
        print("⚠️ 중요: SMTP_PASSWORD를 khu5405@gmail.com의 앱 비밀번호로 변경해야 합니다!")
        print("   Gmail 앱 비밀번호 생성: https://myaccount.google.com/apppasswords")
        return True
    except Exception as e:
        print(f"❌ .env 파일 저장 실패: {e}")
        return False

if __name__ == "__main__":
    try:
        success = update_env_file()
        if success:
            print()
            print("=" * 60)
            print("다음 단계")
            print("=" * 60)
            print("1. .env 파일에서 SMTP_PASSWORD를 khu5405@gmail.com의 앱 비밀번호로 변경")
            print("2. 백엔드 서버 재시작")
            print("3. python scripts/test_email_send.py 로 테스트")
    except KeyboardInterrupt:
        print("\n\n사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()



