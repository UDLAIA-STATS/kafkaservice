import logging
from typing import List
from decouple import config
import httpx
import backoff

logger = logging.getLogger(__name__)

PLAYERS_ENDPOINT = config("PLAYERS_ENDPOINT")
TEAMS_ENDPOINT = config("TEAM_SERVICE")

@backoff.on_exception(backoff.expo, httpx.HTTPError, max_tries=3)
def handle_upload_stats(event: dict):
    stats = event.get("stats")
    match_id = event.get("match_id")

    if not stats or not match_id:
        logger.error(f"Evento inválido: {event}")
        return

    player_endpoint = f"{PLAYERS_ENDPOINT}/jugadores/shirt/" + "{shirt_number}/"
    partido_endpoint = f"{TEAMS_ENDPOINT}/partidos/{match_id}/"
    stats_endpoint = f"{PLAYERS_ENDPOINT}/stats/upload_consolidated/"

    try:
        for stat in stats:
            shirt_number = stat.get("shirt_number")
            if not shirt_number:
                logger.error(f"Falta shirt_number en stat: {stat}")
                stat["player_id"] = None
                continue

            with httpx.Client(timeout=10.0) as client:
                player_response = client.get(player_endpoint.format(shirt_number=int(shirt_number)))
                partido_response = client.get(partido_endpoint)

            player_response.raise_for_status()
            partido_response.raise_for_status()

            player_data = player_response.json()
            stat["player_id"] = player_data.get("id")
            team = int(stat["team"])

            if team == 1:
                real_team = partido_response.json().get("idequipolocal", None)
            else:
                real_team = partido_response.json().get("idequipovisitante", None)

            stat["team"] = real_team

            logger.info(f"Encontrado player_id {stat['player_id']} para shirt_number {shirt_number}")

        with httpx.Client(timeout=10.0) as client:
            stats_response = client.post(stats_endpoint, json={"players": stats})

        stats_response.raise_for_status()
        logger.info(f"Stats subidos exitosamente para match_id {match_id}")

    except httpx.RequestError as e:
        logger.exception(f"Error de red al enviar evento: {e}")
    except httpx.HTTPStatusError as e:
        logger.error(
            f"Backend respondió {e.response.status_code}: {e.response.text}"
        )
