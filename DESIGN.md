# DESIGN.md

## High-Level Architecture Diagram

```
[ Client ] ---> [ FastAPI Application (Rate Limiter inside) ] ---> [ PostgreSQL DB ]
                          |                                             ^
                          | (Pushes task -> `critical/high...`)         |
                          v                                             |
                      [ Redis ]   <------------- [ Celery Worker ] -----|
                                                    (Reads/Updates status)
                                                    (Checks Preferences)
                                                    (Calls Mock Provider)
```

## Database Schema Model

We use **PostgreSQL**.

### 1. `notifications` table
- **id** (String, PK): UUID.
- **user_id** (String, Index).
- **channel** (Enum): `email`, `sms`, `push`.
- **priority** (Enum): `critical`, `high`, `normal`, `low`.
- **status** (Enum): `pending`, `sent`, `delivered`, `failed`.
- **idempotency_key** (String, Unique Index, Nullable): Used to prevent duplicate charges/notifications on network retries from clients.
- **template_name** (String, Nullable): Jinja template target.
- **payload** (JSON): Variables necessary.
- **created_at** / **updated_at**

### 2. `user_preferences` table
- **user_id** (String, PK)
- **channel** (Enum, PK): `email`, `sms`, `push`
- **opt_in** (Boolean): Defaults to `true`.

*Explanation*: We separated the preferences to allow efficient `O(1)` index queries matching `(user_id, channel)`. This prevents fetching large user objects over network if users data is segregated. 

## Handling Failures and Retries

**Celery** is used as our background task processor.
When the API receives a notification request, it strictly writes to the Database as `PENDING` and pushes the UUID to Redis Broker.
The Celery Worker consumes this and executes the `send_via_channel` mock provider.

If the mocked external provider raises an exception (network failure):
- Celery catches `DeliveryFailedException`.
- The task calculates an exponential backoff countdown: `current_retry_number ^ 2` base seconds.
- The task is retried.
- If it exceeds `max_retries=3`, Celery marks the task as failed in the queue, and our application logic sets the PostgreSQL status to `FAILED`.

## System Scaling

- **Web Tier**: FastAPI can easily scale horizontally because it relies on standard REST stateless characteristics. Rate-limiting is centralized on Redis.
- **Worker Tier**: Celery tasks can be horizontally scaled infinitely simply by deploying more worker containers and subscribing them to the Redis Broker. Since queues are logically partitioned by priorities, we can assign 5 workers exclusively for the `critical` queue, and just 1 for the `low` queue.
- **Database**: The database is the bottleneck eventually. We would add read replicas to offload `GET` history requests, dedicating the master entirely for `POST` heavy inserts and queue status updates.

## Trade-offs

1. **Celery/Redis vs. Kafka/SQS**: Redis lists are completely fine for generic workloads. However, Redis queues reside in RAM (unless thoroughly backed with AOF/RDB). A persistent event streaming layer like Kafka guarantees zero drops during broker crashes. We favored Redis/Celery for simplicity and standard industry support.
2. **Synchronous DB calls in Worker vs Async**: Celery natively runs synchronously, unlike FastAPI which handles async loops well. We decided to use standard `psycopg2-binary` engine connections to keep Celery code straightforward without introducing `asyncio.run` thread-unsafe hacks inside tasks. This means the workers are thread/process bound rather than IO-bound. If throughput needs drastically increasing per worker node, an async background orchestrator (like `arq`) should replace Celery.
3. **In-Memory Rate Limiting via Redis**: We rely on an atomic single-key sliding cache layer on Redis. While slightly imprecise over absolute seconds window due to TTL resolution, it is perfectly consistent for an API limit and incredibly low latency.
