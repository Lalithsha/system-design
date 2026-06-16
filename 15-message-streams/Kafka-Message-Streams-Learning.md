# Kafka Message Streams - Learning Notes

## Why We Learned Kafka

Before Kafka, we learned:

* PostgreSQL → Database
* Redis → Cache
* RabbitMQ → Message Queue

Kafka introduces:

* Message Streams
* Event Streaming
* Distributed Logs
* Consumer Groups
* Partitions
* High Throughput Systems

---

# Message Queue vs Message Stream

## RabbitMQ (Message Queue)

Think:

```text
Producer
   |
 Queue
   |
Consumer
```

Typical use cases:

* Send Email
* Generate PDF
* Resize Image
* Process Payment

Goal:

```text
Get work done once
```

After processing:

```text
Message is usually removed
```

---

## Kafka (Message Stream)

Think:

```text
Producer
   |
 Topic
   |
Consumers
```

Typical use cases:

* Order Created
* User Logged In
* Payment Completed

Goal:

```text
Publish an event
Many systems can react
```

Example:

```text
Order Created

      Kafka
         |
--------------------------------
|      |      |      |         |
Email Billing Analytics Inventory Fraud
```

Messages remain stored for a configurable period.

---

# Important Kafka Concepts

## Broker

Kafka server.

Think:

```text
PostgreSQL -> Database Server
RabbitMQ   -> RabbitMQ Server
Kafka      -> Broker
```

Currently we have:

```text
1 Broker
```

running inside Docker.

---

## Topic

A Topic is where messages are written.

Example:

```text
orders
payments
users
```

Think:

```text
Topic = Category of Events
```

---

## Partition

Partitions are Kafka's scaling mechanism.

Example:

```text
orders topic

Partition 0
Partition 1
Partition 2
```

Messages are stored inside partitions.

Important:

```text
Partition = Unit of Parallelism
```

---

## Producer

Creates and sends messages.

Example:

```text
Order Service
Payment Service
User Service
```

---

## Consumer

Reads messages from Kafka.

Example:

```text
Email Service
Analytics Service
Inventory Service
```

---

## Consumer Group

Multiple consumers working together.

Example:

```text
Consumer Group: order-processors

Consumer A
Consumer B
Consumer C
```

Kafka distributes partitions among them.

---

## Offset

Every message inside a partition has a position.

Example:

```text
Partition 0

Offset 0 -> Order1
Offset 1 -> Order2
Offset 2 -> Order3
Offset 3 -> Order4
```

Consumer stores:

```text
Current Offset = 2
```

Meaning:

```text
Messages 0 and 1 already processed
```

---

# Kafka Setup

## docker-compose.yml

```yaml
services:
  kafka:
    image: apache/kafka:latest
    container_name: kafka

    ports:
      - "9092:9092"

    environment:
      KAFKA_NODE_ID: 1
      KAFKA_PROCESS_ROLES: broker,controller

      KAFKA_LISTENERS: PLAINTEXT://:9092,CONTROLLER://:9093

      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092

      KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER

      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,CONTROLLER:PLAINTEXT

      KAFKA_CONTROLLER_QUORUM_VOTERS: 1@localhost:9093

      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
```

---

## Start Kafka

```bash
docker compose up -d
```

Verify:

```bash
docker ps
```

---

# Create Topic

Enter container:

```bash
docker exec -it kafka bash
```

Create topic:

```bash
/opt/kafka/bin/kafka-topics.sh \
  --create \
  --topic orders \
  --partitions 1 \
  --replication-factor 1 \
  --bootstrap-server localhost:9092
```

---

# Describe Topic

```bash
/opt/kafka/bin/kafka-topics.sh \
  --describe \
  --topic orders \
  --bootstrap-server localhost:9092
```

Example output:

```text
Topic: orders
PartitionCount: 1
```

---

# Increase Partitions

Change from:

```text
1 Partition
```

to:

```text
3 Partitions
```

Command:

```bash
/opt/kafka/bin/kafka-topics.sh \
  --alter \
  --topic orders \
  --partitions 3 \
  --bootstrap-server localhost:9092
```

Verify:

```bash
/opt/kafka/bin/kafka-topics.sh \
  --describe \
  --topic orders \
  --bootstrap-server localhost:9092
```

Expected:

```text
PartitionCount: 3
```

---

# Python Producer

## Code

