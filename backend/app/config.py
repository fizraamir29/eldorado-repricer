"""
Central configuration for the repricing bot backend.
All values are loaded from environment variables (see .env.example).
"""
# pyrefly: ignore [missing-import]
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- Database ---
    database_url: str = "postgresql+asyncpg://repricer:repricer@db:5432/repricer"

    # --- Security ---
    # Fernet key used to encrypt marketplace API credentials at rest.
    # Generate one with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    encryption_key: str = "CHANGE_ME_GENERATE_A_REAL_FERNET_KEY"
    jwt_secret: str = "CHANGE_ME_JWT_SECRET"
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 60 * 24 * 365  # 1 year session

    # --- Marketplace API ---
    # Eldorado does not publish public developer docs. These values must be
    # filled in once the client shares their official Seller API documentation.
    marketplace_base_url: str = "https://www.eldorado.gg"  # Official Eldorado Seller API base URL
    marketplace_request_timeout_seconds: int = 15
    marketplace_max_retries: int = 3
    # How the API key gets attached to each request. Set these two from .env
    # once you know the real scheme — no code change needed.
    #   header name examples: "Authorization" or "X-API-Key"
    #   scheme examples: "Bearer" (goes before the key) or "" (raw key, no scheme prefix)
    marketplace_auth_header_name: str = "Authorization"
    marketplace_auth_scheme: str = "Bearer"

    # --- Scheduler ---
    default_check_interval_minutes: int = 5

    # --- App environment ---
    # "development" auto-creates tables on startup for convenience.
    # "production" expects you to have run `alembic upgrade head` yourself.
    environment: str = "development"
    single_admin_mode: bool = True

    # Comma-separated list, e.g. "https://yourdashboard.com,https://app.yourdashboard.com"
    cors_allowed_origins: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()]

    model_config = {"env_file": ".env"}


settings = Settings()
