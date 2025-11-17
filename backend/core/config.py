# settings 객체가 있어야 pytest가 모듈 임포트에 성공합니다.
class Settings:
    # 테스트에 필요한 기본 값
    MQTT_HOST = "test.broker"
    MQTT_PORT = 1883
    
    # InfluxDB 설정 
    INFLUX_URL = "http://localhost:8086"
    INFLUX_TOKEN = "test_token"
    INFLUX_ORG = "moby_org"

settings = Settings()