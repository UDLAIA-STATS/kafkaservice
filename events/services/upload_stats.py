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
    target_color = event.get("color")
    logger.info(
        "handle_upload_stats → match_id %s  (type=%s)", match_id, type(match_id)
    )

    if not stats or not match_id or not target_color:
        logger.error(f"Evento inválido: {event}")
        return

    player_endpoint = f"{PLAYERS_ENDPOINT}/jugadores/shirt"
    partido_endpoint = f"{TEAMS_ENDPOINT}/partidos/{match_id}/"
    stats_endpoint = f"{STATS_ENDPOINT}/events/bulk/"

    filtered_stats = filter_players_by_color(stats, target_color)
    logger.info(f"Jugadores filtrados: {len(filtered_stats)} de {len(stats)}")

    processed_stats = []

    try:
        with httpx.Client(timeout=30.0) as client:
            logger.info(f"Llamando a endpoint de partido: {partido_endpoint}")
            partido_response = client.get(partido_endpoint)

            logger.info("Informar que el partido fue subido y analizado")
            update_response = client.post(
                f"{partido_endpoint}update/", json={"partidosubido": True}
            )
            logger.info(f"Respuesta de update partido: {update_response.status_code}")

            partido_data = None
            if partido_response.status_code == 200:
                partido_data = partido_response.json()
            else:
                logger.error(f"No se encontró partido para match_id {match_id}")

        for stat in filtered_stats:
            shirt_number = stat.get("shirt_number")

            if not shirt_number or shirt_number == "" or shirt_number is None:
                logger.warning(
                    f"Jugador sin shirt_number reconocido: player_id={stat.get('player_id')}"
                )
                continue

            try:
                shirt_number = int(shirt_number)
                if shirt_number == 0:
                    continue

            except (ValueError, TypeError):
                logger.warning(
                    f"Shirt_number inválido: {shirt_number}, marcando como None"
                )
                stat["player_id"] = None
                processed_stats.append(stat)
                continue

            try:
                with httpx.Client(timeout=30.0) as client:
                    shirt_endpoint = f"{player_endpoint}/{shirt_number}/"
                    logger.info(f"Llamando a endpoint de jugador: {shirt_endpoint}")
                    player_response = client.get(shirt_endpoint)

                    if player_response.status_code != 200:
                        logger.warning(
                            f"No se encontró jugador para shirt_number {shirt_number}, "
                            "marcando como None"
                        )
                        stat["player_id"] = None
                        processed_stats.append(stat)
                        continue

                    player_data = player_response.json()
                    player_id = player_data.get("id")

                    if not player_id:
                        logger.warning(
                            f"El jugador con shirt_number {shirt_number} "
                            "no tiene ID, marcando como None"
                        )
                        stat["player_id"] = None
                        processed_stats.append(stat)
                        continue

                    stat["player_id"] = player_id

                    if partido_data:
                        team = int(stat["team"])
                        if team == 1:
                            real_team = partido_data.get("idequipolocal")
                        else:
                            real_team = partido_data.get("idequipovisitante")

                        if real_team:
                            stat["team"] = real_team
                        else:
                            logger.warning(
                                f"No se encontró equipo para team={team}, dejando valor original"
                            )
                        stat["team_color"] = f'[{target_color}]'
                    else:
                        logger.warning(
                            "No hay datos del partido, dejando team original"
                        )

                    logger.info(
                        f"Procesado player_id {player_id} para shirt_number {shirt_number}"
                    )

            except httpx.RequestError as e:
                logger.exception(
                    f"Error de red al procesar shirt_number {shirt_number}: {e}"
                )
                stat["player_id"] = None
            except Exception as e:
                logger.exception(
                    f"Error inesperado al procesar shirt_number {shirt_number}: {e}"
                )
                stat["player_id"] = None

            processed_stats.append(stat)

        if not processed_stats:
            logger.warning("No hay stats para enviar al backend")
            return

        logger.info(
            f"Enviando {len(processed_stats)} stats al endpoint: {stats_endpoint}"
        )

        for stat in processed_stats:
            with httpx.Client(timeout=30.0) as client:
                logger.info(f"Enviando payload con {len(processed_stats)} jugadores")
                client.post(stats_endpoint, json=stat)

    except httpx.RequestError as e:
        logger.exception(f"Error de red al enviar evento: {e}")
    except httpx.HTTPStatusError as e:
        logger.error(f"Backend respondió {e.response.status_code}: {e.response.text}")
    except Exception as e:
        logger.exception(f"Error inesperado al manejar upload stats: {e}")
