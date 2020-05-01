from typing import Optional

from src.ai.AI_GameStatus import AI_GameStatus
from src.ai.AI_MapRepresentation import Tile
from src.ai.toolkit.essentials import AI_OBJ, get_neighbours
from src.misc.game_constants import error, BuildingType, BuildingState


# ------------------------ Basic TOOLKIT FUNCTIONS: ------------------------


def num_resources_on_adjacent(obj: AI_OBJ) -> int:
    """
    returns the number of resources, which are located on adjacent fields

    :param obj: any AI_object.
    :return: number of resource fields
    """
    tile: Tile = get_tile_from_ai_obj(obj)  # assuming this is not none
    value = 0
    for n in get_neighbours(tile):
        if n.has_resource():
            value = value + 1
    return value


def get_tile_from_ai_obj(obj: AI_OBJ) -> Optional[Tile]:
    """

    :param obj:
    :return:
    """
    tile: Optional[Tile] = None
    if type(obj) is Tile:
        tile = obj
    else:
        tile = obj.base_tile
    if tile is None:  # is None
        error("Unable to get Tile from AI_Obj")
    return tile


def num_buidling(building_type: BuildingType, ai_stat: AI_GameStatus, count_under_construction=False):
    """
    get the total number of buildings of a specific type

    :param building_type:
    :param ai_stat:
    :param count_under_construction: if set to true, the buildings which are under construction, are counted as well
    :return: the total count
    """
    value = 0
    for b in ai_stat.map.building_list:
        if b.type == building_type:
            if count_under_construction:
                if b.state == BuildingState.UNDER_CONSTRUCTION or b.state == BuildingState.ACTIVE:
                    value = value + 1
            else:
                if b.state == BuildingState.ACTIVE:
                    value = value + 1
    return value


def has_building_under_construction(building_type: BuildingType, ai_stat: AI_GameStatus):
    """

    :param building_type:
    :param ai_stat:
    :return: true, if a building of the specified type is under construction
    """
    for b in ai_stat.map.building_list:
        if b.type == building_type:
            if b.state == BuildingState.UNDER_CONSTRUCTION:
                return True
    return False


def estimate_res_income(ai_stat: AI_GameStatus) -> int:
    """
    roughly estimates the resource income. Does not take the fact into account, that resources might mine out
    :return:
    """

    from src.misc.building import Building
    res_per_tile = Building.building_info['resource_per_field']
    value = 0
    for b in ai_stat.map.building_list:
        if b.type == BuildingType.HUT:
            for n in get_neighbours(b):
                if n.has_resource():
                    value = value + res_per_tile
    return value


def estimate_cult_income(ai_stat: AI_GameStatus):
    """
    roughly estimates the culture income
    :param ai_stat:
    :return:
    """
    for b in ai_stat.map.building_list:
        pass
