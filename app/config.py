from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str = "sqlite:///./hamsa_dev.db"
    telegram_bot_token: str = ""
    telegram_admin_ids: str = ""
    dashboard_access_token: str = ""
    live_feed_webhook_secret: str = ""
    feed_stale_after_seconds: int = 300
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
