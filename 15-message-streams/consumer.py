from kafka import KafkaConsumer

# For individual consumer
# consumer = KafkaConsumer(
#     "orders",
#     bootstrap_servers="localhost:9092",
#     auto_offset_reset="earliest"
# )

# For group consumers 
consumer = KafkaConsumer(
    "orders",
    bootstrap_servers="localhost:9092",
    auto_offset_reset="earliest"
)


# for message in consumer:
#     print(message.value.decode())

for message in consumer:
    print(
        "Partition:",
        message.partition,
        "Message",
        message.value.decode()
    )
