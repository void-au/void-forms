from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


class AllowAllRateLimiter:
    async def allow(self, key: str) -> bool:
        return True

    async def close(self) -> None:
        return None


class OneShotRateLimiter:
    def __init__(self):
        self._count = 0

    async def allow(self, key: str) -> bool:
        self._count += 1
        return self._count <= 1

    async def close(self) -> None:
        return None


class InMemorySubmissionStore:
    def __init__(self):
        self._count = 0

    def save_submission(self, site_id: str, ip_address: str | None, payload: dict) -> str:
        self._count += 1
        return f"sub_{self._count}"


class StubNotificationService:
    async def send_submission_notification(
        self,
        site,
        payload: dict,
    ) -> tuple[bool, str | None]:
        return True, None


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("SITES_CONFIG_PATH", "config/sites.yaml")
    monkeypatch.setenv("TURNSTILE_SECRET_DEMO_SITE", "test-secret")
    monkeypatch.setenv("MONGODB_URL", "mongodb://localhost:27017")
    monkeypatch.setenv("MONGODB_DATABASE", "void_forms_test")
    monkeypatch.setenv("MONGODB_COLLECTION", "submissions")
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "1")
    monkeypatch.setenv("RATE_LIMIT_PER_HOUR", "3")
    monkeypatch.setenv("RATE_LIMIT_REDIS_URL", "redis://localhost:6379/15")
    monkeypatch.setenv("TURNSTILE_BYPASS", "true")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "")
    monkeypatch.setenv("TELEGRAM_DEFAULT_CHAT_ID", "")

    app = create_app()
    with TestClient(app) as test_client:
        test_client.app.state.rate_limiter = AllowAllRateLimiter()
        test_client.app.state.notification_service = StubNotificationService()
        test_client.app.state.submission_store = InMemorySubmissionStore()
        yield test_client


def _base_payload() -> dict:
    return {
        "site_id": "void-labs",
        "first_name": "Ada",
        "last_name": "Lovelace",
        "message": "I want to know more about your API.",
        "email": "ada@example.com",
        "company": "Analytical Engine",
        "area-of-interest": "web",
    }


def _auth_headers(token: str = "dummy-token") -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_happy_path_submission(client: TestClient):
    response = client.post("/v1/forms", json=_base_payload(), headers=_auth_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["data"]["submission_id"]


def test_invalid_site_returns_404(client: TestClient):
    payload = _base_payload()
    payload["site_id"] = "unknown-site"

    response = client.post("/v1/forms", json=payload, headers=_auth_headers())

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "site_not_found"


def test_disallowed_attributes_returns_422(client: TestClient):
    payload = _base_payload()
    payload["unauthorized_field"] = "x"

    response = client.post("/v1/forms", json=payload, headers=_auth_headers())

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_failed"


def test_turnstile_failure_returns_400(client: TestClient):
    async def failing_verify_token(secret: str, token: str, remote_ip: str | None):
        return False, "invalid-input-response"

    client.app.state.turnstile_verifier.verify_token = failing_verify_token
    response = client.post("/v1/forms", json=_base_payload(), headers=_auth_headers())

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "turnstile_failed"


def test_rate_limit_exceeded_returns_429(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("SITES_CONFIG_PATH", "config/sites.yaml")
    monkeypatch.setenv("TURNSTILE_SECRET_DEMO_SITE", "test-secret")
    monkeypatch.setenv("MONGODB_URL", "mongodb://localhost:27017")
    monkeypatch.setenv("MONGODB_DATABASE", "void_forms_test")
    monkeypatch.setenv("MONGODB_COLLECTION", "submissions")
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "1")
    monkeypatch.setenv("RATE_LIMIT_PER_HOUR", "3")
    monkeypatch.setenv("RATE_LIMIT_REDIS_URL", "redis://localhost:6379/15")
    monkeypatch.setenv("TURNSTILE_BYPASS", "true")

    app = create_app()
    with TestClient(app) as test_client:
        test_client.app.state.rate_limiter = OneShotRateLimiter()
        test_client.app.state.notification_service = StubNotificationService()
        test_client.app.state.submission_store = InMemorySubmissionStore()
        first = test_client.post("/v1/forms", json=_base_payload(), headers=_auth_headers())
        second = test_client.post("/v1/forms", json=_base_payload(), headers=_auth_headers())

    assert first.status_code == 200
    assert second.status_code == 429
    assert second.json()["error"]["code"] == "rate_limited"


def test_telegram_failure_does_not_fail_submission(client: TestClient):
    async def failing_send_submission_notification(site, payload: dict):
        return False, "telegram_http_error"

    client.app.state.notification_service.send_submission_notification = (
        failing_send_submission_notification
    )
    response = client.post("/v1/forms", json=_base_payload(), headers=_auth_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["data"]["notification_sent"] is False
    assert body["data"]["warning"] == "telegram_http_error"


def test_missing_authorization_header_returns_400(client: TestClient):
    response = client.post("/v1/forms", json=_base_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True


def test_invalid_authorization_header_returns_400(client: TestClient):
    response = client.post(
        "/v1/forms",
        json=_base_payload(),
        headers={"Authorization": "Token dummy-token"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True


def test_missing_authorization_header_returns_400_when_dev_mode_disabled(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("SITES_CONFIG_PATH", "config/sites.yaml")
    monkeypatch.setenv("TURNSTILE_SECRET_DEMO_SITE", "test-secret")
    monkeypatch.setenv("MONGODB_URL", "mongodb://localhost:27017")
    monkeypatch.setenv("MONGODB_DATABASE", "void_forms_test")
    monkeypatch.setenv("MONGODB_COLLECTION", "submissions")
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "1")
    monkeypatch.setenv("RATE_LIMIT_PER_HOUR", "3")
    monkeypatch.setenv("RATE_LIMIT_REDIS_URL", "redis://localhost:6379/15")
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("DEV_MODE", "false")
    monkeypatch.setenv("TURNSTILE_BYPASS", "false")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "")
    monkeypatch.setenv("TELEGRAM_DEFAULT_CHAT_ID", "")

    app = create_app()
    with TestClient(app) as test_client:
        test_client.app.state.rate_limiter = AllowAllRateLimiter()
        test_client.app.state.notification_service = StubNotificationService()
        test_client.app.state.submission_store = InMemorySubmissionStore()
        response = test_client.post("/v1/forms", json=_base_payload())

    assert response.status_code == 400
    body = response.json()
    assert body["error"]["code"] == "invalid_authorization_header"
    assert body["error"]["details"] == [
        {"field": "authorization", "message": "missing_or_invalid_bearer_token"}
    ]
