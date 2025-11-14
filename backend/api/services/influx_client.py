from influxdb_client import InfluxDBClient, Point
from core.config import settings

client = InfluxDBClient(
    url=settings.INFLUX_URL,
    token=settings.INFLUX_TOKEN,
    org=settings.INFLUX_ORG
)

def write_point(bucket: str, measurement: str, fields: dict, tags: dict):
    p = Point(measurement)
    for k, v in fields.items():
        p.field(k, v)
    for k, v in tags.items():
        p.tag(k, v)
    w = client.write_api()
    w.write(bucket=bucket, record=p)
