from kafka import KafkaProducer
# from kafka.protocol import metadata

producer = KafkaProducer(
    bootstrap_servers="localhost:9092"
)

future = producer.send(
    "orders",
    b"orders-1"
)

metadata = future.get()
producer.flush()

# print("sent order-1")
print(metadata.partition)