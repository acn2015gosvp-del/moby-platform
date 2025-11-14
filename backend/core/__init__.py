from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 기본 설정
    app_name: str = "MOBY PdM Backend"
    environment: str = "dev"

    # CORS
    cors_allow_origins: list[str] = ["*"]

    # JWT
    jwt_secret_key: str = "change-me-in-.env"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expires_minutes: int = 60

    # DB (지금은 실제로 사용하진 않지만, 나중 확장용)
    database_url: str = "sqlite:///./moby.db"

    # OpenAI / LLM
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
