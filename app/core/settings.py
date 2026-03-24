import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_env: str
    log_level: str
    sites_config_path: str
    mongodb_url: str
    mongodb_database: str
    mongodb_collection: str
    rate_limit_window_seconds: int
    rate_limit_max_requests: int
    rate_limit_redis_url: str
    turnstile_verify_url: str
    turnstile_bypass: bool
    telegram_bot_token: str
    telegram_default_chat_id: str

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            app_env=os.getenv("APP_ENV", "development"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            sites_config_path=os.getenv("SITES_CONFIG_PATH", "config/sites.json"),
            mongodb_url=os.getenv("MONGODB_URL", "mongodb://localhost:27017"),
            mongodb_database=os.getenv("MONGODB_DATABASE", "void_forms"),
            mongodb_collection=os.getenv("MONGODB_COLLECTION", "submissions"),
            rate_limit_window_seconds=int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60")),
            rate_limit_max_requests=int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "10")),
            rate_limit_redis_url=os.getenv("RATE_LIMIT_REDIS_URL", "redis://localhost:6378/0"),
            turnstile_verify_url=os.getenv(
                "TURNSTILE_VERIFY_URL",
                "https://challenges.cloudflare.com/turnstile/v0/siteverify",
            ),
            turnstile_bypass=os.getenv("TURNSTILE_BYPASS", "false").lower() == "true",
            telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
            telegram_default_chat_id=os.getenv("TELEGRAM_DEFAULT_CHAT_ID", ""),
        )
