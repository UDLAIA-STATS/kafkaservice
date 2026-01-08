import logging
from events.services import handle_video_analyzed, handle_video_uploaded

logger = logging.getLogger(__name__)


TOPIC_HANDLERS = {
    "video.progress": handle_video_uploaded,
    "video.analyzed": handle_video_analyzed
}


def dispatch_event(topic: str, event: dict):
    handler = TOPIC_HANDLERS.get(topic)

    if not handler:
        logger.warning(f"Sin handler para tópico {topic}")
        return

    handler(event)
