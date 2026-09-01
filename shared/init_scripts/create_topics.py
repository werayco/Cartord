import os
from confluent_kafka.admin import AdminClient, NewTopic

BOOTSTRAP_SERVERS = 'localhost:9092'

def create_topic(admin, topic_name, num_partitions=3, replication_factor=1):
    existing_topics = admin.list_topics().topics
    if topic_name in existing_topics:
        print(f"Topic '{topic_name}' already exists. Skipping...")
        return
    
    topic = NewTopic(
        topic=topic_name,
        num_partitions=num_partitions,
        replication_factor=replication_factor
    )
    futures = admin.create_topics([topic])

    for name, future in futures.items():
        try:
            future.result()
            print(f"Created topic: {name} (partitions: {num_partitions}, replication: {replication_factor})")
        except Exception as e:
            print(f"Failed to create '{name}': {e}")

def create_all_topics():
    admin = AdminClient({"bootstrap.servers": BOOTSTRAP_SERVERS})
    
    topics = [
        {"name": "inventory", "partitions": 3, "replication": 1},
        {"name": "payment", "partitions": 3, "replication": 1},
        {"name": "order", "partitions": 1, "replication": 1},
        {"name": "chat", "partitions": 1, "replication": 1},
        {"name": "order.dlq", "partitions": 1, "replication": 1},
        {"name": "inventory.dlq", "partitions": 1, "replication": 1},
        {"name": "payment.dlq", "partitions": 1, "replication": 1},
        {"name": "chat.dlq", "partitions": 1, "replication": 1},
    ]
    
    print(f"Creating Kafka topics on {BOOTSTRAP_SERVERS}...")
    
    for topic_config in topics:
        create_topic(
            admin=admin,
            topic_name=topic_config["name"],
            num_partitions=topic_config["partitions"],
            replication_factor=topic_config["replication"]
        )
    
    print("All topics created successfully!")

if __name__ == "__main__":
    create_all_topics()