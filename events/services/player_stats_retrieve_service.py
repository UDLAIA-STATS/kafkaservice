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
class PlayerData:
    stat_id: int
    player_id: int
    player_name: str
    shirt_number: int
    team: str
    team_color: str
    analisys_date: str

    goals: int
    team_goals: int
    avg_speed_kmh: int
    distance_km: int
    heatmap_image_path: str


@dataclass
class MatchData:
    match_id: int
    match_date: str
    marcador: str
    team_heatmap_image_path: str
    players: List[PlayerData]


@backoff.on_exception(backoff.expo, httpx.HTTPError, max_tries=3)
def handle_stats_by_season(event: dict):
    season_id = event.get("season_id")
    responseData: List[Dict] = []

    season_endpoint = f"{TEAMS_ENDPOINT}/partidos/bytemporadas/?temporadaId={season_id}&page=1&offset=1000"
    stats_endpoint = f"{STATS_ENDPOINT}events/by_match"

    with httpx.Client(timeout=30.0) as client:
        matches_res = client.get(season_endpoint)
        logger.info(f"Respuesta de partidos: {matches_res.status_code}")

        if matches_res.status_code != 200:
            raise httpx.HTTPError(
                f"Error al obtener partidos: {matches_res.status_code}"
            )

        matches = matches_res.json()["results"]
        matches_ids = {match["idpartido"]: match for match in matches}

        for match_id, match_info in matches_ids.items():
            match_stats_endpoint = f"{stats_endpoint}/{match_id}/"
            match_stats_res = client.get(match_stats_endpoint)
            logger.info(f"Respuesta de estadísticas: {match_stats_res.status_code}")

            if match_stats_res.status_code != 200:
                raise httpx.HTTPError(
                    f"Error al obtener estadísticas: {match_stats_res.status_code}"
                )

            match_stats = match_stats_res.json()["data"]
            match_data = MatchData(
                marcador=f"{match_info["marcadorequipolocal"]} - {match_info['marcadorequipovisita']}",
                match_date=datetime.strptime(
                    match_info["fecha"], "%Y-%m-%d %H:%M:%S"
                ).strftime("%d-%m-%Y %H:%M:%S"),
                match_id=match_info["idpartido"],
                team_heatmap_image_path=match_stats[0]["team_heatmap_image_path"],
                players=[
                    PlayerData(
                        analisys_date=stat["analisys_date"],
                        avg_speed_kmh=stat["avg_speed_kmh"],
                        distance_km=stat["distance_km"],
                        goals=stat["goals"],
                        heatmap_image_path=stat["heatmap_image_path"],
                        player_id=stat["player_id"],
                        player_name=stat["player_name"],
                        shirt_number=stat["shirt_number"],
                        team=stat["team"],
                        stat_id=stat["stat_id"],
                        team_color=stat["team_color"],
                        team_goals=stat["team_goals"],
                    )
                    for stat in match_stats
                ],
            )

            responseData.append(asdict(match_data))

    return responseData
