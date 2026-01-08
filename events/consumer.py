from channels.generic.websocket import AsyncWebsocketConsumer
from kafka import KafkaConsumer
from django.conf import settings
import json
import logging
import time
from events.services import dispatch_event

logger = logging.getLogger(__name__)


def start_kafka_consumer():
    config = settings.KAFKA_CONFIG

    topics = list(config["ALLOWED_TOPICS"])

    while True:
        try:
            consumer = KafkaConsumer(
                *topics,
                bootstrap_servers=config["BROKER"],
                group_id=config["GROUP_ID"],
                auto_offset_reset="earliest",
                enable_auto_commit=True,
                value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            )

            logger.info(f"Kafka consumer escuchando: {topics}")

            for message in consumer:
                dispatch_event(
                    topic=message.topic,
                    event=message.value
                )

        except Exception:
            logger.exception("Error en Kafka consumer")
            time.sleep(5)

# consumers.py



class VideoProgressConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        url_route = self.scope.get("url_route")
        if not url_route:
            logger.warning("WebSocket sin url_route")
            await self.close()
            return

        kwargs = url_route.get("kwargs", {})
        self.video_id = kwargs.get("video_id")

        if not self.video_id:
            logger.warning("WebSocket sin video_id")
            await self.close()
            return

        if not self.channel_layer:
            logger.error("Channel layer no disponible")
            await self.close()
            return

        self.group_name = f"video_{self.video_id}"

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

        logger.info(f"WebSocket conectado video_id={self.video_id}")

    async def disconnect(self, code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

        logger.info("WebSocket desconectado")

    async def video_progress(self, event):
        await self.send(text_data=json.dumps({
            "progress": event.get("progress"),
            "status": event.get("status"),
        }))