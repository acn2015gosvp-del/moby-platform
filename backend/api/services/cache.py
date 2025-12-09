"""
캐싱 서비스 모듈

메모리 기반 캐싱을 제공합니다.
향후 Redis 등 외부 캐시로 확장 가능하도록 설계되었습니다.
"""

import logging
import hashlib
import json
import time
from typing import Optional, Any, Dict, Callable
from threading import Lock

logger = logging.getLogger(__name__)


class CacheEntry:
    """캐시 엔트리"""

    def __init__(self, value: Any, ttl: float):
        self.value = value
        self.expires_at = time.time() + ttl
        self.created_at = time.time()

    def is_expired(self) -> bool:
        return time.time() > self.expires_at


class MemoryCache:
    """메모리 기반 캐시"""

    def __init__(self, default_ttl: float = 300.0):
        """
        Args:
            default_ttl: 기본 TTL (초), 기본값 5분
        """
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = Lock()
        self.default_ttl = default_ttl

    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """캐시 키 생성"""
        key_data = {
            'prefix': prefix,
            'args': args,
            'kwargs': sorted(kwargs.items()) if kwargs else None,
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """캐시에서 값 조회"""
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None

            if entry.is_expired():
                del self._cache[key]
                return None

            return entry.value

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """캐시에 값 저장"""
        if ttl is None:
            ttl = self.default_ttl

        with self._lock:
            self._cache[key] = CacheEntry(value, ttl)

    def delete(self, key: str) -> None:
        """캐시에서 값 삭제"""
        with self._lock:
            self._cache.pop(key, None)

    def clear(self) -> None:
        """캐시 전체 삭제"""
        with self._lock:
            self._cache.clear()

    def cleanup_expired(self) -> int:
        """만료된 엔트리 정리"""
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items() if entry.is_expired()
            ]
            for key in expired_keys:
                del self._cache[key]
            return len(expired_keys)

    def get_or_set(
        self, key: str, factory: Callable[[], Any], ttl: Optional[float] = None
    ) -> Any:
        """캐시에서 조회하거나, 없으면 factory 함수를 실행하여 저장"""
        value = self.get(key)
        if value is not None:
            return value

        value = factory()
        self.set(key, value, ttl)
        return value

    def size(self) -> int:
        """캐시 크기 반환"""
        with self._lock:
            return len(self._cache)


# 전역 캐시 인스턴스
_cache = MemoryCache(default_ttl=300.0)


def get_cache() -> MemoryCache:
    """전역 캐시 인스턴스 반환"""
    return _cache


def cache_key(prefix: str, *args, **kwargs) -> str:
    """캐시 키 생성 헬퍼"""
    return _cache._generate_key(prefix, *args, **kwargs)


def cached(ttl: float = 300.0, key_prefix: Optional[str] = None) -> Callable:
    """
    함수 결과를 캐싱하는 데코레이터

    Args:
        ttl: 캐시 TTL (초)
        key_prefix: 캐시 키 접두사 (기본값: 함수명)

    Returns:
        데코레이터 함수

    Example:
        @cached(ttl=600)
        def expensive_function(arg1: int, arg2: int) -> int:
            return expensive_computation(arg1, arg2)
    """
    def decorator(func: Callable) -> Callable:
        prefix = key_prefix or func.__name__

        def wrapper(*args: Any, **kwargs: Any) -> Any:
            key = cache_key(prefix, *args, **kwargs)
            cache = get_cache()

            value = cache.get(key)
            if value is not None:
                logger.debug(f"Cache hit: {prefix}")
                return value

            logger.debug(f"Cache miss: {prefix}")
            value = func(*args, **kwargs)
            cache.set(key, value, ttl)
            return value

        return wrapper
    return decorator

