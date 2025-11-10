# producer.py
import asyncio
import json
import os
import time
from aiokafka import AIOKafkaProducer
from pydantic import HttpUrl
from utils import VideoMessage, generate_order_key
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("producer")
load_dotenv(".env")

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "broker1:9092,broker2:9093,broker3:9094")
TOPIC = os.getenv("KAFKA_TOPIC", "video-topic")
USE_VIDEO_AS_KEY = os.getenv("USE_VIDEO_AS_KEY", "true").lower() == "true"
CLIENT_ID = os.getenv("PRODUCER_CLIENT_ID", "video-producer-1")

producer: AIOKafkaProducer

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
async def start_producer():
    global producer
    producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP,
        client_id=CLIENT_ID,
        linger_ms=50,
        acks="all",
        enable_idempotence=True,   # asegura que no se dupliquen mensajes
        compression_type="lz4",    # menor latencia y consumo de red
        max_request_size=10_485_760,
        retry_backoff_ms=500,
        request_timeout_ms=30000,
        )
    await producer.start()

async def stop_producer():
    global producer
    if producer:
        await producer.stop()

async def send_video(video_url: str, metadata: dict = {}):
    """
    Valida payload y envía mensaje. Retorna record metadata.
    """
    if metadata is None:
        metadata = {}

    try:
        # Valida y crea mensaje
        msg = VideoMessage(
            video_url=HttpUrl(url=video_url),
            metadata=metadata)
        key = generate_order_key(
            msg.video_url.encoded_string(),
            use_video_id=USE_VIDEO_AS_KEY)

        payload_bytes = json.dumps({
            "video_url": msg.video_url.encoded_string(),
            "metadata": msg.metadata,
            "message_id": msg.message_id,
            "produced_at": msg.produced_at
        }).encode("utf-8")

        # send and wait for ack
        fut = await producer.send_and_wait(TOPIC, payload_bytes, key=key)
        logger.info(f"Mensaje enviado: {fut.topic}-{fut.partition}@{fut.offset}")
        return fut  # contiene topic, partition, offset info
    except Exception as e:
        logger.error(f"Error enviando mensaje: {e}")
        raise

async def main():
    await start_producer()
    try:
        urls = [
            "https://firebasestorage.googleapis.com/v0/b/mybucket/o/videos%2Fgame1.mp4?alt=media&token=abc",
            "https://firebasestorage.googleapis.com/v0/b/mybucket/o/videos%2Fgame2.mp4?alt=media&token=def",
        ]
        for u in urls:
            meta = {"source": "uploader-web", "priority": "normal"}
            res = await send_video(u, meta)
            print("Enviado:", res)
            await asyncio.sleep(0.1)
    finally:
        await stop_producer()

if __name__ == "__main__":
    asyncio.run(main())
