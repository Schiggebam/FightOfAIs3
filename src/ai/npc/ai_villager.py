from typing import Tuple

from src.ai.AI_MapRepresentation import AI_Trade
from src.ai.ai_npc import *
from src.ai.toolkit.essentials import get_distance, get_neighbours_on_set, get_tile_by_xy
from src.ai.toolkit.movement import next_step_to_target, protective_movement
from src.misc.game_constants import DiploEventType, TradeType, TradeCategory, TradeState


class Villager(AI_NPC):
    """
    Villager AI
    """

    def __init__(self, other_players: List[int], script):
        super().__init__("Villager", other_players, script)
        self.patrol_target: Optional[Tuple[int, int]] = None

    def evaluate_state(self, ai_stat: AI_GameStatus):
        old_state = self.state.name
        hostile_armies = [x for x in ai_stat.map.opp_army_list if x.owner in self.hostile_player]
        hostile_buildings = [x for x in ai_stat.map.opp_building_list if x.owner in self.hostile_player and x.visible]
        """Idea: if a hostile army is in bound -> defencive. Otherwise, raid a hostile building if there is one """
        if self.state is AI_NPC.AI_State.PASSIVE:
            if len(ai_stat.map.opp_army_list) > 0:      # will only remain in defencive state, if army is not too close
                self.state = AI_NPC.AI_State.DEFENSIVE
            if len(hostile_buildings) > 0 and len(hostile_armies) == 0:
                self.state = AI_NPC.AI_State.AGGRESSIVE
        """Idea: if aggressive, become passive once no more targets or defencive is hostile army is in bound"""
        if self.state is AI_NPC.AI_State.AGGRESSIVE:
            if len(hostile_buildings) == 0 and len(hostile_armies) == 0:
                self.state = AI_NPC.AI_State.PASSIVE
            if len(hostile_armies) > 0:
                self.state = AI_NPC.AI_State.DEFENSIVE
        """Idea: if defencive, become passive once there are no more threats, from there it can get aggressive again"""
        if self.state is AI_NPC.AI_State.DEFENSIVE:
            if len(hostile_armies) == 0:
                too_close_for_comfort = False
                for o_a in ai_stat.map.opp_army_list:
                    if get_distance(ai_stat.map.building_list[0].base_tile, o_a.base_tile) <= 2:
                        too_close_for_comfort = True
                if not too_close_for_comfort:
                    self.state = AI_NPC.AI_State.PASSIVE

        self._dump(f"State: {old_state} -> {self.state.name}")

    def update_diplo_events(self, ai_stat: AI_GameStatus):
        village_tile = ai_stat.map.building_list[0].base_tile
        """If a building is built in direct proximity to the village, the villagers get angry"""
        for e_b in ai_stat.map.opp_building_list:
            if e_b.visible:
                if get_distance(village_tile, e_b) > 2:
                    self.diplomacy.add_event(e_b.owner, e_b.offset_coordinates,
                                             DiploEventType.ENEMY_BUILDING_IN_CLAIMED_ZONE, -4.0, 3)
                else:
                    self.diplomacy.add_event(e_b.owner, e_b.offset_coordinates,
                                             DiploEventType.TYPE_ENEMY_BUILDING_SCOUTED, -1.0, 2)

        for e_a in ai_stat.map.opp_army_list:
            if e_a.owner in self.hostile_player:
                self.diplomacy.add_event(e_a.owner, e_a.offset_coordinates, DiploEventType.TYPE_ENEMY_ARMY_INVADING,
                                         -2.0, 1)
            else:
                self.diplomacy.add_event(e_a.owner, e_a.offset_coordinates, DiploEventType.PROTECTIVE_ARMY_SPOTTED,
                                         +2.0, 1)

    def calculate_army_movement(self, ai_stat: AI_GameStatus) -> List[ArmyMovementOption]:
        """
        Villager movement
        In passive state: patrol
        In aggressive state: attack buildings
        In defencive state: protect own village, move to intercept incoming army
        """
        movements: List[ArmyMovementOption] = []
        if len(ai_stat.map.army_list) == 0:
            return movements
        if ai_stat.map.army_list[0].population == 0:
            return movements
        army_tile = ai_stat.map.army_list[0].base_tile
        village_tile = ai_stat.map.building_list[0].base_tile
        # --------------------- Passive movement --------------------
        if self.state is AI_NPC.AI_State.PASSIVE:
            domain = [x for x in ai_stat.map.walkable_tiles if not x.has_building() and not x.has_army()]
            domain.append(army_tile)
            if not self.patrol_target:
                self.patrol_target = random.sample(domain, 1)[0].offset_coordinates
            pt = get_tile_by_xy(self.patrol_target, ai_stat.map.discovered_tiles)
            if pt not in domain:
                self._dump("relocating patrol target, it appears to be blocked")
                pt = random.sample(domain, 1)[0]
            if get_distance(pt, army_tile) > 0:
                self._dump(f"patrol tile: {pt.offset_coordinates}")
                next_step, dist = next_step_to_target(army_tile, pt, domain)
                if next_step:
                    movements.append(ArmyMovementOption(pt, Priority.P_MEDIUM, next_step.offset_coordinates))
            else:
                self.patrol_target = None

        # --------------------- Defencive movement --------------------
        elif self.state is AI_NPC.AI_State.DEFENSIVE:
            hostile_armies = [x for x in ai_stat.map.opp_army_list if x.owner in self.hostile_player]
            for h_a in hostile_armies:
                domain_no_buildings = [x for x in ai_stat.map.walkable_tiles if not x.has_building()]
                next_step, dist = protective_movement(army_tile, h_a.base_tile, village_tile, domain_no_buildings)
                if next_step:
                    movements.append(ArmyMovementOption(self.patrol_target, Priority.P_MEDIUM,
                                                        next_step.offset_coordinates))
            if len(hostile_armies) == 0:
                target = random.sample(get_neighbours_on_set(village_tile, ai_stat.map.walkable_tiles), 1)[0]
                next_step, dist = next_step_to_target(army_tile, target, ai_stat.map.walkable_tiles)
                if next_step:
                    movements.append(ArmyMovementOption(self.patrol_target, Priority.P_MEDIUM,
                                                        next_step.offset_coordinates))
        # --------------------- Aggressive movement --------------------
        elif self.state is AI_NPC.AI_State.AGGRESSIVE:
            hostile_armies = [x for x in ai_stat.map.opp_army_list if x.owner in self.hostile_player]
            hostile_buildings = [x for x in ai_stat.map.opp_building_list if x.owner in self.hostile_player]
            for h_target in list(set().union(hostile_armies, hostile_buildings)):
                next_step, dist = next_step_to_target(army_tile, h_target.base_tile, ai_stat.map.walkable_tiles)
                if next_step:
                    movements.append(ArmyMovementOption(h_target, Priority.P_MEDIUM, next_step.offset_coordinates))
        return movements

    def evaluate_trades(self, ai_stat: AI_GameStatus, move: AI_Move):
        for trade in ai_stat.trades:
            if trade.owner_id == ai_stat.me.id:
                continue
        if ai_stat.me.food > 10:
            # self._dump("new trade: food for culture")
            move.trades.append(AI_Trade(ai_stat.me.id, TradeType.OFFER, (TradeCategory.FOOD, 10),
                                        (TradeCategory.CULTURE, 20), TradeState.NEW))
            # self._dump("new gift for player 0")
            # move.trades.append(AI_Trade(ai_stat.me.id, TradeType.GIFT, (TradeCategory.FOOD, 5), None,
            #                             TradeState.NEW, target_id=0))
            move.trades.append(AI_Trade(ai_stat.me.id, TradeType.CLAIM, None, (TradeCategory.CULTURE, 5),
                                        TradeState.NEW, target_id=0))

