import argparse
from confluent_kafka.admin import AdminClient, NewTopic

BOOTSTRAP_SERVERS = "localhost:9092"

def create_inventory_topic(topic_name="inventory", num_partitions=3, replication_factor=1):
    admin = AdminClient({"bootstrap.servers": BOOTSTRAP_SERVERS})
    topic = NewTopic(topic=topic_name,num_partitions=num_partitions,replication_factor=replication_factor)
    futures = admin.create_topics([topic])

    for name, future in futures.items():
        try:
            future.result()
            print(f"Created topic: {name}")
        except Exception as e:
            print(f"Failed to create '{name}': {e}")

def parse_args():
    parser = argparse.ArgumentParser(description="Create a Kafka topic")
    parser.add_argument("--topic", default="inventory", help="Topic name")
    parser.add_argument("--partitions", type=int, default=3, help="Number of partitions")
    parser.add_argument("--replication", type=int, default=1, help="Replication factor")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    create_inventory_topic(topic_name=args.topic,num_partitions=args.partitions,replication_factor=args.replication)