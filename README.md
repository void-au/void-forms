# Void Forms

## Overview

Form API service for static sites.

It exposes one endpoint (`/v1/forms`) with:
- Cloudflare Turnstile verification
- site-level validation rules
- Redis-backed rate limiting
- Telegram bot notifications
- MongoDB submission storage (document-based, flexible fields)

## API

- `POST /v1/forms`
- `GET /health`

`/v1/forms` accepts:
- `site_id`
- `cloudflare_token`
- standard fields: `first_name`, `last_name`, `company`, `message`, `email`, `dropdown`
- optional extensible `custom_fields` object

## Project Structure

```
app/
	api/
	core/
	models/
	services/
config/
	sites.json
data/
tests/
docs/
```

## Environment

Copy `.env.example` into your local `.env` and set values.

Main vars:
- `SITES_CONFIG_PATH` (default: `config/sites.json`)
- `MONGODB_URL` (default: `mongodb://localhost:27017`)
- `MONGODB_DATABASE` (default: `void_forms`)
- `MONGODB_COLLECTION` (default: `submissions`)
- `RATE_LIMIT_WINDOW_SECONDS`
- `RATE_LIMIT_MAX_REQUESTS`
- `RATE_LIMIT_REDIS_URL` (example: `redis://localhost:6379/0`)
- `TURNSTILE_VERIFY_URL`
- `TURNSTILE_BYPASS` (set to `true` for local testing only)
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_DEFAULT_CHAT_ID`

## Local Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

If `pip` is missing on your system:

```bash
sudo apt update && sudo apt install -y python3-pip python3-venv
```

## Run

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Health check:

```bash
curl http://localhost:8000/health
```

## Run With Docker Compose

```bash
docker compose --profile app up --build
```

This starts:
- `api` on `http://localhost:8000`
- `redis` on `localhost:6379`
- `mongodb` on `localhost:27017`

Stop services:

```bash
docker compose down
```

## Run Infra Only

If you want to run the API directly on your machine and only use containers for MongoDB and Redis:

```bash
docker compose --profile infra up -d
```

Use these local environment values for the API process on your host:

```bash
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=void_forms
MONGODB_COLLECTION=submissions
RATE_LIMIT_REDIS_URL=redis://localhost:6379/0
```

Then start the API locally:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Stop infra containers:

```bash
docker compose down
```

## Example Request

```bash
curl -X POST http://localhost:8000/v1/forms \
	-H 'Content-Type: application/json' \
	-d '{
		"site_id": "demo-site",
		"cloudflare_token": "turnstile-token",
		"first_name": "Ada",
		"last_name": "Lovelace",
		"company": "Analytical Engine",
		"message": "I want to learn more.",
		"email": "ada@example.com",
		"dropdown": "sales",
		"custom_fields": {
			"budget": "5000"
		}
	}'
```

## Test

```bash
pytest -q
```

## Notes

- `config/sites.json` is the source of truth for site validation and Turnstile secrets.
- Telegram failures do not fail form ingestion; they are returned as a warning in success responses.
- Submissions are stored in MongoDB for flexible/expandable document fields.
- Rate limiting is stored in Redis so limits work across multiple API instances.

