# Cartord CDC Stack Cheatsheet

Debezium (curl), PostgreSQL (psql), Kafka CLI, and Elasticsearch (curl).

## 1. Debezium REST API (curl)

Assumes Kafka Connect REST API is reachable at `http://localhost:8083`.

1. List all registered connectors
```
curl -s http://localhost:8083/connectors | jq
```

2. Create or register a new connector
```
curl -s -X POST http://localhost:8083/connectors \
  -H "Content-Type: application/json" \
  -d @payment-connector.json
```

3. Get a connector's config
```
curl -s http://localhost:8083/connectors/payment-connector/config | jq
```

4. Get a connector's status
```
curl -s http://localhost:8083/connectors/payment-connector/status | jq
```

5. Get full connector info, config, status, and tasks
```
curl -s http://localhost:8083/connectors/payment-connector | jq
```

6. Update a connector's config
```
curl -s -X PUT http://localhost:8083/connectors/payment-connector/config \
  -H "Content-Type: application/json" \
  -d @payment-connector-updated.json
```

7. Delete a connector
```
curl -s -X DELETE http://localhost:8083/connectors/payment-connector
```

8. Restart a connector
```
curl -s -X POST http://localhost:8083/connectors/payment-connector/restart
```

9. Restart a connector including failed tasks
```
curl -s -X POST \
  'http://localhost:8083/connectors/payment-connector/restart?includeTasks=true&onlyFailed=true'
```

10. Pause a connector
```
curl -s -X PUT http://localhost:8083/connectors/payment-connector/pause
```

11. Resume a paused connector
```
curl -s -X PUT http://localhost:8083/connectors/payment-connector/resume
```

12. List a connector's tasks
```
curl -s http://localhost:8083/connectors/payment-connector/tasks | jq
```

13. Get a specific task's status
```
curl -s http://localhost:8083/connectors/payment-connector/tasks/0/status | jq
```

14. Restart a specific failed task
```
curl -s -X POST http://localhost:8083/connectors/payment-connector/tasks/0/restart
```

15. Validate a connector config before creating it
```
curl -s -X PUT \
  http://localhost:8083/connector-plugins/io.debezium.connector.postgresql.PostgresConnector/config/validate \
  -H "Content-Type: application/json" \
  -d @payment-connector.json | jq
```

16. List available connector plugins
```
curl -s http://localhost:8083/connector-plugins | jq
```

17. Check Kafka Connect worker info
```
curl -s http://localhost:8083/ | jq
```

18. List connectors with expanded status
```
curl -s http://localhost:8083/connectors?expand=status | jq
```

19. Get topics used by a connector
```
curl -s http://localhost:8083/connectors/payment-connector/topics | jq
```

20. Reset a connector's topic tracking
```
curl -s -X PUT http://localhost:8083/connectors/payment-connector/topics/reset
```

## 2. PostgreSQL (psql)

Includes navigation plus logical replication commands for Debezium CDC and outbox table debugging.

1. Connect to a database
```
psql -h localhost -p 5432 -U postgres -d cartord_payment
```

2. Connect via docker exec
```
docker exec -it cartord-pg psql -U postgres -d cartord_payment
```

3. List all databases
```
\l
```

4. Switch database
```
\c cartord_inventory
```

5. List all tables in current schema
```
\dt
```

6. Describe a table's structure
```
\d payment_outbox
```

7. List all schemas
```
\dn
```

8. Check WAL level, must be logical for Debezium
```
SHOW wal_level;
```

9. List logical replication slots
```
SELECT slot_name, plugin, slot_type, active, restart_lsn
FROM pg_replication_slots;
```

10. Create a logical replication slot manually
```
SELECT pg_create_logical_replication_slot(
  'payment_slot', 'pgoutput'
);
```

11. Drop a replication slot
```
SELECT pg_drop_replication_slot('payment_slot');
```

12. List publications
```
SELECT * FROM pg_publication;
```

