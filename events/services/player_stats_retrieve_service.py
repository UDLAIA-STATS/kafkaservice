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
    crop_image_path: str
    player_movement_trajectories_path: str


@dataclass
class MatchData:
    match_id: int
    nombre_temporada: str
    nombre_torneo: str
    id_temporada: int
    id_torneo: int
    match_date: str
    marcador: str
    team_heatmap_image_path: str
    movement_trajectories_path: str
    team_color_time_kde_path: str
    players: List[PlayerData]


@backoff.on_exception(backoff.expo, httpx.HTTPError, max_tries=3)

def handle_stats_details(season_id: int, torneo_id: int):
    responseData: List[Dict] = []

    season_endpoint = f"{TEAMS_ENDPOINT}/partidos/bytemporadas/?temporadaId={season_id}&page=1&offset=10000"
    stats_endpoint = f"{STATS_ENDPOINT}/events/by-match"

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
                continue

            if match_info["idtorneo"] != torneo_id:
                continue

            match_stats = match_stats_res.json()["data"]

            if not match_stats:
                continue

            match_data = MatchData(
                id_temporada=match_info["idtemporada"],
                id_torneo=match_info["idtorneo"],
                nombre_temporada=match_info["temporada_nombre"],
                nombre_torneo=match_info["torneo_nombre"],
                marcador=f"{match_info["marcadorequipolocal"]} - {match_info['marcadorequipovisitante']}",
                match_date=datetime.fromisoformat(match_info["fechapartido"]).strftime(
                    "%d-%m-%Y %H:%M"
                ),
                match_id=match_info["idpartido"],
                team_heatmap_image_path=match_stats[0]["team_heatmap_image_path"],
                movement_trajectories_path=match_stats[0]["movement_trajectories_path"],
                team_color_time_kde_path=match_stats[0]["team_color_time_kde_path"],
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
                        team=match_info["equipo_local_nombre"],
                        stat_id=stat["stat_id"],
                        team_color=stat["team_color"],
                        team_goals=stat["team_goals"],
                        crop_image_path=stat["crop_image_path"],
                        player_movement_trajectories_path=stat[
                            "player_movement_trajectories_path"
                        ],
                    )
                    for stat in match_stats
                ],
            )

            responseData.append(asdict(match_data))

    return responseData
