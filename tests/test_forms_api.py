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


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("SITES_CONFIG_PATH", "config/sites.yaml")
    monkeypatch.setenv("TURNSTILE_SECRET_DEMO_SITE", "test-secret")
    monkeypatch.setenv("MONGODB_URL", "mongodb://localhost:27017")
    monkeypatch.setenv("MONGODB_DATABASE", "void_forms_test")
    monkeypatch.setenv("MONGODB_COLLECTION", "submissions")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_SECONDS", "60")
    monkeypatch.setenv("RATE_LIMIT_MAX_REQUESTS", "10")
    monkeypatch.setenv("RATE_LIMIT_REDIS_URL", "redis://localhost:6379/15")
    monkeypatch.setenv("TURNSTILE_BYPASS", "true")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "")
    monkeypatch.setenv("TELEGRAM_DEFAULT_CHAT_ID", "")

    app = create_app()
    with TestClient(app) as test_client:
        test_client.app.state.rate_limiter = AllowAllRateLimiter()
        test_client.app.state.submission_store = InMemorySubmissionStore()
        yield test_client


def _base_payload() -> dict:
    return {
        "site_id": "demo-site",
        "cloudflare_token": "dummy-token",
        "first_name": "Ada",
        "last_name": "Lovelace",
        "company": "Analytical Engine",
        "message": "I want to know more about your API.",
        "email": "ada@example.com",
        "dropdown": "sales",
    }


def test_happy_path_submission(client: TestClient):
    response = client.post("/v1/forms", json=_base_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["data"]["submission_id"]


def test_invalid_site_returns_404(client: TestClient):
    payload = _base_payload()
    payload["site_id"] = "unknown-site"

    response = client.post("/v1/forms", json=payload)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "site_not_found"


def test_disallowed_attributes_returns_422(client: TestClient):
    payload = _base_payload()
    payload["custom_fields"] = {"unauthorized_field": "x"}

    response = client.post("/v1/forms", json=payload)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_failed"


def test_turnstile_failure_returns_400(client: TestClient):
    async def failing_verify_token(secret: str, token: str, remote_ip: str | None):
        return False, "invalid-input-response"

    client.app.state.turnstile_verifier.verify_token = failing_verify_token
    response = client.post("/v1/forms", json=_base_payload())

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "turnstile_failed"


def test_rate_limit_exceeded_returns_429(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("SITES_CONFIG_PATH", "config/sites.yaml")
    monkeypatch.setenv("TURNSTILE_SECRET_DEMO_SITE", "test-secret")
    monkeypatch.setenv("MONGODB_URL", "mongodb://localhost:27017")
    monkeypatch.setenv("MONGODB_DATABASE", "void_forms_test")
    monkeypatch.setenv("MONGODB_COLLECTION", "submissions")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_SECONDS", "60")
    monkeypatch.setenv("RATE_LIMIT_MAX_REQUESTS", "1")
    monkeypatch.setenv("RATE_LIMIT_REDIS_URL", "redis://localhost:6379/15")
    monkeypatch.setenv("TURNSTILE_BYPASS", "true")

    app = create_app()
    with TestClient(app) as test_client:
        test_client.app.state.rate_limiter = OneShotRateLimiter()
        test_client.app.state.submission_store = InMemorySubmissionStore()
        first = test_client.post("/v1/forms", json=_base_payload())
        second = test_client.post("/v1/forms", json=_base_payload())

    assert first.status_code == 200
    assert second.status_code == 429
    assert second.json()["error"]["code"] == "rate_limited"


def test_telegram_failure_does_not_fail_submission(client: TestClient):
    async def failing_send_notification(site_id: str, payload: dict, chat_id: str | None = None):
        return False, "telegram_http_error"

    client.app.state.telegram_notifier.send_notification = failing_send_notification
    response = client.post("/v1/forms", json=_base_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["data"]["notification_sent"] is False
    assert body["data"]["warning"] == "telegram_http_error"
