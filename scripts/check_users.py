"""
데이터베이스에 저장된 사용자 정보 조회 스크립트
"""
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.api.services.database import SessionLocal
from backend.api.models.user import User

def check_users():
    """데이터베이스에 저장된 모든 사용자 정보를 출력합니다."""
    db = SessionLocal()
    try:
        users = db.query(User).all()
        
        if not users:
            print("❌ 데이터베이스에 사용자가 없습니다.")
            print("\n💡 사용자를 생성하려면:")
            print("   1. 프론트엔드에서 회원가입 페이지(/register)로 이동")
            print("   2. 또는 API를 통해 사용자 생성")
            return
        
        print(f"✅ 총 {len(users)}명의 사용자가 등록되어 있습니다.\n")
        print("=" * 80)
        
        for user in users:
            print(f"\n📧 이메일: {user.email}")
            print(f"👤 사용자명: {user.username}")
            print(f"🔑 역할: {user.role}")
            print(f"✅ 활성화: {'예' if user.is_active else '아니오'}")
            print(f"📅 생성일: {user.created_at}")
            print("-" * 80)
        
        print("\n⚠️  주의: 비밀번호는 해시화되어 저장되므로 원본을 확인할 수 없습니다.")
        print("   비밀번호를 잊으셨다면 비밀번호 재설정 기능을 사용하거나 새 계정을 만드세요.")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_users()
