from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/eventra"
    SECRET_KEY: str = "change-me-in-production-use-random-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days
    ADMIN_SECRET: str = "admin-setup-secret"
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:5174,http://localhost:5175"

    model_config = {"env_file": ".env"}

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    def model_post_init(self, __context) -> None:
        if self.ENVIRONMENT.lower() == "production":
            unsafe_values = {
                "SECRET_KEY": "change-me-in-production-use-random-32-chars",
                "ADMIN_SECRET": "admin-setup-secret",
            }
            for field, unsafe in unsafe_values.items():
                if getattr(self, field) == unsafe:
                    raise ValueError(f"{field} must be configured in production")


settings = Settings()
