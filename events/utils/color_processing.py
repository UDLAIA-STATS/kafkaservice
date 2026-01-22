import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

def parse_rgb_string(rgb_string: str) -> List[int]:
    """Convierte string 'R,G,B' a lista [R, G, B]"""
    try:
        return [int(x.strip()) for x in rgb_string.split(',')]
    except (ValueError, AttributeError):
        logger.error(f"Formato de color inválido: {rgb_string}")
        return [0, 0, 0]

def color_distance_rgb(target_rgb: List[int], team_rgb: List[int]) -> float:
    """Calcula la distancia euclidiana entre dos colores RGB"""
    return sum((a - b) ** 2 for a, b in zip(target_rgb, team_rgb)) ** 0.5

def filter_players_by_color(
        stats: List[Dict[str, Any]],
        target_rgb_string: str,
        threshold: float = 30.0) -> List[Dict[str, Any]]:
    """
    Filtra jugadores por cercanía de color RGB o team_color=None
    
    Args:
        stats: Lista de estadísticas de jugadores
        target_rgb_string: Color objetivo en formato 'R,G,B'
        threshold: Distancia máxima permitida para considerar colores cercanos
    
    Returns:
        Lista filtrada de estadísticas
    """
    filtered_stats = []
    target_rgb = parse_rgb_string(target_rgb_string)
    
    for stat in stats:
        team_color = stat.get("team_color")
            
        # team_color también viene como string 'R,G,B' o lista RGB
        if isinstance(team_color, str):
            team_rgb = parse_rgb_string(team_color)
        elif isinstance(team_color, list) and len(team_color) == 3:
            team_rgb = team_color
        else:
            logger.warning(f"Formato de team_color desconocido: {team_color}")
            filtered_stats.append(stat)
            continue
            
        try:
            distance = color_distance_rgb(target_rgb, team_rgb)
            if distance <= threshold:
                filtered_stats.append(stat)
                logger.info(f"Jugador incluido - Color RGB: {team_rgb}, Distancia: {distance:.2f}")
            else:
                logger.info(f"Jugador excluido - Color RGB: {team_rgb}, Distancia: {distance:.2f}")
        except Exception as e:
            logger.error(f"Error al calcular distancia de color RGB: {e}")
            filtered_stats.append(stat)

    return filtered_stats
