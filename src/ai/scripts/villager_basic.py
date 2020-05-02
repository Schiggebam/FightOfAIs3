from typing import Dict, Any, List, Tuple, Callable

from src.ai.AI_GameStatus import AI_GameStatus
from src.ai.toolkit.basic import ArmyMovementOption, RecruitmentOption, Option, RaiseArmyOption
from src.ai.ai_npc import AI_NPC
from src.misc.game_constants import BuildingType, UnitType


def on_setup(prop: Dict[str, Any]):
    prop['army_movement'] = "villager"

    prop['threshold_army_movement'] = 3
    """below this diplomatic value, a player is considered to be hostile"""
    prop['diplo_aggressive_threshold'] = 0
    """Does hold all possible buildings with their prerequisite"""
    prop['buildings'] = [(None, BuildingType.VILLAGE_1),
                          (BuildingType.VILLAGE_1, BuildingType.VILLAGE_2),
                          (BuildingType.VILLAGE_2, BuildingType.VILLAGE_3)]
    """contains all units available to this ai"""
    prop['units'] = [UnitType.KNIGHT]

    prop['range_claimed_tiles'] = 1
    """holds the max amount of buildings for this player"""
    prop['max_building_count'] = 1


def setup_weights(self: AI_NPC) -> List[Tuple[Callable, float]]:
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

    return w


def setup_movement_weights(self: AI_NPC) -> List[Tuple[Callable, float]]:
    w: List[Tuple[Callable, float]] = []

    def w1(elem: ArmyMovementOption, ai_stat: AI_GameStatus) -> bool:
        """do the patrols in passive state"""
        if self.state == AI_NPC.AI_State.PASSIVE:
            return True
        return False

    w.append((w1, 2))

    def w2(elem: ArmyMovementOption, ai_stat: AI_GameStatus) -> bool:
        """if aggressive, do only attack if the army has at least a population of 6"""
        if self.state == AI_NPC.AI_State.AGGRESSIVE:
            if ai_stat.me.population > 5:
                return True
        return False

    w.append((w2, 2))

    def w3(elem: ArmyMovementOption, ai_stat: AI_GameStatus) -> bool:
        """if defencive, defend at all cost"""
        if self.state == AI_NPC.AI_State.DEFENSIVE:
            return True
        return False

    w.append((w3, 2))

    return w
