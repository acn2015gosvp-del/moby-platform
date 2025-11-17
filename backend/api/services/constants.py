from enum import Enum

class Severity(str, Enum):
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"

class AlertLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

SEVERITY_TO_LEVEL_MAP = {
    Severity.NORMAL: AlertLevel.INFO,
    Severity.WARNING: AlertLevel.WARNING,
    Severity.CRITICAL: AlertLevel.CRITICAL,
}

class Defaults:
    SENSOR_ID = "unknown_sensor"
    SOURCE = "alert-engine"
    MESSAGE = "Anomaly detected"
    ALERT_ID_PREFIX = "anomaly-"

class ValidationMessages:
    VECTOR_EMPTY = "Vector must not be empty"
    MISSING_THRESHOLDS = "Either 'threshold' or both 'warning_threshold' and 'critical_threshold' must be provided"