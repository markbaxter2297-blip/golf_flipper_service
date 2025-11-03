# Golf Flipper Notifier Service

This service monitors new golf-related listings on eBay and Vinted, evaluates their potential profit for reselling, and notifies you via WhatsApp when opportunities arise. The project is designed to be easy to deploy with minimal setup.

## Features

* Polls eBay and Vinted for new golf listings using configurable keywords and categories.
* Computes the total acquisition cost (item price + buyer protection + shipping) and estimated resale value based on configurable rules or multipliers.
* Determines potential profit and risk level; sends a WhatsApp alert when the profit exceeds a threshold.
* Deduplicates notifications so you never receive the same alert twice.
* Provides a small FastAPI server with health and test alert endpoints.
* Configured entirely via environment variables with no secrets in code.
* Deployable locally via Docker or to cloud providers like Render, Railway, or Fly.io.

## Quick start

### 1. Clone and enter the repo

```bash
git clone <this-repo-url>.git
cd golf_flipper_service
```

### 2. Create and fill the `.env` file

Copy the provided `.env.example` to `.env` and fill in the required secrets. At a minimum you’ll need:

* **WhatsApp Cloud API**: a Meta access token (`WHATSAPP_ACCESS_TOKEN`) and a phone number ID (`WHATSAPP_PHONE_NUMBER_ID`).
* **eBay**: App ID and Cert ID to fetch a Browse API token (`EBAY_APP_ID`, `EBAY_CERT_ID`, `EBAY_REDIRECT_URI`).
* **Optional Vinted cookie** (`VINTED_COOKIE`) if you want to enable Vinted polling.

If you don’t have these yet, follow the [minimal setup checklist](#minimal-setup-checklist) below.

### 3. Build and run locally with Docker

This project includes a `Dockerfile` and `docker-compose.yml` for local development. Run:

```bash
docker compose up --build
```

The service will start on `http://localhost:8080`. It will begin polling for listings in the background according to the `POLL_INTERVAL_SECONDS` environment variable (default every 300 seconds). You can send yourself a test alert using:

```bash
curl -X POST http://localhost:8080/test-alert
```

### 4. Deploy to a cloud host (optional)

This service can be deployed to any platform that can run Docker containers. For example, to deploy on Render:

1. Create a new Web Service on Render and connect your repository.
2. Set the environment to **Docker** and expose port `8080`.
3. Copy the contents of your local `.env` file into the environment variables section in Render.
4. Enable a background cron job or worker to hit the `/health` endpoint every 5 minutes to keep the service alive and ensure polling runs. Alternatively, schedule an external uptime monitor to ping it.

Refer to Render or your chosen platform’s documentation for specifics.

## Configuration

All configuration is handled via environment variables. See `.env.example` for a complete list. Important settings include:

* `KEYWORDS` – comma-separated search terms used for both eBay and Vinted.
* `EBAY_CATEGORY_IDS` – comma-separated eBay category IDs to narrow the search.
* `PROFIT_THRESHOLD_GBP` – minimum profit required to trigger a notification.
* `POLL_INTERVAL_SECONDS` – how often to poll the marketplaces.
* `WHATSAPP_TO_MSISDN` – your WhatsApp phone number in international format (e.g. `+447956909367`).
* `VINTED_ENABLED` – set to `false` if you don’t want to poll Vinted.

You can also modify or extend the resale rules by editing `rules.json`. This file contains brand- and model-specific multipliers or fixed target values. If an item matches a rule, that rule’s resale value will be used; otherwise, the base multiplier applies.

## API Endpoints

| Method | Path        | Description                                   |
|-------:|------------ |-----------------------------------------------|
| `GET`  | `/health`   | Returns a simple JSON indicating service health. |
| `POST` | `/test-alert` | Sends a sample WhatsApp message to verify configuration. |

## Minimal setup checklist

Follow these steps to prepare the necessary credentials before deploying the service:

1. **Create a Meta Developer account** and set up a **WhatsApp Cloud API** application. Obtain:
   * A **permanent access token** (`WHATSAPP_ACCESS_TOKEN`).
   * A **phone number ID** (`WHATSAPP_PHONE_NUMBER_ID`).
   * (Optional) Use Meta’s test phone number if you haven’t set up your own number yet.
2. **Register an eBay developer application**. From the eBay developer portal:
   * Create an application and note your **App ID** (`EBAY_APP_ID`), **Cert ID** (`EBAY_CERT_ID`), and **Redirect URI** (`EBAY_REDIRECT_URI`).
   * You’ll need these to request an OAuth token for the Browse API.
3. (Optional) **Enable Vinted polling**:
   * Visit Vinted in your browser, log in if necessary, and obtain your `vinted_v2` cookie. Copy the entire cookie value into the `VINTED_COOKIE` variable.
4. **Fill out the `.env` file** with all the above credentials and your own phone number (`WHATSAPP_TO_MSISDN`).
5. **Deploy or run locally** using Docker.
6. **Send a test alert** via `POST /test-alert` to confirm WhatsApp notifications.

## Troubleshooting

* **No WhatsApp messages received** – Double-check your Meta token and phone number ID. Ensure the receiving number is registered with WhatsApp and that the number you configured in `WHATSAPP_TO_MSISDN` is correct and in international format.
* **eBay API errors** – Make sure your eBay credentials are correct and that your application has access to the Browse API. Check your current usage limits; eBay imposes call quotas.
* **Vinted requests failing** – If Vinted detection is enabled, verify that your cookie is up to date. Vinted may revoke cookies regularly, so you might need to refresh it periodically.
* **Duplicate notifications** – The service stores sent alerts in a SQLite database; if you delete the `DB_PATH` file or clear the database, it will forget previously processed items.
