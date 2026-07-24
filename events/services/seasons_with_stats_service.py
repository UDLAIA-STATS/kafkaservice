from dataclasses import asdict, dataclass
from datetime import datetime
import logging
from typing import Dict, List

from decouple import config
import httpx
import backoff

logger = logging.getLogger(__name__)

TEAMS_ENDPOINT = config("TEAM_SERVICE")
STATS_ENDPOINT = config("STATS_ENDPOINT")


@dataclass
class SeasonData:
    id_temporada: int
    nombre_temporada: str
    nombre_torneo: str
    id_torneo: int
    velocidad_promedio: float
    distancia_promedio: float

@backoff.on_exception(backoff.expo, httpx.HTTPError, max_tries=3)
def handle_stats_by_season():
    matches_endpoint = f"{TEAMS_ENDPOINT}/partidos/all/?offset=10000"
    stats_endpoint = f"{STATS_ENDPOINT}/events/analyzed/matchs/"

    with httpx.Client(timeout=30.0) as client:
        matches_res = client.get(matches_endpoint)
        stats_res = client.get(stats_endpoint)

    if matches_res.status_code != 200:
        raise httpx.HTTPError(
            f"Error al obtener partidos: {matches_res.status_code}"
        )

    if stats_res.status_code != 200:
        raise httpx.HTTPError(
            f"Error al obtener estadísticas: {stats_res.status_code}"
        )

    matches = matches_res.json()["results"]

    analytics_by_match = {
        stat["match_id"]: stat
        for stat in stats_res.json()["data"]
    }

    tournaments: Dict[int, Dict] = {}

    for match in matches:
        stat = analytics_by_match.get(match["idpartido"])

        if stat is None:
            continue

        tournament_id = match["idtorneo"]

        if tournament_id not in tournaments:
            tournaments[tournament_id] = {
                "data": SeasonData(
                    id_temporada=match["idtemporada"],
                    nombre_temporada=match["temporada_nombre"],
                    id_torneo=tournament_id,
                    nombre_torneo=match["torneo_nombre"],
                    velocidad_promedio=0.0,
                    distancia_promedio=0.0,
                ),
                "speed_sum": 0.0,
                "distance_sum": 0.0,
                "count": 0,
            }

        tournament = tournaments[tournament_id]

        tournament["speed_sum"] += stat["avg_speed"]
        tournament["distance_sum"] += stat["avg_distance"]
        tournament["count"] += 1

    response_data = []

    for tournament in tournaments.values():
        data = tournament["data"]
        count = tournament["count"]

        data.velocidad_promedio = tournament["speed_sum"] / count
        data.distancia_promedio = tournament["distance_sum"] / count

        response_data.append(asdict(data))

    return response_data