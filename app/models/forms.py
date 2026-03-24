from typing import Any

from pydantic import BaseModel, EmailStr, Field


class FormSubmissionRequest(BaseModel):
    site_id: str
    cloudflare_token: str
    first_name: str | None = None
    last_name: str | None = None
    company: str | None = None
    message: str | None = None
    email: EmailStr | None = None
    dropdown: str | None = None
    custom_fields: dict[str, Any] = Field(default_factory=dict)

    def normalized_payload(self) -> dict[str, Any]:
        standard_data = self.model_dump(
            exclude_none=True,
            exclude={"site_id", "cloudflare_token", "custom_fields"},
        )
        return {**standard_data, **self.custom_fields}


class ErrorBody(BaseModel):
    code: str
    message: str
    details: list[dict[str, str]] | None = None


class SuccessData(BaseModel):
    submission_id: str
    notification_sent: bool
    warning: str | None = None


class ApiResponse(BaseModel):
    ok: bool
    request_id: str
    data: SuccessData | None = None
    error: ErrorBody | None = None
