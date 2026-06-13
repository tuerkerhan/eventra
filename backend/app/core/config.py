from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/eventra"
    SECRET_KEY: str = "change-me-in-production-use-random-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days
    ADMIN_SECRET: str = "admin-setup-secret"

    model_config = {"env_file": ".env"}


settings = Settings()
