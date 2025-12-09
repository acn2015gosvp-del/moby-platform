#!/usr/bin/env python3
"""
기본 사용자 생성 스크립트

개발/테스트를 위한 기본 사용자 계정을 생성합니다.
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.api.services.database import SessionLocal
from backend.api.models.user import User
from backend.api.models.role import Role
from backend.api.services.schemas.models.core.logger import setup_logging, get_logger
from backend.api.services.schemas.models.core.config import settings
from backend.api.services.auth_service import get_password_hash

# 로깅 설정
setup_logging(
    log_level=settings.LOG_LEVEL,
    log_file=None  # 콘솔만 출력
)

logger = get_logger(__name__)


def create_default_user():
    """기본 사용자 계정 생성"""
    db = SessionLocal()
    
    try:
        # 기본 사용자 정보
        default_email = "admin@moby.local"
        default_username = "admin"
        default_password = "admin123"  # 개발용 기본 비밀번호 (8자, 영문+숫자)
        
        # 이미 존재하는지 확인
        existing_user = db.query(User).filter(
            (User.email == default_email) | (User.username == default_username)
        ).first()
        
        if existing_user:
            logger.info(f"✅ 기본 사용자가 이미 존재합니다: {existing_user.email}")
            logger.info(f"   이메일: {existing_user.email}")
            logger.info(f"   사용자명: {existing_user.username}")
            logger.info(f"   역할: {existing_user.role}")
            return existing_user
        
        # 비밀번호 해싱 (passlib 사용 - auth_service와 동일한 방식)
        hashed_password = get_password_hash(default_password)
        
        # 사용자 생성
        new_user = User(
            email=default_email,
            username=default_username,
            hashed_password=hashed_password,
            is_active=True,
            role=Role.ADMIN.value  # 관리자 역할
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        logger.info("=" * 60)
        logger.info("✅ 기본 사용자 계정이 생성되었습니다!")
        logger.info("=" * 60)
        logger.info(f"이메일: {default_email}")
        logger.info(f"사용자명: {default_username}")
        logger.info(f"비밀번호: {default_password}")
        logger.info(f"역할: {new_user.role}")
        logger.info("=" * 60)
        logger.info("⚠️  개발 환경에서만 사용하세요!")
        logger.info("⚠️  프로덕션 배포 전에 반드시 비밀번호를 변경하세요!")
        logger.info("=" * 60)
        
        return new_user
        
    except Exception as e:
        logger.exception(f"기본 사용자 생성 중 오류 발생: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def create_test_user():
    """테스트용 일반 사용자 계정 생성"""
    db = SessionLocal()
    
    try:
        # 테스트 사용자 정보
        test_email = "test@moby.local"
        test_username = "testuser"
        test_password = "test1234"  # 8자, 영문+숫자
        
        # 이미 존재하는지 확인
        existing_user = db.query(User).filter(
            (User.email == test_email) | (User.username == test_username)
        ).first()
        
        if existing_user:
            logger.info(f"✅ 테스트 사용자가 이미 존재합니다: {existing_user.email}")
            return existing_user
        
        # 비밀번호 해싱 (passlib 사용 - auth_service와 동일한 방식)
        hashed_password = get_password_hash(test_password)
        
        # 사용자 생성
        new_user = User(
            email=test_email,
            username=test_username,
            hashed_password=hashed_password,
            is_active=True,
            role=Role.USER.value  # 일반 사용자 역할
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        logger.info("=" * 60)
        logger.info("✅ 테스트 사용자 계정이 생성되었습니다!")
        logger.info("=" * 60)
        logger.info(f"이메일: {test_email}")
        logger.info(f"사용자명: {test_username}")
        logger.info(f"비밀번호: {test_password}")
        logger.info(f"역할: {new_user.role}")
        logger.info("=" * 60)
        
        return new_user
        
    except Exception as e:
        logger.exception(f"테스트 사용자 생성 중 오류 발생: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description="기본 사용자 계정 생성 스크립트")
    parser.add_argument(
        "--test",
        action="store_true",
        help="테스트용 일반 사용자도 함께 생성"
    )
    
    args = parser.parse_args()
    
    try:
        # 기본 관리자 계정 생성
        create_default_user()
        
        # 테스트 사용자 생성 (옵션)
        if args.test:
            create_test_user()
            
        logger.info("\n✅ 모든 사용자 계정 생성이 완료되었습니다!")
        
    except Exception as e:
        logger.error(f"❌ 사용자 생성 실패: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

