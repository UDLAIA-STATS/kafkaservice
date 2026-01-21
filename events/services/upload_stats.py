import logging
from decouple import config
import httpx
import backoff

from events.utils.color_processing import filter_players_by_color

logger = logging.getLogger(__name__)

PLAYERS_ENDPOINT = config("PLAYERS_ENDPOINT")
TEAMS_ENDPOINT = config("TEAM_SERVICE")
STATS_ENDPOINT = config("STATS_ENDPOINT")

@backoff.on_exception(backoff.expo, httpx.HTTPError, max_tries=3)
def handle_upload_stats(event: dict):
    stats = event.get("stats")
    match_id = event.get("match_id")
    # target_color = event.get("color")
    logger.info("handle_upload_stats → match_id %s  (type=%s)", match_id, type(match_id))

    if not stats or not match_id: #or not target_color:
        logger.error(f"Evento inválido: {event}")
        return

    player_endpoint = f"{PLAYERS_ENDPOINT}/jugadores/shirt"
    partido_endpoint = f"{TEAMS_ENDPOINT}/partidos/{match_id}/"
    stats_endpoint = f"{STATS_ENDPOINT}/events/bulk/"

    # filtered_stats = filter_players_by_color(stats, target_color)
    # logger.info(f"Jugadores filtrados: {len(filtered_stats)} de {len(stats)}")

    try:
        for stat in stats:
            shirt_number = stat.get("shirt_number")
            if not shirt_number or shirt_number == "" or shirt_number is None:
                logger.error(f"Falta shirt_number en stat: {stat}")
                stat["player_id"] = None
                continue

            with httpx.Client(timeout=30.0) as client:
                shirt_endpoint = f'{player_endpoint}/{shirt_number}/'
                logger.info(f"Llamando a endpoint de jugador: {shirt_endpoint}")
                logger.info(f"Llamando a endpoint de partido: {partido_endpoint}")
                player_response = client.get(shirt_endpoint)
                partido_response = client.get(partido_endpoint)

            if not player_response.status_code == 200:
                logger.error(f"No se encontró jugador para shirt_number {shirt_number}")
                stat["player_id"] = None
                continue

            player_data = player_response.json()
            stat["player_id"] = player_data.get("id")
            team = int(stat["team"])

            if partido_response.status_code != 200:
                logger.error(f"No se encontró partido para match_id {match_id}")
                stat["team"] = None
                continue

            if team == 1:
                real_team = partido_response.json().get("idequipolocal", None)
            else:
                real_team = partido_response.json().get("idequipovisitante", None)

            stat["team"] = real_team

            logger.info(f"Encontrado player_id {stat['player_id']} para shirt_number {shirt_number}")

        logger.info(f"Enviando stats al endpoint: {stats_endpoint} para match_id {match_id}")
        logger.info(f"Stats a enviar: {stats}")
        with httpx.Client(timeout=30.0) as client:
            stats_response = client.post(stats_endpoint, json={"players": stats})

        stats_response.raise_for_status()
        logger.info(f"Stats subidos exitosamente para match_id {match_id}")

    except httpx.RequestError as e:
        logger.exception(f"Error de red al enviar evento: {e}")
    except httpx.HTTPStatusError as e:
        logger.error(
            f"Backend respondió {e.response.status_code}: {e.response.text}"
        )


