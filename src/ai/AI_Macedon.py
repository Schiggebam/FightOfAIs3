import random
import timeit
from dataclasses import dataclass
from enum import Enum
from typing import Set, List, Tuple, Union, Optional, Dict, Any, Callable

from src.ai.AI_GameStatus import AI_GameStatus, AI_Move
from src.ai.AI_MapRepresentation import Tile, AI_Army, AI_Building, AI_Trade
from src.ai.ai_blueprint import AI
from src.ai.toolkit import essentials, basic
from src.ai.toolkit.basic import Weight, BuildOption, RecruitmentOption, WaitOption, Compass, ScoutingOption, Option, \
    CardinalDirection, UpgradeOption
from src.misc.game_constants import DiploEventType, hint, BuildingType, error, debug, UnitType, Priority, MoveType, \
    PlayerType, TradeType, TradeState

DETAILED_DEBUG = False
BASIC_DEBUG = True


class AI_Mazedonian(AI):
    class Strength(Enum):
        STRONGER = 10
        WEAKER = 11
        EQUAL = 12
        UNKNOWN = 13

    class Protocol(Enum):
        EARLY_GAME = 20
        MID_GAME = 21
        LATE_GAME = 22

    class AI_State(Enum):
        PASSIVE = 0
        AGGRESSIVE = 1
        DEFENSIVE = 2
        CRUSADE = 3

    @dataclass
    class ArmyConstellation:
        name: str
        ac: Tuple[float, float]  # should add up to 100%
        # seek_population: int  # possibly change this to a ratio -> this got moved to the build order

    @dataclass
    class BuildOrder:
        name: str
        bo: List[Tuple[BuildingType, int]]
        population: int

    @dataclass
    class RaiseArmyOption:
        score: Priority
        weighted_score: float = 0

    @dataclass()
    class AttackTarget:  # TODO rename to army movement
        target: Union[AI_Building, AI_Army]
        score: int
        weighted_score: float = 0

    Option = Union[BuildOption, RecruitmentOption, ScoutingOption, WaitOption, RaiseArmyOption]

    def __init__(self, name: str, own_id: int, other_players: [int]):
        super().__init__(name, other_players)
        self.personality = "militant"
        # self.personality = "temperate"
        self.own_id: int = own_id
        self.state: AI_Mazedonian.AI_State = AI_Mazedonian.AI_State.PASSIVE
        self.protocol: Optional[AI_Mazedonian.Protocol] = None
        self.build_order: Optional[AI_Mazedonian.BuildOrder] = None
        self.army_comp: Optional[AI_Mazedonian.ArmyConstellation] = None
        self.other_players = other_players
        self.hostile_player: Set[int] = set()  # stores ID of hostile players
        # self.priolist_targets: List[Tuple[int, Union[AI_Army, AI_Building], bool]] = []
        self.priolist_targets: List[AI_Mazedonian.AttackTarget] = []  # TODO rename to army movement
        # self.opponent_strength: Set[Tuple[int, int]] = set()  # stores the ID and the value
        self.opponent_strength: Dict[int, AI_Mazedonian.Strength] = {}
        self.claimed_tiles: Set[Tile] = set()
        self.is_loosing_food: bool = False
        self.inactive_huts: int = 0
        self.center_tile: Optional[Tile] = None
        self.compass: Optional[Compass] = None
        self.danger_zone: Set[Tile] = set()
        self.num_free_tiles: int = 0

        # state variables
        self.previous_army_population: int = -1
        self.previous_amount_of_buildings: int = -1
        self.previous_food: int = -1
        self.crusade_time: int = 0
        self.crusade_target_id: int = -1
        self.previous_attack_target: Optional[AI_Mazedonian.AttackTarget] = None

        # values to move to the xml file: and dependent on personality
        self.properties: Dict[str, Any] = {}
        from src.ai.scripts.macedon_hostile import on_setup, setup_weights, setup_movement_weights, setup_trade_weights
        on_setup(self.properties)

        # self.safety_dist_to_enemy_army: int = 3
        self.claiming_distance: int = 2  # all scouted tiles which are at least this far away are claimed
        self.threshold_considered_hostile: int = 2
        self.threshold_considered_neutral: int = 4
        self.threshold_considered_equal: int = 2
        self.threshold_target_value: int = 3
        self.equal_strength_defencive: bool = False
        self.unknown_strength_defencive: bool = False
        self.tend_to_be_defencive: bool = False
        bo_early_game: List[Tuple[BuildingType, int]] = [(BuildingType.FARM, 3), (BuildingType.HUT, 3),
                                                         (BuildingType.BARRACKS, 2)]
        bo_mid_game: List[Tuple[BuildingType, int]] = [(BuildingType.FARM, 6), (BuildingType.HUT, 5),
                                                       (BuildingType.BARRACKS, 4)]
        bo_late_game: List[Tuple[BuildingType, int]] = [(BuildingType.FARM, 13), (BuildingType.HUT, 9),
                                                        (BuildingType.BARRACKS, 10)]
        self.ac_passive: AI_Mazedonian.ArmyConstellation = AI_Mazedonian.ArmyConstellation("passive", (0.5, 0.5))
        self.ac_aggressive: AI_Mazedonian.ArmyConstellation = AI_Mazedonian.ArmyConstellation("aggressive", (0.8, 0.2))
        self.ac_defencive: AI_Mazedonian.ArmyConstellation = AI_Mazedonian.ArmyConstellation("defencive", (0.3, 0.7))
        self.build_orders: List[AI_Mazedonian.BuildOrder] = []
        self.build_orders.append(AI_Mazedonian.BuildOrder("early game", bo_early_game, 5))
        self.build_orders.append(AI_Mazedonian.BuildOrder("mid game", bo_mid_game, 10))
        self.build_orders.append(AI_Mazedonian.BuildOrder("late game", bo_late_game, 45))
        self.food_lower_limit: int = 15
        self.w_scouting_smooth_border: float = 1
        self.w_scouting_resource: float = 3
        self.w_scouting_claimed: float = 1

        self.weights: List[Weight] = []
        self.m_weights: List[Weight] = []
        self.trade_decisions: List[Callable[[AI_Trade, AI_GameStatus], None]] = setup_trade_weights(self)
        for c, v in setup_weights(self):
            self.weights.append(Weight(c, v))
        for c, v in setup_movement_weights(self):
            self.m_weights.append(Weight(c, v))

    def do_move(self, ai_stat: AI_GameStatus, move: AI_Move):
        self._reset_dump()
        t1 = timeit.default_timer()
        self._dump("------ {} -------".format(self.name))
        self.set_vars(ai_stat)
        self.create_heat_maps(ai_stat, move)
        self.update_diplo_events(ai_stat)
        t1_1 = timeit.default_timer()
        self.evaluate_hostile_players(ai_stat)
        self.estimate_opponent_strength(ai_stat)
        self.__get_attack_target(ai_stat)
        t1_2 = timeit.default_timer()
        self.evaluate_state(ai_stat)
        self.__get_protocol_and_bo(ai_stat)
        self.__evaluate_cardinal_direction(ai_stat)
        self.__evaluate_free_tiles(ai_stat)
        t_test_1 = timeit.default_timer()
        self.__print_situation(ai_stat)
        t_test_2 = timeit.default_timer()
        t2 = timeit.default_timer()

        build_options: List[BuildOption] = self.evaluate_move_building(ai_stat)
        # TODO handle building upgrads
        # t2_1 = timeit.default_timer()
        recruitment_options: List[Union[RecruitmentOption, AI_Mazedonian.RaiseArmyOption]] = \
            self.evaluate_move_recruitment(ai_stat)
        # t2_2 = timeit.default_timer()
        scouting_options: List[ScoutingOption] = self.evaluate_move_scouting(ai_stat)
        t3 = timeit.default_timer()

        all_options: List[Option] = []
        all_options.extend(build_options)
        all_options.extend(recruitment_options)
        all_options.extend(self.evaluate_move_upgrading(ai_stat))
        # all_options.extend(scouting_options)
        if len(scouting_options) > 0:
            all_options.append(scouting_options[0])  # reducing complexity - just consider the best scouting option
        all_options.append(WaitOption(Priority.P_MEDIUM))  # do nothing is an option
        self.weight_options(all_options, ai_stat, move)
        self.evaluate_army_movement(ai_stat, move)
        self.evaluate_trades(ai_stat, move)
        self.set_counters(ai_stat)
        t4 = timeit.default_timer()
        # debug(f"Timings: {t2 - t1}, {t3 - t2}, {t4 - t3}, total: {t4 - t1}")
        # debug(f"Timings {t1_1 - t1}, {t1_2 - t1_1}, {t2 - t1_2}")
        # debug(f"Detailled timing: {t_test_2 - t_test_1}")
        # clear out some data:
        self.reset_vars()
        self.diplomacy.calc_round()
        self.dump_diplomacy()

    def evaluate_trades(self, ai_stat: AI_GameStatus, move: AI_Move):
        for trade in ai_stat.trades:
            for decision in self.trade_decisions:
                decision(trade, ai_stat)
        move.trades = ai_stat.trades

    def evaluate_army_movement(self, ai_stat: AI_GameStatus, move: AI_Move):
        if len(ai_stat.map.army_list) == 0:
            return
        target_str = ""
        self.previous_attack_target = None
        if self.state == AI_Mazedonian.AI_State.PASSIVE:
            # for now, just move it out of the way.
            army_is_on_field = False
            if ai_stat.map.army_list[0].base_tile in ai_stat.map.own_farm_field_tiles:
                army_is_on_field = True
            if not army_is_on_field:
                has_farm = False
                for b in ai_stat.map.building_list:
                    if b.type == BuildingType.FARM:
                        has_farm = True
                if has_farm:
                    # walk to random field
                    path = []
                    idx = random.randint(0, len(ai_stat.map.own_farm_field_tiles) - 1)
                    # print(f"from: {ai_stat.map.army_list[0].base_tile.offset_coordinates} to {ai_stat.map.own_farm_field_tiles[idx].offset_coordinates}")
                    path = essentials.a_star(ai_stat.map.army_list[0].base_tile,
                                                  ai_stat.map.own_farm_field_tiles[idx],
                                                  ai_stat.map.walkable_tiles)
                    if len(path) > 1:
                        move.move_army_to = path[1].offset_coordinates
                        move.doMoveArmy = True
                        target_str = "corn field"

        #elif self.state == AI_Mazedonian.AI_State.DEFENSIVE or self.state == AI_Mazedonian.AI_State.AGGRESSIVE:
        else:
            if len(self.priolist_targets) > 0:
                if self.threshold_target_value <= self.priolist_targets[0].weighted_score:
                    # hint("on warpath: {} {}".format(self.threshold_target_value, self.priolist_targets[0].score))
                    # attack
                    start_tile = ai_stat.map.army_list[0].base_tile
                    target_tile = self.priolist_targets[0].target.base_tile
                    path = essentials.a_star(start_tile, target_tile, ai_stat.map.walkable_tiles)
                    if len(path) > 1:
                        self.previous_attack_target = self.priolist_targets[0]
                        move.move_army_to = path[1].offset_coordinates
                        move.doMoveArmy = True
                        target = self.priolist_targets[0]
                        s = "army" if type(target.target) is AI_Army else "building"
                        target_str = f"Movement: target: {s} @ loc: {target.target.offset_coordinates}"
                        if BASIC_DEBUG:
                            self._dump('moving to: {} from {} to {}'.format(str(move.move_army_to),
                                                                      start_tile.offset_coordinates,
                                                                      target_tile.offset_coordinates))
                else:
                    self._dump("targets value to low. Will not attack")
        if move.doMoveArmy:
            self._dump(target_str)

    def set_vars(self, ai_stat: AI_GameStatus):
        if self.previous_food > ai_stat.me.food:
            if DETAILED_DEBUG:
                self._dump("AI detected that it is loosing food")
            self.is_loosing_food = True
        self.inactive_huts = self.__count_inactive_huts(ai_stat)
        self._dump(f"Inactive huts: {self.inactive_huts}, loosing food: {self.is_loosing_food}")

    def reset_vars(self):
        self.is_loosing_food = False
        self.priolist_targets.clear()
        self.claimed_tiles.clear()
        self.danger_zone.clear()

    def create_heat_maps(self, ai_stat: AI_GameStatus, move: AI_Move):
        # cond = lambda n: AI_Toolkit.is_obj_in_list(n, ai_stat.map.walkable_tiles)
        heat_map = essentials.simple_heat_map(ai_stat.map.building_list, ai_stat.map.walkable_tiles,
                                              lambda n: essentials.is_obj_in_list(n, ai_stat.map.walkable_tiles))
        self.claimed_tiles.clear()
        c_dist = 2 if 'claiming_distance' not in self.properties else self.properties['claiming_distance']
        for d, s in heat_map:
            if d < c_dist:
                self.claimed_tiles.add(s)
        heat_map_2 = essentials.simple_heat_map(ai_stat.map.scoutable_tiles, ai_stat.map.discovered_tiles,
                                                lambda n: True)

        self.center_tile = ai_stat.map.building_list[0].base_tile
        if self.center_tile is None:
            """code to find the center tile"""
            max = -1
            tile_max = None
            for d, s in heat_map_2:
                val = d
                if d > max:
                    max = d
                    tile_max = s
            if BASIC_DEBUG:
                self._dump("Center is located @ " + str(tile_max.offset_coordinates))
            self.center_tile = tile_max
        ## get heatmap for danger zone ->
        heat_map_3 = essentials.simple_heat_map(ai_stat.map.opp_building_list, ai_stat.map.discovered_tiles,
                                                lambda n: True)
        for d, s in heat_map_3:
            if d <= 2:
                self.danger_zone.add(s)
                # move.info_at_tile.append((s.offset_coordinates, "D"))
        # move.info_at_tile.append((self.center_tile.offset_coordinates, str("C")))

        # for t in ai_stat.map.walkable_tiles:
        #     x_val = AI_Toolkit.num_resources_on_adjacent(t)
        #     # x_val = len(AI_Toolkit.get_neighbours(t))
        #     move.info_at_tile.append((t.offset_coordinates, str(x_val)))
        # for s in self.claimed_tiles:
        #     move.info_at_tile.append((s.offset_coordinates, 's'))

    def update_diplo_events(self, ai_stat: AI_GameStatus):

        for e_b in ai_stat.map.opp_building_list:
            if e_b.visible:
                if essentials.is_obj_in_list(e_b, list(self.claimed_tiles)):
                    self.diplomacy.add_event(e_b.owner, e_b.offset_coordinates,
                                             DiploEventType.ENEMY_BUILDING_IN_CLAIMED_ZONE, -2, 3)
        for e_a in ai_stat.map.opp_army_list:
            if essentials.is_obj_in_list(e_a, list(self.claimed_tiles)):
                self.diplomacy.add_event(e_a.owner, e_a.offset_coordinates,
                                         DiploEventType.ENEMY_ARMY_INVADING_CLAIMED_ZONE, -2, 3)

    def evaluate_hostile_players(self, ai_stat: AI_GameStatus):
        for other_p_id in self.other_players:
            if self.diplomacy.get_diplomatic_value_of_player(other_p_id) <= self.threshold_considered_hostile:
                if other_p_id not in self.hostile_player:
                    self.hostile_player.add(other_p_id)
            if self.diplomacy.get_diplomatic_value_of_player(other_p_id) >= self.threshold_considered_neutral:
                if other_p_id in self.hostile_player:
                    self.hostile_player.remove(other_p_id)
        for opp in ai_stat.opponents:
            if opp.has_lost and opp.id in self.hostile_player:
                self.hostile_player.remove(opp.id)
        if self.crusade_target_id != -1:
            if self.crusade_target_id not in self.hostile_player:
                self.hostile_player.add(self.crusade_target_id)
        self._dump(f"hostile players: {str(self.hostile_player)}")

    def estimate_opponent_strength(self, ai_stat: AI_GameStatus):
        """AI tries to estimate opponent's strength. Currently solely based on army population"""
        for other_p_id in self.hostile_player:  # only done for hostile players currently
            if len(ai_stat.map.army_list) == 0:
                self.opponent_strength[other_p_id] = AI_Mazedonian.Strength.STRONGER
                continue
            strength: AI_Mazedonian.Strength = AI_Mazedonian.Strength.UNKNOWN
            for e_a in ai_stat.map.opp_army_list:
                if e_a.owner == other_p_id:
                    factor = 1.0
                    for opp in ai_stat.opponents:
                        if opp.id == other_p_id:
                            if opp.type == PlayerType.BARBARIC:
                                factor = 0.7
                    opp_army_pop = e_a.population * factor
                    t_equal = self.threshold_considered_equal
                    if abs(opp_army_pop - ai_stat.map.army_list[0].population) < t_equal:
                        strength = AI_Mazedonian.Strength.EQUAL
                    elif opp_army_pop > ai_stat.map.army_list[0].population:
                        strength = AI_Mazedonian.Strength.STRONGER
                    elif opp_army_pop < ai_stat.map.army_list[0].population:
                        strength = AI_Mazedonian.Strength.WEAKER
            self.opponent_strength[other_p_id] = strength

    def evaluate_state(self, ai_stat: AI_GameStatus):
        old_state = self.state
        if self.state == AI_Mazedonian.AI_State.PASSIVE:
            if len(self.hostile_player) > 0:
                def_count = 0
                agg_count = 0
                for h_p in self.hostile_player:
                    opp_s = self.opponent_strength[h_p]
                    if opp_s == AI_Mazedonian.Strength.EQUAL:
                        if self.equal_strength_defencive:
                            def_count = def_count + 1
                        else:
                            agg_count = agg_count + 1
                    elif opp_s == AI_Mazedonian.Strength.WEAKER:
                        agg_count = agg_count + 1
                    elif opp_s == AI_Mazedonian.Strength.STRONGER:
                        def_count = def_count + 1
                    elif opp_s == AI_Mazedonian.Strength.UNKNOWN:
                        if self.unknown_strength_defencive:
                            def_count = def_count + 1
                        else:
                            agg_count = agg_count + 1
                if def_count > agg_count:
                    self.state = AI_Mazedonian.AI_State.DEFENSIVE
                elif def_count > agg_count:
                    self.state = AI_Mazedonian.AI_State.AGGRESSIVE
                else:
                    if self.tend_to_be_defencive:
                        self.state = AI_Mazedonian.AI_State.DEFENSIVE
                    else:
                        self.state = AI_Mazedonian.AI_State.AGGRESSIVE
        elif self.state == AI_Mazedonian.AI_State.AGGRESSIVE:
            if len(self.hostile_player) == 0:
                self.state = AI_Mazedonian.AI_State.PASSIVE
            if len(self.priolist_targets) == 0:
                self.state = AI_Mazedonian.AI_State.DEFENSIVE

        elif self.state == AI_Mazedonian.AI_State.DEFENSIVE:
            if len(ai_stat.map.building_list) < self.previous_amount_of_buildings:  # we got attacked
                if len(self.hostile_player) == 0:
                    debug("Problem with AI, we got attacked but no hostile players?!")
                else:
                    self.state = AI_Mazedonian.AI_State.AGGRESSIVE
            if len(self.hostile_player) == 0:
                self.state = AI_Mazedonian.AI_State.PASSIVE

        # crusade ?
        if self.protocol is AI_Mazedonian.Protocol.LATE_GAME and self.state != AI_Mazedonian.AI_State.CRUSADE:
            if ai_stat.me.food > 100 and ai_stat.me.population > 20:
                target_player_id = self.diplomacy.get_player_with_lowest_dv()
                if target_player_id != -1:
                    if len(self.priolist_targets) > 0:
                        self.state = AI_Mazedonian.AI_State.CRUSADE
                        self.crusade_target_id = target_player_id
                        self.crusade_time = 15
                else:
                    self._dump("unable to find ID for crusade")

        if self.state is AI_Mazedonian.AI_State.CRUSADE:
            self.crusade_time -= 1
            if self.crusade_time < 0:
                self.state = AI_Mazedonian.AI_State.PASSIVE
                self.crusade_target_id = -1


        self._dump(f"State: {old_state} -> {self.state}")

    def weight_options(self, options: List[Option], ai_stat: AI_GameStatus, move: AI_Move):
        used_weights: List[str] = []
        for opt in options:                 # --------------------- Action options ----------
            opt.weighted_score = opt.score.value
            if opt.score == Priority.P_NO:  # no option (should not depend on weights) -> contain invalid info
                continue
            for w in self.weights:
                if w.condition(opt, ai_stat):
                    used_weights.append(w.condition.__name__)
                    if DETAILED_DEBUG:
                        self._dump(f"Weight w: {w.weight} applied on score: {opt.weighted_score} of {type(opt)} ")
                    opt.weighted_score = opt.weighted_score + w.weight

        used_weights.append(" | ")

        for m in self.priolist_targets:         # --------------------- Movement options ----------
            if m.score == Priority.P_NO:
                continue
            for w in self.m_weights:
                if w.condition(m, ai_stat):
                    used_weights.append(w.condition.__name__)
                    m.weighted_score = m.weighted_score + w.weight

        options.sort(key=lambda x: x.weighted_score, reverse=True)
        self.priolist_targets.sort(key=lambda x: x.weighted_score, reverse=True)

        self._dump("---")
        for opt in options:
            s = f"\tOption of type: {type(opt)}, score: {opt.weighted_score}"
            if type(opt) == RecruitmentOption or type(opt) == BuildOption:
                s = s + f", type {opt.type}"
            if type(opt) == ScoutingOption:
                s = s + f", site: {opt.site}"
            s = s + f", former priority: {opt.score}"
            self._dump(s)
        for m in self.priolist_targets:
            s = f"\tAttack Target : {'army' if type(m.target) is AI_Army else 'building'}, score: {m.weighted_score}"
            self._dump(s)
        s_tmp = ""
        for w in used_weights:
            s_tmp += w + ", "
        self._dump(s_tmp)
        # translate this into move
        best_option: Option = options[0]
        if type(best_option) == WaitOption:
            move.move_type = MoveType.DO_NOTHING
            move.str_rep_of_action = "waiting"
        elif type(best_option) == BuildOption:
            move.move_type = MoveType.DO_BUILD
            move.loc = best_option.site
            move.type = best_option.type
            for at in best_option.associated_tiles:
                move.info.append(at)
            s_tmp = f"building a {best_option.type} at {str(move.loc)} ({str(best_option.cardinal_direction)})"
            if move.type == BuildingType.FARM:
                s_tmp += f" TL: {str(best_option.threat_level)}"
            move.str_rep_of_action = s_tmp
        elif type(best_option) == RecruitmentOption:
            move.move_type = MoveType.DO_RECRUIT_UNIT
            move.type = best_option.type
            move.str_rep_of_action = f"recruiting a {best_option.type}"
        elif type(best_option) == ScoutingOption:
            move.move_type = MoveType.DO_SCOUT
            move.loc = best_option.site
            move.str_rep_of_action = "scouting at" + str(move.loc)
        elif type(best_option) == AI_Mazedonian.RaiseArmyOption:
            move.move_type = MoveType.DO_RAISE_ARMY
            move.loc = self.get_army_spawn_loc(ai_stat)
            move.str_rep_of_action = "raising new army at"
        elif type(best_option) is UpgradeOption:
            move.move_type = MoveType.DO_UPGRADE_BUILDING
            move.loc = best_option.site
            move.type = best_option.type
            move.str_rep_of_action = "upgrading hut to villa"
        else:
            error("unexpected type")

        self._dump(f"DECISION: {move.str_rep_of_action}")

    def evaluate_move_building(self, ai_stat: AI_GameStatus) -> List[BuildOption]:
        def normalize(value: int) -> Priority:
            if value <= 0:
                return Priority.P_NO
            elif value <= 1:
                return Priority.P_LOW
            elif value <= 2:
                return Priority.P_MEDIUM
            elif value <= 4:
                return Priority.P_HIGH
            return Priority.P_CRITICAL

        # get current bo (somewhat a code duplicate, but offset is required)
        current_bo = self.build_order
        offset_to_bo, _ = self.__compare_to_bo(current_bo, ai_stat)

        if current_bo != None:
            # hint("Currently active build order: {}".format(current_bo.name))
            # value_farm = -1
            prio_racks = Priority.P_NO
            value_hut = -1
            # site_farm = (-1, -1)
            farm_opt = BuildOption(BuildingType.FARM, (-1, -1), [], Priority.P_NO)
            racks_opt = BuildOption(BuildingType.BARRACKS, (-1, -1), [], Priority.P_NO)
            hut_opt = BuildOption(BuildingType.HUT, (-1, -1), [], Priority.P_NO)
            site_racks = (-1, -1)
            site_hut = (-1, -1)
            for t, v in offset_to_bo:
                # hint(f"for type: {t}, v: {v}")
                if v > 0:  # only check this building type if it is part of the bo
                    if t == BuildingType.FARM:
                        farm_opt: BuildOption = self.__best_building_site_farm(ai_stat)
                        if v >= 2:
                            if farm_opt.score.value > 0:  # not Priority.P_NO
                                farm_opt.score = Priority.increase(farm_opt.score)
                    elif t == BuildingType.HUT:
                        value_hut, site_hut = self.__best_building_site_hut(ai_stat)
                        hut_opt = BuildOption(BuildingType.HUT, site_hut, [], normalize(value_hut))
                        v = v + self.inactive_huts
                        if v >= 2:
                            if hut_opt.score.value > 0:  # not Priority.P_NO
                                hut_opt.score = Priority.increase(hut_opt.score)
                    elif t == BuildingType.BARRACKS:
                        prio_racks, site_racks = self.__best_building_site_barracks(ai_stat)
                        racks_opt = BuildOption(BuildingType.BARRACKS, site_racks, [], prio_racks)
                        if v >= 2:
                            if prio_racks.value > 0:  # not Priority.P_NO
                                racks_opt.score = Priority.increase(racks_opt.score)
                    else:
                        debug("Build order contains unknown building type -> " + str(t))
            if ai_stat.me.food < self.food_lower_limit:
                if farm_opt is None:  # we force to look for a site even if the BO does not allow for it
                    farm_opt = value_farm, site_farm = self.__best_building_site_farm(ai_stat)

            # if farm_opt:
            #     hint(f"amount of fields {len(farm_opt.associated_tiles)}")

            return [farm_opt, hut_opt, racks_opt]
        else:
            debug("No building order found. This is not supported so far. Need guidance!")
            return []

    def __best_building_site_farm(self, ai_stat: AI_GameStatus) -> BuildOption:
        """building sites get scored by how many buildable fields there are next to it"""
        best_score = -1
        best_site = (-1, -1)
        best_cd: Optional[List[CardinalDirection]] = None
        best_tl = None
        fields = []
        p = Priority.P_NO
        is_next_to_res = False  # just for printing
        if ai_stat.me.resources >= ai_stat.cost_building_construction[BuildingType.FARM]:
            for ai_t in ai_stat.map.buildable_tiles:
                tmp = False  # just for printing
                possible_fields = []
                score = 0
                for n in essentials.get_neighbours_on_set(ai_t, ai_stat.map.buildable_tiles):
                    if basic.num_resources_on_adjacent(n) == 0:
                        possible_fields.append(n)
                    if essentials.is_obj_in_list(n, ai_stat.map.scoutable_tiles):
                        score += 1
                score += len(possible_fields)
                amount_of_fields = min(3, len(possible_fields))
                sampled = random.sample(possible_fields, amount_of_fields)
                score += len(essentials.get_neighbours_on_set(ai_t, ai_stat.map.scoutable_tiles)) / 2
                # if build site is next to a resource --> reduce value by 1 for each resource field
                score = score - basic.num_resources_on_adjacent(ai_t)
                # make the score dependent on safety level of region
                #score = score - self.compass.get_threat_level(ai_t).value * 2
                if ai_t in self.danger_zone:
                    score += - 10

                if best_score < score:
                    best_score = score
                    is_next_to_res = tmp
                    best_site = ai_t.offset_coordinates
                    best_cd = self.compass.get_cardinal_direction_obj(ai_t, self.compass.center_tile)
                    best_tl = self.compass.get_threat_level(ai_t)
                    fields.clear()
                    for s in sampled:
                        fields.append(s.offset_coordinates)

        if is_next_to_res:
            debug("The farm will be next to a resource (apparently there is no better spot)")

        # translate score to priority (normalization step)
        if len(fields) >= 3:
            p = Priority.P_HIGH
        elif len(fields) >= 2:
            p = Priority.P_MEDIUM
        elif len(fields) >= 1:
            p = Priority.P_LOW
        # hint(f"                            type eval: {type(p)}")
        return BuildOption(BuildingType.FARM, best_site, fields, p, cardinal_direction=best_cd, threat_level=best_tl)

    def __best_building_site_hut(self, ai_stat: AI_GameStatus) -> Tuple[int, Tuple[int, int]]:
        """building sites get scored by their number of resource fields next to them"""
        best_score = -1
        best_site = (-1, -1)
        if ai_stat.me.resources >= ai_stat.cost_building_construction[BuildingType.HUT]:
            for ai_t in ai_stat.map.buildable_tiles:
                score = basic.num_resources_on_adjacent(ai_t)
                if best_score < score:
                    best_score = score
                    best_site = ai_t.offset_coordinates
        return best_score, best_site

    def __best_building_site_barracks(self, ai_stat: AI_GameStatus) -> Tuple[Priority, Tuple[int, int]]:
        """building sites should be a claimed tile and not next to a resource"""
        if ai_stat.me.resources >= ai_stat.cost_building_construction[BuildingType.BARRACKS]:
            candidates = []
            for c in self.claimed_tiles:
                if not c.is_buildable:  # if tile is not buildable, forget it
                    continue
                res_next_to_can = basic.num_resources_on_adjacent(c)

                if res_next_to_can == 0:
                    # very hard constraint (go by value would be better)
                    #if self.compass.get_threat_level(c).value <= ThreatLevel.LOW_RISK.value:
                        # build barracks only in safe zone
                    if c not in self.danger_zone:
                        candidates.append(c)
            if DETAILED_DEBUG:
                debug(f"possible candidates for a barracks: {len(candidates)}")
            if len(candidates) > 0:
                idx = random.randint(0, len(candidates) - 1)
                c = 0
                for e in candidates:
                    if idx == c:
                        return Priority.P_MEDIUM, e.offset_coordinates
                    c = c + 1
        return Priority.P_NO, (-1, -1)

    def evaluate_move_recruitment(self, ai_stat: AI_GameStatus) -> List[Union[RecruitmentOption, RaiseArmyOption]]:
        options = []
        if ai_stat.me.population >= ai_stat.me.population_limit:
            return options
        if len(ai_stat.map.army_list) == 0:
            options.append(AI_Mazedonian.RaiseArmyOption(Priority.P_HIGH))
            return options  # cannot recruit if no army available
        # calculate offset to desired population by build order
        prio_merc = Priority.P_LOW
        prio_knight = Priority.P_LOW
        offset = self.build_order.population - ai_stat.me.population
        if offset > 0:
            prio_merc = Priority.increase(prio_merc)
            prio_knight = Priority.increase(prio_knight)
        else:
            prio_merc = Priority.decrease(prio_merc)
            prio_knight = Priority.decrease(prio_knight)
        # compare to desired army composition:
        army = ai_stat.map.army_list[0]
        if army.population > 0:
            percentage_merc_wanted = self.army_comp.ac[0] / (self.army_comp.ac[0] + self.army_comp.ac[0])
            percentage_merc_actual = army.mercenaries / (army.mercenaries + army.knights)
            percentage_knig_wanted = self.army_comp.ac[1] / (self.army_comp.ac[0] + self.army_comp.ac[0])
            percentage_knig_actual = army.knights / (army.mercenaries + army.knights)
            if DETAILED_DEBUG:
                debug(f"merc: {percentage_merc_wanted} - {percentage_merc_actual} | knight: {percentage_knig_wanted} - {percentage_knig_actual}")
            if (percentage_knig_wanted - percentage_knig_actual) < (percentage_merc_wanted - percentage_merc_actual):
                prio_merc = Priority.increase(prio_merc)
            else:
                prio_knight = Priority.increase(prio_knight)
        else:   # in case the population is 0, we cannot compute the above. Just increase the priority
            prio_knight = Priority.increase(prio_knight)
            prio_merc = Priority.increase(prio_merc)
        # mercenary
        cost_unit_me = ai_stat.cost_unit_recruitment[UnitType.MERCENARY]
        if ai_stat.me.population + cost_unit_me.population <= ai_stat.me.population_limit:
            if ai_stat.me.resources >= cost_unit_me.resources:
                if ai_stat.me.culture >= cost_unit_me.culture:
                    options.append(RecruitmentOption(UnitType.MERCENARY, prio_merc))
                else:
                    if DETAILED_DEBUG:
                        hint("not enough culture to recruit a mercenary. actual: {} required: {}".format(
                            ai_stat.me.culture, cost_unit_me.culture))
            else:
                if DETAILED_DEBUG:
                    hint("not enough resources to recruit a mercenary. actual: {} required: {}".format(
                        ai_stat.me.resources, cost_unit_me.resources))
        else:
            if DETAILED_DEBUG:
                hint("not enough free population to recruit a mercenary")
        # knight
        cost_unit_kn = ai_stat.cost_unit_recruitment[UnitType.KNIGHT]
        if ai_stat.me.population + cost_unit_kn.population <= ai_stat.me.population_limit:
            if ai_stat.me.resources >= cost_unit_kn.resources:
                if ai_stat.me.culture >= cost_unit_kn.culture:
                    options.append(RecruitmentOption(UnitType.KNIGHT, prio_knight))
                else:
                    if DETAILED_DEBUG:
                        hint("not enough culture to recruit a knight. actual: {} required: {}".format(
                            ai_stat.me.culture, cost_unit_kn.culture))
            else:
                if DETAILED_DEBUG:
                    hint("not enough resources to recruit a knight. actual: {} required: {}".format(
                        ai_stat.me.resources, cost_unit_kn.resources))
        else:
            if DETAILED_DEBUG:
                hint("not enough free population to recruit a knight")
        return options

    def evaluate_move_upgrading(self, ai_stat: AI_GameStatus) -> List[UpgradeOption]:
        """ find best option for an upgradable building
        Idea: reduce score if there are still adjacent resource fields or if the hut is in the danger zone
        Increase score if number of inactive huts is high and if located in save zone"""
        def normalize(s: float) -> Priority:
            if s < 0:
                return Priority.P_NO
            elif 0 <= s < 3:
                return Priority.P_MEDIUM
            elif s >= 3:
                return Priority.P_HIGH

        options: List[UpgradeOption] = []
        if ai_stat.me.resources < ai_stat.cost_building_construction[BuildingType.VILLA]:
            return options

        huts = [x for x in ai_stat.map.building_list if x.type is BuildingType.HUT]
        best_score: float = -100
        best_option: Optional[UpgradeOption] = None
        for hut in huts:
            score = - basic.num_resources_on_adjacent(hut)
            score += self.inactive_huts
            if hut.base_tile in self.claimed_tiles:
                score = score + 1
            if hut.base_tile in self.danger_zone:
                score = score - 2
            if score > best_score:
                best_score = score
                best_option = UpgradeOption(BuildingType.VILLA, hut.offset_coordinates, normalize(score))
        return [best_option]

    def evaluate_move_scouting(self, ai_stat: AI_GameStatus) -> List[ScoutingOption]:
        """scores the scouting options, currently by the distance to a own building
        (want to make sure that all claimable tiles are scouted) and by the proximity to a resource fieled"""
        options: List[ScoutingOption] = []
        if ai_stat.me.resources < ai_stat.costScout:
            return options

        for s in ai_stat.map.scoutable_tiles:
            options.append(ScoutingOption(s.offset_coordinates, Priority.P_NO))

        for so in options:
            value = 0
            tmp_tile = ai_stat.map.get_tile(so.site)
            dist1 = essentials.get_neighbours(tmp_tile)
            # 1. increase value by resources nearby
            num_of_tiles_with_res = 0
            for t_at_dist_1 in dist1:
                if t_at_dist_1.has_resource():
                    num_of_tiles_with_res = num_of_tiles_with_res + 1
            value = value + (num_of_tiles_with_res * self.w_scouting_resource)
            # 2. increase value by proximity to claimed tiles
            num_of_claimed_tiles = 0
            for t_at_dist_1 in dist1:
                if essentials.is_obj_in_list(t_at_dist_1, list(self.claimed_tiles)):
                    num_of_claimed_tiles = num_of_claimed_tiles + 1
            value = value + (num_of_claimed_tiles * self.w_scouting_claimed)
            # 3. try to smooth out border
            # value = value + (len(dist1) * self.w_scouting_smooth_border)

            # Normalize
            high = max(2 * self.w_scouting_resource, 4 * self.w_scouting_claimed, 4 * self.w_scouting_smooth_border)
            # hint(f"scouting value: {value} (res nearby: {num_of_tiles_with_res},")
            # f" claimed_tiles near_by: {num_of_claimed_tiles} ) ")
            if value < 0.3 * high:
                so.score = Priority.P_LOW
            elif value < 0.6 * high:
                so.score = Priority.P_MEDIUM
            elif value < high:
                so.score = Priority.P_HIGH
            else:
                so.score = Priority.P_CRITICAL

            # hint("Tile at {} has scouting prio: {}".format(so.site, so.score))
        options.sort(key=lambda x: x.score.value, reverse=True)
        return options

    def set_counters(self, ai_stat: AI_GameStatus):
        self.previous_amount_of_buildings = len(ai_stat.map.building_list)
        if len(ai_stat.map.army_list) > 0:
            self.previous_army_population = ai_stat.map.army_list[0].population
        else:
            self.previous_army_population = 0
        self.previous_food = ai_stat.me.food

    def __get_protocol_and_bo(self, ai_stat: AI_GameStatus):
        """simply defines if the AI is in early game, mid-game or late-game -> done by build order
        make sure that this gets called after the state has been determined """
        # ugly implementation - but most of it has to be hard-coded
        done_build_orders = 0
        undone = False
        current_bo = None
        for bo in self.build_orders:
            current_bo = bo
            (c_list, p_offset) = self.__compare_to_bo(bo, ai_stat)
            # hint(f"p_offset {p_offset}")
            for c, v in c_list:
                if v > 0 or p_offset > 0:
                    undone = True
            if undone:
                break
            done_build_orders = done_build_orders + 1
        self.build_order = current_bo
        if done_build_orders == 0:
            self.protocol = AI_Mazedonian.Protocol.EARLY_GAME
        elif done_build_orders == 1:
            self.protocol = AI_Mazedonian.Protocol.MID_GAME
        elif done_build_orders == 2:
            self.protocol = AI_Mazedonian.Protocol.LATE_GAME
        if self.state == AI_Mazedonian.AI_State.PASSIVE:
            self.army_comp = self.ac_passive
        if self.state == AI_Mazedonian.AI_State.DEFENSIVE:
            self.army_comp = self.ac_defencive
        if self.state == AI_Mazedonian.AI_State.AGGRESSIVE:
            self.army_comp = self.ac_aggressive

        self._dump(f"Active protocol: {self.protocol}, build order: {self.build_order.name}, army comp: {self.army_comp.name}")

    def __compare_to_bo(self, bo: BuildOrder, ai_stat: AI_GameStatus):
        """this will return a list of tuples, comparing every b type the with desired value according to the bo
        (b_type, value) -> if value < 0 there are x more buildings than wanted - otherwise > 0
        if all values are <= 0, the bo is complete"""
        tmp = []
        for b_type, value in bo.bo:
            tmp.append([b_type, value])
        for b in ai_stat.map.building_list:
            for t in tmp:
                if t[0] == b.type:
                    t[1] = t[1] - 1
        return (tmp, bo.population - ai_stat.me.population)

    def __compare_to_ac(self, army: AI_Army, ac: ArmyConstellation) -> UnitType:
        off_merc = ac.ac[0] - (army.mercenaries / army.population)
        off_knight = ac.ac[1] - (army.knights / army.population)
        if off_merc < 0:  # we have too many mercs
            return UnitType.KNIGHT
        if off_knight < 0:  # too many knights
            return UnitType.MERCENARY
        error("This should not happen")

    def __get_buildings_of_type(self, t: BuildingType, ai_stat: AI_GameStatus) -> int:
        value = 0
        for b in ai_stat.map.building_list:
            if b.type == t:
                value = value + 1
        return value

    def __get_attack_target(self, ai_stat: AI_GameStatus):
        """get's the best attack target
        currently only buildings and armies of hostile players are considered to be attackable"""
        targets: Set[Tuple[Union[AI_Building, AI_Army], bool]] = set()
        # priority_list: List[Tuple[int, Union[AI_Building, AI_Army]]]= []
        if len(ai_stat.map.army_list) == 0:  # in case we don't have an army
            return
        for e_a in ai_stat.map.opp_army_list:
            targets.add((e_a, True))
        for e_b in ai_stat.map.opp_building_list:
            if e_b.visible:
                targets.add((e_b, False))

        self._dump(f"Found {len(targets)} target(s) for our army")
        for target, is_army in targets:
            value = 0
            if target.owner in self.hostile_player:
                if self.opponent_strength[target.owner] == AI_Mazedonian.Strength.STRONGER:
                    value = 1 if is_army else 0
                elif self.opponent_strength[target.owner] == AI_Mazedonian.Strength.WEAKER:
                    value = 5 if is_army else 4
                else:  # opp has unknown strength or equal
                    value = 3 if is_army else 2
            if BASIC_DEBUG:
                self._dump(f"Target @ {str(target.offset_coordinates)} ({'army' if is_army else 'building'}) has value {value}")
            self.priolist_targets.append(AI_Mazedonian.AttackTarget(target, value))
        if len(self.priolist_targets) > 0:
            self.priolist_targets.sort(key=lambda x: x.score, reverse=True)

            self._dump("Best attack target: {} ({}) value:{}".format(str(self.priolist_targets[0].target.offset_coordinates),
                                                                         'army' if type(
                                                                       self.priolist_targets[0].target) else 'building',
                                                                   self.priolist_targets[0].score))
        else:
            self._dump("No Targets found")

    def __print_situation(self, ai_stat: AI_GameStatus):

        self._dump(f"Res: {ai_stat.me.resources}, Cul: {ai_stat.me.culture}, Food: {ai_stat.me.food}"
                   f", Pop: {ai_stat.me.population} / {ai_stat.me.population_limit}")
        for h in self.hostile_player:
            self._dump("hostile player: [ID:] {} estimated strength: {}".format(h, self.opponent_strength[h]))
        #if self.inactive_huts > 0:
        self._dump(f"Inactive huts: {self.inactive_huts}")
        s_tmp = ""
        for key, value in self.compass.book.items():
            s_tmp += f"{key} -> {value.value}, "
        self._dump(s_tmp)
        self._dump(f"Free tiles: {self.num_free_tiles} ({self.num_free_tiles/len(ai_stat.map.discovered_tiles)*100:.1} %)")
        # hint(f"N: {self.compass.}, E: {self.compass.east}, S: {self.compass.south}, W: {self.compass.west}")
        # dump active events:


    def get_army_spawn_loc(self, ai_stat: AI_GameStatus) -> Tuple[int, int]:
        nei: List[Tile] = essentials.get_neighbours_on_set(ai_stat.map.building_list[0].base_tile, ai_stat.map.walkable_tiles)
        idx = random.randint(0, len(nei)-1)
        return nei[idx].offset_coordinates

    def __count_inactive_huts(self, ai_stat) -> int:
        count = 0
        for b in ai_stat.map.building_list:
            if b.type == BuildingType.HUT:
                has_res = False
                for n in essentials.get_neighbours_on_set(b.base_tile, ai_stat.map.discovered_tiles):
                    if n.has_resource():
                        has_res = True
                if not has_res:
                    count += 1
        return count

    def __evaluate_cardinal_direction(self, ai_stat: AI_GameStatus):
        if self.center_tile is None:
            return
        self.compass = Compass(self.center_tile)
        for opp_a in ai_stat.map.opp_army_list:
            self.compass.raise_threat_level(opp_a.base_tile)
            self.compass.raise_threat_level(opp_a.base_tile)
        for opp_b in ai_stat.map.opp_building_list:
            if opp_b.visible:
                self.compass.raise_threat_level(opp_b.base_tile)
        # for a in ai_stat.map.army_list:
        #     self.compass.lower_threat_level(a.base_tile)

    def __evaluate_free_tiles(self, ai_stat: AI_GameStatus):
        value = 0
        for n in ai_stat.map.discovered_tiles:
            if not n.has_resource():
                if not n.has_building():
                    if n not in self.danger_zone:
                        value += 1
        self.num_free_tiles = value


    def get_state_as_str(self) -> str:
        s = "    STATE: "
        if self.state == AI_Mazedonian.AI_State.PASSIVE:
            s = s + "passive"
        elif self.state == AI_Mazedonian.AI_State.DEFENSIVE:
            s = s + "defensive"
        elif self.state == AI_Mazedonian.AI_State.AGGRESSIVE:
            s = s + "aggressive"
        elif self.state == AI_Mazedonian.AI_State.CRUSADE:
            s = s + "crusade"
        s = s + "\n    PR:" + str(self.protocol)
        if self.build_order:
            s = s + "\n    BO:" + str(self.build_order.name)
        return s
