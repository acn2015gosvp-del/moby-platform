"""
이메일 발송 테스트 스크립트

실제로 이메일이 발송되는지 테스트합니다.
"""

import sys
import os
import asyncio

# 프로젝트 루트를 Python 경로에 추가
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

async def test_email_send():
    """이메일 발송 테스트"""
    try:
        from backend.api.services.email_service import alert_email_manager
        from backend.api.services.schemas.models.core.config import settings
        from datetime import datetime
        
        print("=" * 60)
        print("이메일 발송 테스트")
        print("=" * 60)
        print()
        
        # 이메일 서비스가 초기화되었는지 확인하고, 없으면 초기화
        if alert_email_manager.service is None:
            print("⚠️ 이메일 서비스가 초기화되지 않았습니다. 초기화 중...")
            
            # SMTP 설정 확인
            smtp_configs = [
                settings.SMTP_HOST,
                settings.SMTP_USER,
                settings.SMTP_PASSWORD,
                settings.SMTP_FROM_EMAIL,
                settings.SMTP_TO_EMAILS
            ]
            
            if not all(config and str(config).strip() for config in smtp_configs):
                print("❌ SMTP 설정이 완전하지 않습니다.")
                print("   .env 파일에 다음 설정을 확인하세요:")
                print("   - SMTP_HOST")
                print("   - SMTP_USER")
                print("   - SMTP_PASSWORD")
                print("   - SMTP_FROM_EMAIL")
                print("   - SMTP_TO_EMAILS")
                return
            
            # 수신자 이메일 파싱
            to_emails = [email.strip() for email in str(settings.SMTP_TO_EMAILS).split(',') if email.strip()]
            
            if not to_emails:
                print("❌ SMTP_TO_EMAILS에 유효한 이메일 주소가 없습니다.")
                return
            
            # 이메일 서비스 초기화
            alert_email_manager.initialize(
                smtp_host=str(settings.SMTP_HOST).strip(),
                smtp_port=settings.SMTP_PORT,
                smtp_user=str(settings.SMTP_USER).strip(),
                smtp_password=str(settings.SMTP_PASSWORD).strip(),
                from_email=str(settings.SMTP_FROM_EMAIL).strip(),
                to_emails=to_emails,
                max_retries=3,
                throttle_window=60  # 1분
            )
            print("✅ 이메일 서비스 초기화 완료")
        else:
            print("✅ 이메일 서비스 초기화 확인됨")
        print()
        
        # 테스트 알림 생성
        print("📧 테스트 이메일 발송 시도...")
        print(f"   발신자: {settings.SMTP_FROM_EMAIL}")
        print(f"   수신자: {settings.SMTP_TO_EMAILS}")
        print()
        
        success = await alert_email_manager.handle_alert(
            alert_type="WARNING",
            message="이것은 테스트 이메일입니다. 시스템이 정상 작동 중입니다.",
            source="테스트-시스템",
            severity=3
        )
        
        if success:
            print("✅ 이메일 발송 성공!")
            print(f"   {settings.SMTP_TO_EMAILS}로 이메일이 발송되었습니다.")
            print("   받은편지함(스팸 포함)을 확인해주세요.")
        else:
            print("❌ 이메일 발송 실패")
            print("   로그를 확인하여 오류 원인을 파악하세요.")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(test_email_send())
    except KeyboardInterrupt:
        print("\n\n사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

