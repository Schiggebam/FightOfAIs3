from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Tuple, List, Union, Optional, Dict

from src.ai.AI_GameStatus import AI_GameStatus
from src.ai.AI_MapRepresentation import AI_Building, AI_Army, Tile
from src.ai.toolkit import essentials
from src.ai.toolkit.essentials import get_neighbours, AI_OBJ
from src.misc.game_constants import error, Priority, UnitType, BuildingType, BuildingState


# ------------------------ Basic TOOLKIT FUNCTIONS/CLASSES: ------------------------


class CardinalDirection(Enum):
    """Cardinal directions in a hexagonal system (6)"""
    North = 0
    NorthEast = 1
    SouthEast = 2
    South = 3
    SouthWest = 4
    NorthWest = 5


@dataclass
class WaitOption:
    score: Priority
    weighted_score: float = 0


@dataclass
class UpgradeOption:
    type: BuildingType
    site: Tuple[int, int]
    score: Priority
    weighted_score: float = 0


@dataclass
class BuildOption:
    type: BuildingType
    site: Tuple[int, int]
    associated_tiles: List[Tuple[int, int]]
    score: Priority
    cardinal_direction: Optional[List[CardinalDirection]] = None
    threat_level: Optional[ThreatLevel] = None
    weighted_score: float = 0


@dataclass
class RecruitmentOption:
    type: UnitType
    score: Priority
    weighted_score: float = 0


@dataclass
class RaiseArmyOption:
    site: Tuple[int, int]
    score: Priority
    weighted_score: float = 0


@dataclass
class ScoutingOption:
    site: Tuple[int, int]
    score: Priority  # Caution changed this to Priority!!
    weighted_score: float = 0


@dataclass()
class ArmyMovementOption:
    target: Union[AI_Building, AI_Army, Tile]
    score: Priority
    next_step: Tuple[int, int]
    weighted_score: float = 0


Option = Union[BuildOption, RecruitmentOption, ScoutingOption, WaitOption, RaiseArmyOption, UpgradeOption]


class ThreatLevel(Enum):
    SECURE = -1
    NO_RISK = 0
    LOW_RISK = 1
    MEDIUM_RISK = 2
    HIGH_RISK = 3

    @staticmethod
    def increase(t: ThreatLevel) -> ThreatLevel:
        """Increase the threat level by one"""
        return ThreatLevel(min(3, t.value + 1))

    @staticmethod
    def decrease(t: ThreatLevel) -> ThreatLevel:
        """Decrease the threat level by one"""
        return ThreatLevel(max(-1, t.value - 1))

    @staticmethod
    def avg(t1: ThreatLevel, t2: ThreatLevel) -> ThreatLevel:
        return ThreatLevel(round((t1.value + t2.value) / 2))


class Compass:
    def __init__(self, center_tile: Tile, book=None):
        self.center_tile: Tile = center_tile
        if book is None:
            self.book: Dict[CardinalDirection, ThreatLevel] = {}
            for cd in CardinalDirection:
                self.book[cd] = ThreatLevel.NO_RISK
        else:
            self.book = book

    def get_threat_level(self, t: Tile) -> ThreatLevel:
        cd = self.get_cardinal_direction_obj(t, self.center_tile)
        if len(cd) == 1:
            return self.book[cd[0]]
        elif len(cd) == 2:
            return ThreatLevel.avg(self.book[cd[0]], self.book[cd[1]])

    def raise_threat_level(self, t: Tile):
        for cd in self.get_cardinal_direction_obj(t, self.center_tile):
            self.book[cd] = ThreatLevel.increase(self.book[cd])

    def lower_threat_level(self, t: Tile):
        for cd in self.get_cardinal_direction_obj(t, self.center_tile):
            self.book[cd] = ThreatLevel.decrease(self.book[cd])

    @staticmethod
    def get_cardinal_direction_obj(tile: Tile, base: Tile) -> List[CardinalDirection]:
        """wrapper function for get_cardinal_direction(...)"""
        cc1 = essentials.offset_to_cube_coord(tile)
        cc2 = essentials.offset_to_cube_coord(base)
        return Compass.get_cardinal_direction(cc1, cc2)

    @staticmethod
    def get_cardinal_direction(tile: Tuple[int, int, int], base: Tuple[int, int, int]) -> List[CardinalDirection]:
        """get the cardinal direction of the cube coordinates of a tile with respect to a base
        function may return two adjacent CDs. IN This case, the tile is placed on the border"""
        x_normal = tile[0] - base[0]
        y_normal = tile[1] - base[1]
        z_normal = tile[2] - base[2]
        if x_normal + y_normal + z_normal != 0:
            error("error in CD")
        ret = []
        if x_normal <= 0 and y_normal > 0 and z_normal <= 0:
            ret.append(CardinalDirection.SouthWest)
        if x_normal >= 0 and y_normal >= 0 and z_normal < 0:
            ret.append(CardinalDirection.South)
        if x_normal > 0 and y_normal <= 0 and z_normal <= 0:
            ret.append(CardinalDirection.SouthEast)
        if x_normal >= 0 and y_normal < 0 and z_normal >= 0:
            ret.append(CardinalDirection.NorthEast)
        if x_normal <= 0 and y_normal <= 0 and z_normal > 0:
            ret.append(CardinalDirection.North)
        if x_normal < 0 and y_normal >= 0 and z_normal >= 0:
            ret.append(CardinalDirection.NorthWest)
        return ret


# a = AI_Toolkit.offset_to_cube_xy(7, 10)
# b = AI_Toolkit.offset_to_cube_xy(10, 10)
# compass = Compass(None)
# print(compass.get_cardinal_direction(a, b))


@dataclass
class Weight:
    condition: Callable[..., bool]
    weight: float


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


def num_building(building_type: BuildingType, ai_stat: AI_GameStatus, count_under_construction=False):
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
    res_per_tile = Building.building_info[BuildingType.HUT]['resource_per_field']
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