13. Show tables in a publication
```
SELECT * FROM pg_publication_tables WHERE pubname = 'dbz_publication';
```

14. Create a publication for specific tables
```
CREATE PUBLICATION dbz_publication FOR TABLE payment_outbox;
```

15. Check replication slot lag
```
SELECT slot_name,
  pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)) AS lag
FROM pg_replication_slots;
```

16. View active connections and queries
```
SELECT pid, usename, application_name, state, query
FROM pg_stat_activity;
```

17. Kill a stuck or blocking query
```
SELECT pg_terminate_backend(12345);
```

18. Query the outbox table directly
```
SELECT id, aggregatetype, aggregateid, type, timestamp
FROM payment_outbox
ORDER BY timestamp DESC
LIMIT 20;
```

19. Check column data type for a specific column
```
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'payment_outbox' AND column_name = 'created_at';
```

20. Alter a column to TIMESTAMPTZ
```
ALTER TABLE payment_outbox
ALTER COLUMN created_at TYPE TIMESTAMPTZ
USING created_at AT TIME ZONE 'UTC';
```

## 3. Kafka CLI

Commands run via `docker exec -it cartord-kf /opt/kafka/bin/<script>` against a broker at `localhost:9092`.

1. List all topics
```
docker exec -it cartord-kf /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 --list
```

2. Describe a topic
```
docker exec -it cartord-kf /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 --describe --topic payment.public.payment_outbox
```

3. Create a topic
```
docker exec -it cartord-kf /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 --create \
  --topic order.events --partitions 3 --replication-factor 1
```

4. Delete a topic
```
docker exec -it cartord-kf /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 --delete --topic order.events
```

5. Alter a topic's partition count
```
docker exec -it cartord-kf /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 --alter \
  --topic order.events --partitions 6
```

6. Consume a topic from the beginning with keys and headers
```
docker exec -it cartord-kf /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 --topic topic_name \
  --from-beginning --property print.key=true --property print.headers=true
```

7. Consume only new messages
```
docker exec -it cartord-kf /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 --topic order.events
```

8. Consume as part of a named consumer group
```
docker exec -it cartord-kf /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 --topic order.events \
  --group cartord-debug-group
```

9. Produce a test message
```
docker exec -it cartord-kf /opt/kafka/bin/kafka-console-producer.sh \
  --bootstrap-server localhost:9092 --topic order.events
```

10. Produce a message with a key
```
docker exec -it cartord-kf /opt/kafka/bin/kafka-console-producer.sh \
  --bootstrap-server localhost:9092 --topic order.events \
  --property 'parse.key=true' --property 'key.separator=:'
```

11. List all consumer groups
```
docker exec -it cartord-kf /opt/kafka/bin/kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 --list
```

12. Describe a consumer group for lag check
```
docker exec -it cartord-kf /opt/kafka/bin/kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 --describe --group cartord-debug-group
```

13. Reset a consumer group's offsets to earliest
```
docker exec -it cartord-kf /opt/kafka/bin/kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 --group cartord-debug-group \
  --topic order.events --reset-offsets --to-earliest --execute
```

14. Delete a consumer group
```
docker exec -it cartord-kf /opt/kafka/bin/kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 --delete --group cartord-debug-group
```

15. Get earliest and latest offsets for a topic
```
docker exec -it cartord-kf /opt/kafka/bin/kafka-run-class.sh \
  kafka.tools.GetOffsetShell \
  --broker-list localhost:9092 --topic order.events --time -1
```

16. View or alter topic configs
```
docker exec -it cartord-kf /opt/kafka/bin/kafka-configs.sh \
  --bootstrap-server localhost:9092 \
  --entity-type topics --entity-name order.events --describe
```

17. Set a topic to compacted for outbox style topics
```
docker exec -it cartord-kf /opt/kafka/bin/kafka-configs.sh \
  --bootstrap-server localhost:9092 --entity-type topics \
  --entity-name order.events --alter \
  --add-config cleanup.policy=compact
```

