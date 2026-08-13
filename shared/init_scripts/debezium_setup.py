import json
import os
import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path="./shared/compose_files/.env")
DEBEZIUM_URL = "http://localhost:8083/connectors"

connector_config = {
    "name": "order-outbox-connector",
    "config": {
        "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
        "database.hostname": "postgres",
        "database.port":os.getenv("DB_PORT"),
        "database.user": os.getenv("POSTGRES_USER"),
        "database.password": os.getenv("POSTGRES_PASSWORD"),
        "database.dbname": "order_db",
        "topic.prefix": "order_db",
        "plugin.name": "pgoutput",
        "slot.name": "order_outbox_slot",
        "publication.autocreate.mode": "filtered",
        "table.include.list": "public.outbox_events",
        "tombstones.on.delete": "false",

        "transforms": "outbox",
        "transforms.outbox.type": "io.debezium.transforms.outbox.EventRouter",
        "transforms.outbox.table.field.event.id": "id",
        "transforms.outbox.table.field.event.key": "aggregate_id",
        "transforms.outbox.table.field.event.timestamp": "created_at",
        "transforms.outbox.table.field.event.payload": "payload",
        "transforms.outbox.route.by.field": "event_type",
        "transforms.outbox.route.topic.replacement": "cartord.events.${routedByValue}",
    },
}

def register_connector():
    response = requests.post(
        DEBEZIUM_URL,
        headers={"Content-Type": "application/json"},
        data=json.dumps(connector_config),
    )

    if response.status_code == 201:
        print("Connector registered successfully.")
        print(json.dumps(response.json(), indent=2))
    elif response.status_code == 409:
        print("Connector already exists. Use PUT to update its config instead:")
        print(f"  {DEBEZIUM_URL}/{connector_config['name']}/config")
    else:
        print(f"Failed to register connector: {response.status_code}")
        print(response.text)
        response.raise_for_status()


if __name__ == "__main__":
    register_connector()