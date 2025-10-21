from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./parkwise_dev.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    PREDICTOR_URL: str = 'http://predictor:8080'
    EDGE_API_KEY: str = 'dev-edge-key'  # Default for development, should be set in production
    HOST: str = '0.0.0.0'
    PORT: int = 8000
    JWT_SECRET_KEY: str = "c4dde266b5e2e9acfadaec3294a128cc"
    JWT_ALGORITHM: str = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    class Config:
        env_file = '.env'
        case_sensitive = True

settings = Settings()