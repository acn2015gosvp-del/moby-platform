"""
권한 체크 유틸리티

FastAPI 의존성으로 사용할 수 있는 권한 체크 함수들을 제공합니다.
"""

from typing import List
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.api.services.database import get_db
from backend.api.models.user import User
from backend.api.models.role import Role, Permission, has_permission, get_permissions_for_role
from backend.api.routes_auth import get_current_user
from backend.api.core.responses import SuccessResponse
from backend.api.services.schemas.models.core.logger import get_logger

logger = get_logger(__name__)


def require_permissions(*required_permissions: Permission):
    """
    권한 체크 의존성 함수
    
    사용 예:
        @router.get("/admin/users")
        async def get_users(
            current_user: User = Depends(require_permissions(Permission.USER_READ))
        ):
            ...
    
    Args:
        *required_permissions: 필요한 권한들
        
    Returns:
        의존성 함수
    """
    def permission_checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        """
        권한을 체크하고 사용자를 반환합니다.
        
        Args:
            current_user: 현재 로그인한 사용자
            db: 데이터베이스 세션
            
        Returns:
            권한이 있는 사용자
            
        Raises:
            HTTPException: 권한이 없는 경우 403 Forbidden
        """
        # 사용자 역할 확인
        try:
            user_role = Role(current_user.role)
        except ValueError:
            logger.warning(f"Invalid role for user {current_user.id}: {current_user.role}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid user role"
            )
        
        # 필요한 권한 확인
        for permission in required_permissions:
            if not has_permission(user_role, permission):
                logger.warning(
                    f"User {current_user.id} ({user_role.value}) "
                    f"attempted to access resource requiring {permission.value}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required: {permission.value}"
                )
        
        return current_user
    
    return permission_checker


def require_role(*allowed_roles: Role):
    """
    역할 체크 의존성 함수
    
    사용 예:
        @router.get("/admin/dashboard")
        async def admin_dashboard(
            current_user: User = Depends(require_role(Role.ADMIN))
        ):
            ...
    
    Args:
        *allowed_roles: 허용된 역할들
        
    Returns:
        의존성 함수
    """
    def role_checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        """
        역할을 체크하고 사용자를 반환합니다.
        
        Args:
            current_user: 현재 로그인한 사용자
            db: 데이터베이스 세션
            
        Returns:
            허용된 역할의 사용자
            
        Raises:
            HTTPException: 허용되지 않은 역할인 경우 403 Forbidden
        """
        try:
            user_role = Role(current_user.role)
        except ValueError:
            logger.warning(f"Invalid role for user {current_user.id}: {current_user.role}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid user role"
            )
        
        if user_role not in allowed_roles:
            logger.warning(
                f"User {current_user.id} ({user_role.value}) "
                f"attempted to access resource requiring roles: {[r.value for r in allowed_roles]}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient role. Required: {[r.value for r in allowed_roles]}"
            )
        
        return current_user
    
    return role_checker


def get_user_permissions(user: User) -> List[Permission]:
    """
    사용자의 모든 권한을 반환합니다.
    
    Args:
        user: 사용자 객체
        
    Returns:
        권한 목록
    """
    try:
        user_role = Role(user.role)
        return list(get_permissions_for_role(user_role))
    except ValueError:
        logger.warning(f"Invalid role for user {user.id}: {user.role}")
        return []

