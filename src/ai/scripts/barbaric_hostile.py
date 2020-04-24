from typing import Dict, Any, List, Tuple, Callable

from src.ai.AI_MapRepresentation import AI_Building, AI_Army
from src.ai.ai_npc import AI_NPC
from src.ai.AI_GameStatus import AI_GameStatus
from src.ai.ai_blueprint import ArmyMovementOption, Option, RaiseArmyOption, RecruitmentOption, WaitOption
from src.misc.game_constants import BuildingType, UnitType


def on_setup(prop: Dict[str, Any]):
    prop['army_movement'] = "barbaric"
    """Army movements have to have at least this value to be considered reasonable"""
    prop['threshold_army_movement'] = 2
    """below this diplomatic value, a player is considered to be hostile"""
    prop['diplo_aggressive_threshold'] = 2
    """Does hold all possible buildings with their prerequisite"""
    prop['buildings'] = [(None, BuildingType.CAMP_1),
                          (BuildingType.CAMP_1, BuildingType.CAMP_2),
                          (BuildingType.CAMP_2, BuildingType.CAMP_3)]
    """contains all units available to this ai"""
    prop['units'] = [UnitType.BABARIC_SOLDIER]
    """minumum range away from building that the tile is still considered claimed.
    Only claimed tiles will be considered to be buildable"""
    prop['range_claimed_tiles'] = 1
    """holds the max amount of buildings for this player"""
    prop['max_building_count'] = 3


def setup_weights(self) -> List[Tuple[Callable, float]]:
    w: List[Tuple[Callable, float]] = []

    def w1(elem: Option, ai_stat: AI_GameStatus) -> bool:
        """If it is possible to raise an army, do so!"""
        if type(elem) is RaiseArmyOption:
            return True
        return False
    w.append((w1, 2))

    def w2(elem: Option, ai_stat: AI_GameStatus) -> bool:
        """If state is passive, stop recruiting at 70%"""
        if type(elem) is RecruitmentOption:
            if self.state == AI_NPC.AI_State.PASSIVE:
                if ai_stat.me.population >= 0.7 * ai_stat.me.population_limit:
                    return True
        return False
    w.append((w2, -2))

    def w3(elem: Option, ai_stat: AI_GameStatus) -> bool:
        """generally don't weight the wait option too high"""
        if type(elem) is WaitOption:
            return True
        return False
    w.append((w3, -1))

    return w


def setup_movement_weights(self: AI_NPC) -> List[Tuple[Callable, float]]:
    w: List[Tuple[Callable, float]] = []

    def w1(elem: ArmyMovementOption, ai_stat: AI_GameStatus) -> bool:
        """reduce army movement in passive state"""
        if self.state == AI_NPC.AI_State.PASSIVE:
            return True
        return False
    w.append((w1, -2))

    def w2(elem: ArmyMovementOption, ai_stat: AI_GameStatus) -> bool:
        """only strong armies schould attack a barracks"""
        if type(elem.target) is AI_Building:
            if elem.target.type is BuildingType.BARRACKS:
                if ai_stat.map.army_list[0].population < 20:
                    return True
        return False
    w.append((w2, -3))

    def w3(elem: ArmyMovementOption, ai_stat: AI_GameStatus) -> bool:
        """don't move army if army has less than 3 supply"""
        if ai_stat.me.population < 4:
            return True
        return False
    w.append((w3, -2))

    def w4(elem: ArmyMovementOption, ai_stat: AI_GameStatus) -> bool:
        """discourage attacking a stronger army"""
        if type(elem.target) is AI_Army:
            if ai_stat.map.army_list[0].population < elem.target.population:
                return True
        return False
    w.append((w4, -1))

    return w
