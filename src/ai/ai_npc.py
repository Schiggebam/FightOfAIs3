from enum import Enum
import random
import importlib

from typing import Set, Optional, Union, List, Any, Dict, Tuple

from src.ai import AI_Toolkit
from src.ai.AI_GameStatus import AI_Move, AI_GameStatus
from src.ai.AI_MapRepresentation import AI_Building, AI_Army, Tile
from src.ai.ai_blueprint import AI, Weight, BuildOption, RecruitmentOption, RaiseArmyOption, ArmyMovementOption, \
    WaitOption, UpgradeOption
from src.misc.game_constants import DiploEventType, hint, BuildingType, error, MoveType, Priority, UnitType

DETAILED_DEBUG = False

class AI_NPC(AI):
    class AI_State(Enum):
        PASSIVE = 0
        AGGRESSIVE = 1
        DEFENSIVE = 2

    class Script(Enum):
        BARBARIC_HOSTILE = 10
        VILLAGER = 11

        @staticmethod
        def get_script_location(script) -> str:
            if script is AI_NPC.Script.BARBARIC_HOSTILE:
                return "ai.scripts.barbaric_hostile"
            if script is AI_NPC.Script.VILLAGER:
                return "ai.scripts.villager_basic"
            return ""


    def __init__(self, own_id: int, other_players: List[int], script):
        super().__init__("Barbaric", other_players)
        self.personality = "militant"
        # self.personality = "temperate"
        self.own_id = own_id
        self.state = AI_NPC.AI_State.PASSIVE
        self.other_players = other_players
        self.hostile_player: Set[int] = set()
        self.previous_army_strength = -1
        self.previous_amount_of_buildings = -1
        self.issue_attack = False                   # make sure this is set to true if the AI commands an attack
        # values to move to the xml file:
        self.safety_dist_to_enemy_army = 3
        self.claimed_tiles: List[Tile] = []

        # Load the script
        script_loc = AI_NPC.Script.get_script_location(script)
        on_setup = getattr(importlib.import_module(script_loc), 'on_setup')
        setup_weights = getattr(importlib.import_module(script_loc), 'setup_weights')
        setup_movement_weights = getattr(importlib.import_module(script_loc), 'setup_movement_weights')


        self.properties: Dict[str, Any] = {}
        on_setup(self.properties)
        self.weights: List[Weight] = []
        self.m_weights: List[Weight] = []
        for c, v in setup_weights(self):
            self.weights.append(Weight(c, v))
        for c, v in setup_movement_weights(self):
            self.m_weights.append(Weight(c, v))

    def do_move(self, ai_stat: AI_GameStatus, move: AI_Move):
        self.update_diplo_events(ai_stat)
        self.diplomacy.calc_round()
        self.evaluate_state(ai_stat)
        self.calculate_heatmaps(ai_stat)
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
        self.hostile_player.clear()
        self.claimed_tiles.clear()

    def evaluate_state(self, ai_stat: AI_GameStatus):
        if self.state == AI_NPC.AI_State.PASSIVE:
            if len(self.hostile_player) > 0 and (len(ai_stat.map.opp_army_list) > 0 or len(ai_stat.map.opp_building_list) > 0):
                hint("Barbaric AI: Passive -> Aggressive")
                self.state = AI_NPC.AI_State.AGGRESSIVE
            if len(ai_stat.map.opp_army_list) > 0:
                hint("Barbaric AI: Passive -> Defensive")
                self.state = AI_NPC.AI_State.DEFENSIVE
        elif self.state == AI_NPC.AI_State.DEFENSIVE:
            if len(ai_stat.map.opp_army_list) == 0:
                hint("Barbaric AI: Defensive -> Passive")
                self.state = AI_NPC.AI_State.PASSIVE
            if self.has_been_attacked(ai_stat):
                hint("Barbaric AI: Notices an attack! Defensive -> Aggressive")
                self.state = AI_NPC.AI_State.AGGRESSIVE
        elif self.state == AI_NPC.AI_State.AGGRESSIVE:
            if len(self.hostile_player) == 0 or len(ai_stat.map.army_list) == 0:       # become defensive if army is lost or no more hostile players
                hint("Barbaric AI: Aggressive -> Defensive")
                self.state = AI_NPC.AI_State.DEFENSIVE
            if len(ai_stat.map.opp_army_list) == 0 and len(ai_stat.map.opp_building_list) == 0:
                hint("Barbaric AI: Aggressive -> Passive")
                self.state = AI_NPC.AI_State.PASSIVE

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
                move.str_rep_of_action = f"upgrading building to {move.tpye}"
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
            if best_m_option.weighted_score >= self.properties['threshold_army_movement']:
                move.move_army_to = best_m_option.next_step
                move.doMoveArmy = True

        if DETAILED_DEBUG:
            for opt in all_options:
                s = f"Option of type {type(opt)}, score: {opt.weighted_score} ({opt.score})"
                if not (type(opt) == WaitOption or type(opt) == RaiseArmyOption):
                    s = s + f" -> Type: {opt.type}"
                hint(s)
            for m_opt in movement_options:
                stmp = 'army' if type(m_opt.target) is AI_Army else ''
                stmp = 'building' if type(m_opt.target) is AI_Building else ''
                s = f"M-Option target: {type(m_opt)} target({stmp}), score: {m_opt.weighted_score} ({m_opt.score})"
                hint(s)

        s = f"DECISION: {move.str_rep_of_action}"
        if move.doMoveArmy:
            s += f" moving army to {move.move_army_to}"
        hint(s)

    def calculate_heatmaps(self, ai_stat: AI_GameStatus):
        heat_map = AI_Toolkit.simple_heat_map(ai_stat.map.building_list, ai_stat.map.walkable_tiles,
                                              lambda n: AI_Toolkit.is_obj_in_list(n, ai_stat.map.walkable_tiles))
        for d, s in heat_map:
            if d <= self.properties['range_claimed_tiles']:
                self.claimed_tiles.append(s)


    def evaluate_move_building(self, ai_stat: AI_GameStatus) -> Optional[BuildOption]:
        if len(ai_stat.map.building_list) < self.properties['max_building_count']:
            for pre_t, bui_t in self.properties['buildings']:
                if pre_t is None:     # no prerequisite, thus we can build and not upgrade
                    if ai_stat.me.resources >= ai_stat.cost_building_construction[bui_t]:
                        # find a random building location
                        idx = random.randint(0, len(self.claimed_tiles) - 1)
                        site = self.claimed_tiles[idx].offset_coordinates
                        return BuildOption(bui_t, site, [], Priority.P_MEDIUM)
        return None


    def evaluate_move_upgrade(self, ai_stat: AI_GameStatus) -> Optional[UpgradeOption]:
        list_of_upgradable_buildings = []
        for b in ai_stat.map.building_list:
            for pre_t, up_t in self.properties['buildings']:
                if b.type == pre_t:
                    if ai_stat.me.resources >= ai_stat.cost_building_construction[up_t]:
                        list_of_upgradable_buildings.append((b, up_t))

        if len(list_of_upgradable_buildings) == 0:
            return None          # no building available that the AI can upgrade
        idx = random.randint(0, len(list_of_upgradable_buildings) - 1)
        site = list_of_upgradable_buildings[idx][0].offset_coordinates
        btype = list_of_upgradable_buildings[idx][1]
        return UpgradeOption(btype, site, Priority.P_MEDIUM)

    def evaluate_move_recruit_unit(self, ai_stat: AI_GameStatus) -> Union[None, RaiseArmyOption, RecruitmentOption]:
        if len(ai_stat.map.army_list) == 0:
            for b in ai_stat.map.building_list:
                nei = AI_Toolkit.get_neibours_on_set(b, ai_stat.map.buildable_tiles)  # buildable -> to avoid opp armies
                if len(nei) == 0:
                    continue
                x = random.sample(nei, 1)[0]
                return RaiseArmyOption(x.offset_coordinates, Priority.P_MEDIUM)
        for t_u in self.properties['units']:
            if ai_stat.me.population + ai_stat.cost_unit_recruitment[t_u].population <= ai_stat.me.population_limit:
                if ai_stat.me.resources >= ai_stat.cost_unit_recruitment[t_u].resources:
                    if ai_stat.me.culture >= ai_stat.cost_unit_recruitment[t_u].culture:
                        return RecruitmentOption(t_u, Priority.P_MEDIUM)
        return None

    def calculate_army_movement(self, ai_stat: AI_GameStatus, move: AI_Move) -> List[ArmyMovementOption]:
        targets: List[AI_Building, AI_Army] = []
        movements = []
        if self.properties['army_movement'] == "barbaric":
            if len(ai_stat.map.army_list) == 0:
                return movements
            if self.state == AI_NPC.AI_State.AGGRESSIVE or self.state == AI_NPC.AI_State.PASSIVE:
                """Identify targets and calculate path towards them"""
                for e_b in ai_stat.map.opp_building_list:
                    if e_b.visible:
                        targets.append(e_b)
                for e_a in ai_stat.map.opp_army_list:
                    targets.append(e_a)

                start_tile = ai_stat.map.army_list[0].base_tile
                for target in targets:
                    target_tile = target.base_tile
                    path = []
                    if not (start_tile is None or target_tile is None):
                        path = AI_Toolkit.dijkstra_pq(start_tile, target_tile, ai_stat.map.walkable_tiles)
                    else:
                        print(target_tile)
                        print(start_tile)
                        error("error in pathfinding of ai npc.")
                    # for p in path:
                    #     print(p.offset_coordinates, end=" ")
                    # print(" ")
                    if len(path) > 1:
                        movements.append(ArmyMovementOption(target, Priority.P_MEDIUM, path[1].offset_coordinates))
                    else:
                        hint("no path found to " + str(target.offset_coordinates))
            else:
                """Defencive army movement"""
                if len(ai_stat.map.opp_army_list) > 0:
                    hint("AI Barbaric: evading enemy army")
                    longest_path: Tuple[int, Optional[Tile]] = (-1, None)
                    target_tile = ai_stat.map.opp_army_list[0].base_tile
                    dist_to_army = AI_Toolkit.get_distance(target_tile, ai_stat.map.army_list[0].base_tile)
                    if dist_to_army >= self.safety_dist_to_enemy_army:
                        hint("AI Barbaric: Enemy army far enough away, no need to evade.")
                        return movements
                    neighbours = AI_Toolkit.get_neibours_on_set(ai_stat.map.army_list[0], ai_stat.map.walkable_tiles)
                    for nei in neighbours:
                        path = []
                        start_tile = nei
                        if start_tile and target_tile:
                            path = AI_Toolkit.dijkstra_pq(start_tile, target_tile, ai_stat.map.walkable_tiles)
                        else:
                            error("AI Barbaric: start_tile or target_tile not valid!")
                        if len(path) > 1:
                            if len(path) > longest_path[0]:
                                longest_path = (len(path), nei)
                    if longest_path[1] is not None:
                        movements.append(ArmyMovementOption(longest_path[1], Priority.P_MEDIUM, longest_path[1].offset_coordinates))
        elif self.properties['army_movement'] == "villager":
            if len(ai_stat.map.opp_army_list) > 0:
                hint("AI npc: moving between village and enemy army")
                shortest_path: Tuple[int, Optional[Tile]] = (100, None)
                neighbours = AI_Toolkit.get_neibours_on_set(ai_stat.map.building_list[0], ai_stat.map.walkable_tiles)
                target_tile = ai_stat.map.opp_army_list[0].base_tile
                for nei in neighbours:
                    path = []
                    start_tile = nei
                    if start_tile and target_tile:
                        path = AI_Toolkit.dijkstra_pq(start_tile, target_tile, ai_stat.map.walkable_tiles)
                    if len(path) > 1:
                        if len(path) < shortest_path[0]:
                            shortest_path = (len(path), nei)
                # calculate movement for army
                start_tile = ai_stat.map.army_list[0].base_tile
                target_tile = shortest_path[1]
                path = AI_Toolkit.dijkstra_pq(start_tile, target_tile, ai_stat.map.walkable_tiles)
                if len(path) > 1:
                    movements.append(ArmyMovementOption(path[1], Priority.P_MEDIUM, path[1].offset_coordinates))
        return movements

    def update_diplo_events(self, ai_stat: AI_GameStatus):
        """Idea: for each opponent building in the visible area of the barbaric, reduce diplo value by 2"""
        for e_b in ai_stat.map.opp_building_list:
            if e_b.visible:
                self.diplomacy.add_event(e_b.owner, e_b.offset_coordinates,
                                         DiploEventType.TYPE_ENEMY_BUILDING_SCOUTED, -2.0, 5, self.name)

        """Idea, for each opponent army movement in the visible area of the barbaric, reduce diplo value by 1
        Note: if the army moves, this gets triggered again, thus the lifetime of this event is only 1"""
        for e_a in ai_stat.map.opp_army_list:
            self.diplomacy.add_event(e_a.owner, e_a.offset_coordinates,
                                     DiploEventType.ENEMY_ARMY_INVADING_CLAIMED_ZONE, -1.0, 1, self.name)

        for opp in ai_stat.opponents:
            if opp.has_attacked:
                self.diplomacy.add_event(opp.id, (0, 0), DiploEventType.ATTACKED_BY_FACTION,
                                         -3.0, 3, self.name)

        for other_p_id in self.other_players:
            # hint(f"diplomatic value to {other_p_id}: {self.diplomacy.get_diplomatic_value_of_player(other_p_id)}")
            if self.diplomacy.get_diplomatic_value_of_player(other_p_id) < self.properties['diplo_aggressive_threshold']:
                if other_p_id not in self.hostile_player:
                    hint("Barbaric AI: Player id: " + str(other_p_id) + " got added to hostile players." )
                    self.hostile_player.add(other_p_id)


    def has_been_attacked(self, ai_stat: AI_GameStatus):
        for opp in ai_stat.opponents:
            if opp.has_attacked:
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

    # def get_army_spawn_loc(self, ai_stat: AI_GameStatus) -> (int, int):
    #     building_tile = ai_stat.map.building_list[0]
    #     nei = AI_Toolkit.get_neibours_on_set(building_tile, ai_stat.map.buildable_tiles)
    #     if len(nei) == 0:           # this seems to be unlikely but avoids crashing just in case
    #         hint("No suitable tile to spawn the army!")
    #         return -1, -1
    #     idx = random.randint(0, len(nei) - 1)
    #     for opp_a in ai_stat.map.opp_army_list:
    #         if opp_a.offset_coordinates == nei[idx].offset_coordinates:
    #             return -1, -1
    #     return nei[idx].offset_coordinates

    def get_state_as_str(self):
        if self.state == AI_NPC.AI_State.PASSIVE:
            return "    passive"
        elif self.state == AI_NPC.AI_State.DEFENSIVE:
            return "    defensive"
        elif self.state == AI_NPC.AI_State.AGGRESSIVE:
            return "    aggressive"
        return "    no state"
