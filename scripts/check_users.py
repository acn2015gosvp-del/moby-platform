#!/usr/bin/env python3
"""
데이터베이스 사용자 확인 스크립트
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.api.services.database import SessionLocal
from backend.api.models.user import User

def check_users():
    """데이터베이스의 모든 사용자 확인"""
    db = SessionLocal()
    
    try:
        users = db.query(User).all()
        
        if not users:
            print("❌ 데이터베이스에 사용자가 없습니다.")
            print("   다음 명령어로 기본 사용자를 생성하세요:")
            print("   python scripts/create_default_user.py --test")
            return
        
        print("=" * 60)
        print(f"✅ 데이터베이스에 {len(users)}명의 사용자가 있습니다:")
        print("=" * 60)
        
        for user in users:
            print(f"\n이메일: {user.email}")
            print(f"사용자명: {user.username}")
            print(f"역할: {user.role}")
            print(f"활성화: {user.is_active}")
            print(f"비밀번호 해시: {user.hashed_password[:50]}...")
        
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_users()

