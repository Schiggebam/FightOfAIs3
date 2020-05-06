from src.ai.ai_npc import *
from src.ai.toolkit.essentials import get_distance
from src.ai.toolkit.movement import next_step_to_target, evasive_movement
from src.misc.game_constants import DiploEventType


class Barbaric(AI_NPC):
    """
    Barbaric AI
    """

    def __init__(self, other_players: List[int], script):
        super().__init__("Barbaric", other_players, script)

    def evaluate_state(self, ai_stat: AI_GameStatus):
        old_state = self.state.name
        if self.state == AI_NPC.AI_State.PASSIVE:
            if len(self.hostile_player) > 0 and (len(ai_stat.map.opp_army_list) > 0 or len(ai_stat.map.opp_building_list) > 0):
                self.state = AI_NPC.AI_State.AGGRESSIVE
            if len(ai_stat.map.opp_army_list) > 0:
                self.state = AI_NPC.AI_State.DEFENSIVE
        elif self.state == AI_NPC.AI_State.DEFENSIVE:
            if len(ai_stat.map.opp_army_list) == 0:
                self.state = AI_NPC.AI_State.PASSIVE
            if self.has_been_attacked(ai_stat):
                self.state = AI_NPC.AI_State.AGGRESSIVE
        elif self.state == AI_NPC.AI_State.AGGRESSIVE:
            if len(self.hostile_player) == 0 or len(ai_stat.map.army_list) == 0:       # become defensive if army is lost or no more hostile players
                self.state = AI_NPC.AI_State.DEFENSIVE
            if len(ai_stat.map.opp_army_list) == 0 and len(ai_stat.map.opp_building_list) == 0:
                self.state = AI_NPC.AI_State.PASSIVE
        self._dump(f"State: {old_state} -> {self.state.name}")

    def update_diplo_events(self, ai_stat: AI_GameStatus):
        """Idea: for each opponent building in the visible area of the barbaric, reduce diplo value by 2"""
        for e_b in ai_stat.map.opp_building_list:
            if e_b.visible:
                self.diplomacy.add_event(e_b.owner, e_b.offset_coordinates,
                                         DiploEventType.TYPE_ENEMY_BUILDING_SCOUTED, -2.0, 5)

        """Idea, for each opponent army movement in the visible area of the barbaric, reduce diplo value by 1
        Note: if the army moves, this gets triggered again, thus the lifetime of this event is only 1"""
        for e_a in ai_stat.map.opp_army_list:
            self.diplomacy.add_event(e_a.owner, e_a.offset_coordinates,
                                     DiploEventType.ENEMY_ARMY_INVADING_CLAIMED_ZONE, -1.0, 1)

        for opp in ai_stat.opponents:
            if opp.has_attacked:
                self.diplomacy.add_event(opp.id, (0, 0), DiploEventType.ATTACKED_BY_FACTION, -3.0, 3)

    def calculate_army_movement(self, ai_stat: AI_GameStatus) -> List[ArmyMovementOption]:
        targets: List[Union[AI_Building, AI_Army]] = []
        movements = []
        if len(ai_stat.map.army_list) == 0:
            return movements
        if ai_stat.map.army_list[0].population == 0:
            return movements
        army_tile = ai_stat.map.army_list[0].base_tile
        # --------------------- Passive / Aggressive movement --------------------
        if self.state is AI_NPC.AI_State.AGGRESSIVE or self.state is AI_NPC.AI_State.PASSIVE:
            """Identify targets and calculate path towards them"""
            for e_b in ai_stat.map.opp_building_list:
                if e_b.visible:
                    targets.append(e_b)
            for e_a in ai_stat.map.opp_army_list:
                targets.append(e_a)

            for target in targets:
                next_step, dist = next_step_to_target(army_tile, target.base_tile, ai_stat.map.walkable_tiles)
                if next_step:
                    movements.append(ArmyMovementOption(target, Priority.P_MEDIUM,
                                                        next_step.offset_coordinates))
        # --------------------- Defencive movement --------------------
        elif self.state is AI_NPC.AI_State.DEFENSIVE:
            if len(ai_stat.map.opp_army_list) > 0:
                for h_a in ai_stat.map.opp_army_list:
                    if get_distance(h_a, army_tile) <= 2:
                        self._dump(f"evading opponent army {get_distance(h_a, army_tile)}")
                        next_step, dist = evasive_movement(army_tile, h_a.base_tile, ai_stat.map.walkable_tiles)
                        if next_step:
                            movements.append(ArmyMovementOption(h_a, Priority.P_MEDIUM,
                                                                next_step.offset_coordinates))
        return movements