18. Check broker and cluster metadata in KRaft mode
```
docker exec -it cartord-kf /opt/kafka/bin/kafka-metadata-quorum.sh \
  --bootstrap-server localhost:9092 describe --status
```

19. Check under replicated or unavailable partitions
```
docker exec -it cartord-kf /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 \
  --describe --under-replicated-partitions
```

20. Dump a topic's messages to a file with timestamps
```
docker exec -it cartord-kf /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 --topic order.events \
  --from-beginning --property print.timestamp=true \
  > order_events_dump.log
```

## 4. Elasticsearch (curl)

Assumes Elasticsearch is reachable at `http://localhost:9200`.

1. Check cluster health
```
curl -s http://localhost:9200/_cluster/health?pretty
```

2. Get cluster and node info
```
curl -s http://localhost:9200/
```

3. List all indices
```
curl -s 'http://localhost:9200/_cat/indices?v'
```

4. Create an index
```
curl -s -X PUT http://localhost:9200/index_name
```

5. Create an index with mapping and settings
```
curl -s -X PUT http://localhost:9200/index_name \
  -H "Content-Type: application/json" -d '{
    "settings": {"number_of_shards": 1, "number_of_replicas": 0},
    "mappings": {"properties": {
      "title": {"type": "text"},
      "created_at": {"type": "date"}
    }}
  }'
```

6. Delete an index
```
curl -s -X DELETE http://localhost:9200/index_name
```

7. Get an index's mapping
```
curl -s http://localhost:9200/index_name/_mapping?pretty
```

8. Get an index's settings
```
curl -s http://localhost:9200/index_name/_settings?pretty
```

9. Index a document with a given ID
```
curl -s -X PUT http://localhost:9200/index_name/_doc/1 \
  -H "Content-Type: application/json" -d '{
    "title": "Sample document",
    "created_at": "2026-08-15T10:00:00Z"
  }'
```

10. Index a document with an auto generated ID
```
curl -s -X POST http://localhost:9200/index_name/_doc \
  -H "Content-Type: application/json" -d '{
    "title": "Another document"
  }'
```

11. Get a document by ID
```
curl -s http://localhost:9200/index_name/_doc/1?pretty
```

12. Check if a document exists
```
curl -s -I http://localhost:9200/index_name/_doc/1
```

13. Update a document with a partial update
```
curl -s -X POST http://localhost:9200/index_name/_update/1 \
  -H "Content-Type: application/json" -d '{
    "doc": {"title": "Updated title"}
  }'
```

14. Delete a document by ID
```
curl -s -X DELETE http://localhost:9200/index_name/_doc/1
```

15. Search with a simple query string
```
curl -s 'http://localhost:9200/index_name/_search?q=title:sample&pretty'
```

16. Search with a JSON query body using match
```
curl -s -X GET http://localhost:9200/index_name/_search \
  -H "Content-Type: application/json" -d '{
    "query": {"match": {"title": "sample"}}
  }'
```

17. Search with filters and pagination
```
curl -s -X GET http://localhost:9200/index_name/_search \
  -H "Content-Type: application/json" -d '{
    "from": 0, "size": 10,
    "query": {"bool": {"filter": [
      {"term": {"status": "active"}}
    ]}}
  }'
```

18. Count matching documents
```
curl -s -X GET http://localhost:9200/index_name/_count \
  -H "Content-Type: application/json" -d '{
    "query": {"match": {"title": "sample"}}
  }'
```

19. Bulk index multiple documents
```
curl -s -X POST http://localhost:9200/_bulk \
  -H "Content-Type: application/x-ndjson" --data-binary @bulk_data.ndjson
```

20. Reindex from one index to another
```
curl -s -X POST http://localhost:9200/_reindex \
  -H "Content-Type: application/json" -d '{
    "source": {"index": "index_name"},
    "dest": {"index": "index_name_v2"}
  }'
```
