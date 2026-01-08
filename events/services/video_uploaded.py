import logging
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)


def handle_video_uploaded(event: dict):
    video_id = event.get("video_id")
    progress = event.get("progress")
    status = event.get("status", "uploading")

    if video_id is None or progress is None:
        logger.error(f"Evento inválido: {event}")
        return
    

    channel_layer = get_channel_layer()

    if not channel_layer:
        logger.error("No se pudo obtener el channel layer")
        return

    async_to_sync(channel_layer.group_send)(
        f"video_{video_id}",
        {
            "type": "video.progress",
            "progress": progress,
            "status": status,
        }
    )

    logger.info(f"Progreso enviado video={video_id} {progress}%")
