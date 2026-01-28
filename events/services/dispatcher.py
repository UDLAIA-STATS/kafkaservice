import logging
from events.services import handle_upload_stats, handle_video_uploaded
from events.services.start_analysis import handle_start_analysis

logger = logging.getLogger(__name__)


TOPIC_HANDLERS = {
    "video.progress": handle_video_uploaded,
    "upload.stats": handle_upload_stats,
    "start.analysis": handle_start_analysis,
}


def dispatch_event(topic: str, event: dict):
    handler = TOPIC_HANDLERS.get(topic)

    if not handler:
        logger.warning(f"Sin handler para tópico {topic}")
        return

    logger.info(f"Despachando evento para tópico {topic}: {event}")
    handler(event)
