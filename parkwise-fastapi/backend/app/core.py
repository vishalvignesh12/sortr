from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./parkwise_dev.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    PREDICTOR_URL: str = 'http://predictor:8080'
    EDGE_API_KEY: str
    HOST: str = '0.0.0.0'
    PORT: int = 8000
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    LOG_LEVEL: str = 'INFO'
    DEBUG: bool = False

    model_config = SettingsConfigDict(
        env_file='.env',
        case_sensitive=True
    )

settings = Settings()
