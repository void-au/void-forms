from typing import Protocol

from app.models.config import SiteConfig


class NotificationProvider(Protocol):
    async def send_submission_notification(
        self,
        site: SiteConfig,
        payload: dict[str, object],
    ) -> tuple[bool, str | None]: ...


class NotificationService:
    def __init__(self, providers: list[NotificationProvider]):
        self.providers = providers

    async def send_submission_notification(
        self,
        site: SiteConfig,
        payload: dict[str, object],
    ) -> tuple[bool, str | None]:
        if not self.providers:
            return False, "notification_not_configured"

        sent_any = False
        errors: list[str] = []

        for provider in self.providers:
            sent, error = await provider.send_submission_notification(site=site, payload=payload)
            if sent:
                sent_any = True
                continue
            if error:
                errors.append(error)

        if sent_any:
            return True, ",".join(errors) if errors else None

        if errors and all("not_configured" in error for error in errors):
            return False, "notification_not_configured"

        return False, ",".join(errors) if errors else "notification_failed"