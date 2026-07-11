import logging
import numpy as np
from typing import Any, Dict, List
from skimage import color

logger = logging.getLogger(__name__)


def parse_rgb_string(rgb_string: str) -> List[int]:
    """Convierte string 'R,G,B' a lista [R, G, B] de enteros."""
    try:
        logger.info(f"Parseando color RGB desde string: {rgb_string}")
        return [int(x.strip()) for x in rgb_string.split(",")]
    except (ValueError, AttributeError) as e:
        logger.error(f"Formato de color inválido: {rgb_string} - {e}")
        return [0, 0, 0]

def rgb_string_to_lab(color_str: str) -> np.ndarray:
    """Convierte una cadena 'R,G,B' a un vector LAB (np.ndarray shape (3,))."""
    try:
        rgb = np.array(
            [int(x.strip()) for x in color_str.split(",")],
            dtype=np.float32,
        ) / 255.0
        return color.rgb2lab(rgb.reshape(1, 1, 3))[0, 0]
    except Exception as e:
        logger.error(f"Error convirtiendo a LAB: {color_str} - {e}")
        return np.array([0.0, 0.0, 0.0], dtype=np.float32)


def lab_to_rgb_string(lab: np.ndarray) -> str:
    """Convierte un vector LAB a cadena 'R,G,B' (valores enteros 0-255)."""
    try:
        lab = np.asarray(lab, dtype=np.float32).reshape(1, 1, 3)
        rgb = color.lab2rgb(lab)[0, 0]
        rgb = np.clip(rgb * 255.0, 0, 255).astype(np.uint8)
        return f"{rgb[0]},{rgb[1]},{rgb[2]}"
    except Exception as e:
        logger.error(f"Error convirtiendo desde LAB: {lab} - {e}")
        return "0,0,0"


def color_distance(
    target_rgb: List[int],
    team_rgb: List[int],
    use_lab: bool = True
) -> float:
    """
    Calcula la distancia euclidiana entre dos colores.

    Args:
        target_rgb: color objetivo como lista [R, G, B]
        team_rgb: color del equipo como lista [R, G, B]
        use_lab: si True, convierte ambos a LAB y calcula distancia en ese espacio;
                 si False, calcula distancia RGB euclidiana.

    Returns:
        Distancia (float). En RGB puede ser > 0; en LAB también.
    """
    if use_lab:
        # Convertir a cadena y luego a LAB
        target_str = f"{target_rgb[0]},{target_rgb[1]},{target_rgb[2]}"
        team_str = f"{team_rgb[0]},{team_rgb[1]},{team_rgb[2]}"
        lab1 = rgb_string_to_lab(target_str)
        lab2 = rgb_string_to_lab(team_str)
        # Distancia euclidiana en espacio LAB
        return float(np.linalg.norm(lab1 - lab2))
    else:
        # Distancia RGB original
        return sum((a - b) ** 2 for a, b in zip(target_rgb, team_rgb)) ** 0.5


def filter_players_by_color(
    stats: List[Dict[str, Any]],
    target_rgb_string: str,
    threshold: float = 200.0,
    use_lab: bool = True,
) -> List[Dict[str, Any]]:
    """
    Filtra jugadores por cercanía de color (RGB o LAB).

    Args:
        stats: Lista de estadísticas de jugadores.
        target_rgb_string: Color objetivo en formato 'R,G,B'.
        threshold: Distancia máxima permitida (ajustar según espacio usado).
        use_lab: Si True, usa distancia LAB (más perceptual); si False, usa RGB.

    Returns:
        Lista filtrada de estadísticas (jugadores cuyo color esté dentro del umbral).
    """
    filtered_stats = []
    target_rgb = parse_rgb_string(target_rgb_string)

    for stat in stats:
        team_color = stat.get("team_color")

        # Ahora team_color siempre es una cadena 'R,G,B' (formato unificado)
        if isinstance(team_color, str):
            team_rgb = parse_rgb_string(team_color)
        elif isinstance(team_color, list) and len(team_color) == 3:
            # Si por casualidad llega como lista, la convertimos a cadena para mantener consistencia
            team_rgb = team_color
            logger.warning("team_color es lista, se esperaba cadena. Convirtiendo internamente.")
        else:
            logger.warning(f"Formato de team_color desconocido: {team_color}")
            filtered_stats.append(stat)
            continue

        try:
            distance = color_distance(target_rgb, team_rgb, use_lab=use_lab)
            if distance <= threshold:
                filtered_stats.append(stat)
                logger.info(
                    f"Jugador incluido - Color RGB: {team_rgb}, Distancia: {distance:.2f}"
                )
            else:
                logger.info(
                    f"Jugador excluido - Color RGB: {team_rgb}, Distancia: {distance:.2f}"
                )
        except Exception as e:
            logger.error(f"Error al calcular distancia de color: {e}")
            filtered_stats.append(stat)

    return filtered_stats
