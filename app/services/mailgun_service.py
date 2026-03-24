import html

import httpx

from app.models.config import SiteConfig


class MailgunNotifier:
    def __init__(
        self,
        api_key: str,
        domain: str,
        from_name: str,
        from_email: str,
        default_to_emails: list[str] | None = None,
    ):
        self.api_key = api_key
        self.domain = domain
        self.from_name = from_name
        self.from_email = from_email or (f"postmaster@{domain}" if domain else "")
        self.default_to_emails = default_to_emails or []

    async def send_submission_notification(
        self,
        site: SiteConfig,
        payload: dict[str, object],
    ) -> tuple[bool, str | None]:
        if not self.api_key or not self.domain:
            return False, "mailgun_not_configured"
        if not self.from_email:
            return False, "mailgun_sender_not_configured"

        recipients = site.mailgun_to_emails or self.default_to_emails
        if not recipients:
            return False, "mailgun_recipient_not_configured"

        url = f"https://api.mailgun.net/v3/{self.domain}/messages"
        body = {
            "from": self._build_from_header(),
            "to": ", ".join(recipients),
            "subject": f"New form submission: {site.site_id}",
            "text": self._build_submission_text(site.site_id, payload),
            "html": self._build_submission_html(site.site_id, payload),
        }

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(url, data=body, auth=("api", self.api_key))
                response.raise_for_status()
        except httpx.TimeoutException:
            return False, "mailgun_timeout"
        except httpx.HTTPError:
            return False, "mailgun_http_error"

        return True, None

    def _build_from_header(self) -> str:
        if self.from_name:
            return f"{self.from_name} <{self.from_email}>"
        return self.from_email

    def _build_submission_text(self, site_id: str, payload: dict[str, object]) -> str:
        lines = ["New form submission", f"site_id: {site_id}"]
        for key, value in payload.items():
            lines.append(f"{key}: {value}")
        return "\n".join(lines)

    def _build_submission_html(self, site_id: str, payload: dict[str, object]) -> str:
        items = [
            "<h2>New form submission</h2>",
            f"<p><strong>site_id:</strong> {html.escape(site_id)}</p>",
            "<ul>",
        ]
        for key, value in payload.items():
            items.append(
                f"<li><strong>{html.escape(key)}:</strong> {html.escape(str(value))}</li>"
            )
        items.append("</ul>")
        return "".join(items)