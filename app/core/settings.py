import os
from dataclasses import dataclass

from dotenv import load_dotenv


def _env_flag(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_list(name: str) -> list[str]:
    value = os.getenv(name, "")
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    app_env: str
    log_level: str
    sites_config_path: str
    mongodb_url: str
    mongodb_database: str
    mongodb_collection: str
    rate_limit_per_minute: int
    rate_limit_per_hour: int
    rate_limit_redis_url: str
    turnstile_verify_url: str
    turnstile_bypass: bool
    telegram_bot_token: str
    telegram_default_chat_id: str
    mailgun_api_key: str
    mailgun_domain: str
    mailgun_from_name: str
    mailgun_from_email: str
    mailgun_default_to_emails: list[str]

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        app_env = os.getenv("APP_ENV", "development")
        return cls(
            app_env=app_env,
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            sites_config_path=os.getenv("SITES_CONFIG_PATH", "config/sites.yaml"),
            mongodb_url=os.getenv("MONGODB_URL", "mongodb://localhost:27017"),
            mongodb_database=os.getenv("MONGODB_DATABASE", "void_forms"),
            mongodb_collection=os.getenv("MONGODB_COLLECTION", "submissions"),
            rate_limit_per_minute=int(
                os.getenv("RATE_LIMIT_PER_MINUTE", os.getenv("RATE_LIMIT_MAX_REQUESTS", "1"))
            ),
            rate_limit_per_hour=int(os.getenv("RATE_LIMIT_PER_HOUR", "3")),
            rate_limit_redis_url=os.getenv("RATE_LIMIT_REDIS_URL", "redis://localhost:6378/0"),
            turnstile_verify_url=os.getenv(
                "TURNSTILE_VERIFY_URL",
                "https://challenges.cloudflare.com/turnstile/v0/siteverify",
            ),
            turnstile_bypass=_env_flag("TURNSTILE_BYPASS", False),
            telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
            telegram_default_chat_id=os.getenv("TELEGRAM_DEFAULT_CHAT_ID", ""),
            mailgun_api_key=os.getenv("MAILGUN_API_KEY", ""),
            mailgun_domain=os.getenv("MAILGUN_DOMAIN", ""),
            mailgun_from_name=os.getenv("MAILGUN_FROM_NAME", "Void Forms"),
            mailgun_from_email=os.getenv("MAILGUN_FROM_EMAIL", ""),
            mailgun_default_to_emails=_env_list("MAILGUN_DEFAULT_TO_EMAILS"),
        )
