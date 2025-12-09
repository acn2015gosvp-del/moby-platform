"""
역할(Role) 및 권한(Permission) 정의

사용자 역할과 권한을 관리하는 모듈입니다.
"""

from enum import Enum
from typing import List, Set


class Role(str, Enum):
    """사용자 역할"""
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"


class Permission(str, Enum):
    """권한 정의"""
    # 알림 관련
    ALERT_READ = "alert:read"
    ALERT_WRITE = "alert:write"
    ALERT_DELETE = "alert:delete"
    
    # 센서 관련
    SENSOR_READ = "sensor:read"
    SENSOR_WRITE = "sensor:write"
    
    # Grafana 관련
    GRAFANA_READ = "grafana:read"
    GRAFANA_WRITE = "grafana:write"
    
    # 사용자 관리
    USER_READ = "user:read"
    USER_WRITE = "user:write"
    USER_DELETE = "user:delete"
    
    # 시스템 관리
    SYSTEM_ADMIN = "system:admin"


# 역할별 권한 매핑
ROLE_PERMISSIONS: dict[Role, Set[Permission]] = {
    Role.ADMIN: {
        Permission.ALERT_READ,
        Permission.ALERT_WRITE,
        Permission.ALERT_DELETE,
        Permission.SENSOR_READ,
        Permission.SENSOR_WRITE,
        Permission.GRAFANA_READ,
        Permission.GRAFANA_WRITE,
        Permission.USER_READ,
        Permission.USER_WRITE,
        Permission.USER_DELETE,
        Permission.SYSTEM_ADMIN,
    },
    Role.USER: {
        Permission.ALERT_READ,
        Permission.ALERT_WRITE,
        Permission.SENSOR_READ,
        Permission.SENSOR_WRITE,
        Permission.GRAFANA_READ,
    },
    Role.VIEWER: {
        Permission.ALERT_READ,
        Permission.SENSOR_READ,
        Permission.GRAFANA_READ,
    },
}


def get_permissions_for_role(role: Role) -> Set[Permission]:
    """
    역할에 대한 권한 목록을 반환합니다.
    
    Args:
        role: 사용자 역할
        
    Returns:
        권한 집합
    """
    return ROLE_PERMISSIONS.get(role, set())


def has_permission(role: Role, permission: Permission) -> bool:
    """
    역할이 특정 권한을 가지고 있는지 확인합니다.
    
    Args:
        role: 사용자 역할
        permission: 확인할 권한
        
    Returns:
        권한이 있으면 True, 없으면 False
    """
    return permission in get_permissions_for_role(role)


def require_permissions(*permissions: Permission) -> List[Permission]:
    """
    데코레이터나 의존성에서 사용할 권한 목록을 반환합니다.
    
    Args:
        *permissions: 필요한 권한들
        
    Returns:
        권한 목록
    """
    return list(permissions)

