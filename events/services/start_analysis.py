import logging
from asgiref.sync import async_to_sync
import backoff
from channels.layers import get_channel_layer
from decouple import config
import httpx

logger = logging.getLogger(__name__)

TEAMS_ENDPOINT = config("TEAM_SERVICE")
ANALYSIS_ENDPOINT = config("ANALYSIS_SERVICE")

@backoff.on_exception(backoff.expo, httpx.HTTPError, max_tries=3)
def handle_start_analysis(event: dict):
    id_partido = event.get("id_partido")
    color = event.get("color")
    video_id = event.get("video_id")
    partido_endpoint = f"{TEAMS_ENDPOINT}/partidos/{id_partido}/update/"

    if video_id is None or color is None or id_partido is None:
        logger.error(f"Evento inválido: {event}")
        return
    
    try:
        with httpx.Client(timeout=30.0) as client:
            update_response = client.post(partido_endpoint, json={"partidosubido": True})
            analysis_response = client.post(f"{ANALYSIS_ENDPOINT}/", json={
                "match_id": id_partido,
                "color": color,
                "video_name": video_id
            })
            logger.info(f"Respuesta de update partido: {update_response.status_code}")
            logger.info(f"Respuesta de análisis: {analysis_response.status_code}")
    except httpx.HTTPError as e:
        logger.error(f"Error en la solicitud HTTP: {e}")
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
