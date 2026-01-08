from django.apps import AppConfig
import threading
import os
from services import logger

class EventsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "events"

    def ready(self):
        if os.environ.get("RUN_MAIN") != "true":
            return

        from events.consumer import start_kafka_consumer

        thread = threading.Thread(
            target=start_kafka_consumer,
            daemon=True,
            name="kafka-consumer-thread"
        )
        thread.start()

        logger.info("Kafka consumer thread iniciado")
