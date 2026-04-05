
# Notification Service

A centralized, highly scalable Notification Service that delivers notifications across multiple channels (Email, SMS, Push) with priority support and robust delivery tracking.

## Overview

This backend application handles incoming notification requests asynchronously. It validates user preferences, renders Jinja2 templates, applies per-user rate limiting, and dispatches messages to mocked delivery providers via Celery and Redis.

## Tech Stack

- **Framework**: FastAPI (High performance, async support natively, auto-generation of OpenAPI spec).
- **Database**: PostgreSQL with SQLAlchemy ORM.
- **Message Broker & Cache**: Redis (Used for Celery task queuing, and for atomic rate-limiting checks).
- **Task Queue**: Celery (Built-in retry strategies with exponential backoff and multiple queue routing mapping to priorities).
- **Templating Engine**: Jinja2.

## Setup Instructions (Local Development)

### Prerequisites

- Docker and Docker Compose installed.

### Running with Docker

1. Clone the repository and navigate to the root directory `notification_service/`.
2. Start the services:
   ```bash
   docker compose up --build
   ```
3. This spins up four containers:
   - `api`: FastAPI application on http://localhost:8000
   - `worker`: Celery background worker
   - `db`: PostgreSQL instance
   - `redis`: Redis server

### Viewing the API Docs

Navigate to `http://localhost:8000/docs` to view the interactive Swagger/OpenAPI documentation.

## Running Tests

To run tests seamlessly via Docker:

```bash
docker compose run --rm api pytest -v tests/
```

This will run all API unit/integration tests using an in-memory SQLite database to keep tests decoupled and fast.

## API Examples

### Send a Notification (Idempotent)

```bash
curl -X POST "http://localhost:8000/notifications" \
     -H "Content-Type: application/json" \
     -d '{
       "user_id": "u123",
       "channel": "email",
       "priority": "critical",
       "idempotency_key": "txn-999",
       "template_name": "welcome_email",
       "payload": {
         "name": "Jane"
       }
     }'
```

Returns `202 Accepted` with the notification ID.

### Check Status

```bash
curl -X GET "http://localhost:8000/notifications/<notification-id>"
```

### Update User Preferences

To opt a user out of SMS:
```bash
curl -X POST "http://localhost:8000/users/u123/preferences" \
     -H "Content-Type: application/json" \
     -d '{"channel": "sms", "opt_in": false}'
```

## Assumptions Made

1. **Authentication:** The assignment stated auth could be skipped or assumed to be an API Gateway responsibility. Therefore, endpoints are unauthenticated.
2. **Template Storage:** Templates are hardcoded in `MOCK_TEMPLATES` inside `app/services/template_engine.py` to simplify setup for demonstration purposes.
3. **Mock Providers:** `send_email`, `send_sms`, and `send_push` simulate network latency and randomly fail 10% of the time to demonstrate Celery's built-in exponential backoff retries.
4. **Schema Initialization:** In production, `Alembic` would handle migrations. For this demo, SQLAlchemy `Base.metadata.create_all` initializes models upon FastAPI app lifespan startup.
