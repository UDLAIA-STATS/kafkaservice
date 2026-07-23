from dataclasses import asdict, dataclass
import logging
from typing import Dict, List

from decouple import config
import httpx
import backoff

logger = logging.getLogger(__name__)

TEAMS_ENDPOINT = config("TEAM_SERVICE")
STATS_ENDPOINT = config("STATS_ENDPOINT")


@dataclass
class StructResponse:
    torneo: str
    temporada: str
    resultado: str
    fecha_analisis: str
    fecha_partido: str
    velocidad_promedio: float
    distancia_promedio: float


@backoff.on_exception(backoff.expo, httpx.HTTPError, max_tries=3)
def handle_general_stats(event: dict):
    retrieve_stats_endpoint = f"{STATS_ENDPOINT}/events/analyzed/matchs/"
    matches_endpoint = f"{TEAMS_ENDPOINT}/partidos/all/?offset=10000"
    struct_response: List[Dict] = []

    with httpx.Client(timeout=30.0) as client:
        response = client.get(retrieve_stats_endpoint)
        logger.info(f"Respuesta de stats: {response.status_code}")

        if response.status_code != 200:
            raise httpx.HTTPError(f"Error al obtener stats: {response.status_code}")

        stats = response.json()["data"]

        matches_res = client.get(matches_endpoint)
        logger.info(f"Respuesta de partidos: {matches_res.status_code}")

        if matches_res.status_code != 200:
            raise httpx.HTTPError(
                f"Error al obtener partidos: {matches_res.status_code}"
            )

        matches = matches_res.json()["results"]
        matches_ids = {match["id"]: match for match in matches}

        for stat in stats:
            match_id = stat["match_id"]
            match_info = matches_ids.get(match_id)

            if not match_info:
                continue

            marcador = f"{match_info["marcadorequipolocal"]} - {match_info['marcadorequipovisitante']}"
            item = StructResponse(
                torneo=match_info["torneo_nombre"],
                temporada=match_info["temporada_nombre"],
                resultado=marcador,
                fecha_analisis=stat["created_at"],
                fecha_partido=match_info["fechapartido"],
                velocidad_promedio=stat["avg_speed"],
                distancia_promedio=stat["avg_distance"],
            )
            struct_response.append(asdict(item))

    return struct_response
