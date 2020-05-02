from typing import Any, Dict, Callable, Tuple, List

from src.ai.toolkit import essentials
from src.ai.AI_GameStatus import AI_GameStatus
from src.ai.AI_Macedon import AI_Mazedonian
from src.ai.AI_MapRepresentation import AI_Army, AI_Building
from src.ai.toolkit.basic import WaitOption, BuildOption, RecruitmentOption, ScoutingOption, RaiseArmyOption, \
    has_building_under_construction, UpgradeOption
from src.misc.game_constants import hint, BuildingType


def on_setup(prop: Dict[str, Any]):
    """Idea: Move all adjustable variables in the script"""


    """At this distance or smaller from any own building a tile is considered claimed"""
    prop['claiming_distance'] = 2

    """Currently no meaning to it"""
    prop['safety_dist_to_enemy_army'] = 3


def setup_weights(self) -> List[Tuple[Callable, float]]:
    w: List[Tuple[Callable, float]] = []

    def w1(elem: AI_Mazedonian.Option, ai_stat: AI_GameStatus) -> bool:
        """Idea: If AI looses food -> Make building a farm more important!"""
        if type(elem) is BuildOption:
            if elem.type == BuildingType.FARM:
                return self.is_loosing_food
        return False

    w.append((w1, 3))

    def w1_1(elem: AI_Mazedonian.Option, ai_stat: AI_GameStatus) -> bool:
        """Idea: addition to w1: if we are gaining food, make building a farm less important"""
        if type(elem) is BuildOption:
            if elem.type == BuildingType.FARM:
                return not self.is_loosing_food
        return False

    w.append((w1_1, -1.5))

    def w2(elem: AI_Mazedonian.Option, ai_stat: AI_GameStatus) -> bool:
        """Idea: If AI looses food, recruitment is halted"""
        if self.is_loosing_food:
            if type(elem) is RecruitmentOption or type(elem) is ScoutingOption:
                return True
        return False

    w.append((w2, -5))

    def w3(elem: AI_Mazedonian.Option, ai_stat: AI_GameStatus) -> bool:
        """Idea: If AI has no army -> Recruiting an army is important"""
        if type(elem) is RaiseArmyOption:
            if len(ai_stat.map.army_list) == 0:
                return True
        return False

    w.append((w3, 3))

    def w4(elem: AI_Mazedonian.Option, ai_stat: AI_GameStatus) -> bool:
        """Idea, once we have enough resources (and is in passive/def state),
         make scouting slightly more important"""
        if type(elem) is ScoutingOption:
            if ai_stat.me.resources > 10:
                if self.state == AI_Mazedonian.AI_State.PASSIVE or self.state == AI_Mazedonian.AI_State.DEFENSIVE:
                    return True
        return False

    w.append((w4, 1))

    def w5(elem: AI_Mazedonian.Option, ai_stat: AI_GameStatus) -> bool:
        """Idea: reduce significance of scouting in a low eco game"""
        if type(elem) is ScoutingOption:
            if ai_stat.me.resources < 10:
                return True
        return False

    w.append((w5, -1))

    def w6(elem: AI_Mazedonian.Option, ai_stat: AI_GameStatus) -> bool:
        """Idea: If AI has more than 70 food, cut down on additional farms"""
        if type(elem) is BuildOption:
            if elem.type == BuildingType.FARM:
                if ai_stat.me.food > 70:
                    return True
        return False

    w.append((w6, -1))

    def w7(elem: AI_Mazedonian.Option, ai_stat: AI_GameStatus) -> bool:
        """Idea: slightly decrease scouting and waiting if a lot of resources are available"""
        if type(elem) is ScoutingOption or type(elem) is WaitOption:
            if ai_stat.me.resources > 40:
                return True
        return False

    w.append((w7, -1.5))

    def w8(elem: AI_Mazedonian.Option, ai_stat: AI_GameStatus) -> bool:
        """Idea: slightly decrease scouting in early game"""
        if type(elem) is ScoutingOption:
            if self.protocol == AI_Mazedonian.Protocol.EARLY_GAME:
                return True
        return False

    w.append((w8, -1))

    def w9(elem: AI_Mazedonian.Option, ai_stat: AI_GameStatus) -> bool:
        """Idea: slightly increase building in early game"""
        if type(elem) is BuildOption:
            if self.protocol == AI_Mazedonian.Protocol.EARLY_GAME:
                return True
        return False

    w.append((w9, 1))

    def w10(elem: AI_Mazedonian.Option, ai_stat: AI_GameStatus) -> bool:
        """Idea: if AI lacks population by twice the desired value -> double down"""
        if type(elem) is RecruitmentOption:
            if self.build_order.population / 2 > ai_stat.me.population:
                return True
        return False

    w.append((w10, 0.9))

    def w11(elem: AI_Mazedonian.Option, ai_stat: AI_GameStatus) -> bool:
        """Idea: if AI doesn't have a farm -> highest prio (if it cannot build one -> wait)"""
        if type(elem) is BuildOption:
            if elem.type == BuildingType.FARM:
                for b in ai_stat.map.building_list:
                    if b.type == BuildingType.FARM:
                        return False
                return True  # returns true if AI does not have a farm and building one is an option
        return False

    w.append((w11, 10))

    def w12(elem: AI_Mazedonian.Option, ai_stat: AI_GameStatus) -> bool:
        """Idea: extension to w11 (if it cannot build one -> wait)"""
        if type(elem) is WaitOption:
            for b in ai_stat.map.building_list:
                if b.type == BuildingType.FARM:
                    return False
            return True  # returns true if AI does not have a farm
        return False

    w.append((w12, 5))

    def w13(elem: AI_Mazedonian.Option, ai_stat: AI_GameStatus) -> bool:
        """Idea: if pop >= pop_limit, make building barracks slightly more popular"""
        if ai_stat.me.population_limit <= ai_stat.me.population:
            if type(elem) is BuildOption:
                if elem.type == BuildingType.BARRACKS:
                    if not has_building_under_construction(BuildingType.BARRACKS, ai_stat):
                        return True
            if type(elem) is WaitOption:
                if not has_building_under_construction(BuildingType.BARRACKS, ai_stat):
                    return True
            return False

    w.append((w13, 1.7))

    def w14(elem: AI_Mazedonian.Option, ai_stat: AI_GameStatus) -> bool:
        """during Crusade, build troops"""
        if type(elem) is RecruitmentOption:
            if self.state is AI_Mazedonian.AI_State.CRUSADE:
                return True
        return False

    w.append((w14, 5))

    def w15(elem: AI_Mazedonian.Option, ai_stat: AI_GameStatus) -> bool:
        """Idea: Upgrade villa if possible"""""
        if type(elem) is UpgradeOption:
            if self.protocol is AI_Mazedonian.Protocol.LATE_GAME:
                return True
        return False

    w.append((w15, 3))

    hint(f"AI has found {len(w)} weight functions.")
    return w


