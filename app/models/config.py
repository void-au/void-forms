from pydantic import BaseModel, Field


class ValidationRule(BaseModel):
    required: bool = False
    min_length: int | None = None
    max_length: int | None = None
    regex: str | None = None
    options: list[str] = Field(default_factory=list)
    type: str = "string"


class SiteConfig(BaseModel):
    site_id: str
    allowed_attributes: set[str]
    validation: dict[str, ValidationRule] = Field(default_factory=dict)
    turnstile_secret: str | None = None
    turnstile_secret_env: str | None = None
    telegram_chat_id: str | None = None


class SitesConfig(BaseModel):
    sites: list[SiteConfig]
