from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class ApiError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: list[dict[str, str]] | None = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details


def _request_id_from_request(request: Request) -> str:
    return getattr(request.state, "request_id", "unknown")


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def handle_api_error(request: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "ok": False,
                "request_id": _request_id_from_request(request),
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                },
            },
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        details = []
        for err in exc.errors():
            details.append(
                {
                    "field": ".".join(str(part) for part in err.get("loc", [])),
                    "message": err.get("msg", "invalid_request"),
                }
            )
        return JSONResponse(
            status_code=422,
            content={
                "ok": False,
                "request_id": _request_id_from_request(request),
                "error": {
                    "code": "invalid_request",
                    "message": "Request body validation failed",
                    "details": details,
                },
            },
        )

    @app.exception_handler(Exception)
    async def handle_generic_error(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "request_id": _request_id_from_request(request),
                "error": {
                    "code": "internal_error",
                    "message": "Unexpected server error",
                    "details": None,
                },
            },
        )
