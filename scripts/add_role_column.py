#!/usr/bin/env python3
"""
users 테이블에 role 컬럼 추가 스크립트

기존 데이터베이스에 role 컬럼이 없는 경우 사용합니다.
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from backend.api.services.database import engine
from backend.api.services.schemas.models.core.logger import setup_logging, get_logger
from backend.api.services.schemas.models.core.config import settings

# 로깅 설정
setup_logging(
    log_level=settings.LOG_LEVEL,
    log_file=None
)

logger = get_logger(__name__)


def check_column_exists(column_name: str) -> bool:
    """컬럼이 존재하는지 확인"""
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(users)"))
        columns = [row[1] for row in result]
        return column_name in columns


def add_role_column():
    """users 테이블에 role 컬럼 추가"""
    try:
        # role 컬럼이 이미 있는지 확인
        if check_column_exists("role"):
            logger.info("✅ 'role' 컬럼이 이미 존재합니다.")
            return True
        
        logger.info("'role' 컬럼을 추가하는 중...")
        
        # SQLite는 ALTER TABLE ADD COLUMN 지원
        with engine.connect() as conn:
            conn.execute(text(
                "ALTER TABLE users ADD COLUMN role VARCHAR(50) DEFAULT 'user' NOT NULL"
            ))
            conn.commit()
        
        logger.info("✅ 'role' 컬럼이 성공적으로 추가되었습니다.")
        return True
        
    except Exception as e:
        logger.exception(f"❌ 'role' 컬럼 추가 중 오류 발생: {e}")
        return False


def main():
    """메인 함수"""
    logger.info("=" * 60)
    logger.info("users 테이블에 role 컬럼 추가")
    logger.info("=" * 60)
    
    if add_role_column():
        logger.info("\n✅ 작업이 완료되었습니다!")
    else:
        logger.error("\n❌ 작업이 실패했습니다.")
        sys.exit(1)


if __name__ == "__main__":
    main()