def setup_movement_weights(self: AI_Mazedonian) -> List[Tuple[Callable, float]]:
    aw: List[Tuple[Callable, float]] = []

    def aw1(elem: AI_Mazedonian.AttackTarget, ai_stat: AI_GameStatus) -> bool:
        if type(elem.target) == AI_Army:
            if essentials.is_obj_in_list(elem.target, self.claimed_tiles):
                return True
        return False

    aw.append((aw1, 2))

    def aw2(elem: AI_Mazedonian.AttackTarget, ai_stat: AI_GameStatus) -> bool:
        if type(elem.target) == AI_Army:
            if self.previous_amount_of_buildings > len(ai_stat.map.building_list):
                return True
        return False

    aw.append((aw2, 1))

    def aw3(elem: AI_Mazedonian.AttackTarget, ai_stat: AI_GameStatus) -> bool:
        """Idea: reduce aggressifness in opponant is stronger"""
        if type(elem.target) == AI_Army:
            if elem.target.owner in self.hostile_player:
                if self.opponent_strength[elem.target.owner] == AI_Mazedonian.Strength.STRONGER:
                    return True
        return False

    aw.append((aw3, -1))

    def aw4(elem: AI_Mazedonian.AttackTarget, ai_stat: AI_GameStatus) -> bool:
        """Idea: Reduce will to attack in early game, but defend"""
        if type(elem.target) == AI_Army:
            if self.protocol == AI_Mazedonian.Protocol.EARLY_GAME:
                if len(self.hostile_player) == 0:
                    return True
        return False

    aw.append((aw4, -2))

    def aw5(elem: AI_Mazedonian.AttackTarget, ai_stat: AI_GameStatus) -> bool:
        """Idea: Move in for the kill if the opp is weaker"""
        if type(elem.target) == AI_Building:
            if elem.target.owner in self.hostile_player:
                if self.opponent_strength[elem.target.owner] == AI_Mazedonian.Strength.WEAKER:
                    return True
        return False

    aw.append((aw5, 2))

    def aw6(elem: AI_Mazedonian.AttackTarget, ai_stat: AI_GameStatus) -> bool:
        """Idea: Defend if attacked by opponent"""
        if type(elem.target) == AI_Army:
            if elem.target.owner in self.hostile_player:
                for opp in ai_stat.opponents:
                    if opp.id == elem.target.owner:
                        if opp.has_attacked:
                            return True
        return False

    aw.append((aw6, 1))

    def aw7(elem: AI_Mazedonian.AttackTarget, ai_stat: AI_GameStatus) -> bool:
        """Idea: during crusade, attack target player"""
        if self.state is AI_Mazedonian.AI_State.CRUSADE:
            if elem.target.owner == self.crusade_target_id:
                return True
        return False

    aw.append((aw7, 5))

    def aw8(elem: AI_Mazedonian.AttackTarget, ai_stat: AI_GameStatus) -> bool:
        """Keep the previous attack target for static targets"""
        if self.previous_attack_target is not None:
            if elem.target.offset_coordinates == self.previous_attack_target.target.offset_coordinates:
                return True
        return False

    aw.append((aw8, 2))

    hint(f"AI has found {len(aw)} movement weight functions.")
    return aw
