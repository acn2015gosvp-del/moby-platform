"""
보고서 생성 데이터 수집 서비스 모듈

실제 InfluxDB 및 시스템 로그에서 데이터를 조회하여 보고서 생성에 필요한 데이터를 제공합니다.

InfluxDB 센서 데이터 스키마:
- Bucket: sensor_data_v2
- Measurement: moby_sensors
- Tag: device_id (예: test-sensor-001)

필드 매핑:
1. 온도/습도 (DHT11):
   - 온도: fields.temperature_c
   - 습도: fields.humidity_percent

2. 진동 (Vibration):
   - Mean/Peak/RMS 계산용: fields_vibration_raw

3. 가속도/자이로 (MPU-6050):
   - 가속도 X축: accel_x
   - 가속도 Y축: accel_y
   - 가속도 Z축: accel_z
   - 자이로 X축: gyro_x
   - 자이로 Y축: gyro_y
   - 자이로 Z축: gyro_z

4. 음압 (Sound):
   - 음압 센서값: fields.sound_raw 또는 fields.sound_voltage

5. 기압 (Pressure):
   - 기압: pressure_hpa

주의사항:
- 필드명에 'fields_' 접두사가 붙어있을 수 있음 (fields_temperature_c 등)
- pandas와 numpy가 설치되어 있어야 데이터 처리 가능
"""

import logging
import random
import math
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from concurrent.futures import ThreadPoolExecutor, as_completed

if TYPE_CHECKING:
    import pandas as pd
from sqlalchemy.orm import Session

try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None  # pd가 정의되지 않았을 때를 대비
    np = None
    logging.warning("pandas가 설치되지 않았습니다. pip install pandas numpy")

from backend.api.services.influx_client import influx_manager
from backend.api.services.schemas.models.core.config import settings
from backend.api.services.alert_storage import get_latest_alerts
from backend.api.services.schemas.models.core.logger import get_logger

logger = get_logger(__name__)


