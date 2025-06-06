#!/bin/bash
# init_kafka_broker.sh

# Dentro del shell del contenedor, ejecuta los comandos de configuración:
export CLUSTER_ID="${KAFKA_CLUSTER_ID}"

SERVER_PROPERTIES_PATH=/tmp/kafka_storage_config.properties
echo "node.id="${KAFKA_NODE_ID}"" > "${SERVER_PROPERTIES_PATH}"
echo "log.dirs=/tmp/kraft-kafka-logs" >> "${SERVER_PROPERTIES_PATH}"
echo "process.roles=broker,controller" >> "${SERVER_PROPERTIES_PATH}"
echo "controller.quorum.voters=1@localhost:9093" >> "${SERVER_PROPERTIES_PATH}"
echo "listeners=PLAINTEXT://localhost:9092,BROKER://localhost:9093" >> "${SERVER_PROPERTIES_PATH}"
echo "controller.listener.names=BROKER" >> "${SERVER_PROPERTIES_PATH}"
echo "advertised.listeners=PLAINTEXT://localhost:9092" >> "${SERVER_PROPERTIES_PATH}" 

rm -rf /tmp/kraft-kafka-logs 

/usr/bin/kafka-storage format --cluster-id "${CLUSTER_ID}" --config "${SERVER_PROPERTIES_PATH}"



export CLUSTER_ID="${KAFKA_CLUSTER_ID}"

SERVER_PROPERTIES_PATH=/tmp/kafka_storage_config.properties
echo "node.id=1" > "${SERVER_PROPERTIES_PATH}"
echo "log.dirs=/tmp/kraft-kafka-logs" >> "${SERVER_PROPERTIES_PATH}"
echo "process.roles=broker,controller" >> "${SERVER_PROPERTIES_PATH}"
echo "controller.quorum.voters=1@localhost:9093" >> "${SERVER_PROPERTIES_PATH}"
echo "listeners=PLAINTEXT://localhost:9092,BROKER://localhost:9093" >> "${SERVER_PROPERTIES_PATH}"
echo "controller.listener.names=BROKER" >> "${SERVER_PROPERTIES_PATH}"
echo "advertised.listeners=PLAINTEXT://localhost:9092" >> "${SERVER_PROPERTIES_PATH}" 

/usr/bin/kafka-storage format --cluster-id "${CLUSTER_ID}" --config "${SERVER_PROPERTIES_PATH}"

/etc/confluent/docker/run