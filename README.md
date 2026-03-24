# Void Forms

A barebones, secure application that accepts forms from static sites and sends a Telegram message.

Extendable, expandable, robust.

Keep the .env for configuration (edit `.env` before running).

Getting started (local dev):

- Start infra (MongoDB + Redis):

```bash
docker compose --profile infra up -d
```

- Run the API locally:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Production one-liner:

```bash
docker compose --profile app up -d --build
```

That's it — edit `.env` to add your secrets (Turnstile, Telegram) before running.

Form submissions must send the Cloudflare Turnstile token in the `Authorization` header as `Bearer <token>`, not in the JSON body.

The request body only requires `site_id`. Any other submitted form fields are accepted dynamically at the top level and then validated against the matching site rules in `config/sites.yaml`.

When `DEV_MODE=true` or `TURNSTILE_BYPASS=true`, the API accepts form submissions without an `Authorization` header so local and preview environments can work without a Turnstile token. In production, keep both disabled so the bearer token is required.

Rate limiting is applied per `site_id` and client IP: by default the API allows 1 submission per minute and 3 submissions per hour.

Notifications are provider-based. Telegram is supported, and Mailgun is now supported as well. Mailgun can use `MAILGUN_DEFAULT_TO_EMAILS` from the environment or per-site `mailgun_to_emails` values in `config/sites.yaml`.

