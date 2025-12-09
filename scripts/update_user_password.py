#!/usr/bin/env python3
"""
사용자 비밀번호 업데이트 스크립트

기존 사용자의 비밀번호를 passlib 형식으로 다시 해싱합니다.
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.api.services.database import SessionLocal
from backend.api.models.user import User
from backend.api.services.auth_service import get_password_hash, verify_password
from backend.api.services.schemas.models.core.logger import setup_logging, get_logger
from backend.api.services.schemas.models.core.config import settings

# 로깅 설정
setup_logging(
    log_level=settings.LOG_LEVEL,
    log_file=None
)
logger = get_logger(__name__)


def update_user_password(email: str, new_password: str):
    """사용자 비밀번호 업데이트"""
    db = SessionLocal()
    
    try:
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            logger.error(f"❌ 사용자를 찾을 수 없습니다: {email}")
            return False
        
        # 새 비밀번호 해싱
        new_hashed = get_password_hash(new_password)
        
        # 비밀번호 업데이트
        user.hashed_password = new_hashed
        db.commit()
        
        # 검증 테스트
        if verify_password(new_password, new_hashed):
            logger.info("=" * 60)
            logger.info(f"✅ 비밀번호 업데이트 성공: {email}")
            logger.info(f"   새 비밀번호: {new_password}")
            logger.info("=" * 60)
            return True
        else:
            logger.error("❌ 비밀번호 검증 실패")
            return False
        
    except Exception as e:
        logger.exception(f"비밀번호 업데이트 중 오류 발생: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def main():
    """메인 함수"""
    # admin 사용자 비밀번호 업데이트
    logger.info("관리자 계정 비밀번호 업데이트 중...")
    update_user_password("admin@moby.local", "admin123")
    
    # test 사용자 생성 또는 업데이트
    db = SessionLocal()
    try:
        test_user = db.query(User).filter(User.email == "test@moby.local").first()
        if test_user:
            logger.info("테스트 사용자 비밀번호 업데이트 중...")
            update_user_password("test@moby.local", "test1234")
        else:
            logger.info("테스트 사용자가 없습니다. create_default_user.py를 실행하세요.")
    finally:
        db.close()


if __name__ == "__main__":
    main()

