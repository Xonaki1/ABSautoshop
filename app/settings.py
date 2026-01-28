from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = (
        "postgresql+asyncpg://autoshop:autoshop@localhost:5432/autoshop"
    )

    jwt_secret: str = "change-me"
    jwt_issuer: str = "autoshop"
    jwt_audience: str = "autoshop-clients"
    jwt_expires_minutes: int = 60

    supplier_api_base_url: str = ""
    supplier_auth: str = ""
    supplier_login: str = ""
    supplier_password: str = ""
    supplier_agreement_id: int | None = None


settings = Settings()
