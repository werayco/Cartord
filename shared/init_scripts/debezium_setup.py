import json
import os
import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path="./shared/compose_files/.env")
DEBEZIUM_URL = "http://localhost:8083/connectors"

def outbox_connector(name, db_name, table_name, slot_name, topic):
    return {
        "name": name,
        "config": {
            "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
            "database.hostname": "postgres",
            "database.port": os.getenv("DB_PORT"),
            "database.user": os.getenv("POSTGRES_USER"),
            "database.password": os.getenv("POSTGRES_PASSWORD"),
            "database.dbname": db_name,
            "topic.prefix": db_name,
            "plugin.name": "pgoutput",
            "slot.name": slot_name,
            "publication.autocreate.mode": "filtered",
            "table.include.list": f"public.{table_name}",
            "tombstones.on.delete": "false",

            "transforms": "outbox",
            "transforms.outbox.type": "io.debezium.transforms.outbox.EventRouter",
            "transforms.outbox.table.field.event.id": "id",
            "transforms.outbox.table.field.event.key": "aggregate_id",
            "transforms.outbox.table.field.event.timestamp": "created_at",
            "transforms.outbox.table.field.event.payload": "payload",
            "transforms.outbox.table.expand.json.payload": "true",
            "transforms.outbox.table.fields.additional.placement": "event_type:header:eventType",
            "transforms.outbox.route.by.field": "event_type",
            "transforms.outbox.route.topic.replacement": topic,
        },
    }


connector_config_order = outbox_connector(
    name="order-outbox-connector",
    db_name="order_db",
    table_name="outbox_events",
    slot_name="order_outbox_slot",
    topic="order",
)

connector_config_inventory = outbox_connector(
    name="inventory-outbox-connector",
    db_name="inventory_db",
    table_name="inventory_outbox_events",
    slot_name="inventory_outbox_slot",
    topic="inventory",
)

def register_connector(connector_config):
    response = requests.post(
        DEBEZIUM_URL,
        headers={"Content-Type": "application/json"},
        data=json.dumps(connector_config),
    )
    if response.status_code == 201:
        print(f"Connector {connector_config['name']} registered successfully.")
    elif response.status_code == 409:
        print(f"Connector {connector_config['name']} already exists. Use PUT to update its config instead:")
        print(f"  {DEBEZIUM_URL}/{connector_config['name']}/config")
    else:
        print(f"Failed to register {connector_config['name']}: {response.status_code}")
        print(response.text)
        response.raise_for_status()


if __name__ == "__main__":
    register_connector(connector_config_order)
    register_connector(connector_config_inventory)