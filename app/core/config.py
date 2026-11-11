from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Appointment & Booking API"
    APP_ENV: str = "development"
    DATABASE_URL: str
    SUPABASE_URL: Optional[str] = None
    SUPABASE_KEY: Optional[str] = None
    TEST_BASE_URL: str = "http://localhost:8000"

    # Must match the secret used by auths_service so its access tokens
    # can be verified here.
    JWT_SECRET: str = "your-jwt-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"

    # Shared secret for service-to-service calls to /internal endpoints.
    INTERNAL_API_KEY: str = "internal-secret-key"

    ENVIRONMENT: str = "development"  # "development" or "production" (production disables /docs)

    # Explicit list of browser origins; empty means no cross-origin access.
    ALLOWED_ORIGINS: list[str] = ["*"]

    # Brevo (Sendinblue) Transactional Email Configuration
    BREVO_API_KEY: Optional[str] = None
    BREVO_SENDER_EMAIL: str = "noreply@sronoh.com"
    BREVO_SENDER_NAME: str = "Sronoh Portal"
    BREVO_SMTP_LOGIN: Optional[str] = None
    BREVO_SMTP_HOST: str = "smtp-relay.brevo.com"
    BREVO_SMTP_PORT: int = 587

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
