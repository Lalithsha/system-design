# Circuit Breaker V1 - Database Polling Approach

## Goal

Understand why a naïve circuit breaker implementation becomes expensive in distributed systems.

In this version, every service directly queries the Circuit Breaker database before calling another service.

---

# Problem Statement

Assume we have these services:

* Profile Service
* Recommendation Service
* Trending Service
* Feed Service

All services depend on:

```text
Profile Service
```

If Profile Service goes down:

* Recommendation Service fails
* Trending Service fails
* Feed Service fails

This causes:

```text
Cascading Failure
```

where one service failure spreads throughout the system.

---

# Architecture

```text
Recommendation Service
        |
        |
        v
Circuit Breaker DB
        |
        |
        v
Profile Service

Trending Service
        |
        |
        v
Circuit Breaker DB
        |
        |
        v
Profile Service

Feed Service
        |
        |
        v
Circuit Breaker DB
        |
        |
        v
Profile Service
```

Every request does:

1. Read Circuit DB
2. Check profile status
3. Call Profile Service if UP
4. Execute fallback logic if DOWN

---

# Request Flow (Profile Service UP)

```text
User
 |
 v
Recommendation Service
 |
 |-----> Query DB
 |         status = UP
 |
 |-----> Call Profile Service
 |
 |-----> Receive Profile Data
 |
 v
Return Recommendation Response
```

---

# Request Flow (Profile Service DOWN)

```text
User
 |
 v
Recommendation Service
 |
 |-----> Query DB
 |         status = DOWN
 |
 |-----> Skip Profile Service
 |
 |-----> Execute fallback
 |
 v
Return Fallback Response
```

---

# Example Database

Table:

service_status

| service_name | status |
| ------------ | ------ |
| profile      | UP     |

or

| service_name | status |
| ------------ | ------ |
| profile      | DOWN   |

---

# Example Code Flow

Pseudo code:

```python
def recommendations():

    status = get_status_from_db()

    if status == "UP":
        profile = call_profile_service()
        return response(profile)

    return fallback()
```

---

# Why This Works

The service avoids calling a dead dependency.

Without Circuit Breaker:

```text
Recommendation
        |
        v
Profile (DOWN)

wait...
timeout...
retry...
more timeout...
```

Eventually threads become blocked.

Latency increases.

Requests pile up.

System becomes unhealthy.

---

# Problems With V1

## Problem 1 - Database Hit Per Request

Suppose:

1000 requests/sec

Recommendation Service:

1000 DB reads/sec

Trending Service:

1000 DB reads/sec

Feed Service:

1000 DB reads/sec

Total:

3000 reads/sec

just to check:

```text
Is Profile Service UP?
```

The DB becomes a bottleneck.

---

## Problem 2 - Increased Latency

Every request:

```text
API Request
      |
      v
Database Query
      |
      v
Profile Service
```

Extra network roundtrip.

---

## Problem 3 - Single Point of Failure

If Circuit DB goes down:

```text
Recommendation Service
      |
      X
Cannot determine status
```

Now everything may fail.

---

## Problem 4 - Poor Scalability

As services increase:

```text
10 services
20 services
50 services
100 services
```

DB traffic explodes.

---

# Learning Objectives From V1

1. Understand cascading failures.
2. Understand why circuit breakers exist.
3. Understand dependency protection.
4. Observe database overhead.
5. Observe extra network latency.
6. Understand why polling databases is inefficient.

---

# Real World Analogy

Imagine a hospital.

Before entering every room, every doctor asks reception:

"Is MRI machine working?"

Reception gets flooded.

Instead:

Reception announces:

"MRI machine is DOWN."

Everyone immediately knows.

That announcement system is what V2 builds.
