"""
이메일 설정 확인 스크립트

현재 설정된 이메일 주소를 확인합니다.
"""

import sys
import os

# 프로젝트 루트를 Python 경로에 추가
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

try:
    from backend.api.services.schemas.models.core.config import settings
    
    print("=" * 60)
    print("이메일 설정 확인")
    print("=" * 60)
    print()
    
    print("=" * 60)
    print("SMTP 설정")
    print("=" * 60)
    print(f"📧 SMTP_HOST: {settings.SMTP_HOST or '❌ 설정 안 됨'}")
    print(f"📧 SMTP_PORT: {settings.SMTP_PORT}")
    print(f"📧 SMTP_USER: {settings.SMTP_USER or '❌ 설정 안 됨'}")
    print(f"📧 SMTP_PASSWORD: {'***' if settings.SMTP_PASSWORD else '❌ 설정 안 됨'}")
    print(f"📧 SMTP_FROM_EMAIL: {settings.SMTP_FROM_EMAIL or '❌ 설정 안 됨'}")
    print(f"📧 SMTP_TO_EMAILS: {settings.SMTP_TO_EMAILS or '❌ 설정 안 됨'}")
    print()
    
    # 이메일 주소 확인
    print("=" * 60)
    print("이메일 주소 확인")
    print("=" * 60)
    
    target_email = "khu5405@gmail.com"
    
    if settings.SMTP_USER:
        if settings.SMTP_USER.strip() == target_email:
            print(f"✅ SMTP_USER가 '{target_email}'로 설정되어 있습니다.")
        else:
            print(f"⚠️ SMTP_USER가 '{target_email}'가 아닙니다.")
            print(f"   현재 값: {settings.SMTP_USER}")
    else:
        print(f"❌ SMTP_USER가 설정되지 않았습니다.")
    
    if settings.SMTP_FROM_EMAIL:
        if settings.SMTP_FROM_EMAIL.strip() == target_email:
            print(f"✅ SMTP_FROM_EMAIL이 '{target_email}'로 설정되어 있습니다.")
        else:
            print(f"⚠️ SMTP_FROM_EMAIL이 '{target_email}'가 아닙니다.")
            print(f"   현재 값: {settings.SMTP_FROM_EMAIL}")
    else:
        print(f"❌ SMTP_FROM_EMAIL이 설정되지 않았습니다.")
    
    if settings.SMTP_TO_EMAILS:
        to_emails = [email.strip() for email in str(settings.SMTP_TO_EMAILS).split(',') if email.strip()]
        if target_email in to_emails:
            print(f"✅ SMTP_TO_EMAILS에 '{target_email}'가 포함되어 있습니다.")
        else:
            print(f"⚠️ SMTP_TO_EMAILS에 '{target_email}'가 포함되어 있지 않습니다.")
            print(f"   현재 값: {settings.SMTP_TO_EMAILS}")
    else:
        print(f"❌ SMTP_TO_EMAILS가 설정되지 않았습니다.")
    
    print()
    print("=" * 60)
    print("요약")
    print("=" * 60)
    
    all_set = all([
        settings.SMTP_HOST,
        settings.SMTP_USER,
        settings.SMTP_PASSWORD,
        settings.SMTP_FROM_EMAIL,
        settings.SMTP_TO_EMAILS
    ])
    
    if all_set:
        print("✅ 모든 SMTP 설정이 완료되었습니다.")
    else:
        print("❌ 일부 SMTP 설정이 누락되었습니다.")
        print("   .env 파일에 다음 설정을 추가하세요:")
        print("   - SMTP_HOST")
        print("   - SMTP_USER")
        print("   - SMTP_PASSWORD")
        print("   - SMTP_FROM_EMAIL")
        print("   - SMTP_TO_EMAILS")
    
except Exception as e:
    print(f"❌ 오류 발생: {e}")
    import traceback
    traceback.print_exc()




