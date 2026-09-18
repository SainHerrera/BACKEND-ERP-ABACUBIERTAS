from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEV_JWT_SECRET = "change-me-in-production-use-a-random-32-bytes-secret"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"

    database_url: str = (
        "postgresql+psycopg2://erpdb:erpdev_secret_2025@db:5432/erpdatabase"
    )

    jwt_secret_key: str = DEV_JWT_SECRET
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    allow_registration: bool = True
    cors_origins: str = "http://localhost:5173,http://localhost:8080"

    admin_email: str = "admin_user@abacubiertas.com"
    admin_password: str = "B7eRc5qsqKFnDU5HZubRoU1L"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @model_validator(mode="after")
    def _validar_secret_en_produccion(self) -> "Settings":
        if self.environment.lower() == "production" and self.jwt_secret_key == DEV_JWT_SECRET:
            raise ValueError(
                "JWT_SECRET_KEY no puede ser el valor por defecto en producción. "
                "Genera uno con: python -c \"import secrets; print(secrets.token_urlsafe(48))\""
            )
        if self.environment.lower() == "production" and len(self.jwt_secret_key) < 32:
            raise ValueError("JWT_SECRET_KEY debe tener al menos 32 caracteres en producción.")
        return self


settings = Settings()