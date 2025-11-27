"""
알림 상태 관리 서비스

Critical(임계치) 상태를 전역으로 관리하여
우선순위 로직을 구현합니다.

핵심 규칙: Critical 상태일 때 Warning(AI 예지) 알림을 무시합니다.
"""

import threading
import logging
from typing import Optional
from datetime import datetime

from backend.api.services.schemas.models.core.logger import get_logger

logger = get_logger(__name__)


class AlertStateManager:
    """알림 상태 관리 클래스 (싱글톤)"""
    
    _instance: Optional['AlertStateManager'] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """싱글톤 패턴 구현"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """상태 관리자 초기화"""
        if self._initialized:
            return
        
        self._is_critical_active = False
        self._state_lock = threading.RLock()  # 재진입 가능한 락
        self._critical_device_id: Optional[str] = None
        self._critical_start_time: Optional[datetime] = None
        
        self._initialized = True
        logger.info("✅ AlertStateManager 초기화 완료")
    
    @property
    def is_critical_active(self) -> bool:
        """
        Critical 상태 여부를 반환합니다.
        
        Returns:
            Critical 상태 활성화 여부
        """
        with self._state_lock:
            return self._is_critical_active
    
    @property
    def critical_device_id(self) -> Optional[str]:
        """
        현재 Critical 상태인 디바이스 ID를 반환합니다.
        
        Returns:
            디바이스 ID 또는 None
        """
        with self._state_lock:
            return self._critical_device_id
    
    def set_critical_active(self, device_id: Optional[str] = None) -> None:
        """
        Critical 상태를 활성화합니다.
        
        Args:
            device_id: Critical 상태를 발생시킨 디바이스 ID (선택)
        """
        with self._state_lock:
            if not self._is_critical_active:
                self._is_critical_active = True
                self._critical_device_id = device_id
                self._critical_start_time = datetime.now()
                logger.warning(
                    f"🚨 Critical 상태 활성화: device_id={device_id}, "
                    f"time={self._critical_start_time.isoformat()}"
                )
            else:
                logger.debug(f"Critical 상태 이미 활성화됨: device_id={device_id}")
    
    def set_critical_inactive(self) -> None:
        """Critical 상태를 비활성화합니다."""
        with self._state_lock:
            if self._is_critical_active:
                duration = None
                if self._critical_start_time:
                    duration = (datetime.now() - self._critical_start_time).total_seconds()
                
                self._is_critical_active = False
                device_id = self._critical_device_id
                self._critical_device_id = None
                self._critical_start_time = None
                
                logger.info(
                    f"✅ Critical 상태 해제: device_id={device_id}, "
                    f"duration={duration:.2f}s" if duration else f"duration=unknown"
                )
            else:
                logger.debug("Critical 상태 이미 비활성화됨")
    
    def should_ignore_warning(self) -> bool:
        """
        Warning 알림을 무시해야 하는지 확인합니다.
        
        Critical 상태일 때 Warning 알림은 무시됩니다.
        
        Returns:
            무시해야 하면 True, 아니면 False
        """
        with self._state_lock:
            return self._is_critical_active


# 전역 상태 관리자 인스턴스
_alert_state_manager: Optional[AlertStateManager] = None


def get_alert_state_manager() -> AlertStateManager:
    """
    AlertStateManager 인스턴스를 싱글톤 패턴으로 반환합니다.
    
    Returns:
        AlertStateManager: 상태 관리자 인스턴스
    """
    global _alert_state_manager
    if _alert_state_manager is None:
        _alert_state_manager = AlertStateManager()
    return _alert_state_manager

