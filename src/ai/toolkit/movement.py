from typing import Optional, List, Tuple

from src.ai.AI_MapRepresentation import Tile
from src.ai.toolkit import essentials
from src.misc.game_constants import error


# ------------------------ Movement TOOLKIT FUNCTIONS: ------------------------


def next_step_to_target(current_tile: Tile, target_tile: Tile, domain: List[Tile]) -> Tuple[Optional[Tile], int]:
    """
    basic movement, returns next step, not the complete path

    :param current_tile: current tile of the walkable entity
    :param target_tile: target
    :param domain: the search domain, typically a subset of the walkable tiles
    :return: None, if no path is found, otherwise the next tile (step) where the army can move and the distance of the path
    """
    if not current_tile:
        error("current tile is None")
        return None, -1
    if not target_tile:
        error("target tile is None")
        return None, -1
    path = essentials.a_star(current_tile, target_tile, domain)
    if len(path) <= 1:  # no path found
        return None, -1
    return path[1], len(path) - 1          # return next step and distance of the path


def evasive_movement(current_tile: Tile, target_tile: Tile, domain: List[Tile]) -> Tuple[Optional[Tile], int]:
    """
    This movement calculates the next step which maximizes the distance to the target_tile
    Use with method to avoid collision between the entity placed on the current_tile, with a potentially
    hostile entity located on the target_tile

    :param current_tile: tile of the evading entity
    :param target_tile: tile of the hostile entity
    :param domain: the search domain, typically a subset of the walkable tiles
    :return: None, if no path is found, otherwise the next step and the distance of the resulting distance to target
    """
    if not current_tile:
        error("current tile is None")
        return None, -1
    if not target_tile:
        error("target tile is None")
        return None, -1
    longest_path: Tuple[int, Optional[Tile]] = (-1, None)
    for nei in essentials.get_neighbours_on_set(current_tile, domain):
        step, dist = next_step_to_target(nei, target_tile, domain)
        if step:
            if dist > longest_path[0]:
                longest_path = (dist, nei)

    return longest_path[1], longest_path[0]


def protective_movement(current_tile: Tile, target_tile: Tile, protected_tile: Tile,
                        domain: List[Tile]) -> Tuple[Optional[Tile], int]:
    """
    If an army/obj chooses to use protective movement, it will stay close to the entity it is protecting
    It will position itself such that it intercepts the incoming hostile entity on the target tile if possible

    :param current_tile: tile of the entity which is protecting (friendly army for instance)
    :param target_tile: tile of the hostile entity
    :param protected_tile: tile of the entity which is to be protected
    :param domain: the search domain, typically a subset of the walkable tiles
    :return: None if there is a problem or no path is found, otherwise the next step and the size of the path
    """
    if not (current_tile and target_tile and protected_tile):
        error("a tile is None")
        return None, -1
    shortest_path: Tuple[int, Optional[Tile]] = (1000, None)
    for nei in essentials.get_neighbours_on_set(protected_tile, domain):
        step, dist = next_step_to_target(nei, target_tile, domain)
        if step:
            if dist < shortest_path[0]:
                shortest_path = (dist, nei)
    return next_step_to_target(current_tile, shortest_path[1], domain)



