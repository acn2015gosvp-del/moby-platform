"""
InfluxDB 클라이언트 서비스 모듈

주요 기능:
- 배치 쓰기로 성능 최적화
- 자동 플러시 (시간 기반 또는 크기 기반)
- 쓰기 실패 시 자동 재시도
- 에러 처리 및 로깅
"""

import logging
import threading
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional, List

from influxdb_client import InfluxDBClient, Point, WriteApi, WriteOptions
from influxdb_client.client.exceptions import InfluxDBError
from influxdb_client.client.query_api import QueryApi

from .schemas.models.core.config import settings

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------
# 배치 쓰기 버퍼 항목
# -------------------------------------------------------------------

@dataclass
class BufferedPoint:
    """버퍼에 저장된 포인트 정보"""
    bucket: str
    measurement: str
    fields: Dict[str, Any]
    tags: Dict[str, Any]
    timestamp: datetime
    retry_count: int = 0
    max_retries: int = 3


# -------------------------------------------------------------------
# InfluxDB 클라이언트 관리자
# -------------------------------------------------------------------

class InfluxDBManager:
    """
    InfluxDB 클라이언트의 배치 쓰기, 버퍼링, 재시도를 관리합니다.
    
    주요 기능:
    - 배치 쓰기로 성능 최적화
    - 자동 플러시 (시간 기반 또는 크기 기반)
    - 쓰기 실패 시 자동 재시도
    """
    
    def __init__(
        self,
        buffer_size: int = 100,
        flush_interval: float = 5.0,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        InfluxDB 관리자 초기화
        
        Args:
            buffer_size: 버퍼 크기 (이 크기에 도달하면 자동 플러시)
            flush_interval: 플러시 간격 (초)
            max_retries: 최대 재시도 횟수
            retry_delay: 재시도 간격 (초)
        """
        self.client = InfluxDBClient(
            url=settings.INFLUX_URL,
            token=settings.INFLUX_TOKEN,
            org=settings.INFLUX_ORG
        )
        
        # Write API 설정 (배치 쓰기 최적화)
        write_options = WriteOptions(
            batch_size=buffer_size,
            flush_interval=int(flush_interval * 1000),  # 밀리초로 변환
            jitter_interval=2000,  # 2초 지터
            retry_interval=5000,  # 5초 재시도 간격
            max_retries=max_retries,
            max_retry_delay=30000,  # 30초 최대 재시도 지연
            exponential_base=2
        )
        
        self.write_api: WriteApi = self.client.write_api(write_options=write_options)
        self.query_api: QueryApi = self.client.query_api()
        
        # 버퍼 관리
        self.buffer: deque = deque()
        self.buffer_lock = threading.Lock()
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval
        
        # 재시도 설정
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # 스레드 종료 플래그
        self._shutdown_flag = threading.Event()
        
        # 플러시 스레드
        self.flush_thread = threading.Thread(
            target=self._periodic_flush,
            daemon=True,
            name="InfluxDB-Flush"
        )
        self.flush_thread.start()
        
        try:
            if logger.handlers:
                logger.info(
                    f"✅ InfluxDB manager initialized. "
                    f"URL: {settings.INFLUX_URL}, "
                    f"Buffer size: {buffer_size}, "
                    f"Flush interval: {flush_interval}s"
                )
        except (ValueError, OSError, AttributeError, RuntimeError):
            # 로거가 닫힌 파일에 쓰려고 시도하는 경우 무시
            pass
    
    def write_point(
        self,
        bucket: str,
        measurement: str,
        fields: Dict[str, Any],
        tags: Dict[str, Any],
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        포인트를 버퍼에 추가합니다. 버퍼가 가득 차면 자동으로 플러시됩니다.
        
        Args:
            bucket: InfluxDB 버킷 이름
            measurement: 측정값 이름
            fields: 필드 딕셔너리
            tags: 태그 딕셔너리
            timestamp: 타임스탬프 (None이면 현재 시간)
            
        Returns:
            버퍼 추가 성공 여부
        """
        try:
            buffered_point = BufferedPoint(
                bucket=bucket,
                measurement=measurement,
                fields=fields,
                tags=tags,
                timestamp=timestamp or datetime.now(),
                retry_count=0,
                max_retries=self.max_retries
            )
            
            with self.buffer_lock:
                self.buffer.append(buffered_point)
                buffer_len = len(self.buffer)
                
                try:
                    if logger.handlers:
                        logger.debug(
                            f"📥 Point buffered. "
                            f"Measurement: {measurement}, "
                            f"Buffer size: {buffer_len}/{self.buffer_size}"
                        )
                except (ValueError, OSError, AttributeError, RuntimeError):
                    # 로거가 닫힌 파일에 쓰려고 시도하는 경우 무시
                    pass
                
                # 버퍼가 가득 차면 즉시 플러시
                if buffer_len >= self.buffer_size:
                    try:
                        if logger.handlers:
                            logger.info(
                                f"🔄 Buffer full ({buffer_len} points). "
                                f"Triggering immediate flush..."
                            )
                    except (ValueError, OSError, AttributeError, RuntimeError):
                        # 로거가 닫힌 파일에 쓰려고 시도하는 경우 무시
                        pass
                    threading.Thread(
                        target=self._flush_buffer,
                        daemon=True,
                        name="InfluxDB-ImmediateFlush"
                    ).start()
            
            return True
            
        except Exception as e:
            try:
                if logger.handlers:
                    logger.error(
                        f"❌ Failed to buffer point. "
                        f"Measurement: {measurement}, Error: {e}",
                        exc_info=True
                    )
            except (ValueError, OSError, AttributeError, RuntimeError):
                # 로거가 닫힌 파일에 쓰려고 시도하는 경우 무시
                pass
            return False
    
    def _periodic_flush(self):
        """
        주기적으로 버퍼를 플러시하는 백그라운드 스레드 함수.
        """
        try:
            if logger.handlers:
                logger.info("🔄 InfluxDB periodic flush thread started.")
        except (ValueError, OSError, AttributeError, RuntimeError):
            # 로거가 닫힌 파일에 쓰려고 시도하는 경우 무시
            pass
        
        while not self._shutdown_flag.is_set():
            try:
                # shutdown_flag가 설정되면 즉시 종료
                if self._shutdown_flag.wait(timeout=self.flush_interval):
                    break
                
                with self.buffer_lock:
                    if len(self.buffer) > 0:
                        try:
                            if logger.handlers:
                                logger.debug(
                                    f"⏰ Periodic flush triggered. "
                                    f"Buffer size: {len(self.buffer)}"
                                )
                        except (ValueError, OSError, AttributeError, RuntimeError):
                            # 로거가 닫힌 파일에 쓰려고 시도하는 경우 무시
                            pass
                        self._flush_buffer_internal()
                        
            except Exception as e:
                # shutdown_flag가 설정되었으면 종료
                if self._shutdown_flag.is_set():
                    break
                try:
                    if logger.handlers:
                        logger.error(
                            f"❌ Error in periodic flush thread: {e}",
                            exc_info=True
                        )
                except (ValueError, OSError, AttributeError, RuntimeError):
                    # 로거가 닫힌 파일에 쓰려고 시도하는 경우 무시
                    pass
    
    def _flush_buffer(self):
        """
        버퍼를 플러시합니다 (스레드 안전).
        """
        with self.buffer_lock:
            self._flush_buffer_internal()
    
    def _flush_buffer_internal(self):
        """
        버퍼를 실제로 플러시합니다 (내부 메서드, lock 보호 필요).
        """
        if len(self.buffer) == 0:
            return
        
        # 버퍼에서 모든 포인트 가져오기
        points_to_write: List[BufferedPoint] = []
        while len(self.buffer) > 0:
            points_to_write.append(self.buffer.popleft())
        
        if not points_to_write:
            return
        
        try:
            if logger.handlers:
                logger.info(
                    f"📤 Flushing {len(points_to_write)} points to InfluxDB..."
                )
        except (ValueError, OSError, AttributeError, RuntimeError):
            # 로거가 닫힌 파일에 쓰려고 시도하는 경우 무시
            pass
        
        # 포인트를 InfluxDB Point 객체로 변환
        influx_points = []
        for buffered_point in points_to_write:
            try:
                point = Point(buffered_point.measurement)
                
                # 필드 추가
                for key, value in buffered_point.fields.items():
                    point.field(key, value)
                
                # 태그 추가
                for key, value in buffered_point.tags.items():
                    point.tag(key, value)
                
                # 타임스탬프 설정
                point.time(buffered_point.timestamp)
                
                influx_points.append(point)
                
            except Exception as e:
                try:
                    if logger.handlers:
                        logger.error(
                            f"❌ Failed to convert point. "
                            f"Measurement: {buffered_point.measurement}, Error: {e}",
                            exc_info=True
                        )
                except (ValueError, OSError, AttributeError, RuntimeError):
                    # 로거가 닫힌 파일에 쓰려고 시도하는 경우 무시
                    pass
                # 변환 실패한 포인트는 재시도 큐에 추가
                self._retry_point(buffered_point)
        
        if not influx_points:
            try:
                if logger.handlers:
                    logger.warning("⚠️ No valid points to write after conversion.")
            except (ValueError, OSError, AttributeError, RuntimeError):
                # 로거가 닫힌 파일에 쓰려고 시도하는 경우 무시
                pass
            return
        
        # 배치 쓰기 시도
        success = self._write_batch(points_to_write, influx_points)
        
        if not success:
            try:
                if logger.handlers:
                    logger.warning(
                        f"⚠️ Batch write failed. "
                        f"Re-queuing {len(points_to_write)} points for retry."
                    )
            except (ValueError, OSError, AttributeError, RuntimeError):
                # 로거가 닫힌 파일에 쓰려고 시도하는 경우 무시
                pass
    
    def _write_batch(
        self,
        buffered_points: List[BufferedPoint],
        influx_points: List[Point]
    ) -> bool:
        """
        배치로 포인트를 쓰기 시도합니다.
        
        Args:
            buffered_points: 원본 버퍼 포인트 리스트
            influx_points: InfluxDB Point 객체 리스트
            
        Returns:
            쓰기 성공 여부
        """
        if not influx_points:
            return False
        
        # 모든 포인트가 같은 버킷인지 확인
        bucket = buffered_points[0].bucket
        if not all(p.bucket == bucket for p in buffered_points):
            try:
                if logger.handlers:
                    logger.warning(
                        "⚠️ Points have different buckets. "
                        "Writing separately by bucket."
                    )
            except (ValueError, OSError, AttributeError, RuntimeError):
                # 로거가 닫힌 파일에 쓰려고 시도하는 경우 무시
                pass
            return self._write_batch_by_bucket(buffered_points, influx_points)
        
        try:
            # 배치 쓰기
            self.write_api.write(bucket=bucket, record=influx_points)
            
            try:
                if logger.handlers:
                    logger.info(
                        f"✅ Successfully wrote {len(influx_points)} points to bucket '{bucket}'."
                    )
            except (ValueError, OSError, AttributeError, RuntimeError):
                # 로거가 닫힌 파일에 쓰려고 시도하는 경우 무시
                pass
            return True
            
        except InfluxDBError as e:
            try:
                if logger.handlers:
                    logger.error(
                        f"❌ InfluxDB error during batch write. "
                        f"Bucket: {bucket}, Points: {len(influx_points)}, Error: {e}",
                        exc_info=True
                    )
            except (ValueError, OSError, AttributeError, RuntimeError):
                # 로거가 닫힌 파일에 쓰려고 시도하는 경우 무시
                pass
            # 재시도 큐에 추가
            for buffered_point in buffered_points:
                self._retry_point(buffered_point)
            return False
            
        except Exception as e:
            try:
                if logger.handlers:
                    logger.error(
                        f"❌ Unexpected error during batch write. "
                        f"Bucket: {bucket}, Points: {len(influx_points)}, Error: {e}",
                        exc_info=True
                    )
            except (ValueError, OSError, AttributeError, RuntimeError):
                # 로거가 닫힌 파일에 쓰려고 시도하는 경우 무시
                pass
            # 재시도 큐에 추가
            for buffered_point in buffered_points:
                self._retry_point(buffered_point)
            return False
    
    def _write_batch_by_bucket(
        self,
        buffered_points: List[BufferedPoint],
        influx_points: List[Point]
    ) -> bool:
        """
        버킷별로 그룹화하여 배치 쓰기를 수행합니다.
        """
        # 버킷별로 그룹화
        by_bucket: Dict[str, List[tuple]] = {}
        for buffered_point, influx_point in zip(buffered_points, influx_points):
            bucket = buffered_point.bucket
            if bucket not in by_bucket:
                by_bucket[bucket] = []
            by_bucket[bucket].append((buffered_point, influx_point))
        
        all_success = True
        for bucket, point_pairs in by_bucket.items():
            bucket_points = [p for _, p in point_pairs]
            bucket_buffered = [b for b, _ in point_pairs]
            
            try:
                self.write_api.write(bucket=bucket, record=bucket_points)
                try:
                    if logger.handlers:
                        logger.info(
                            f"✅ Successfully wrote {len(bucket_points)} points to bucket '{bucket}'."
                        )
                except (ValueError, OSError, AttributeError, RuntimeError):
                    # 로거가 닫힌 파일에 쓰려고 시도하는 경우 무시
                    pass
            except Exception as e:
                try:
                    if logger.handlers:
                        logger.error(
                            f"❌ Failed to write to bucket '{bucket}'. Error: {e}",
                            exc_info=True
                        )
                except (ValueError, OSError, AttributeError, RuntimeError):
                    # 로거가 닫힌 파일에 쓰려고 시도하는 경우 무시
                    pass
                for buffered_point in bucket_buffered:
                    self._retry_point(buffered_point)
                all_success = False
        
        return all_success
    
    def _retry_point(self, buffered_point: BufferedPoint):
        """
        실패한 포인트를 재시도 큐에 추가합니다.
        
        Args:
            buffered_point: 재시도할 포인트
        """
        if buffered_point.retry_count >= buffered_point.max_retries:
            try:
                if logger.handlers:
                    logger.error(
                        f"❌ Point exceeded max retries. Dropping point. "
                        f"Measurement: {buffered_point.measurement}, "
                        f"Bucket: {buffered_point.bucket}, "
                        f"Retry count: {buffered_point.retry_count}"
                    )
            except (ValueError, OSError, AttributeError, RuntimeError):
                # 로거가 닫힌 파일에 쓰려고 시도하는 경우 무시
                pass
            return
        
        buffered_point.retry_count += 1
        
        # 재시도 지연 후 버퍼에 다시 추가
        def delayed_retry():
            try:
                time.sleep(self.retry_delay * buffered_point.retry_count)  # 지수적 지연
                with self.buffer_lock:
                    self.buffer.append(buffered_point)
                # 로거 핸들러가 닫혔는지 확인
                if logger.handlers:
                    try:
                        logger.info(
                            f"🔄 Re-queued point for retry. "
                            f"Measurement: {buffered_point.measurement}, "
                            f"Retry count: {buffered_point.retry_count}/{buffered_point.max_retries}"
                        )
                    except (ValueError, OSError, AttributeError, RuntimeError):
                        # 로거가 닫힌 파일에 쓰려고 시도하는 경우 무시
                        # 테스트 종료 시 로거 핸들러가 이미 닫혔을 수 있음
                        pass
            except Exception:
                # 스레드가 종료되는 동안 발생할 수 있는 모든 예외 무시
                pass
        
        threading.Thread(
            target=delayed_retry,
            daemon=True,
            name=f"InfluxDB-Retry-{buffered_point.measurement}"
        ).start()
    
    def flush(self):
        """
        수동으로 버퍼를 플러시합니다.
        """
        try:
            if logger.handlers:
                logger.info("🔄 Manual flush requested.")
        except (ValueError, OSError, AttributeError, RuntimeError):
            # 로거가 닫힌 파일에 쓰려고 시도하는 경우 무시
            pass
        self._flush_buffer()
    
    def query_sensor_status(
        self,
        bucket: str,
        inactive_threshold_minutes: int = 5
    ) -> Dict[str, Any]:
        """
        센서 상태를 조회합니다.
        
        최근 inactive_threshold_minutes 분 내에 데이터가 있는 센서를 활성으로 간주합니다.
        
        Args:
            bucket: InfluxDB 버킷 이름
            inactive_threshold_minutes: 비활성으로 간주할 시간(분)
            
        Returns:
            센서 상태 정보 딕셔너리
        """
        try:
            from datetime import timedelta
            
            # Flux 쿼리 작성
            # 최근 inactive_threshold_minutes 분 내에 데이터가 있는 device_id 목록 조회
            query = f'''
            from(bucket: "{bucket}")
              |> range(start: -{inactive_threshold_minutes}m)
              |> filter(fn: (r) => r["_measurement"] == "sensor_data")
              |> filter(fn: (r) => r["_field"] == "temperature" or r["_field"] == "humidity" or r["_field"] == "vibration" or r["_field"] == "sound")
              |> group(columns: ["device_id"])
              |> distinct(column: "device_id")
              |> keep(columns: ["device_id"])
            '''
            
            try:
                if logger.handlers:
                    logger.debug(f"Querying sensor status from InfluxDB. Bucket: {bucket}")
            except (ValueError, OSError, AttributeError, RuntimeError):
                # 로거가 닫힌 파일에 쓰려고 시도하는 경우 무시
                pass
            
            # 쿼리 실행
            result = self.query_api.query(query=query, org=settings.INFLUX_ORG)
            
            # 결과 파싱
            active_devices = set()
            for table in result:
                for record in table.records:
                    device_id = record.values.get("device_id")
                    if device_id:
                        active_devices.add(device_id)
            
            active_count = len(active_devices)
            
            # 전체 센서 수는 활성 센서 수로 추정 (실제로는 별도 관리 필요)
            # 향후 센서 등록 시스템이 있으면 그곳에서 전체 수를 조회
            total_count = active_count  # 임시: 활성 센서 수를 전체로 간주
            inactive_count = 0  # 현재는 비활성 센서를 구분할 수 없음
            
            try:
                if logger.handlers:
                    logger.info(
                        f"✅ Sensor status queried. "
                        f"Active: {active_count}, Total: {total_count}"
                    )
            except (ValueError, OSError, AttributeError, RuntimeError):
                # 로거가 닫힌 파일에 쓰려고 시도하는 경우 무시
                pass
            
            return {
                "total_count": total_count,
                "active_count": active_count,
                "inactive_count": inactive_count,
                "devices": list(active_devices)
            }
            
        except Exception as e:
            try:
                if logger.handlers:
                    logger.error(
                        f"❌ Failed to query sensor status from InfluxDB. Error: {e}",
                        exc_info=True
                    )
            except (ValueError, OSError, AttributeError, RuntimeError):
                # 로거가 닫힌 파일에 쓰려고 시도하는 경우 무시
                pass
            # 에러 발생 시 빈 결과 반환
            return {
                "total_count": 0,
                "active_count": 0,
                "inactive_count": 0,
                "devices": []
            }
    
    def close(self):
        """
        리소스를 정리합니다.
        """
        try:
            if logger.handlers:
                logger.info("🔄 Closing InfluxDB manager...")
        except (ValueError, OSError, AttributeError, RuntimeError):
            # 로거가 닫힌 파일에 쓰려고 시도하는 경우 무시
            pass
        
        # 백그라운드 스레드 종료 신호
        if hasattr(self, '_shutdown_flag'):
            self._shutdown_flag.set()
        
        # 스레드가 종료될 때까지 대기 (최대 5초)
        if hasattr(self, 'flush_thread') and self.flush_thread.is_alive():
            self.flush_thread.join(timeout=5.0)
        
        # 남은 버퍼 플러시
        self._flush_buffer()
        
        # Write API 종료
        try:
            self.write_api.close()
            self.client.close()
            try:
                if logger.handlers:
                    logger.info("✅ InfluxDB manager closed successfully.")
            except (ValueError, OSError, AttributeError, RuntimeError):
                # 로거가 닫힌 파일에 쓰려고 시도하는 경우 무시
                pass
        except Exception as e:
            try:
                if logger.handlers:
                    logger.error(f"❌ Error closing InfluxDB manager: {e}", exc_info=True)
            except (ValueError, OSError, AttributeError, RuntimeError):
                # 로거가 닫힌 파일에 쓰려고 시도하는 경우 무시
                pass


# -------------------------------------------------------------------
# 글로벌 인스턴스 (지연 초기화)
# -------------------------------------------------------------------

_influx_manager_instance = None
_influx_manager_lock = threading.Lock()

def _get_influx_manager():
    """
    InfluxDB Manager 인스턴스를 지연 초기화하여 반환합니다.
    서버 시작 시 즉시 초기화되지 않고, 처음 사용될 때만 초기화됩니다.
    """
    global _influx_manager_instance
    if _influx_manager_instance is None:
        with _influx_manager_lock:
            if _influx_manager_instance is None:
                _influx_manager_instance = InfluxDBManager(
                    buffer_size=100,
                    flush_interval=5.0,
                    max_retries=3,
                    retry_delay=1.0
                )
    return _influx_manager_instance

# 호환성을 위한 속성처럼 접근 가능한 객체
class _InfluxManagerProxy:
    """InfluxDB Manager에 대한 프록시 객체 (지연 초기화)"""
    def __getattr__(self, name):
        return getattr(_get_influx_manager(), name)
    
    def __call__(self, *args, **kwargs):
        return _get_influx_manager()(*args, **kwargs)
    
    def __getstate__(self):
        # pickle 지원
        return {}
    
    def __setstate__(self, state):
        # pickle 지원
        pass

influx_manager = _InfluxManagerProxy()


# -------------------------------------------------------------------
# 공개 API (기존 호환성 유지)
# -------------------------------------------------------------------

def write_point(bucket: str, measurement: str, fields: dict, tags: dict):
    """
    단일 포인트를 쓰기합니다 (기존 API 호환성).
    
    이 함수는 내부적으로 버퍼에 추가하며, 배치로 쓰기가 수행됩니다.
    
    Args:
        bucket: InfluxDB 버킷 이름
        measurement: 측정값 이름
        fields: 필드 딕셔너리
        tags: 태그 딕셔너리
    """
    return _get_influx_manager().write_point(
        bucket=bucket,
        measurement=measurement,
        fields=fields,
        tags=tags
    )


def flush_influxdb():
    """
    InfluxDB 버퍼를 수동으로 플러시합니다.
    """
    _get_influx_manager().flush()


def query_sensor_status(bucket: str, inactive_threshold_minutes: int = 5) -> Dict[str, Any]:
    """
    센서 상태를 조회합니다.
    
    Args:
        bucket: InfluxDB 버킷 이름
        inactive_threshold_minutes: 비활성으로 간주할 시간(분) - 이 시간 동안 데이터가 없으면 비활성
        
    Returns:
        센서 상태 정보 딕셔너리:
        {
            "total_count": int,
            "active_count": int,
            "inactive_count": int,
            "devices": List[str]  # 활성 센서 목록
        }
    """
    return _get_influx_manager().query_sensor_status(bucket, inactive_threshold_minutes)


def close_influxdb():
    """
    InfluxDB 리소스를 정리합니다.
    """
    global _influx_manager_instance
    if _influx_manager_instance is not None:
        _influx_manager_instance.close()
        _influx_manager_instance = None
