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

