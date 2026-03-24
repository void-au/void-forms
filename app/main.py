import logging
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.forms import router as forms_router
from app.core.errors import register_exception_handlers
from app.core.settings import Settings
from app.services.config_service import SiteRegistry
from app.services.mailgun_service import MailgunNotifier
from app.services.notification_service import NotificationService
from app.services.rate_limiter import RedisFixedWindowRateLimiter
from app.services.submission_store import SubmissionStore
from app.services.telegram_service import TelegramNotifier
from app.services.turnstile_service import TurnstileVerifier


def _setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings.from_env()
    _setup_logging(settings.log_level)

    app.state.settings = settings
    app.state.site_registry = SiteRegistry.from_file(settings.sites_config_path)
    app.state.rate_limiter = RedisFixedWindowRateLimiter(
        redis_url=settings.rate_limit_redis_url,
        per_minute_limit=settings.rate_limit_per_minute,
        per_hour_limit=settings.rate_limit_per_hour,
    )
    app.state.turnstile_verifier = TurnstileVerifier(
        verify_url=settings.turnstile_verify_url,
        bypass=settings.turnstile_bypass,
    )
    app.state.notification_service = NotificationService(
        providers=[
            TelegramNotifier(
                bot_token=settings.telegram_bot_token,
                default_chat_id=settings.telegram_default_chat_id,
            ),
            MailgunNotifier(
                api_key=settings.mailgun_api_key,
                domain=settings.mailgun_domain,
                from_name=settings.mailgun_from_name,
                from_email=settings.mailgun_from_email,
                default_to_emails=settings.mailgun_default_to_emails,
            ),
        ]
    )
    app.state.submission_store = SubmissionStore(
        mongodb_url=settings.mongodb_url,
        database_name=settings.mongodb_database,
        collection_name=settings.mongodb_collection,
    )

    yield

    await app.state.rate_limiter.close()


def create_app() -> FastAPI:
    app = FastAPI(title="Void Forms API", version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["x-request-id"],
    )

    register_exception_handlers(app)

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        request_id = request.headers.get("x-request-id") or str(uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["x-request-id"] = request_id
        return response

    @app.get("/health")
    async def health() -> JSONResponse:
        return JSONResponse({"ok": True})

    app.include_router(forms_router)
    return app


app = create_app()
