from src.misc.game_constants import *


def unit_type_conversion(ut: UnitType) -> str:
    if ut == UnitType.MERCENARY:
        return "mercenary"
    elif ut == UnitType.KNIGHT:
        return "knight"
    elif ut == UnitType.BABARIC_SOLDIER:
        return "barbaric soldier"
    return "unknown unit"

def building_state_conversion(bs: BuildingState) -> str:
    if bs == BuildingState.UNDER_CONSTRUCTION:
        return "under construction"
    elif bs == BuildingState.ACTIVE:
        return "active"
    elif bs == BuildingState.DESTROYED:
        return "destroyed"
    return "unknown state"


def building_type_conversion(bt: BuildingType) -> str:
    if bt == BuildingType.HUT:
        return "hut"
    elif bt == BuildingType.FARM:
        return "farm"
    elif bt == BuildingType.VILLA:
        return "villa"
    elif bt == BuildingType.CAMP_1:
        return "barbaric camp level 1"
    elif bt == BuildingType.CAMP_2:
        return "barbaric camp level 2"
    elif bt == BuildingType.CAMP_3:
        return "barbaric camp level 3"
    elif bt == BuildingType.VILLAGE:
        return "village"
    return "unknown building"
