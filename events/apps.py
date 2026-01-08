from django.apps import AppConfig
import threading
import os
from events.services import logger
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import asyncio
from django.core.exceptions import ImproperlyConfigured

class EventsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "events"

    def ready(self):
        if os.environ.get("RUN_MAIN") != "true":
            return

        layer = get_channel_layer()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        if not layer:
            raise ImproperlyConfigured("No se pudo obtener el channel layer")

        try:
            loop.run_until_complete(layer.send("test", {"type": "test"}))
        except Exception as e:
            raise ImproperlyConfigured("Redis no alcanzable para CHANNEL_LAYERS") from e

        from events.consumer import start_kafka_consumer

        thread = threading.Thread(
            target=start_kafka_consumer,
            daemon=True,
            name="kafka-consumer-thread"
        )
        thread.start()

        logger.info("Kafka consumer thread iniciado")
