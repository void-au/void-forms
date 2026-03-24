import html

import httpx


class TelegramNotifier:
    def __init__(self, bot_token: str, default_chat_id: str = ""):
        self.bot_token = bot_token
        self.default_chat_id = default_chat_id

    async def send_notification(
        self,
        site_id: str,
        payload: dict[str, object],
        chat_id: str | None = None,
    ) -> tuple[bool, str | None]:
        target_chat_id = chat_id or self.default_chat_id
        if not self.bot_token:
            return False, "telegram_not_configured"
        if not target_chat_id:
            return False, "telegram_chat_not_configured"

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        message = self._build_message(site_id, payload)
        body = {
            "chat_id": target_chat_id,
            "text": message,
            "parse_mode": "HTML",
        }

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(url, json=body)
                response.raise_for_status()
        except httpx.TimeoutException:
            return False, "telegram_timeout"
        except httpx.HTTPError:
            return False, "telegram_http_error"

        return True, None

    def _build_message(self, site_id: str, payload: dict[str, object]) -> str:
        lines = [f"<b>New form submission</b>", f"<b>site_id:</b> {html.escape(site_id)}"]
        for key, value in payload.items():
            value_text = html.escape(str(value))
            lines.append(f"<b>{html.escape(key)}:</b> {value_text}")
        return "\n".join(lines)
