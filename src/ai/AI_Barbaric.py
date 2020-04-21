from enum import Enum
import random

from typing import Set, Optional, Union

from src.ai import AI_Toolkit
from src.ai.AI_GameStatus import AI_Move, AI_GameStatus
from src.ai.AI_MapRepresentation import AI_Building, AI_Army
from src.ai.ai_blueprint import AI, Weight, BuildOption, RecruitmentOption, RaiseArmyOption, ArmyMovementOption, \
    WaitOption, UpgradeOption
from src.misc.game_constants import DiploEventType, hint, BuildingType, error, MoveType, Priority, UnitType
from src.ai.scripts.barbaric_hostile import *

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
        self.hostile_player: Set[int] = set()       # TODO clear that list?
        self.previous_army_strength = -1
        self.previous_amount_of_buildings = -1
        self.issue_attack = False                   # make sure this is set to true if the AI commands an attack
        # values to move to the xml file:
        self.safety_dist_to_enemy_army = 3

        # calling out to the script
        self.properties: Dict[str, Any] = {}
        on_setup(self.properties)
        self.weights: List[Weight] = []
        self.m_weights: List[Weight] = []
        for c, v in setup_weights(self):
            self.weights.append(Weight(c, v))
        for c, v in setup_movement_weights(self):
            self.m_weights.append(Weight(c, v))

    def do_move(self, ai_stat: AI_GameStatus, move: AI_Move):
        if len(ai_stat.map.army_list) > 0:
            print(ai_stat.map.army_list[0].offset_coordinates)
        self.update_diplo_events(ai_stat)
        self.diplomacy.calc_round()
        self.evaluate_state(ai_stat)
        hint("Barbaric AI: hostile players: " + str(self.hostile_player))

        # self.calculate_heatmaps()
        all_options = [self.evaluate_move_building(ai_stat),
                       self.evaluate_move_upgrade(ai_stat),
                       self.evaluate_move_recruit_unit(ai_stat),
                       WaitOption(Priority.P_MEDIUM)]
        all_options = list(filter(None, all_options))
        movement_options = []
        movement_options.extend(self.calculate_army_movement(ai_stat, move))

        self.weight_options(ai_stat, move, all_options, movement_options)


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

    def weight_options(self, ai_stat: AI_GameStatus, move: AI_Move,
                       all_options: List[Union[BuildOption, RecruitmentOption, RaiseArmyOption, WaitOption]],
                       movement_options: List[ArmyMovementOption]):
        for opt in all_options:
            if opt.score == Priority.P_NO:
                continue
            opt.weighted_score = opt.score.value
            for w in self.weights:
                if w.condition(opt, ai_stat):
                    opt.weighted_score = opt.weighted_score + w.weight
        for opt in movement_options:
            if opt.score == Priority.P_NO:
                continue
            opt.weighted_score = opt.score.value
            for w in self.m_weights:
                if w.condition(opt, ai_stat):
                    opt.weighted_score = opt.weighted_score + w.weight

        all_options.sort(key=lambda x: x.weighted_score, reverse=True)
        movement_options.sort(key=lambda x: x.weighted_score, reverse=True)

        if len(all_options) > 0:
            best_option = all_options[0]
            if type(best_option) == WaitOption:
                move.move_type = MoveType.DO_NOTHING
                move.str_rep_of_action = "waiting"
            elif type(best_option) == BuildOption:
                move.move_type = MoveType.DO_BUILD
                move.loc = best_option.site
                move.type = best_option.type
                move.str_rep_of_action = f"building a {best_option.type} at " + str(move.loc)
            elif type(best_option) == UpgradeOption:
                move.move_type = MoveType.DO_UPGRADE_BUILDING
                move.loc = best_option.site
                move.type = best_option.type
            elif type(best_option) == RecruitmentOption:
                move.move_type = MoveType.DO_RECRUIT_UNIT
                move.type = best_option.type
                move.str_rep_of_action = f"recruiting a {best_option.type}"
            elif type(best_option) == RaiseArmyOption:
                move.move_type = MoveType.DO_RAISE_ARMY
                move.loc = best_option.site
                move.str_rep_of_action = "raising new army at"
            else:
                error("unexpected type")
        if len(movement_options) > 0:
            best_m_option = movement_options[0]
            move.move_army_to = best_m_option.next_step
            move.doMoveArmy = True


        for opt in all_options:
            s = f"Option of type {type(opt)}, score: {opt.weighted_score} ({opt.score})"
            if not (type(opt) == WaitOption or type(opt) == RaiseArmyOption):
                s = s + f" -> Type: {opt.type}"
            hint(s)
        for m_opt in movement_options:
            s = f"M-Option target: {type(m_opt)}, score: {m_opt.weighted_score} ({m_opt.score})"

        s = f"DECISION: {move.str_rep_of_action}"
        if move.doMoveArmy:
            s += f" moving army to {move.move_army_to}"
        hint(s)



        # army_building_ratio = 0.5
        # if self.state == AI_Barbaric.AI_State.AGGRESSIVE:
        #     army_building_ratio = 1
        # elif self.state == AI_Barbaric.AI_State.DEFENSIVE:
        #     army_building_ratio = 0.8
        #
        # wait: bool = False
        # if len(ai_stat.map.army_list) == 0:
        #     # if score_a > 0:
        #     if self.get_army_spawn_loc(ai_stat) != (-1, -1):
        #         hint("AI Barbaric: Decision: Recruit new army")
        #         # move.doRecruitArmy = True
        #         move.move_type = MoveType.DO_RAISE_ARMY
        #     else:
        #         hint("No suitable tile to spawn the army")
        #     # else:
        #     #     hint("AI Barbaric: Decision: Store more resources (not enough resources to recruit new army)")
        #     #     wait = True
        # elif ai_stat.map.army_list[0].population < army_building_ratio * ai_stat.me.population_limit:
        #     if ai_stat.me.population < ai_stat.me.population_limit:
        #         if score_a > 0:
        #             hint("AI Barbaric: Decision: Upgrade the army")
        #             # move.doUpArmy = True
        #             move.move_type = MoveType.DO_RECRUIT_UNIT
        #         else:
        #             hint("AI Barbaric: Decision: Store more resources (not enough resources to upgrade the army)")
        #             wait = True
        #     else:
        #         hint("Population ceiling reached")
        #         move.move_type = MoveType.DO_NOTHING
        #
        # if not wait:              # so far no valid option found
        #     if not (move.move_type is MoveType.DO_RECRUIT_UNIT or
        #             move.move_type is MoveType.DO_RAISE_ARMY or
        #             move.move_type is MoveType.DO_NOTHING):
        #         if score_u > 0:
        #             hint("AI Barbaric: Decision: Upgrade")
        #             move.move_type = MoveType.DO_UPGRADE_BUILDING
        #         elif score_b > 0:
        #             hint("AI Barbaric: Decision: Build")
        #             move.move_type = MoveType.DO_BUILD
        #         else:
        #             hint("AI Barbaric: Decision: Store more resources")
        #             wait = True
        # # ...
        # if wait:
        #     move.move_type = MoveType.DO_NOTHING
        #     # Ai decides to wait


    def calculate_heatmaps(self):
        pass

    def evaluate_move_building(self, ai_stat: AI_GameStatus) -> Optional[BuildOption]:
        if len(ai_stat.map.building_list) < 3:
            if ai_stat.me.resources >= ai_stat.costBuildC1 and len(ai_stat.map.buildable_tiles) > 0:
                # find a random building location
                idx = random.randint(0, len(ai_stat.map.buildable_tiles) - 1)
                site = ai_stat.map.buildable_tiles[idx].offset_coordinates
                return BuildOption(BuildingType.CAMP_1, site, [], Priority.P_MEDIUM)
        return None

    def evaluate_move_upgrade(self, ai_stat: AI_GameStatus) -> Optional[UpgradeOption]:
        list_of_upgradable_buildings = []
        for b in ai_stat.map.building_list:
            if b.type == BuildingType.CAMP_1:
                if ai_stat.me.resources >= ai_stat.costBuildC2:
                    list_of_upgradable_buildings.append((b, BuildingType.CAMP_2))
            if b.type == BuildingType.CAMP_2:
                if ai_stat.me.resources >= ai_stat.costBuildC3:
                    list_of_upgradable_buildings.append((b, BuildingType.CAMP_3))
        if len(list_of_upgradable_buildings) == 0:
            return None          # no building available that the AI can upgrade
        idx = random.randint(0, len(list_of_upgradable_buildings) - 1)
        site = list_of_upgradable_buildings[idx][0].offset_coordinates
        btype = list_of_upgradable_buildings[idx][1]
        return UpgradeOption(btype, site, Priority.P_MEDIUM)

    def evaluate_move_recruit_unit(self, ai_stat: AI_GameStatus) -> Union[None, RaiseArmyOption, RecruitmentOption]:
        if len(ai_stat.map.army_list) == 0:
            for b in ai_stat.map.building_list:
                nei = AI_Toolkit.get_neibours_on_set(b, ai_stat.map.walkable_tiles)
                if len(nei) == 0:
                    continue
                x = random.sample(nei, 1)[0]
                return RaiseArmyOption(x.offset_coordinates, Priority.P_MEDIUM)
        if ai_stat.me.resources >= ai_stat.costUnitBS.resources:
            return RecruitmentOption(UnitType.BABARIC_SOLDIER, Priority.P_MEDIUM)
        return None

    def calculate_army_movement(self, ai_stat: AI_GameStatus, move: AI_Move) -> List[ArmyMovementOption]:
        targets: List[AI_Building, AI_Army] = []
        movements = []
        if len(ai_stat.map.army_list) == 0:
            return movements

        for e_b in ai_stat.map.opp_building_list:
            if e_b.visible:
                targets.append(e_b)
        for e_a in ai_stat.map.opp_army_list:
            targets.append(e_a)

        start_tile = ai_stat.map.army_list[0].base_tile
        for target in targets:
            target_tile = target.base_tile
            path = AI_Toolkit.dijkstra_pq(start_tile, target_tile, ai_stat.map.walkable_tiles)
            for p in path:
                print(p.offset_coordinates, end=" ")
            print(" ")
            if len(path) > 1:
                movements.append(ArmyMovementOption(target, Priority.P_MEDIUM, path[1].offset_coordinates))
            else:
                hint("no path found to " + str(target.offset_coordinates))
        return movements


        # if len(ai_stat.map.army_list) == 0:
        #     return []           # no army, cannot move
        # if ai_stat.map.army_list[0].population == 0:
        #     return []           # no population
        # if self.state == AI_Barbaric.AI_State.PASSIVE:
        #     return []            # not moving in passive state
        # if self.state == AI_Barbaric.AI_State.AGGRESSIVE:
        #     start_tile = ai_stat.map.army_list[0].base_tile
        #     # start_tile = AI_Toolkit.get_tile_by_xy(ai_stat.map.army_list[0].offset_coordinates,
        #     #                                        ai_stat.map.walkable_tiles)
        #     target_tile = None
        #     path = []
        #     for e_a in ai_stat.map.opp_army_list:
        #         if e_a.owner in self.hostile_player:
        #             hint("AI Barbaric: found hostile army to attack")
        #             # target_tile = AI_Toolkit.get_tile_by_xy(e_a.offset_coordinates, ai_stat.tiles_walkable)
        #             target_tile = e_a.base_tile
        #     if target_tile is None:
        #         for e_b in ai_stat.map.opp_building_list:
        #             if e_b.visible:
        #                 if e_b.owner in self.hostile_player:
        #                     if e_b.type != BuildingType.BARRACKS:
        #                         hint("AI Barbaric: found hostile building to attack")
        #                         # target_tile = AI_Toolkit.get_tile_by_xy(e_b.offset_coordinates, ai_stat.tiles_walkable)
        #                         target_tile = e_b.base_tile
        #
        #     if start_tile and target_tile:
        #         path = AI_Toolkit.dijkstra_pq(start_tile, target_tile, ai_stat.map.walkable_tiles)
        #     else:
        #         error("AI Barbaric: start_tile or target_tile not valid! (1)")
        #         # for walk in ai_stat.map.walkable_tiles:
        #         #     move.info_at_tile.append((walk.offset_coordinates, "w"))
        #         error(str(start_tile))
        #         error(str(target_tile))
        #     if len(path) > 1:
        #         # for p in path:
        #         #     print(str(p.offset_coordinates) + " ", end="")
        #         #     move.info_at_tile.append((p.offset_coordinates, "W"))
        #         # print("")
        #         hint("AI Barbaric: found path to hostile army / building")
        #         return path[1].offset_coordinates
        #     else:
        #         hint("AI Barbaric: NO path to hostile army found")
        # if self.state == AI_Barbaric.AI_State.DEFENSIVE:
        #     if len(ai_stat.map.opp_army_list) > 0:
        #         hint("AI Barbaric: evading enemy army")
        #         longest_path: (int, (int, int)) = (-1, (0, 0))
        #         target_tile = ai_stat.map.opp_army_list[0].base_tile
        #         dist_to_army = AI_Toolkit.get_distance(target_tile, ai_stat.map.army_list[0].base_tile)
        #         if dist_to_army >= self.safety_dist_to_enemy_army:
        #             hint("AI Barbaric: Enemy army far enough away, no need to evade.")
        #             return -1, -1
        #         neighbours = AI_Toolkit.get_neibours_on_set(ai_stat.map.army_list[0], ai_stat.map.walkable_tiles)
        #         for nei in neighbours:
        #             path = []
        #             start_tile = nei
        #             if start_tile and target_tile:
        #                 path = AI_Toolkit.dijkstra_pq(start_tile, target_tile, ai_stat.map.walkable_tiles)
        #             else:
        #                 error("AI Barbaric: start_tile or target_tile not valid!")
        #             if len(path) > longest_path[0]:
        #                 longest_path = (len(path), nei.offset_coordinates)
        #         hint("AI Barbaric: evading by moving to tile: " + str(longest_path[1]))
        #         return longest_path[1]
        # return -1, -1

    def update_diplo_events(self, ai_stat: AI_GameStatus):
        for e_b in ai_stat.map.opp_building_list:
            if e_b.visible:
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
        for opp in ai_stat.opponents:
            self.hostile_player.add(opp.id)
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
        nei = AI_Toolkit.get_neibours_on_set(building_tile, ai_stat.map.buildable_tiles)
        if len(nei) == 0:           # this seems to be unlikely but avoids crashing just in case
            hint("No suitable tile to spawn the army!")
            return -1, -1
        idx = random.randint(0, len(nei) - 1)
        return nei[idx].offset_coordinates

    def get_state_as_str(self):
        if self.state == AI_Barbaric.AI_State.PASSIVE:
            return "    passive"
        elif self.state == AI_Barbaric.AI_State.DEFENSIVE:
            return "    defensive"
        elif self.state == AI_Barbaric.AI_State.AGGRESSIVE:
            return "    aggressive"
        return "    no state"
