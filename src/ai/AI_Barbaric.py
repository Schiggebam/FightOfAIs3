from enum import Enum
import random
from typing import Set

from src.ai import AI_Toolkit
from src.ai.AI_GameStatus import AI_Move, AI_GameStatus
from src.ai.ai_blueprint import AI
from src.misc.game_constants import DiploEventType, hint, BuildingType, error


class AI_Barbaric(AI):
    class AI_State(Enum):
        PASSIVE = 0
        AGGRESSIVE = 1
        DEFENSIVE = 2


    def __init__(self, own_id: int, other_players: [int]):
        super().__init__("Barbaric", other_players)
        self.personality = "militant"
        # self.personality = "temperate"
        self.own_id = own_id
        self.state = AI_Barbaric.AI_State.PASSIVE
        self.other_players = other_players
        self.hostile_player: Set[int] = set()
        self.previous_army_strength = -1
        self.previous_amount_of_buildings = -1
        self.issue_attack = False                   # make sure this is set to true if the AI commands an attack
        # values to move to the xml file:
        self.safety_dist_to_enemy_army = 3

    def do_move(self, ai_stat: AI_GameStatus, move: AI_Move):
        self.update_diplo_events(ai_stat)
        self.diplomacy.calc_round()
        self.evaluate_state(ai_stat)
        hint("Barbaric AI: hostile players: " + str(self.hostile_player))

        # self.calculate_heatmaps()
        score_b, loc_b = self.evaluate_move_building(ai_stat)
        score_u, loc_u = self.evaluate_move_upgrade(ai_stat)
        score_a = self.evaluate_move_up_army(ai_stat)
        loc_a = self.calculate_army_movement(ai_stat, move)

        self.weight_scores(ai_stat, move, score_b, score_u, score_a)

        if move.doUpArmy:
            move.str_rep_of_action = "Upgrading the army"
        elif move.doBuild:
            move.loc = loc_b
            move.str_rep_of_action = "Building @ " + str(move.loc)
        elif move.doUpgrade:
            move.loc = loc_u
            move.str_rep_of_action = "Upgrading @ " + str(move.loc)
        elif move.doRecruitArmy:
            move.loc = self.get_army_spawn_loc(ai_stat)
            move.str_rep_of_action = "Recruiting @ " + str(move.loc)

        if loc_a != (-1, -1):
            move.move_army_to = loc_a
            move.doMoveArmy = True

        # keep values
        if len(ai_stat.map.army_list) > 0:
            self.previous_army_strength = ai_stat.map.army_list[0].population
        else:
            self.previous_army_strength = 0
        self.previous_amount_of_buildings = len(ai_stat.map.building_list)

    def evaluate_state(self, ai_stat: AI_GameStatus):
        if self.state == AI_Barbaric.AI_State.PASSIVE:
            if len(self.hostile_player) > 0 and (len(ai_stat.map.opp_army_list) > 0 or len(ai_stat.map.opp_building_list) > 0):
                hint("Barbaric AI: Passive -> Aggressive")
                self.state = AI_Barbaric.AI_State.AGGRESSIVE
            if len(ai_stat.map.opp_army_list) > 0:
                hint("Barbaric AI: Passive -> Defensive")
                self.state = AI_Barbaric.AI_State.DEFENSIVE
        elif self.state == AI_Barbaric.AI_State.DEFENSIVE:
            if len(ai_stat.map.opp_army_list) == 0:
                hint("Barbaric AI: Defensive -> Passive")
                self.state = AI_Barbaric.AI_State.PASSIVE
            if self.has_been_attacked(ai_stat):
                hint("Barbaric AI: Notices an attack! Defensive -> Aggressive")
                self.state = AI_Barbaric.AI_State.AGGRESSIVE
        elif self.state == AI_Barbaric.AI_State.AGGRESSIVE:
            if len(self.hostile_player) == 0 or len(ai_stat.map.army_list) == 0:       # become defensive if army is lost or no more hostile players
                hint("Barbaric AI: Aggressive -> Defensive")
                self.state = AI_Barbaric.AI_State.DEFENSIVE
            if len(ai_stat.map.opp_army_list) == 0 and len(ai_stat.map.opp_building_list) == 0:
                hint("Barbaric AI: Aggressive -> Passive")
                self.state = AI_Barbaric.AI_State.PASSIVE

    def weight_scores(self, ai_stat: AI_GameStatus, move: AI_Move, score_b: int, score_u: int, score_a: int):
        army_building_ratio = 0.5
        if self.state == AI_Barbaric.AI_State.AGGRESSIVE:
            army_building_ratio = 1
        elif self.state == AI_Barbaric.AI_State.DEFENSIVE:
            army_building_ratio = 0.8

        wait: bool = False
        if len(ai_stat.map.army_list) == 0:
            if score_a > 0:
                hint("AI Barbaric: Decision: Recruit new army")
                move.doRecruitArmy = True
            else:
                hint("AI Barbaric: Decision: Store more resources (not enough resources to recruit new army)")
                wait = True
        elif ai_stat.map.army_list[0].population < army_building_ratio * ai_stat.population_limit:
            if ai_stat.population < ai_stat.population_limit:
                if score_a > 0:
                    hint("AI Barbaric: Decision: Upgrade the army")
                    move.doUpArmy = True
                else:
                    hint("AI Barbaric: Decision: Store more resources (not enough resources to upgrade the army)")
                    wait = True
            else:
                hint("Population ceiling reached")
                move.doNothing = True   # but wait is false because we check the building options in this case

        if not wait:              # so far no valid option found
            if score_u > 0:
                hint("AI Barbaric: Decision: Upgrade")
                move.doUpgrade = True
            elif score_b > 0:
                hint("AI Barbaric: Decision: Build")
                move.doBuild = True
            else:
                hint("AI Barbaric: Decision: Store more resources")
                wait = True
        # ...
        if wait:
            move.doNothing = True       # Ai decides to wait


    def calculate_heatmaps(self):
        pass

    def evaluate_move_building(self, ai_stat: AI_GameStatus) -> (int, (int, int)):
        if len(ai_stat.map.building_list) < 3:
            if ai_stat.player_resources >= ai_stat.costBuildC1 and len(ai_stat.map.buildable_tiles) > 0:
                # find a random building location
                idx = random.randint(0, len(ai_stat.map.buildable_tiles) - 1)
                return 1, ai_stat.map.buildable_tiles[idx].offset_coordinates
        return -1, (0, 0)

    def evaluate_move_upgrade(self, ai_stat: AI_GameStatus) -> (int, (int, int)):
        list_of_upgradable_buildings = []
        for b in ai_stat.map.building_list:
            if b.type == BuildingType.CAMP_1:
                if ai_stat.player_resources >= ai_stat.costBuildC2:
                    list_of_upgradable_buildings.append(b)
            if b.type == BuildingType.CAMP_2:
                if ai_stat.player_resources >= ai_stat.costBuildC3:
                    list_of_upgradable_buildings.append(b)
        if len(list_of_upgradable_buildings) == 0:
            return -1, (0, 0)           # no building available that the AI can upgrade
        idx = random.randint(0, len(list_of_upgradable_buildings) - 1)
        return 1, list_of_upgradable_buildings[idx].offset_coordinates

    def evaluate_move_up_army(self, ai_stat: AI_GameStatus) -> int:
        if ai_stat.player_resources >= ai_stat.costUnitBS[0]:
            return 1
        return -1

    def calculate_army_movement(self, ai_stat: AI_GameStatus, move: AI_Move) -> (int, int):
        if len(ai_stat.map.army_list) == 0:
            return -1, -1            # no army, cannot move
        if self.state == AI_Barbaric.AI_State.PASSIVE:
            return -1, -1            # not moving in passive state
        if self.state == AI_Barbaric.AI_State.AGGRESSIVE:
            start_tile = ai_stat.map.army_list[0].base_tile
            # start_tile = AI_Toolkit.get_tile_by_xy(ai_stat.map.army_list[0].offset_coordinates,
            #                                        ai_stat.map.walkable_tiles)
            target_tile = None
            path = []
            for e_a in ai_stat.map.opp_army_list:
                if e_a.owner in self.hostile_player:
                    hint("AI Barbaric: found hostile army to attack")
                    # target_tile = AI_Toolkit.get_tile_by_xy(e_a.offset_coordinates, ai_stat.tiles_walkable)
                    target_tile = e_a.base_tile
            if target_tile is None:
                for e_b in ai_stat.map.opp_building_list:
                    if e_b.owner in self.hostile_player:
                        hint("AI Barbaric: found hostile building to attack")
                        # target_tile = AI_Toolkit.get_tile_by_xy(e_b.offset_coordinates, ai_stat.tiles_walkable)
                        target_tile = e_b.base_tile

            if start_tile and target_tile:
                path = AI_Toolkit.dijkstra_pq(start_tile, target_tile, ai_stat.map.walkable_tiles)
            else:
                error("AI Barbaric: start_tile or target_tile not valid! (1)")
                for walk in ai_stat.map.walkable_tiles:
                    move.info_at_tile.append((walk.offset_coordinates, "w"))
                error(str(start_tile))
                error(str(target_tile))
            if len(path) > 1:
                hint("AI Barbaric: found path to hostile army / building")
                return path[1].offset_coordinates
            else:
                hint("AI Barbaric: NO path to hostile army found")
        if self.state == AI_Barbaric.AI_State.DEFENSIVE:
            if len(ai_stat.map.opp_army_list) > 0:
                hint("AI Barbaric: evading enemy army")
                longest_path: (int, (int, int)) = (-1, (0, 0))
                target_tile = ai_stat.map.opp_army_list[0].base_tile
                dist_to_army = AI_Toolkit.get_distance(target_tile, ai_stat.map.army_list[0].base_tile)
                if dist_to_army >= self.safety_dist_to_enemy_army:
                    hint("AI Barbaric: Enemy army far enough away, no need to evade.")
                    return -1, -1
                neighbours = AI_Toolkit.get_neibours_on_set(ai_stat.map.army_list[0], ai_stat.map.walkable_tiles)
                for nei in neighbours:
                    path = []
                    start_tile = nei
                    if start_tile and target_tile:
                        path = AI_Toolkit.dijkstra_pq(start_tile, target_tile, ai_stat.map.walkable_tiles)
                    else:
                        error("AI Barbaric: start_tile or target_tile not valid!")
                    if len(path) > longest_path[0]:
                        longest_path = (len(path), nei.offset_coordinates)
                hint("AI Barbaric: evading by moving to tile: " + str(longest_path[1]))
                return longest_path[1]
        return -1, -1

    def update_diplo_events(self, ai_stat: AI_GameStatus):
        for e_b in ai_stat.map.opp_building_list:
            self.diplomacy.add_event(e_b.owner, e_b.offset_coordinates,
                                     DiploEventType.TYPE_ENEMY_BUILDING_SCOUTED,
                                     -1.0, 5, self.name)
            #for e_a in ai_stat.enemy_armies:
            #    if e_a.offset_coordinates == tile.offset_coordinates:
            #        self.diplomacy.add_event(e_a.owner, tile.offset_coordinates,
            #                                 DiploEventType.TYPE_ENEMY_ARMY_INVADING,
            #                                 -2.0, 5, self.name)

        for other_p_id in self.other_players:
            if self.diplomacy.get_diplomatic_value_of_player(other_p_id) < 0:
                if other_p_id not in self.hostile_player:
                    hint("Barbaric AI: Player id: " + str(other_p_id) + " got added to hostile players." )
                    self.hostile_player.add(other_p_id)
            #if self.diplomacy.get_diplomatic_value_of_player(other_p_id) > 2:
            #    if other_p_id in self.hostile_player:
            #        hint("Barbaric AI: Player id: " + str(other_p_id) + " got removed from hostile players.")
            #        self.hostile_player.remove(other_p_id)

    def has_been_attacked(self, ai_stat: AI_GameStatus):
        if len(ai_stat.aggressions) > 0:
            for a in ai_stat.aggressions:
                self.hostile_player.add(a)
            hint("Barbaric AI: aggression found!")
            return True
        if self.previous_amount_of_buildings > len(ai_stat.map.building_list):
            return True         # lost a building
        if len(ai_stat.map.army_list) == 0 and not self.issue_attack:
            return True         # lost army without commanding an attack
        # if self.previous_army_strength > ai_stat.armies[0].strength and not self.issue_attack:
        #     return True         # army got attacked without commanding it
        return False

    def get_army_spawn_loc(self, ai_stat: AI_GameStatus) -> (int, int):
        building_tile = ai_stat.map.building_list[0]
        # building_tile = AI_Toolkit.get_tile_by_xy(ai_stat.map.building_list[0].offset_coordinates,
        #                                           ai_stat.tiles_discovered)
        # nei = AI_Toolkit.getListDistanceOne(building_tile, ai_stat.tiles_buildable)
        nei = AI_Toolkit.get_neibours_on_set(building_tile, ai_stat.map.buildable_tiles)
        idx = random.randint(0, len(nei) - 1)
        return nei[idx].offset_coordinates

    def get_state_as_str(self):
        if self.state == AI_Barbaric.AI_State.PASSIVE:
            return "passive"
        elif self.state == AI_Barbaric.AI_State.DEFENSIVE:
            return "defensive"
        elif self.state == AI_Barbaric.AI_State.AGGRESSIVE:
            return "aggressive"
        return "no state"
