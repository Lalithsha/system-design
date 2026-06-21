# Circuit Breaker V2 - Local Memory + Redis Pub/Sub

## Goal

Build an efficient circuit breaker implementation that avoids querying the database on every request.

This is much closer to real production systems.

---

# High Level Idea

Every service keeps the dependency status in memory.

Example:

```python
profile_status = "UP"
```

or

```python
profile_status = "DOWN"
```

Requests read memory instead of querying the database.

Memory lookup is extremely fast.

---

# Architecture

```text
                   +-------------------+
                   | Circuit Manager   |
                   +-------------------+
                            |
                            |
                     Update Database
                            |
                            |
                            v
                  +----------------+
                  | Circuit DB     |
                  +----------------+

                            |
                     Publish Event
                            |
                            v

                  Redis Pub/Sub Channel
                      circuit_updates
                            |
        ------------------------------------------
        |                    |                  |
        |                    |                  |
        v                    v                  v
Recommendation       Trending Service      Feed Service
Service              Service               Service
(profile_status)     (profile_status)      (profile_status)
```

---

# Startup Flow

## Step 1

Service starts.

```python
profile_status = "UNKNOWN"
```

---

## Step 2

Load status from database.

```python
SELECT status
FROM service_status
WHERE service_name='profile'
```

Example:

```python
profile_status = "UP"
```

---

## Step 3

Start Redis subscriber thread.

```python
threading.Thread(
    target=listen_for_updates,
    daemon=True
)
```

Now service continuously listens for status changes.

---

# Runtime Request Flow

## Profile Service UP

```text
User
 |
 v
Recommendation Service
 |
 |-----> profile_status == UP
 |
 |-----> Call Profile Service
 |
 v
Return Response
```

No database query.

No Redis query.

Only memory access.

---

## Profile Service DOWN

```text
User
 |
 v
Recommendation Service
 |
 |-----> profile_status == DOWN
 |
 |-----> Skip Profile Service
 |
 |-----> Return fallback
 |
 v
Response
```

Again:

No database query.

No Redis query.

---

# How Status Changes

Suppose Profile Service becomes unhealthy.

Circuit Manager updates DB:

```text
profile -> DOWN
```

Then publishes:

```text
profile:DOWN
```

to:

```text
circuit_updates
```

Redis channel.

---

# Subscriber Thread

Subscriber receives:

```text
profile:DOWN
```

Updates memory:

```python
profile_status = "DOWN"
```

Every future request immediately sees:

```python
profile_status == "DOWN"
```

No DB access required.

---

# Thread Flow

There are two threads.

## Thread 1 - Flask Thread

Handles HTTP requests.

```text
Request
    |
    v
recommendations()
```

---

## Thread 2 - Redis Subscriber Thread

Continuously waits:

```python
for message in pubsub.listen():
```

Receives updates and modifies:

```python
profile_status
```

---

# Diagram

```text
                    Flask Thread
                 ------------------
Request 1 ---> recommendations()
Request 2 ---> recommendations()
Request 3 ---> recommendations()

                        reads

                  profile_status


                 Redis Subscriber Thread
              --------------------------------

for message in pubsub.listen():

    profile:DOWN
            |
            v
profile_status = "DOWN"
```

Both threads share:

```python
profile_status
```

which acts like:

```text
Shared In-Memory State
```

---

# Why We Use Global Variable

```python
profile_status = "UP"
```

This is essentially our local cache.

Every request checks:

```python
if profile_status == "UP":
```

instead of:

```python
SELECT status FROM service_status
```

This removes:

* DB latency
* DB load
* Extra network roundtrips

---

# Performance Comparison

## V1

Every request:

```text
Request
    |
Database
    |
Profile Service
```

---

## V2

Every request:

```text
Request
    |
Memory
    |
Profile Service
```

Memory lookup is dramatically faster.

---

# Why Redis Pub/Sub

Question:

How does every service know status changed?

Answer:

Broadcast.

Redis Pub/Sub sends update to all services.

Example:

```text
profile:DOWN
```

All services receive it instantly.

---

# Why Database Still Exists

Database remains the source of truth.

Suppose:

Recommendation Service crashes.

When it starts again:

1. Read database
2. Get latest status
3. Subscribe again

Database provides recovery.

Redis Pub/Sub provides realtime updates.

Together they solve:

* Recovery
* Realtime synchronization

---

# Why This Is Better

## Database Reads

V1:

# 1000 requests/sec

1000 DB reads/sec

V2:

# 1000 requests/sec

0 DB reads/sec

---

## Latency

V1:

```text
Request
 -> DB
 -> Service
```

V2:

```text
Request
 -> Memory
 -> Service
```

---

## Scalability

As services increase:

```text
10 services
20 services
50 services
100 services
```

Memory reads remain extremely cheap.

---

# Production Concepts This Introduces

This exercise teaches:

1. Circuit Breaker Pattern
2. Local Caching
3. Shared State
4. Pub/Sub
5. Background Threads
6. Event Driven Updates
7. Source of Truth Database
8. Dependency Isolation
9. Fallback Logic
10. Preventing Cascading Failures

---

# Real World Analogy

Airport displays.

Database:

```text
Flight AI101 = DELAYED
```

Redis Pub/Sub:

Broadcast:

```text
AI101:DELAYED
```

Every display board updates instantly.

Passengers read display boards.

Nobody repeatedly asks the database.

That display board is equivalent to:

```python
profile_status
```

inside each service.
