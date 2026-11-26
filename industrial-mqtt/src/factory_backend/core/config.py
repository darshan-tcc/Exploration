"""Core configuration module loading environment variables via Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    # PostgreSQL Database
    POSTGRES_USER: str = "factory_user"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = "factory_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5434
    DATABASE_URL: str = "postgresql+asyncpg://factory_user@/factory_db?host=/tmp&port=5434"

    # Architecture A: Factory API Integration
    FACTORY_API_BASE_URL: str = "http://localhost:8005/api/v1"
    FACTORY_API_KEY: str = "plant-secret-api-token-2026"
    FACTORY_API_POLL_INTERVAL_SECONDS: float = 3.0

    # Architecture B: MQTT Broker Configuration
    MQTT_BROKER_HOST: str = "localhost"
    MQTT_BROKER_PORT: int = 1883
    MQTT_USERNAME: str = "backend_service"
    MQTT_PASSWORD: str = "backend_pass_secure"
    MQTT_CLIENT_ID: str = "factory_backend_subscriber"
    MQTT_TOPIC_TELEMETRY: str = "plant/+/+/telemetry"
    MQTT_TOPIC_SPARKPLUG: str = "spBv1.0/+/+/+"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