```python
from kafka import KafkaProducer

producer = KafkaProducer(
    bootstrap_servers="localhost:9092"
)

producer.send(
    "orders",
    value=b"order-1"
)

producer.flush()

print("Sent order-1")
```

---

## Explanation

### KafkaProducer(...)

Creates producer object.

Equivalent Java:

```java
KafkaProducer producer = new KafkaProducer(...);
```

Purpose:

```text
Send messages to Kafka
```

---

### bootstrap_servers

```python
bootstrap_servers="localhost:9092"
```

Meaning:

```text
Kafka is running at localhost on port 9092
```

---

### producer.send()

```python
producer.send(
    "orders",
    value=b"order-1"
)
```

Meaning:

```text
Send order-1 message
to orders topic
```

---

### value=b"order-1"

Python bytes.

Equivalent Java:

```java
"order-1".getBytes()
```

Kafka sends bytes internally.

---

### producer.flush()

Meaning:

```text
Immediately send buffered messages
Wait for Kafka confirmation
```

---

# Python Consumer

## Code

```python
from kafka import KafkaConsumer

consumer = KafkaConsumer(
    "orders",
    bootstrap_servers="localhost:9092",
    auto_offset_reset="earliest",
    group_id="order-processors"
)

for message in consumer:
    print(
        "Partition:",
        message.partition,
        "Message:",
        message.value.decode()
    )
```

---

# Explanation

## KafkaConsumer(...)

Creates consumer object.

Equivalent Java:

```java
new KafkaConsumer(...)
```

Purpose:

```text
Read messages from Kafka
```

---

## Topic Name

```python
"orders"
```

Meaning:

```text
Subscribe to orders topic
```

---

## auto_offset_reset

```python
auto_offset_reset="earliest"
```

Meaning:

```text
Read from first available message
```

Alternative:

```python
auto_offset_reset="latest"
```

Meaning:

```text
Only read new messages
```

---

## group_id

```python
group_id="order-processors"
```

Meaning:

```text
Join consumer group:
order-processors
```

Consumers in same group share partitions.

---

## for message in consumer

Python syntax.

Meaning:

```text
Keep listening forever
```

Equivalent idea:

```java
while(true)
{
   read next message
}
```

---

## message.partition

Returns:

```text
0
1
2
```

depending on partition.

---

## message.value

Returns message bytes.

---

## decode()

Converts bytes to string.

Equivalent Java:

```java
new String(bytes)
```

---

# Exercises Performed

## Exercise 1

Topic:

```text
orders
```

Partitions:

```text
1
```

Observation:

```text
Consumer reads messages sequentially
```

Learning:

```text
Ordering is guaranteed within a partition
```

---

## Exercise 2

Partitions increased:

```text
1 -> 3
```

Observation:

```text
Messages distributed across partitions
```

Learning:

```text
Partitions are Kafka's scaling mechanism
```

---

## Exercise 3

Multiple consumers added.

Example:

```text
Consumer A
Consumer B
Consumer C
```

Observation:

```text
Kafka rebalanced partitions
```

Example:

```text
Partition 0 -> Consumer A
Partition 1 -> Consumer B
Partition 2 -> Consumer C
```

Learning:

```text
Kafka scales by assigning partitions
to consumers inside a consumer group
```

---

# Important Kafka Rules

## Rule 1

```text
Ordering is guaranteed
within a partition
```

---

## Rule 2

```text
Maximum Active Consumers
=
Number of Partitions
```

Example:

```text
3 Partitions
```

allows:

```text
3 active consumers
```

inside a consumer group.

---

## Rule 3

Adding partitions:

```text
1 -> 3
```

does NOT redistribute old messages.

Only new messages use new partitions.

---

## Rule 4

Same key goes to same partition.

Example:

```python
producer.send(
    "orders",
    key=b"user1",
    value=b"order-1"
)
```

Kafka hashes:

```text
user1
```

and always chooses same partition.

Useful for:

```text
User Ordering
Account Ordering
Order Ordering
```

---

# Kafka Scaling Formula

```text
Topic
   |
Partitions
   |
Consumer Group
   |
Parallel Processing
```

Kafka scales because of:

```text
Partitions
```

not because of consumers alone.

---

# Biggest Learning

RabbitMQ:

```text
Task Processing
```

Kafka:

```text
Event Streaming
```

RabbitMQ asks:

```text
Who should do this work?
```

Kafka asks:

```text
Who wants to know this happened?
```

This is the fundamental difference.
