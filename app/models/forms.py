from typing import Any

from pydantic import BaseModel, ConfigDict


class FormSubmissionRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    site_id: str

    def normalized_payload(self) -> dict[str, Any]:
        return self.model_dump(exclude_none=True, exclude={"site_id"})


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
