from pydantic import BaseSettings

class Settings(BaseSettings):
    MQTT_HOST: str = "localhost"
    MQTT_PORT: int = 1883

    INFLUX_URL: str = "http://localhost:8086"
    INFLUX_TOKEN: str = "your-token"
    INFLUX_ORG: str = "your-org"

    OPENAI_API_KEY: str = "your-api-key"

settings = Settings()
