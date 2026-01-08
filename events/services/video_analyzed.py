import logging
from decouple import config
import httpx

logger = logging.getLogger(__name__)

BACKEND_ENDPOINT = config("BACKEND_ENDPOINT")

def handle_video_analyzed(event: dict):
    video_name = event.get("video_name")
    match_id = event.get("match_id")

    if not video_name or not match_id:
        logger.error(f"Evento inválido: {event}")
        return

    payload = {
        "video_name": video_name,
        "match_id": match_id,
    }

    endpoint = f"{BACKEND_ENDPOINT}/analyze/run"

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(endpoint, json=payload)

        response.raise_for_status()

        logger.info(f"Evento enviado correctamente: {payload}")

    except httpx.RequestError as e:
        logger.exception(f"Error de red al enviar evento: {e}")

    except httpx.HTTPStatusError as e:
        logger.error(
            f"Backend respondió {e.response.status_code}: {e.response.text}"
        )