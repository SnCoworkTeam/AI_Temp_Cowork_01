from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False

    # DB
    DB_HOST: str = "postgres"
    DB_PORT: int = 5432
    DB_USER: str = "ai_user"
    DB_PASSWORD: str = "ai_password"
    DB_NAME: str = "ai_platform"
    DATABASE_URL: str | None = None

    # Auth
    AUTH_ENABLED: bool = True
    JWT_SECRET_KEY: str = Field(default="your-secret-key-change-in-production")
    JWT_ALGORITHM: str = Field(default="HS256")

    # Uploads
    UPLOAD_DIR: str = "/app/uploads"
    MAX_UPLOAD_MB: int = 20

    class Config:
        env_file = ".env"
        case_sensitive = True

    def get_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


settings = Settings()
