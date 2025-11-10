# consumer.py
import asyncio
import os
import json
import logging
import signal
from typing import Optional

import aiohttp
from aiokafka import AIOKafkaConsumer, ConsumerRecord
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, RetryError

from utils import VideoMessage

load_dotenv(".env")

# --- Configuración desde .env (valores por defecto seguros) ---
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BROKERS", "broker1:9092,broker2:9093,broker3:9094")
TOPIC = os.getenv("KAFKA_TOPIC", "video-topic")
GROUP_ID = os.getenv("KAFKA_GROUP_ID", "video-group")
BACKEND_ENDPOINT = os.getenv("BACKEND_ENDPOINT", "http://backend:8000/process_video")
CLIENT_ID = os.getenv("CONSUMER_CLIENT_ID", "video-consumer-1")

# --- Logging estructurado simple ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s: %(message)s")
logger = logging.getLogger("kafka-consumer")

# --- Consumer global y control de shutdown ---
consumer: AIOKafkaConsumer
shutdown_event = asyncio.Event()

# Circuit-breaker / backoff control: si el backend falla muchas veces consecutivas, pausamos brevemente
CONSECUTIVE_FAILURE_THRESHOLD = int(os.getenv("CB_THRESHOLD", "5"))
CONSECUTIVE_FAILURE_PAUSE_SECONDS = int(os.getenv("CB_PAUSE", "30"))
consecutive_failures = 0

# Retry wrapper para llamadas al backend (retry a nivel de petición HTTP)
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
async def call_backend_request(session: aiohttp.ClientSession, payload: dict):
    async with session.post(BACKEND_ENDPOINT, json=payload, timeout=aiohttp.ClientTimeout(total=15)) as resp:
        text = await resp.text()
        status = resp.status
        if status >= 500:
            # provocar retry en tenacity
            raise Exception(f"Backend server error {status}: {text}")
        return status, text

async def start_consumer():
    global consumer
    # Configuración pensada para: procesar 1 mensaje por partición y solo commitear tras éxito
    consumer = AIOKafkaConsumer(
        TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        group_id=GROUP_ID,
        enable_auto_commit=False,     # commit manual
        auto_offset_reset="earliest", # si no hay offset, leer desde el inicio
        isolation_level="read_committed",  # leer solo mensajes committeados (útil si usas transacciones)
        client_id=CLIENT_ID,
        max_poll_records=1,           # procesar 1 mensaje por poll -> ayuda a mantener orden en cada partición
        session_timeout_ms=30000,
        heartbeat_interval_ms=10000,
        request_timeout_ms=40000
    )
    await consumer.start()
    logger.info("Kafka consumer started")

async def stop_consumer():
    global consumer
    if consumer:
        logger.info("Stopping consumer...")
        await consumer.stop()
        logger.info("Consumer stopped")

async def process_message(msg: ConsumerRecord):
    """
    Procesa un mensaje individual:
     - valida esquema (pydantic)
     - llama al backend (con reintentos para errores transitorios)
     - solo si backend responde 2xx se realiza commit del offset
    Retorna True si se puede commitear, False si no (ej: payload inválido).
    """
    global consecutive_failures

    try:
        if not msg.value:
            raise ValueError("Empty message value")
        body = json.loads(msg.value.decode("utf-8"))
        video_msg = VideoMessage(**body)
    except Exception as e:
        # Payload inválido -> log y commit para evitar bloqueo
        logger.warning("Invalid message schema. Skipping and committing offset. Error=%s", e)
        return True

    backend_payload = {
        "video_url": str(video_msg.video_url),
        "message_id": video_msg.message_id,
        "produced_at": video_msg.produced_at,
        "metadata": video_msg.metadata,
        "kafka_partition": msg.partition,
        "kafka_offset": msg.offset,
    }

    async with aiohttp.ClientSession() as session:
        try:
            status, text = await call_backend_request(session, backend_payload)
        except RetryError as re:
            # fallaron todos los retries de tenacity -> considere error transitorio grave
            logger.error("Backend retries exhausted for offset=%s partition=%s: %s", msg.offset, msg.partition, re)
            consecutive_failures += 1
            raise  # re-lanzamos para que el consumer no commitee y permita reintento por Kafka
        except Exception as e:
            logger.error("Unexpected error calling backend for offset=%s partition=%s: %s", msg.offset, msg.partition, e)
            consecutive_failures += 1
            raise

    # Si llegamos aquí, tuvimos una respuesta del backend
    if 200 <= status < 300:
        logger.info("Processed message offset=%s partition=%s (message_id=%s)", msg.offset, msg.partition, video_msg.message_id)
        consecutive_failures = 0
        return True
    else:
        # 4xx => probablemente payload inválido — commitear para evitar bloqueo
        if 400 <= status < 500:
            logger.warning("Backend returned 4xx for offset=%s partition=%s: %s. Committing offset to skip.", msg.offset, msg.partition, status)
            consecutive_failures = 0
            return True
        # 5xx => error servidor: incrementar contador y lanzar excepción para reintento
        logger.error("Backend returned %s for offset=%s partition=%s: %s", status, msg.offset, msg.partition, text)
        consecutive_failures += 1
        raise Exception(f"Backend error {status}")

async def consume_loop():
    """
    Loop principal de consumo:
      - procesa mensajes uno a uno
      - commitea manualmente solo si process_message retorna True
      - maneja circuit-breaker simple en caso de fallas repetidas en backend
    """
    await start_consumer()
    try:
        async for msg in consumer:
            if shutdown_event.is_set():
                logger.info("Shutdown flagged — breaking consume loop.")
                break

            # Si circuit-breaker activado: pausa consumo temporalmente
            if consecutive_failures >= CONSECUTIVE_FAILURE_THRESHOLD:
                logger.error("Circuit-breaker: %s consecutive failures. Pausing consumption for %s seconds",
                             consecutive_failures, CONSECUTIVE_FAILURE_PAUSE_SECONDS)
                await asyncio.sleep(CONSECUTIVE_FAILURE_PAUSE_SECONDS)
                # tras esperar, resetear contador para intentar de nuevo
                # Nota: podrías implementar backoff exponencial aquí
                # pero dejamos un reset parcial para recuperar con prudencia.
                # No reseteamos a 0 para mantener visibilidad.
                # consecutive_failures = 0

            try:
                ok = await process_message(msg)
                if ok:
                    # Commit explícito y sincrónico del offset actual
                    try:
                        await consumer.commit()
                        logger.debug("Committed offset=%s partition=%s", msg.offset, msg.partition)
                    except Exception as e:
                        logger.error("Failed to commit offset=%s partition=%s: %s", msg.offset, msg.partition, e)
                        # si commit falla, preferimos relanzar para que el mensaje sea re-procesado
                        raise
                else:
                    # decidir qué hacer si process_message devolvió False (aquí no ocurre en impl actual)
                    logger.info("process_message returned False, leaving offset uncommitted for retry.")
            except Exception as e:
                # Error transitorio: no commiteamos, dejamos que Kafka reentregue según group rebalances / retries.
                logger.exception("Error processing message offset=%s partition=%s: %s", msg.offset, msg.partition, e)
                # opcional: backoff corto antes de continuar
                await asyncio.sleep(2)
    finally:
        await stop_consumer()

def _signal_handler(sig):
    logger.info("Signal received: %s. Initiating shutdown.", sig)
    shutdown_event.set()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()

    # Capturar señales para shutdown ordenado
    for s in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(s, lambda s=s: _signal_handler(s))

    try:
        loop.run_until_complete(consume_loop())
    finally:
        logger.info("Consumer exiting.")
