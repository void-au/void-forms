from typing import Any

import httpx


class TurnstileVerifier:
    def __init__(self, verify_url: str, bypass: bool = False):
        self.verify_url = verify_url
        self.bypass = bypass

    async def verify_token(
        self,
        secret: str,
        token: str,
        remote_ip: str | None,
    ) -> tuple[bool, str | None]:
        if self.bypass:
            return True, None

        payload: dict[str, Any] = {
            "secret": secret,
            "response": token,
        }
        if remote_ip:
            payload["remoteip"] = remote_ip

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(self.verify_url, data=payload)
                response.raise_for_status()
                result = response.json()
        except httpx.TimeoutException:
            return False, "turnstile_timeout"
        except httpx.HTTPError:
            return False, "turnstile_http_error"

        if bool(result.get("success")):
            return True, None

        error_codes = result.get("error-codes") or []
        error_reason = ",".join(error_codes) if error_codes else "turnstile_verification_failed"
        return False, error_reason
