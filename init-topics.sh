#!/bin/sh
set -eu

TOPIC_NAME="${TOPIC_NAME:-video-topic}"
BOOTSTRAP="${BOOTSTRAP:-broker1:9092}"
PARTITIONS="${PARTITIONS:-3}"
REPLICATION="${REPLICATION:-3}"

echo "Iniciando init-topics. Bootstrap=${BOOTSTRAP} Topic=${TOPIC_NAME}"

MAX_RETRIES=60
SLEEP_SECS=2
i=0

# Esperar a que al menos un broker responda a kafka-topics / api versions
while true; do
  if kafka-topics --bootstrap-server "$BOOTSTRAP" --list > /dev/null 2>&1; then
    echo "Broker disponible en $BOOTSTRAP"
    break
  fi
  i=$((i+1))
  if [ "$i" -ge "$MAX_RETRIES" ]; then
    echo "Timeout esperando broker en $BOOTSTRAP" >&2
    exit 1
  fi
  echo "Esperando broker... intento $i/$MAX_RETRIES"
  sleep "$SLEEP_SECS"
done

# Crear topic si no existe
echo "Creando topic '$TOPIC_NAME' (partitions=${PARTITIONS}, replication=${REPLICATION}) si no existe..."
kafka-topics --create \
  --if-not-exists \
  --bootstrap-server "$BOOTSTRAP" \
  --topic "$TOPIC_NAME" \
  --partitions "$PARTITIONS" \
  --replication-factor "$REPLICATION" \
  --config retention.ms=259200000 \
  --config cleanup.policy=delete || {
    echo "La creación del topic devolvió error (posible ya existente). Continuando..."
  }

echo "Listando topics disponibles:"
kafka-topics --list --bootstrap-server "$BOOTSTRAP" || true

echo "✅ init-topics finalizado."