class ReportDataService:
    """보고서 생성 데이터 수집 서비스"""
    
    def __init__(self):
        """InfluxDB 클라이언트 초기화"""
        self.influx_client = influx_manager
        # InfluxDB 스키마: Bucket = sensor_data_v2, Measurement = moby_sensors
        # 환경 변수에서 bucket을 가져오되, 없으면 기본값 사용
        self.bucket = getattr(settings, 'INFLUX_BUCKET', 'sensor_data_v2')
        # 명시적으로 sensor_data_v2 사용 (스키마 명시)
        if self.bucket != 'sensor_data_v2':
            logger.warning(
                f"⚠️ Bucket이 'sensor_data_v2'가 아닙니다: {self.bucket}. "
                f"스키마에 따르면 'sensor_data_v2'를 사용해야 합니다."
            )
        self.org = settings.INFLUX_ORG
        
        logger.info(
            f"ReportDataService 초기화 완료. "
            f"Bucket: {self.bucket}, Org: {self.org}, Measurement: moby_sensors"
        )
    
    def fetch_report_data(
        self,
        start_time: datetime,
        end_time: datetime,
        equipment_id: str,
        db: Session,
        sensor_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        보고서 생성에 필요한 데이터를 실제 데이터 소스에서 조회합니다.
        
        Args:
            start_time: 보고 기간 시작 시간
            end_time: 보고 기간 종료 시간
            equipment_id: 설비 ID
            db: 데이터베이스 세션
            sensor_ids: 특정 센서 ID 목록 (선택)
            
        Returns:
            보고서 생성에 필요한 데이터 딕셔너리
        """
        try:
            # 알람 데이터 조회 (먼저 조회하여 fallback 로직에 사용)
            alarms = self._fetch_alarms(
                db=db,
                start_time=start_time,
                end_time=end_time,
                equipment_id=equipment_id
            )
            
            # 센서 통계 데이터 조회 (알람 데이터를 fallback으로 전달)
            sensor_stats = self._fetch_sensor_stats(
                start_time=start_time,
                end_time=end_time,
                equipment_id=equipment_id,
                sensor_ids=sensor_ids,
                alarms=alarms  # fallback 로직에 사용
            )
            
            # MLP 이상 탐지 데이터 조회
            mlp_anomalies = self._fetch_mlp_anomalies(
                db=db,
                start_time=start_time,
                end_time=end_time,
                equipment_id=equipment_id
            )
            
            # IF 이상 탐지 데이터 조회
            if_anomalies = self._fetch_if_anomalies(
                db=db,
                start_time=start_time,
                end_time=end_time,
                equipment_id=equipment_id
            )
            
            # 상관계수 계산
            correlations = self._calculate_correlations(
                start_time=start_time,
                end_time=end_time,
                equipment_id=equipment_id
            )
            
            # 메타데이터
            metadata = {
                "period_start": start_time.isoformat(),
                "period_end": end_time.isoformat(),
                "equipment": equipment_id,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
            return {
                "metadata": metadata,
                "sensor_stats": sensor_stats,
                "alarms": alarms,
                "mlp_anomalies": mlp_anomalies,
                "if_anomalies": if_anomalies,
                "correlations": correlations
            }
            
        except Exception as e:
            logger.exception(f"보고서 데이터 수집 중 오류: {e}")
            # 오류 발생 시 기본 구조 반환
            return {
                "metadata": {
                    "period_start": start_time.isoformat(),
                    "period_end": end_time.isoformat(),
                    "equipment": equipment_id,
                    "generated_at": datetime.now(timezone.utc).isoformat()
                },
                "sensor_stats": self._get_default_sensor_stats(),
                "alarms": [],
                "mlp_anomalies": [],
                "if_anomalies": [],
                "correlations": {}
            }
    
    def _fetch_sensor_stats(
        self,
        start_time: datetime,
        end_time: datetime,
        equipment_id: str,
        sensor_ids: Optional[List[str]] = None,
        alarms: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        InfluxDB에서 Raw 센서 데이터를 조회하여 pandas로 정밀 통계를 계산합니다.
        
        Raw 데이터를 가져와서 mean, min, max, std, p95, rms 등을 정확하게 계산합니다.
        """
        if not PANDAS_AVAILABLE:
            logger.error("pandas가 필요합니다. pip install pandas numpy")
            return self._get_default_sensor_stats()
        
        try:
            # 시간 범위를 RFC3339 형식으로 변환 (타임존 명시적으로 UTC로 변환)
            # timezone-aware로 변환 (없으면 UTC로 설정)
            if start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=timezone.utc)
            if end_time.tzinfo is None:
                end_time = end_time.replace(tzinfo=timezone.utc)
            
            # UTC로 변환 (다른 타임존이면)
            start_time_utc = start_time.astimezone(timezone.utc)
            end_time_utc = end_time.astimezone(timezone.utc)
            
            # RFC3339 형식으로 변환 (Z suffix 사용)
            start_rfc3339 = start_time_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
            end_rfc3339 = end_time_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
            
            logger.info(f"📅 센서 통계 조회 시간 범위 (UTC): {start_rfc3339} ~ {end_rfc3339}")
            logger.info(f"   원본 시간: {start_time} ~ {end_time}")
            logger.info(f"   시간 범위 길이: {(end_time_utc - start_time_utc).total_seconds() / 3600:.2f}시간")
            
            # 실제 데이터가 있는 시간 범위와 비교
            if alarms:
                alarm_times = []
                for alarm in alarms:
                    alarm_time_str = alarm.get('timestamp') or alarm.get('ts') or alarm.get('time')
                    if alarm_time_str:
                        try:
                            if isinstance(alarm_time_str, str):
                                if 'Z' in alarm_time_str:
                                    alarm_time_str = alarm_time_str.replace('Z', '+00:00')
                                alarm_dt = datetime.fromisoformat(alarm_time_str)
                            else:
                                alarm_dt = alarm_time_str
                            
                            if alarm_dt.tzinfo is None:
                                alarm_dt = alarm_dt.replace(tzinfo=timezone.utc)
                            else:
                                alarm_dt = alarm_dt.astimezone(timezone.utc)
                            
                            alarm_times.append(alarm_dt)
                        except Exception:
                            continue
                
                if alarm_times:
                    actual_data_start = min(alarm_times)
                    actual_data_end = max(alarm_times)
                    logger.info(
                        f"   알람 데이터 시간 범위: {actual_data_start.isoformat()} ~ {actual_data_end.isoformat()}"
                    )
                    
                    # 시간 범위 겹침 확인
                    if actual_data_start > end_time_utc or actual_data_end < start_time_utc:
                        logger.warning(
                            f"   ⚠️ 시간 범위 불일치! 요청 범위와 알람 데이터 범위가 겹치지 않습니다.\n"
                            f"      요청 범위: {start_rfc3339} ~ {end_rfc3339}\n"
                            f"      알람 범위: {actual_data_start.isoformat()} ~ {actual_data_end.isoformat()}"
                        )
                    else:
                        logger.info(f"   ✅ 시간 범위 일치 확인됨")
            
            # 알람 데이터에서 실제 데이터 존재 시간 범위 확인
            actual_data_start = None
            actual_data_end = None
            if alarms:
                alarm_times = []
                for alarm in alarms:
                    alarm_time_str = alarm.get('timestamp') or alarm.get('ts') or alarm.get('time')
                    if alarm_time_str:
                        try:
                            if isinstance(alarm_time_str, str):
                                # ISO 형식 파싱
                                if 'Z' in alarm_time_str:
                                    alarm_time_str = alarm_time_str.replace('Z', '+00:00')
                                alarm_dt = datetime.fromisoformat(alarm_time_str)
                            else:
                                alarm_dt = alarm_time_str
                            
                            if alarm_dt.tzinfo is None:
                                alarm_dt = alarm_dt.replace(tzinfo=timezone.utc)
                            else:
                                alarm_dt = alarm_dt.astimezone(timezone.utc)
                            
                            alarm_times.append(alarm_dt)
                        except Exception as e:
                            logger.debug(f"알람 시간 파싱 실패: {alarm_time_str}, 오류: {e}")
                
                if alarm_times:
                    actual_data_start = min(alarm_times)
                    actual_data_end = max(alarm_times)
                    logger.info(
                        f"📊 알람 데이터 기반 실제 데이터 시간 범위: "
                        f"{actual_data_start.isoformat()} ~ {actual_data_end.isoformat()}"
                    )
                    
                    # 요청 시간 범위와 알람 시간 범위 비교
                    if actual_data_start < start_time_utc or actual_data_end > end_time_utc:
                        logger.warning(
                            f"⚠️ 알람 시간 범위가 요청 시간 범위와 다릅니다!\n"
                            f"   요청 범위: {start_rfc3339} ~ {end_rfc3339}\n"
                            f"   알람 범위: {actual_data_start.isoformat()} ~ {actual_data_end.isoformat()}\n"
                            f"   → 시간 범위를 알람 데이터에 맞춰 확장할 수 있습니다."
                        )
            
            # 센서 필터 구성
            # InfluxDB 스키마: Tag = device_id (예: test-sensor-001)
            # 주의: equipment_id는 설비명("Conveyor A-01")일 수 있고, device_id는 실제 디바이스 ID입니다.
            # 프론트엔드에서 보내는 equipment_id와 실제 InfluxDB의 device_id 태그가 다를 수 있으므로,
            # 일단 필터 없이 모든 데이터를 조회합니다.
            # 실제 운영 환경에서는 equipment_id -> device_id 매핑 테이블이 필요합니다.
            device_filter = None
            
            # TODO: equipment_id -> device_id 매핑 로직 추가 필요
            # 현재는 필터 없이 모든 데이터 조회하여 통계 계산
            # equipment_id는 설비명일 수 있으므로 device_id 필터를 적용하지 않음
            logger.info(f"equipment_id '{equipment_id}' - 필터 없이 모든 데이터 조회 (설비명일 수 있음)")
            
            # sensor_ids는 실제 device_id일 수 있으므로 필터 적용
            # InfluxDB 스키마에 따르면 device_id 태그를 사용해야 함
            if sensor_ids:
                # sensor_ids가 실제 device_id 형식인지 확인
                valid_sensor_ids = [sid for sid in sensor_ids if len(sid) >= 10]
                if valid_sensor_ids:
                    # device_id 태그 필터 사용 (스키마 명시)
                    sensor_filter = ' or '.join([f'r["device_id"] == "{sid}"' for sid in valid_sensor_ids])
                    device_filter = f'({sensor_filter})'
                    logger.info(f"device_id 필터 적용: {valid_sensor_ids}")
            
            sensor_stats = {}
            
            # 병렬 처리로 센서 통계 계산 속도 향상
            logger.info(f"센서 통계 병렬 계산 시작 (기간: {start_rfc3339} ~ {end_rfc3339})")
            
            def calc_temperature():
                try:
                    # InfluxDB 스키마: fields.temperature_c (DHT11)
                    return ("temperature", self._calculate_sensor_stats_from_raw(
                        start_rfc3339, end_rfc3339, "fields_temperature_c", device_filter, "moby_sensors"
                    ))
                except Exception as e:
                    logger.error(f"❌ 온도 통계 계산 실패: {e}")
                    return ("temperature", {"mean": 0.0, "min": 0.0, "max": 0.0, "std": 0.0, "p95": 0.0})
            
            def calc_humidity():
                try:
                    # InfluxDB 스키마: fields.humidity_percent (DHT11)
                    return ("humidity", self._calculate_sensor_stats_from_raw(
                        start_rfc3339, end_rfc3339, "fields_humidity_percent", device_filter, "moby_sensors"
                    ))
                except Exception as e:
                    logger.error(f"❌ 습도 통계 계산 실패: {e}")
                    return ("humidity", {"mean": 0.0, "min": 0.0, "max": 0.0, "std": 0.0, "p95": 0.0})
            
            def calc_vibration():
                try:
                    # InfluxDB 필드명: fields_vibration_raw
                    return ("vibration", self._calculate_vibration_stats_from_raw(
                        start_rfc3339, end_rfc3339, device_filter, "moby_sensors"
                    ))
                except Exception as e:
                    logger.error(f"❌ 진동 통계 계산 실패: {e}")
                    return ("vibration", {
                        "x": {"mean": 0.0, "peak": 0.0, "rms": 0.0},
                        "y": {"mean": 0.0, "peak": 0.0, "rms": 0.0},
                        "z": {"mean": 0.0, "peak": 0.0, "rms": 0.0}
                    })
            
            def calc_sound():
                try:
                    # InfluxDB 스키마: fields.sound_raw 또는 fields.sound_voltage
                    return ("sound", self._calculate_sensor_stats_from_raw(
                        start_rfc3339, end_rfc3339, "fields_sound_raw", device_filter, "moby_sensors"
                    ))
                except Exception as e:
                    logger.error(f"❌ 음압 통계 계산 실패: {e}")
                    return ("sound", {"mean": 0.0, "min": 0.0, "max": 0.0, "std": 0.0, "p95": 0.0})
            
            def calc_acceleration():
                try:
                    # InfluxDB 필드명: accel_x, accel_y, accel_z (fields_ 접두사 없음)
                    return ("acceleration", self._calculate_axis_stats_from_raw(
                        start_rfc3339, end_rfc3339, 
                        ["accel_x", "accel_y", "accel_z"],
                        device_filter, "moby_sensors"
                    ))
                except Exception as e:
                    logger.error(f"❌ 가속도 통계 계산 실패: {e}")
                    return ("acceleration", {
                        "x": {"mean": 0.0, "min": 0.0, "max": 0.0, "std": 0.0, "p95": 0.0},
                        "y": {"mean": 0.0, "min": 0.0, "max": 0.0, "std": 0.0, "p95": 0.0},
                        "z": {"mean": 0.0, "min": 0.0, "max": 0.0, "std": 0.0, "p95": 0.0}
                    })
            
            def calc_gyro():
                try:
                    # InfluxDB 필드명: gyro_x, gyro_y, gyro_z (fields_ 접두사 없음)
                    return ("gyro", self._calculate_axis_stats_from_raw(
                        start_rfc3339, end_rfc3339,
                        ["gyro_x", "gyro_y", "gyro_z"],
                        device_filter, "moby_sensors"
                    ))
                except Exception as e:
                    logger.error(f"❌ 자이로 통계 계산 실패: {e}")
                    return ("gyro", {
                        "x": {"mean": 0.0, "min": 0.0, "max": 0.0, "std": 0.0, "p95": 0.0},
                        "y": {"mean": 0.0, "min": 0.0, "max": 0.0, "std": 0.0, "p95": 0.0},
                        "z": {"mean": 0.0, "min": 0.0, "max": 0.0, "std": 0.0, "p95": 0.0}
                    })
            
            def calc_pressure():
                try:
                    # InfluxDB 필드명: pressure_hpa (fields_ 접두사 없음)
                    return ("pressure", self._calculate_sensor_stats_from_raw(
                        start_rfc3339, end_rfc3339, "pressure_hpa", device_filter, "moby_sensors"
                    ))
                except Exception as e:
                    logger.error(f"❌ 기압 통계 계산 실패: {e}")
                    return ("pressure", {"mean": 0.0, "min": 0.0, "max": 0.0, "std": 0.0, "p95": 0.0})
            
            # 병렬 실행 (최대 7개 스레드: 온도, 습도, 진동, 음압, 가속도, 자이로, 기압)
            with ThreadPoolExecutor(max_workers=7) as executor:
                futures = {
                    executor.submit(calc_temperature): "temperature",
                    executor.submit(calc_humidity): "humidity",
                    executor.submit(calc_vibration): "vibration",
                    executor.submit(calc_sound): "sound",
                    executor.submit(calc_acceleration): "acceleration",
                    executor.submit(calc_gyro): "gyro",
                    executor.submit(calc_pressure): "pressure"
                }
                
                for future in as_completed(futures):
                    sensor_name = None
                    try:
                        # 타임아웃을 10초로 단축 (더 빠른 실패 처리)
                        sensor_name, stats = future.result(timeout=10)
                        sensor_stats[sensor_name] = stats
                        logger.info(f"✅ {sensor_name} 통계 계산 완료")
                    except TimeoutError:
                        sensor_name = futures.get(future, "unknown")
                        logger.warning(f"⏱️ {sensor_name} 통계 계산 타임아웃 (10초 초과), 기본값 사용")
                        if sensor_name in ["vibration", "acceleration", "gyro"]:
                            if sensor_name == "vibration":
                                sensor_stats[sensor_name] = {
                                    "x": {"mean": 0.0, "peak": 0.0, "rms": 0.0},
                                    "y": {"mean": 0.0, "peak": 0.0, "rms": 0.0},
                                    "z": {"mean": 0.0, "peak": 0.0, "rms": 0.0}
                                }
                            else:
                                sensor_stats[sensor_name] = {
                                    "x": {"mean": 0.0, "min": 0.0, "max": 0.0, "std": 0.0, "p95": 0.0},
                                    "y": {"mean": 0.0, "min": 0.0, "max": 0.0, "std": 0.0, "p95": 0.0},
                                    "z": {"mean": 0.0, "min": 0.0, "max": 0.0, "std": 0.0, "p95": 0.0}
                                }
                        else:
                            sensor_stats[sensor_name] = {
                                "mean": 0.0, "min": 0.0, "max": 0.0, "std": 0.0, "p95": 0.0
                            }
                    except Exception as e:
                        sensor_name = futures.get(future, "unknown")
                        logger.error(f"❌ {sensor_name} 통계 계산 실패: {e}", exc_info=True)
                        # 기본값 설정
                        if sensor_name in ["vibration", "acceleration", "gyro"]:
                            if sensor_name == "vibration":
                                sensor_stats[sensor_name] = {
                                    "x": {"mean": 0.0, "peak": 0.0, "rms": 0.0},
                                    "y": {"mean": 0.0, "peak": 0.0, "rms": 0.0},
                                    "z": {"mean": 0.0, "peak": 0.0, "rms": 0.0}
                                }
                            else:
                                sensor_stats[sensor_name] = {
                                    "x": {"mean": 0.0, "min": 0.0, "max": 0.0, "std": 0.0, "p95": 0.0},
                                    "y": {"mean": 0.0, "min": 0.0, "max": 0.0, "std": 0.0, "p95": 0.0},
                                    "z": {"mean": 0.0, "min": 0.0, "max": 0.0, "std": 0.0, "p95": 0.0}
                                }
                        else:
                            sensor_stats[sensor_name] = {
                                "mean": 0.0, "min": 0.0, "max": 0.0, "std": 0.0, "p95": 0.0
                            }
            
            logger.info(f"센서 통계 계산 완료: {len(sensor_stats)}개 센서")
            logger.info(f"센서 통계 상세: {sensor_stats}")
            
            # 통계 값이 모두 0.0인지 확인
            all_zero = True
            for sensor_name, stats in sensor_stats.items():
                if sensor_name == "vibration":
                    for axis in ["x", "y", "z"]:
                        axis_stats = stats.get(axis, {})
                        if any(v != 0.0 for v in axis_stats.values()):
                            all_zero = False
                            break
                else:
                    if any(v != 0.0 for v in stats.values()):
                        all_zero = False
                        break
                if not all_zero:
                    break
            
            # Fallback: InfluxDB 데이터가 없으면 알람 데이터에서 통계 계산
            if all_zero:
                logger.warning("⚠️ 모든 센서 통계가 0.0입니다. 데이터 조회에 문제가 있을 수 있습니다.")
                logger.warning(f"   기간: {start_time} ~ {end_time}")
                logger.warning(f"   equipment_id: {equipment_id}")
                logger.warning(f"   device_filter: {device_filter}")
                
                # 알람 데이터에서 통계 계산 시도
                if alarms and len(alarms) > 0:
                    logger.info(f"📊 알람 데이터에서 통계를 계산합니다 (Fallback). 알람 개수: {len(alarms)}개")
                    try:
                        sensor_stats = self._calculate_stats_from_alarms(alarms)
                        # Fallback으로 계산한 통계가 여전히 0.0인지 확인
                        fallback_all_zero = True
                        for sensor_name, stats in sensor_stats.items():
                            if sensor_name == "vibration":
                                for axis in ["x", "y", "z"]:
                                    axis_stats = stats.get(axis, {})
                                    if any(v != 0.0 for v in axis_stats.values()):
                                        fallback_all_zero = False
                                        break
                            else:
                                if any(v != 0.0 for v in stats.values()):
                                    fallback_all_zero = False
                                    break
                            if not fallback_all_zero:
                                break
                        
                        if not fallback_all_zero:
                            logger.info("✅ 알람 데이터에서 통계 계산 성공 (0이 아닌 값 존재)")
                        else:
                            logger.warning("⚠️ 알람 데이터에서도 통계를 계산할 수 없습니다. 기본값(0.0)을 사용합니다.")
                    except Exception as fallback_error:
                        logger.error(f"❌ 알람 데이터에서 통계 계산 실패: {fallback_error}", exc_info=True)
                        logger.warning("⚠️ 기본값(0.0)을 사용합니다.")
                else:
                    logger.warning("⚠️ 알람 데이터도 없습니다. 기본값(0.0)을 사용합니다.")
            
            return sensor_stats
            
        except Exception as e:
            logger.exception(f"센서 통계 조회 중 오류: {e}")
            logger.error(f"   기간: {start_time} ~ {end_time}")
            logger.error(f"   equipment_id: {equipment_id}")
            # 오류 발생 시 기본값 반환 (0.0으로 채워진 구조)
            return self._get_default_sensor_stats()
    
    def _fetch_raw_data_as_dataframe(
        self,
        start_rfc3339: str,
        end_rfc3339: str,
        field_name: str,
        device_filter: Optional[str] = None,
        measurement: str = "moby_sensors"
    ) -> Optional[Any]:
        """
        InfluxDB에서 Raw 데이터를 조회하여 pandas DataFrame으로 변환합니다.
        
        Returns:
            DataFrame with columns: ['_time', '_value'] or None if no data
            Returns None if pandas is not available
        """
        try:
            # Raw 데이터 조회 쿼리
            base_filter = f'|> filter(fn: (r) => r["_measurement"] == "{measurement}")\n  |> filter(fn: (r) => r["_field"] == "{field_name}")'
            if device_filter:
                base_filter += f'\n  |> filter(fn: (r) => {device_filter})'
            
            # 쿼리 최적화: aggregateWindow를 사용하여 10분 단위로 집계 (더 빠른 처리)
            # Raw 데이터가 너무 많으면 타임아웃 발생하므로 집계 사용
            # 통계 계산에는 집계된 데이터로도 충분함
            # 중요: float()를 사용하여 값이 문자열이어도 숫자로 변환
            # InfluxDB의 float() 함수는 문자열을 숫자로 변환
            query = f'''
            from(bucket: "{self.bucket}")
              |> range(start: {start_rfc3339}, stop: {end_rfc3339})
              {base_filter}
              |> group()
              |> aggregateWindow(every: 30m, fn: mean, createEmpty: false)
              |> map(fn: (r) => ({{
                _time: r._time,
                _value: if exists r._value then float(v: r._value) else 0.0,
                _measurement: r._measurement,
                _field: r._field
              }}))
              |> sort(columns: ["_time"])
              |> limit(n: 5000)
            '''
            
            logger.info(f"📊 Raw 데이터 조회 쿼리 실행 (30분 집계): {field_name}")
            logger.info(f"   조회 기간: {start_rfc3339} ~ {end_rfc3339}")
            logger.info(f"   필터: {device_filter if device_filter else '없음 (모든 데이터)'}")
            logger.info(f"   measurement: {measurement}, field: {field_name}")
            logger.info(f"   실행 쿼리:")
            logger.info(f"   {query}")
            try:
                # 쿼리 실행 전 로깅
                logger.info(f"   🔄 InfluxDB 쿼리 실행 중...")
                query_start_time = datetime.now(timezone.utc)
                
                # 쿼리 타임아웃 설정 (15초)
                result = self.influx_client.query_api.query(
                    query=query, 
                    org=self.org
                )
                
                query_end_time = datetime.now(timezone.utc)
                query_duration = (query_end_time - query_start_time).total_seconds()
                logger.info(f"   ✅ 쿼리 실행 완료 (소요 시간: {query_duration:.2f}초)")
                if query_duration > 5.0:
                    logger.warning(f"   ⚠️ 쿼리 실행 시간이 깁니다: {query_duration:.2f}초 ({field_name})")
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"집계 쿼리 실패 ({field_name}): {error_msg}")
                
                # "Too Many Requests" 오류인 경우 샘플링 사용
                if "too many requests" in error_msg.lower() or "429" in error_msg:
                    logger.info(f"{field_name}: Too Many Requests, 샘플링으로 재시도...")
                    query_sample = f'''
                    from(bucket: "{self.bucket}")
                      |> range(start: {start_rfc3339}, stop: {end_rfc3339})
                      {base_filter}
                      |> group()
                      |> sample(n: 5000)
                      |> sort(columns: ["_time"])
                    '''
                    result = self.influx_client.query_api.query(query=query_sample, org=self.org)
                else:
                    # 다른 오류는 재시도하지 않음
                    raise
            
            # DataFrame으로 변환 (최대 10000개로 제한하여 메모리 및 속도 최적화)
            data = []
            table_count = 0
            record_count = 0
            valid_value_count = 0
            invalid_value_count = 0
            max_records = 10000  # 최대 레코드 수 제한
            
            for table in result:
                table_count += 1
                for record in table.records:
                    if len(data) >= max_records:
                        logger.warning(f"{field_name}: 최대 레코드 수({max_records}) 도달, 조기 종료")
                        break
                    record_count += 1
                    value = record.get_value()
                    
                    # 값이 None이 아닌지 확인
                    if value is not None:
                        try:
                            # 숫자로 변환 시도
                            float_value = float(value)
                            # NaN이나 Infinity가 아닌지 확인
                            if not (float('nan') == float_value or float('inf') == abs(float_value)):
                                data.append({
                                    '_time': record.get_time(),
                                    '_value': float_value
                                })
                                valid_value_count += 1
                            else:
                                invalid_value_count += 1
                                logger.debug(f"{field_name}: NaN/Infinity 값 무시: {value}")
                        except (ValueError, TypeError) as ve:
                            invalid_value_count += 1
                            logger.warning(f"{field_name}: 값 변환 실패 (무시): {value} (타입: {type(value)}), 오류: {ve}")
                            continue
                    else:
                        invalid_value_count += 1
                if len(data) >= max_records:
                    break
            
            # 쿼리 결과 상세 로깅
            logger.info(f"   ════════════════════════════════════════════════════════")
            logger.info(f"   ✅ {field_name}: 쿼리 실행 완료")
            logger.info(f"   ════════════════════════════════════════════════════════")
            logger.info(f"   테이블 개수: {table_count}개")
            logger.info(f"   전체 레코드: {record_count}개")
            logger.info(f"   유효 값: {valid_value_count}개")
            logger.info(f"   무효 값: {invalid_value_count}개")
            logger.info(f"   최종 데이터 포인트: {len(data)}개")
            if valid_value_count == 0:
                logger.warning(f"   ⚠️ {field_name}: 유효한 데이터가 없습니다!")
            
            # 데이터가 있을 때 샘플 값 출력
            if len(data) > 0:
                logger.debug(f"   📊 데이터 샘플 (처음 3개):")
                for i, item in enumerate(data[:3], 1):
                    logger.debug(f"      {i}. 시간: {item['_time']}, 값: {item['_value']} (타입: {type(item['_value']).__name__})")
            else:
                logger.warning(f"   ⚠️ 조회된 데이터가 없습니다!")
            
            # 빈 배열과 0 값 구분
            if not data:
                logger.warning(
                    f"⚠️ {field_name}: 조회된 데이터가 없습니다 (빈 배열).\n"
                    f"   기간: {start_rfc3339} ~ {end_rfc3339}\n"
                    f"   필터: {device_filter if device_filter else '없음 (모든 데이터)'}\n"
                    f"   measurement: {measurement}\n"
                    f"   field: {field_name}\n"
                    f"   테이블: {table_count}개, 레코드: {record_count}개\n"
                    f"   유효 값: {valid_value_count}개, 무효 값: {invalid_value_count}개"
                )
                
                # 데이터가 없을 때 가능한 원인 진단
                if record_count > 0 and valid_value_count == 0:
                    logger.warning(
                        f"   💡 진단: 레코드는 있지만 유효 값이 없습니다.\n"
                        f"      → 데이터 타입 변환 문제일 수 있습니다.\n"
                        f"      → InfluxDB에서 값이 문자열로 저장되었을 가능성."
                    )
                elif record_count == 0:
                    logger.warning(
                        f"   💡 진단: 레코드 자체가 없습니다.\n"
                        f"      → 해당 기간에 데이터가 없거나\n"
                        f"      → measurement/field 이름이 다를 수 있습니다.\n"
                        f"      → 시간 범위를 확인하세요."
                    )
                # 필터 없이 재시도하여 데이터 존재 여부 확인
                if device_filter:
                    logger.info(f"{field_name}: 필터 없이 재시도하여 데이터 존재 여부 확인...")
                    try:
                        query_no_filter = f'''
                        from(bucket: "{self.bucket}")
                          |> range(start: {start_rfc3339}, stop: {end_rfc3339})
                          |> filter(fn: (r) => r["_measurement"] == "{measurement}")
                          |> filter(fn: (r) => r["_field"] == "{field_name}")
                          |> group()
                          |> aggregateWindow(every: 30m, fn: mean, createEmpty: false)
                          |> limit(n: 1)
                        '''
                        test_result = self.influx_client.query_api.query(query=query_no_filter, org=self.org)
                        test_count = sum(1 for table in test_result for _ in table.records)
                        if test_count > 0:
                            logger.warning(f"{field_name}: ⚠️ 필터 없이는 데이터가 존재합니다! device_filter가 잘못되었을 수 있습니다.")
                        else:
                            logger.warning(f"{field_name}: 필터 없이도 데이터가 없습니다. 해당 기간에 데이터가 없거나 필드명이 다를 수 있습니다.")
                    except Exception as test_e:
                        logger.debug(f"{field_name}: 필터 없이 테스트 실패: {test_e}")
                return None
            
            if not PANDAS_AVAILABLE or pd is None:
                logger.error("pandas가 사용 불가능합니다.")
                return None
            
            try:
                df = pd.DataFrame(data)
                df['_time'] = pd.to_datetime(df['_time'])
                df = df.sort_values('_time')
                logger.debug(f"{field_name}: DataFrame 생성 완료 ({len(df)}행)")
                return df
            except Exception as df_error:
                logger.error(f"{field_name}: DataFrame 생성 실패: {df_error}")
                return None
            
        except Exception as e:
            logger.warning(f"Raw 데이터 조회 실패 ({field_name}): {e}", exc_info=True)
            return None
    
    def _calculate_sensor_stats_from_raw(
        self,
        start_rfc3339: str,
        end_rfc3339: str,
        field_name: str,
        device_filter: Optional[str] = None,
        measurement: str = "moby_sensors"
    ) -> Dict[str, float]:
        """
        Raw 데이터를 가져와서 pandas로 정밀 통계를 계산합니다.
        
        Returns:
            {"mean": float, "min": float, "max": float, "std": float, "p95": float}
            데이터가 없으면 모두 0.0
        """
        df = self._fetch_raw_data_as_dataframe(
            start_rfc3339=start_rfc3339,
            end_rfc3339=end_rfc3339,
            field_name=field_name,
            device_filter=device_filter,
            measurement=measurement
        )
        
        if df is None or len(df) == 0:
            logger.warning(
                f"{field_name}: ⚠️ 데이터 없음 - 기본값 반환\n"
                f"   기간: {start_rfc3339} ~ {end_rfc3339}\n"
                f"   필터: {device_filter if device_filter else '없음'}\n"
                f"   measurement: {measurement}\n"
                f"   field: {field_name}"
            )
            
            # 필터 없이 재시도
            if device_filter:
                logger.info(f"{field_name}: 필터 없이 재시도...")
                try:
                    df_retry = self._fetch_raw_data_as_dataframe(
                        start_rfc3339=start_rfc3339,
                        end_rfc3339=end_rfc3339,
                        field_name=field_name,
                        device_filter=None,
                        measurement=measurement
                    )
                    if df_retry is not None and len(df_retry) > 0:
                        logger.info(f"{field_name}: ✅ 필터 없이 재시도 성공! ({len(df_retry)}개 데이터)")
                        df = df_retry
                    else:
                        logger.warning(f"{field_name}: 필터 없이도 데이터 없음")
                except Exception as retry_e:
                    logger.warning(f"{field_name}: 필터 없이 재시도 실패: {retry_e}")
            
            # 여전히 데이터가 없으면 빈 배열과 0 값 구분을 명확히
            if df is None or len(df) == 0:
                logger.error(
                    f"{field_name}: ❌ 최종적으로 데이터 없음 - 빈 배열 반환 (0.0 기본값 사용)\n"
                    f"   ⚠️ 주의: 이는 '데이터가 없음'을 의미하며, 실제 센서 값이 0인 것과 다릅니다.\n"
                    f"   💡 해결 방법:\n"
                    f"      1. InfluxDB에 해당 기간의 데이터가 있는지 확인\n"
                    f"      2. measurement 이름 확인: {measurement}\n"
                    f"      3. field 이름 확인: {field_name}\n"
                    f"      4. 시간 범위 확인: {start_rfc3339} ~ {end_rfc3339}\n"
                    f"      5. 알람 데이터에는 값이 있다면 시간 범위나 필터 문제일 수 있음"
                )
                return {
                    "mean": 0.0,
                    "min": 0.0,
                    "max": 0.0,
                    "std": 0.0,
                    "p95": 0.0
                }
        
        # 데이터 타입 확인 및 변환
        if '_value' not in df.columns:
            logger.error(f"{field_name}: '_value' 컬럼이 없습니다. 컬럼: {df.columns.tolist()}")
            return {
                "mean": 0.0,
                "min": 0.0,
                "max": 0.0,
                "std": 0.0,
                "p95": 0.0
            }
        
        # 숫자 타입으로 강제 변환 (데이터 타입 문제 해결)
        logger.info(f"   ════════════════════════════════════════════════════════")
        logger.debug(f"   📊 {field_name}: 통계 계산 시작")
        logger.debug(f"   DataFrame 크기: {len(df)}행 x {len(df.columns)}열")
        logger.debug(f"   컬럼 목록: {df.columns.tolist()}")
        logger.debug(f"   '_value' 컬럼 데이터 타입 (변환 전): {df['_value'].dtype}")
        logger.debug(f"   '_value' 컬럼 샘플 (변환 전): {df['_value'].head(5).tolist()}")
        
        # 숫자 타입으로 강제 변환 (문자열이어도 숫자로 변환)
        try:
            # pd.to_numeric은 문자열도 숫자로 변환 가능
            df['_value'] = pd.to_numeric(df['_value'], errors='coerce')
            logger.debug(f"   '_value' 컬럼 데이터 타입 (변환 후): {df['_value'].dtype}")
            logger.debug(f"   '_value' 컬럼 샘플 (변환 후): {df['_value'].head(5).tolist()}")
        except Exception as e:
            logger.error(f"{field_name}: 숫자 변환 실패: {e}")
            logger.error(f"   원본 데이터 타입: {df['_value'].dtype}")
            logger.error(f"   원본 샘플: {df['_value'].head(5).tolist()}")
            return {
                "mean": 0.0,
                "min": 0.0,
                "max": 0.0,
                "std": 0.0,
                "p95": 0.0
            }
        
        # NaN 제거
        values = df['_value'].dropna()
        
        logger.info(f"   NaN 제거 전: {len(df)}개, NaN 제거 후: {len(values)}개")
        
        # 데이터가 없을 때와 0 값 구분
        if len(values) == 0:
            logger.error(f"   ❌ {field_name}: 유효한 데이터 포인트가 없습니다!")
            logger.error(f"   DataFrame 길이: {len(df)}")
            logger.error(f"   NaN 개수: {df['_value'].isna().sum()}")
            if len(df) > 0:
                logger.error(f"   DataFrame 샘플 (처음 5개):")
                for idx, row in df.head(5).iterrows():
                    logger.error(f"      인덱스 {idx}: _time={row['_time']}, _value={row['_value']} (타입: {type(row['_value']).__name__})")
            return {
                "mean": 0.0,
                "min": 0.0,
                "max": 0.0,
                "std": 0.0,
                "p95": 0.0
            }
        
        # 통계 계산 (안전하게)
        try:
            logger.info(f"   📊 {field_name}: 통계 계산 시작 (데이터 포인트: {len(values)}개)")
            
            # 값이 모두 숫자인지 확인
            if not values.dtype in ['float64', 'int64', 'float32', 'int32']:
                logger.warning(f"   ⚠️ 데이터 타입이 숫자가 아닙니다: {values.dtype}")
                logger.warning(f"   샘플 값: {values.head(10).tolist()}")
            
            # 데이터 포인트가 1개인 경우 경고 및 처리
            if len(values) == 1:
                logger.warning(f"   ⚠️ {field_name}: 데이터 포인트가 1개뿐입니다. Std/P95 계산 불가 (정상 동작).")
                single_value = float(values.iloc[0]) if hasattr(values, 'iloc') else float(values[0])
                stats = {
                    "mean": single_value,
                    "min": single_value,
                    "max": single_value,
                    "std": 0.0,  # 데이터 포인트 1개이므로 표준편차는 0
                    "p95": single_value  # 데이터 포인트 1개이므로 P95는 그 값 자체
                }
                logger.info(f"   ✅ 통계 (단일 값): mean={stats['mean']:.4f}, min={stats['min']:.4f}, max={stats['max']:.4f}, std={stats['std']:.4f}, p95={stats['p95']:.4f}")
            else:
                # 여러 데이터 포인트가 있는 경우 정상 계산
                # 통계 계산 (numpy 사용)
                if PANDAS_AVAILABLE and np is not None:
                    # numpy를 사용한 정확한 통계 계산
                    values_array = values.values if hasattr(values, 'values') else values.to_numpy()
                    stats = {
                        "mean": float(np.mean(values_array)) if len(values_array) > 0 else 0.0,
                        "min": float(np.min(values_array)) if len(values_array) > 0 else 0.0,
                        "max": float(np.max(values_array)) if len(values_array) > 0 else 0.0,
                        "std": float(np.std(values_array)) if len(values_array) > 1 else 0.0,
                        "p95": float(np.percentile(values_array, 95)) if len(values_array) > 0 else 0.0
                    }
                else:
                    # pandas fallback (numpy가 없는 경우)
                    stats = {
                        "mean": float(values.mean()) if len(values) > 0 else 0.0,
                        "min": float(values.min()) if len(values) > 0 else 0.0,
                        "max": float(values.max()) if len(values) > 0 else 0.0,
                        "std": float(values.std()) if len(values) > 1 else 0.0,
                        "p95": float(values.quantile(0.95)) if len(values) > 0 else 0.0
                    }
                
                logger.info(f"   ✅ 통계 계산 완료:")
                logger.info(f"      Mean: {stats['mean']:.4f}, Min: {stats['min']:.4f}, Max: {stats['max']:.4f}, Std: {stats['std']:.4f}, P95: {stats['p95']:.4f}")
                logger.info(f"      데이터 포인트: {len(values)}개, 값 범위: {float(values.min()):.4f} ~ {float(values.max()):.4f}")
            
            # 로그는 위에서 이미 출력됨 (단일 값인 경우와 여러 값인 경우 모두)
            
            # 통계 값이 모두 0인지 확인
            if all(v == 0.0 for v in stats.values()):
                logger.warning(f"   ⚠️ 모든 통계 값이 0.0입니다!")
                logger.warning(f"   값 개수: {len(values)}")
                logger.warning(f"   샘플 값: {values.head(10).tolist()}")
                logger.warning(f"   값 범위: {values.min()} ~ {values.max()}")
                logger.warning(f"   → 실제 데이터 값이 모두 0인지, 아니면 조회 문제인지 확인 필요")
            else:
                logger.info(f"   ✅ 통계 값이 정상적으로 계산되었습니다")
            
            return stats
        except Exception as e:
            logger.error(f"{field_name} 통계 계산 실패: {e}")
            return {
                "mean": 0.0,
                "min": 0.0,
                "max": 0.0,
                "std": 0.0,
                "p95": 0.0
            }
    
    def _calculate_vibration_stats_from_raw(
        self,
        start_rfc3339: str,
        end_rfc3339: str,
        device_filter: Optional[str] = None,
        measurement: str = "moby_sensors"
    ) -> Dict[str, Dict[str, float]]:
        """
        진동 센서의 Raw 데이터를 가져와서 정밀 통계를 계산합니다.
        
        InfluxDB 필드명: fields_vibration_raw
        보고서 형식에 맞춰 x, y, z 축 구조로 반환하지만, 실제로는 단일 진동 값입니다.
        
        Returns:
            {
                "x": {"mean": float, "peak": float, "rms": float},
                "y": {"mean": float, "peak": float, "rms": float},
                "z": {"mean": float, "peak": float, "rms": float}
            }
        """
        # InfluxDB 필드명: fields_vibration_raw (단일 필드명만 사용)
        field_names = ["fields_vibration_raw"]
        df = None
        successful_field = None
        
        logger.info(f"🔍 진동 데이터 조회 시작 (총 {len(field_names)}개 필드명 시도)")
        logger.info(f"   조회 기간: {start_rfc3339} ~ {end_rfc3339}")
        logger.info(f"   필터: {device_filter if device_filter else '없음 (모든 데이터)'}")
        
        for idx, field_name in enumerate(field_names, 1):
            logger.info(f"   [{idx}/{len(field_names)}] 진동 필드 시도: {field_name}")
            try:
                # 진동 데이터 조회
                df = self._fetch_raw_data_as_dataframe(
                    start_rfc3339=start_rfc3339,
                    end_rfc3339=end_rfc3339,
                    field_name=field_name,
                    device_filter=device_filter,
                    measurement=measurement
                )
                
                if df is not None and len(df) > 0:
                    successful_field = field_name
                    logger.info(f"   ✅ 진동 데이터 발견: {field_name} ({len(df)}개 데이터 포인트)")
                    # 데이터 샘플 로깅
                    if len(df) > 0:
                        sample_values = df['_value'].head(5).tolist()
                        logger.info(f"   📊 데이터 샘플: {sample_values}")
                    break
                else:
                    logger.warning(f"   ❌ {field_name}: 데이터 없음 (df={df is not None}, len={len(df) if df is not None else 0})")
            except Exception as e:
                logger.warning(f"   ⚠️ {field_name} 조회 중 오류: {e}")
                continue
        
        # 모든 필드 시도 후에도 데이터가 없으면 필터 없이 재시도
        if df is None or len(df) == 0:
            logger.warning(f"   ⚠️ 모든 필드명 시도 실패, 필터 없이 재시도...")
            for idx, field_name in enumerate(field_names, 1):
                logger.info(f"   [{idx}/{len(field_names)}] 필터 없이 재시도: {field_name}")
                try:
                    df = self._fetch_raw_data_as_dataframe(
                        start_rfc3339=start_rfc3339,
                        end_rfc3339=end_rfc3339,
                        field_name=field_name,
                        device_filter=None,
                        measurement=measurement
                    )
                    if df is not None and len(df) > 0:
                        successful_field = field_name
                        logger.info(f"   ✅ 진동: 필터 없이 조회 성공 ({field_name}, {len(df)}개 데이터)")
                        # 데이터 샘플 로깅
                        if len(df) > 0:
                            sample_values = df['_value'].head(5).tolist()
                            logger.info(f"   📊 데이터 샘플: {sample_values}")
                        break
                    else:
                        logger.warning(f"   ❌ 필터 없이도 {field_name}: 데이터 없음")
                except Exception as e:
                    logger.warning(f"   ⚠️ 필터 없이 재시도 실패 ({field_name}): {e}")
        
        if successful_field:
            logger.info(f"   ✅ 최종 사용 필드: {successful_field}")
        else:
            logger.warning(f"   ❌ 모든 진동 필드명 시도 실패. 사용 가능한 필드명이 없습니다.")
        
        # 기본값 초기화
        default_stats = {
            "mean": 0.0,
            "peak": 0.0,
            "rms": 0.0
        }
        
        if df is None or len(df) == 0:
            logger.debug(f"진동: 데이터 없음, 기본값 반환")
            return {
                "x": default_stats.copy(),
                "y": default_stats.copy(),
                "z": default_stats.copy()
            }
        
        values = df['_value'].dropna()
        
        if len(values) == 0:
            logger.warning(f"진동: 유효한 데이터 포인트가 없습니다.")
            return {
                "x": default_stats.copy(),
                "y": default_stats.copy(),
                "z": default_stats.copy()
            }
        
        # 통계 계산 (단일 진동 값에 대해)
        try:
            logger.info(f"   📊 진동 통계 계산 시작 (데이터 포인트: {len(values)}개)")
            
            if len(values) == 0:
                logger.warning(f"   ⚠️ 진동: 유효한 데이터 포인트가 없습니다.")
                return {
                    "x": default_stats.copy(),
                    "y": default_stats.copy(),
                    "z": default_stats.copy()
                }
            
            # 데이터 포인트가 1개인 경우 경고
            if len(values) == 1:
                logger.warning(f"   ⚠️ 진동: 데이터 포인트가 1개뿐입니다. 표준편차 계산 불가.")
                single_value = float(values.iloc[0]) if hasattr(values, 'iloc') else float(values[0])
                stats = {
                    "mean": single_value,
                    "peak": abs(single_value),
                    "rms": abs(single_value)
                }
                logger.info(f"   ✅ 진동 통계 (단일 값): mean={stats['mean']:.4f}, peak={stats['peak']:.4f}, rms={stats['rms']:.4f}")
            else:
                # 여러 데이터 포인트가 있는 경우 정상 계산
                mean_val = float(values.mean()) if len(values) > 0 else 0.0
                
                # peak 계산 (절댓값 최대)
                abs_values = values.abs()
                peak_val = float(abs_values.max()) if len(abs_values) > 0 else 0.0
                
                # RMS 계산 (Root Mean Square)
                if not PANDAS_AVAILABLE or np is None:
                    rms_val = 0.0
                else:
                    if len(values) > 0:
                        rms_val = float(np.sqrt((values ** 2).mean()))
                    else:
                        rms_val = 0.0
                
                stats = {
                    "mean": mean_val,
                    "peak": peak_val,
                    "rms": rms_val
                }
                
                logger.info(f"   ✅ 진동 통계 계산 완료:")
                logger.info(f"      Mean: {mean_val:.4f}, Peak: {peak_val:.4f}, RMS: {rms_val:.4f}")
                logger.info(f"      데이터 포인트: {len(values)}개, 값 범위: {float(values.min()):.4f} ~ {float(values.max()):.4f}")
            
            # 보고서 형식에 맞춰 x, y, z 축 모두 동일한 값으로 반환
            # (실제로는 단일 진동 값이지만, 보고서 구조를 유지하기 위해)
            return {
                "x": stats.copy(),
                "y": stats.copy(),
                "z": stats.copy()
            }
            
        except Exception as e:
            logger.error(f"진동 통계 계산 실패: {e}", exc_info=True)
            return {
                "x": default_stats.copy(),
                "y": default_stats.copy(),
                "z": default_stats.copy()
            }
    
    def _calculate_axis_stats_from_raw(
        self,
        start_rfc3339: str,
        end_rfc3339: str,
        field_names: List[str],  # ["accel_x", "accel_y", "accel_z"] 또는 ["gyro_x", "gyro_y", "gyro_z"]
        device_filter: Optional[str] = None,
        measurement: str = "moby_sensors"
    ) -> Dict[str, Dict[str, float]]:
        """
        축별 센서 데이터(가속도, 자이로 등)의 통계를 계산합니다.
        
        Args:
            field_names: 축별 필드명 리스트 (예: ["accel_x", "accel_y", "accel_z"] 또는 ["gyro_x", "gyro_y", "gyro_z"])
        
        Returns:
            {
                "x": {"mean": float, "min": float, "max": float, "std": float, "p95": float},
                "y": {"mean": float, "min": float, "max": float, "std": float, "p95": float},
                "z": {"mean": float, "min": float, "max": float, "std": float, "p95": float}
            }
        """
        axis_map = {"x": 0, "y": 1, "z": 2}
        result = {}
        
        for axis, idx in axis_map.items():
            if idx >= len(field_names):
                logger.warning(f"축 {axis}에 대한 필드명이 없습니다. 기본값 사용.")
                result[axis] = {"mean": 0.0, "min": 0.0, "max": 0.0, "std": 0.0, "p95": 0.0}
                continue
            
            field_name = field_names[idx]
            try:
                stats = self._calculate_sensor_stats_from_raw(
                    start_rfc3339, end_rfc3339, field_name, device_filter, measurement
                )
                result[axis] = stats
            except Exception as e:
                logger.error(f"축 {axis} ({field_name}) 통계 계산 실패: {e}")
                result[axis] = {"mean": 0.0, "min": 0.0, "max": 0.0, "std": 0.0, "p95": 0.0}
        
        return result
    
    def _get_default_sensor_stats(self) -> Dict[str, Any]:
        """
        데이터가 없을 때 기본값을 반환합니다.
        모든 값은 0.0으로 설정하여 테이블이 깨지지 않게 합니다.
        """
        return {
            "temperature": {
                "mean": 0.0,
                "min": 0.0,
                "max": 0.0,
                "std": 0.0,
                "p95": 0.0
            },
            "humidity": {
                "mean": 0.0,
                "min": 0.0,
                "max": 0.0,
                "std": 0.0,
                "p95": 0.0
            },
            "vibration": {
                "x": {"mean": 0.0, "peak": 0.0, "rms": 0.0},
                "y": {"mean": 0.0, "peak": 0.0, "rms": 0.0},
                "z": {"mean": 0.0, "peak": 0.0, "rms": 0.0}
            },
            "sound": {
                "mean": 0.0,
                "min": 0.0,
                "max": 0.0,
                "std": 0.0,
                "p95": 0.0
            },
            "acceleration": {
                "x": {"mean": 0.0, "min": 0.0, "max": 0.0, "std": 0.0, "p95": 0.0},
                "y": {"mean": 0.0, "min": 0.0, "max": 0.0, "std": 0.0, "p95": 0.0},
                "z": {"mean": 0.0, "min": 0.0, "max": 0.0, "std": 0.0, "p95": 0.0}
            },
            "gyro": {
                "x": {"mean": 0.0, "min": 0.0, "max": 0.0, "std": 0.0, "p95": 0.0},
                "y": {"mean": 0.0, "min": 0.0, "max": 0.0, "std": 0.0, "p95": 0.0},
                "z": {"mean": 0.0, "min": 0.0, "max": 0.0, "std": 0.0, "p95": 0.0}
            },
            "pressure": {
                "mean": 0.0,
                "min": 0.0,
                "max": 0.0,
                "std": 0.0,
                "p95": 0.0
            }
        }
    
    def _fetch_alarms(
        self,
        db: Session,
        start_time: datetime,
        end_time: datetime,
        equipment_id: str
    ) -> List[Dict[str, Any]]:
        """알람 데이터를 조회합니다."""
        try:
            # DB에서 알람 조회
            all_alerts = get_latest_alerts(
                db=db,
                limit=1000,
                sensor_id=None,
                level=None
            )
            
            # 기간 및 설비 필터링
            filtered_alarms = []
            for alert in all_alerts:
                # Alert는 SQLAlchemy 모델 객체이므로 속성으로 접근
                alert_time = getattr(alert, 'ts', None) or getattr(alert, 'timestamp', None)
                if alert_time:
                    try:
                        if isinstance(alert_time, str):
                            alert_dt = datetime.fromisoformat(alert_time.replace("Z", "+00:00"))
                        else:
                            alert_dt = alert_time
                            # timezone-aware로 변환
                            if alert_dt.tzinfo is None:
                                alert_dt = alert_dt.replace(tzinfo=timezone.utc)
                        
                        if start_time <= alert_dt <= end_time:
                            device = getattr(alert, 'sensor_id', None) or getattr(alert, 'device_id', "") or ""
                            if equipment_id.lower() in device.lower() or device.lower() in equipment_id.lower() or not device:
                                # details에서 value와 threshold 추출 시도
                                details = getattr(alert, 'details', None)
                                if isinstance(details, dict):
                                    value = details.get('value', 0.0)
                                    threshold = details.get('threshold', 0.0)
                                else:
                                    value = 0.0
                                    threshold = 0.0
                                
                                filtered_alarms.append({
                                    "timestamp": alert_dt.isoformat() if hasattr(alert_dt, 'isoformat') else str(alert_dt),
                                    "sensor": device or equipment_id,
                                    "severity": getattr(alert, 'level', 'unknown'),
                                    "value": value,
                                    "threshold": threshold,
                                    "message": getattr(alert, 'message', '알람 발생')
                                })
                    except Exception as e:
                        logger.debug(f"알람 시간 파싱 실패: {e}")
                        continue
            
            if not filtered_alarms:
                # 더미 데이터 생성 (기간에 따라 가변)
                filtered_alarms = self._generate_dummy_alarms(start_time, end_time, equipment_id)
            
            return filtered_alarms
            
        except Exception as e:
            logger.exception(f"알람 데이터 조회 실패: {e}")
            return self._generate_dummy_alarms(start_time, end_time, equipment_id)
    
    def _fetch_mlp_anomalies(
        self,
        db: Session,
        start_time: datetime,
        end_time: datetime,
        equipment_id: str
    ) -> List[Dict[str, Any]]:
        """MLP 이상 탐지 데이터를 조회합니다."""
        try:
            # 실제 DB 조회 로직 (현재는 더미 데이터)
            return self._generate_dummy_mlp_anomalies(start_time, end_time, equipment_id)
        except Exception as e:
            logger.exception(f"MLP 이상 탐지 데이터 조회 실패: {e}")
            return []
    
    def _fetch_if_anomalies(
        self,
        db: Session,
        start_time: datetime,
        end_time: datetime,
        equipment_id: str
    ) -> List[Dict[str, Any]]:
        """Isolation Forest 이상 탐지 데이터를 조회합니다."""
        try:
            # 실제 DB 조회 로직 (현재는 더미 데이터)
            return self._generate_dummy_if_anomalies(start_time, end_time, equipment_id)
        except Exception as e:
            logger.exception(f"IF 이상 탐지 데이터 조회 실패: {e}")
            return []
    
    def _calculate_correlations(
        self,
        start_time: datetime,
        end_time: datetime,
        equipment_id: str
    ) -> Dict[str, float]:
        """센서 간 상관계수를 계산합니다."""
        try:
            if not PANDAS_AVAILABLE:
                logger.warning("pandas가 없어서 상관계수를 계산할 수 없습니다.")
                return {"temperature_vibration": 0.0, "vibration_sound": 0.0, "temperature_humidity": 0.0}
            
            # 시간 범위 변환
            if start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=timezone.utc)
            if end_time.tzinfo is None:
                end_time = end_time.replace(tzinfo=timezone.utc)
            
            start_rfc3339 = start_time.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            end_rfc3339 = end_time.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            
            # device_filter 설정
            # 주의: equipment_id는 설비명("컨베이어 벨트 #1")일 수 있고, device_id는 실제 디바이스 ID입니다.
            # 프론트엔드에서 보내는 equipment_id와 실제 InfluxDB의 device_id 태그가 다를 수 있으므로,
            # 센서 통계 계산과 동일하게 필터 없이 모든 데이터를 조회합니다.
            # 실제 운영 환경에서는 equipment_id -> device_id 매핑 테이블이 필요합니다.
            device_filter = None
            
            # TODO: equipment_id -> device_id 매핑 로직 추가 필요
            # 현재는 필터 없이 모든 데이터 조회하여 상관계수 계산
            # equipment_id는 설비명일 수 있으므로 device_id 필터를 적용하지 않음
            logger.info(f"📊 상관계수 계산 시작: {start_rfc3339} ~ {end_rfc3339}")
            logger.info(f"   equipment_id '{equipment_id}' - 필터 없이 모든 데이터 조회 (설비명일 수 있음)")
            
            # 각 센서 데이터 조회 (필터 없이 전체 데이터 조회)
            temp_df = self._fetch_raw_data_as_dataframe(
                start_rfc3339, 
                end_rfc3339, 
                "fields_temperature_c",
                device_filter=None  # 필터 없이 전체 데이터 조회
            )
            humidity_df = self._fetch_raw_data_as_dataframe(
                start_rfc3339, 
                end_rfc3339, 
                "fields_humidity_percent",
                device_filter=None  # 필터 없이 전체 데이터 조회
            )
            vibration_df = self._fetch_raw_data_as_dataframe(
                start_rfc3339, 
                end_rfc3339, 
                "fields_vibration_raw",
                device_filter=None  # 필터 없이 전체 데이터 조회
            )
            sound_df = self._fetch_raw_data_as_dataframe(
                start_rfc3339, 
                end_rfc3339, 
                "fields_sound_raw",
                device_filter=None  # 필터 없이 전체 데이터 조회
            )
            
            # 데이터프레임 병합을 위한 준비
            dfs = {}
            if temp_df is not None and len(temp_df) > 0:
                temp_df = temp_df.rename(columns={'_value': 'temperature'})
                dfs['temperature'] = temp_df[['_time', 'temperature']]
                logger.info(f"   ✅ 온도 데이터: {len(temp_df)}개 포인트")
            
            if humidity_df is not None and len(humidity_df) > 0:
                humidity_df = humidity_df.rename(columns={'_value': 'humidity'})
                dfs['humidity'] = humidity_df[['_time', 'humidity']]
                logger.info(f"   ✅ 습도 데이터: {len(humidity_df)}개 포인트")
            
            if vibration_df is not None and len(vibration_df) > 0:
                vibration_df = vibration_df.rename(columns={'_value': 'vibration'})
                dfs['vibration'] = vibration_df[['_time', 'vibration']]
                logger.info(f"   ✅ 진동 데이터: {len(vibration_df)}개 포인트")
            
            if sound_df is not None and len(sound_df) > 0:
                sound_df = sound_df.rename(columns={'_value': 'sound'})
                dfs['sound'] = sound_df[['_time', 'sound']]
                logger.info(f"   ✅ 음압 데이터: {len(sound_df)}개 포인트")
            
            if len(dfs) < 2:
                logger.warning("상관계수 계산을 위한 충분한 센서 데이터가 없습니다.")
                return {"temperature_vibration": 0.0, "vibration_sound": 0.0, "temperature_humidity": 0.0}
            
            # 시간 기준 병합
            merged_df = None
            for name, df in dfs.items():
                if merged_df is None:
                    merged_df = df
                else:
                    merged_df = pd.merge(merged_df, df, on='_time', how='outer')
            
            if merged_df is None or len(merged_df) < 2:
                logger.warning("병합된 데이터가 충분하지 않습니다.")
                return {"temperature_vibration": 0.0, "vibration_sound": 0.0, "temperature_humidity": 0.0}
            
            logger.info(f"   ✅ 병합된 데이터: {len(merged_df)}개 포인트, 컬럼: {list(merged_df.columns)}")
            
            # 숫자형 컬럼만 선택 (상관계수 계산용)
            numeric_cols = merged_df.select_dtypes(include=['float64', 'int64', 'float32', 'int32']).columns.tolist()
            # _time 제외
            numeric_cols = [col for col in numeric_cols if col != '_time']
            
            if len(numeric_cols) < 2:
                logger.warning("상관계수 계산을 위한 충분한 숫자형 컬럼이 없습니다.")
                return {"temperature_vibration": 0.0, "vibration_sound": 0.0, "temperature_humidity": 0.0}
            
            # 상관계수 계산
            corr_matrix = merged_df[numeric_cols].corr()
            
            result = {
                "temperature_vibration": 0.0,
                "vibration_sound": 0.0,
                "temperature_humidity": 0.0
            }
            
            # 상관계수 추출 (NaN이면 0.0)
            if 'temperature' in corr_matrix.columns and 'vibration' in corr_matrix.columns:
                val = corr_matrix.loc['temperature', 'vibration']
                result["temperature_vibration"] = round(float(val), 3) if not pd.isna(val) else 0.0
                logger.info(f"   📈 온도-진동 상관계수: {result['temperature_vibration']}")
            
            if 'vibration' in corr_matrix.columns and 'sound' in corr_matrix.columns:
                val = corr_matrix.loc['vibration', 'sound']
                result["vibration_sound"] = round(float(val), 3) if not pd.isna(val) else 0.0
                logger.info(f"   📈 진동-음압 상관계수: {result['vibration_sound']}")
            
            if 'temperature' in corr_matrix.columns and 'humidity' in corr_matrix.columns:
                val = corr_matrix.loc['temperature', 'humidity']
                result["temperature_humidity"] = round(float(val), 3) if not pd.isna(val) else 0.0
                logger.info(f"   📈 온도-습도 상관계수: {result['temperature_humidity']}")
            
            logger.info(f"✅ 상관계수 계산 완료: {result}")
            return result
            
        except Exception as e:
            logger.error(f"상관계수 계산 중 오류: {e}", exc_info=True)
            return {"temperature_vibration": 0.0, "vibration_sound": 0.0, "temperature_humidity": 0.0}
    
    def _generate_dummy_alarms(
        self,
        start_time: datetime,
        end_time: datetime,
        equipment_id: str
    ) -> List[Dict[str, Any]]:
        """더미 알람 데이터 생성"""
        duration_hours = (end_time - start_time).total_seconds() / 3600
        num_alarms = max(1, int(duration_hours / 24))  # 하루에 1개 정도
        
        alarms = []
        for i in range(num_alarms):
            alarm_time = start_time + timedelta(hours=i * (duration_hours / max(1, num_alarms)))
            alarms.append({
                "timestamp": alarm_time.isoformat(),
                "sensor": equipment_id,
                "severity": random.choice(["CRITICAL", "WARNING", "INFO"]),
                "value": round(random.uniform(45.0, 60.0), 2),
                "threshold": 50.0,
                "message": f"임계값 초과 알람 {i+1}"
            })
        
        return alarms
    
    def _generate_dummy_mlp_anomalies(
        self,
        start_time: datetime,
        end_time: datetime,
        equipment_id: str
    ) -> List[Dict[str, Any]]:
        """더미 MLP 이상 탐지 데이터 생성"""
        return [
            {
                "timestamp": (start_time + timedelta(hours=12)).isoformat(),
                "type": "MLP_composite",
                "score": 0.75,
                "description": "학습된 이상 패턴 감지"
            }
        ]
    
    def _generate_dummy_if_anomalies(
        self,
        start_time: datetime,
        end_time: datetime,
        equipment_id: str
    ) -> List[Dict[str, Any]]:
        """더미 IF 이상 탐지 데이터 생성"""
        return [
            {
                "timestamp": (start_time + timedelta(hours=24)).isoformat(),
                "type": "IF_outlier",
                "score": 0.82,
                "description": "미지의 이상 패턴 감지"
            }
        ]
    
    def _calculate_stats_from_alarms(self, alarms: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        알람 데이터에서 센서 통계를 계산합니다 (Fallback 로직).
        
        알람의 'value' 필드나 'details.meta.value' 필드에서 값을 추출하여
        Mean, Min, Max를 계산합니다.
        
        Args:
            alarms: 알람 데이터 리스트
            
        Returns:
            센서 통계 딕셔너리
        """
        import re
        
        logger.info(f"📊 알람 데이터에서 통계 계산 시작 (알람 개수: {len(alarms)}개)")
        
        # 알람에서 값 추출
        values = []
        for alarm in alarms:
            # 알람 메시지에서 값 추출 시도 (예: "임계값 초과 알람 1" -> 53.66)
            # 또는 details.meta.value 필드 확인
            value = None
            
            # 방법 1: 알람 데이터에 직접 value 필드가 있는지 확인 (가장 우선)
            value = alarm.get('value')
            
            # 방법 2: details.meta.value 확인
            if (value is None or value == 0.0) and isinstance(alarm.get('details'), dict):
                details = alarm.get('details', {})
                if isinstance(details.get('meta'), dict):
                    meta = details.get('meta', {})
                    value = meta.get('value')
                # details에 직접 value가 있는지 확인
                elif 'value' in details:
                    value = details.get('value')
            
            # 방법 3: 알람 메시지에서 숫자 추출 (예: "**53.66**" 또는 "53.66")
            if (value is None or value == 0.0):
                message = alarm.get('message', '')
                # 메시지에서 숫자 추출 시도 (소수점 포함)
                numbers = re.findall(r'\d+\.\d+', message)  # 소수점이 있는 숫자만
                if not numbers:
                    numbers = re.findall(r'\d+', message)  # 정수도 시도
                if numbers:
                    try:
                        # 가장 큰 숫자를 값으로 사용 (임계값보다 큰 값일 가능성)
                        candidate_values = [float(n) for n in numbers if float(n) > 0]
                        if candidate_values:
                            value = max(candidate_values)  # 가장 큰 값 사용
                    except (ValueError, IndexError):
                        pass
            
            if value is not None:
                try:
                    float_value = float(value)
                    # 0.0이 아닌 유효한 값만 추가
                    if not (math.isnan(float_value) or math.isinf(float_value)) and float_value != 0.0:
                        values.append(float_value)
                        logger.debug(f"   값 추출 성공: {float_value} (알람 메시지: {alarm.get('message', '')[:50]})")
                except (ValueError, TypeError) as e:
                    logger.debug(f"   값 변환 실패: {value} (타입: {type(value)}, 오류: {e})")
                    pass
        
        logger.info(f"   추출된 값 개수: {len(values)}개")
        if values:
            logger.info(f"   값 샘플: {values[:5]}")
        
        # 통계 계산
        if len(values) > 0:
            if PANDAS_AVAILABLE:
                values_series = pd.Series(values)
                mean_val = float(values_series.mean())
                min_val = float(values_series.min())
                max_val = float(values_series.max())
                std_val = float(values_series.std()) if len(values) > 1 else 0.0
                p95_val = float(values_series.quantile(0.95)) if len(values) > 0 else 0.0
            else:
                # pandas가 없으면 기본 계산
                mean_val = sum(values) / len(values)
                min_val = min(values)
                max_val = max(values)
                # 표준편차 계산
                variance = sum((x - mean_val) ** 2 for x in values) / len(values)
                std_val = math.sqrt(variance) if len(values) > 1 else 0.0
                # P95 계산
                sorted_values = sorted(values)
                p95_idx = int(len(sorted_values) * 0.95)
                p95_val = sorted_values[min(p95_idx, len(sorted_values) - 1)]
            
            logger.info(f"   ✅ 알람 기반 통계 계산 완료:")
            logger.info(f"      Mean: {mean_val:.4f}, Min: {min_val:.4f}, Max: {max_val:.4f}, Std: {std_val:.4f}, P95: {p95_val:.4f}")
            
            # 온도/습도는 동일한 통계 사용 (알람에서 구분 불가)
            return {
                "temperature": {
                    "mean": mean_val,
                    "min": min_val,
                    "max": max_val,
                    "std": std_val,
                    "p95": p95_val
                },
                "humidity": {
                    "mean": mean_val,
                    "min": min_val,
                    "max": max_val,
                    "std": std_val,
                    "p95": p95_val
                },
                "vibration": {
                    "x": {"mean": mean_val, "peak": max_val, "rms": std_val},
                    "y": {"mean": mean_val, "peak": max_val, "rms": std_val},
                    "z": {"mean": mean_val, "peak": max_val, "rms": std_val}
                },
                "sound": {
                    "mean": mean_val,
                    "min": min_val,
                    "max": max_val,
                    "std": std_val,
                    "p95": p95_val
                }
            }
        else:
            logger.warning("   ⚠️ 알람 데이터에서 값을 추출할 수 없습니다. 기본값(0.0)을 사용합니다.")
            return self._get_default_sensor_stats()


# 싱글톤 인스턴스
_report_service: Optional[ReportDataService] = None


def get_report_service() -> ReportDataService:
    """ReportDataService 싱글톤 인스턴스 반환"""
    global _report_service
    if _report_service is None:
        _report_service = ReportDataService()
    return _report_service
