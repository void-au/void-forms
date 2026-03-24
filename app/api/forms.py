import logging

from fastapi import APIRouter, Request

from app.core.errors import ApiError
from app.models.forms import ApiResponse, FormSubmissionRequest
from app.services.rate_limiter import RateLimiterUnavailable
from app.services.submission_store import SubmissionStoreUnavailable
from app.services.validation_service import validate_submission

logger = logging.getLogger(__name__)

router = APIRouter()


def _extract_turnstile_token(request: Request, required: bool) -> str:
    authorization = request.headers.get("authorization", "")
    if not authorization.strip():
        if required:
            raise ApiError(
                400,
                "invalid_authorization_header",
                "Authorization header must use Bearer token format",
                details=[{"field": "authorization", "message": "missing_or_invalid_bearer_token"}],
            )
        return ""

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        if not required:
            return ""
        raise ApiError(
            400,
            "invalid_authorization_header",
            "Authorization header must use Bearer token format",
            details=[{"field": "authorization", "message": "missing_or_invalid_bearer_token"}],
        )
    return token.strip()


@router.post("/v1/forms", response_model=ApiResponse)
async def submit_form(payload: FormSubmissionRequest, request: Request) -> dict:
    request_id = request.state.request_id
    client_ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip() or (
        request.client.host if request.client else None
    )

    site_registry = request.app.state.site_registry
    rate_limiter = request.app.state.rate_limiter
    turnstile_verifier = request.app.state.turnstile_verifier
    telegram_notifier = request.app.state.telegram_notifier
    submission_store = request.app.state.submission_store
    settings = request.app.state.settings

    site = site_registry.get_site(payload.site_id)
    if site is None:
        raise ApiError(404, "site_not_found", "No site configuration found for site_id")

    require_turnstile_token = not (settings.dev_mode or settings.turnstile_bypass)
    turnstile_token = _extract_turnstile_token(request, required=require_turnstile_token)

    limiter_key = f"{payload.site_id}:{client_ip}"
    try:
        allowed = await rate_limiter.allow(limiter_key)
    except RateLimiterUnavailable:
        raise ApiError(503, "rate_limiter_unavailable", "Rate limiter unavailable")

    if not allowed:
        raise ApiError(429, "rate_limited", "Rate limit exceeded")

    turnstile_ok, turnstile_error = await turnstile_verifier.verify_token(
        secret=site.turnstile_secret,
        token=turnstile_token,
        remote_ip=client_ip,
    )
    if not turnstile_ok:
        raise ApiError(
            400,
            "turnstile_failed",
            "Cloudflare Turnstile verification failed",
            details=[{"field": "authorization", "message": turnstile_error or "invalid"}],
        )

    attributes = payload.normalized_payload()
    validation_errors = validate_submission(attributes, site)
    if validation_errors:
        raise ApiError(
            422,
            "validation_failed",
            "Submission failed site validation",
            details=validation_errors,
        )

    try:
        submission_id = submission_store.save_submission(
            site_id=payload.site_id,
            ip_address=client_ip,
            payload=attributes,
        )
    except SubmissionStoreUnavailable:
        raise ApiError(503, "submission_store_unavailable", "Submission store unavailable")

    notification_sent, notification_error = await telegram_notifier.send_notification(
        site_id=payload.site_id,
        payload=attributes,
        chat_id=site.telegram_chat_id,
    )

    logger.info(
        "form_submission_processed",
        extra={
            "request_id": request_id,
            "site_id": payload.site_id,
            "submission_id": submission_id,
            "notification_sent": notification_sent,
            "notification_error": notification_error,
        },
    )

    return {
        "ok": True,
        "request_id": request_id,
        "data": {
            "submission_id": submission_id,
            "notification_sent": notification_sent,
            "warning": notification_error,
        },
        "error": None,
    }
