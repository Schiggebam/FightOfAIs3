import random
from enum import Enum
from typing import Set, List, Callable, Tuple, Union, Optional

from dataclasses import dataclass

from src.ai import AI_Toolkit
from src.ai.AI_GameStatus import AI_GameStatus, AI_Move, AI_Tile, AI_Building, AI_Army
from src.ai.ai_blueprint import AI
from src.misc.game_constants import DiploEventType, hint, BuildingType, error, debug, UnitType, Priority

DETAILED_DEBUG = False

class AI_Mazedonian(AI):
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

    @dataclass
    class ArmyConstellation:
        name: str
        ac: Tuple[float, float]  # should add up to 100%
        #seek_population: int  # possibly change this to a ratio -> this got moved to the build order

    @dataclass
    class BuildOrder:
        name: str
        bo: List[Tuple[BuildingType, int]]
        population: int

    @dataclass
    class WaitOption:
        score: Priority
        weighted_score: float = 0

    @dataclass()
    class BuildOption:
        type: BuildingType
        site: Tuple[int, int]
        associated_tiles: List[Tuple[int, int]]
        score: Priority
        weighted_score: float = 0

    @dataclass
    class RecruitmentOption:
        type: UnitType
        score: Priority
        weighted_score: float = 0

    @dataclass
    class RaiseArmyOption:
        score: Priority
        weighted_score: float = 0

    @dataclass
    class ScoutingOption:
        site: Tuple[int, int]
        score: Priority
        weighted_score: float = 0

    @dataclass
    class Weight:
        condition: Callable[..., bool]
        weight: float

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
        self.priolist_targets: List[Tuple[int, Union[AI_Army, AI_Building], bool]] = []
        self.opponent_strength: Set[Tuple[int, int]] = set()  # stores the ID and the value
        self.claimed_tiles: Set[AI_Tile] = set()
        self.is_loosing_food: bool = False

        # state variables
        self.previous_army_population: int = -1
        self.previous_amount_of_buildings: int = -1
        self.previous_food: int = -1

        # values to move to the xml file: and dependent on personality
        self.safety_dist_to_enemy_army: int = 3
        self.claiming_distance: int = 2  # all scouted tiles which are at least this far away are claimed
        self.threshold_considered_hostile: int = 2
        self.threshold_considered_neutral: int = 4
        self.threshold_considered_equal: int = 2
        self.equal_strength_defencive: bool = False
        self.unknown_strength_defencive: bool = False
        self.tend_to_be_defencive: bool = False
        bo_early_game: List[Tuple[BuildingType, int]] = [(BuildingType.FARM, 2), (BuildingType.HUT, 2),
                                                         (BuildingType.BARRACKS, 2)]
        bo_mid_game: List[Tuple[BuildingType, int]] = [(BuildingType.FARM, 6), (BuildingType.HUT, 5),
                                                       (BuildingType.BARRACKS, 4)]
        bo_late_game: List[Tuple[BuildingType, int]] = [(BuildingType.FARM, 7), (BuildingType.HUT, 7),
                                                        (BuildingType.BARRACKS, 10)]
        self.ac_passive: AI_Mazedonian.ArmyConstellation = AI_Mazedonian.ArmyConstellation("passive", (0.5, 0.5))
        self.ac_aggressive: AI_Mazedonian.ArmyConstellation = AI_Mazedonian.ArmyConstellation("aggressive", (0.8, 0.2))
        self.ac_defencive: AI_Mazedonian.ArmyConstellation = AI_Mazedonian.ArmyConstellation("defencive", (0.3, 0.7))
        self.build_orders: List[AI_Mazedonian.BuildOrder] = []
        self.build_orders.append(AI_Mazedonian.BuildOrder("early game", bo_early_game, 5))
        self.build_orders.append(AI_Mazedonian.BuildOrder("mid game", bo_mid_game, 10))
        self.build_orders.append(AI_Mazedonian.BuildOrder("late game", bo_late_game, 15))
        self.food_lower_limit: int = 15
        self.w_scouting_smooth_border: float = 1
        self.w_scouting_resource: float = 1
        self.w_scouting_claimed: float = 1

        self.weights: List[AI_Mazedonian.Weight] = []
        for c, w in self.__setup_weights():
            self.weights.append(AI_Mazedonian.Weight(c, w))

    def do_move(self, ai_stat: AI_GameStatus, move: AI_Move):
        self.__print_situation(ai_stat)
        self.create_heat_maps(ai_stat, move)
        self.update_diplo_events(ai_stat)
        self.diplomacy.calc_round()
        self.evaluate_hostile_players()
        self.__get_attack_target(ai_stat)
        self.evaluate_state(ai_stat)
        self.__get_protocol_and_bo(ai_stat)

        build_options: List[AI_Mazedonian.BuildOption] = self.evaluate_move_building(ai_stat)
        # TODO upgrade
        recruitment_options: List[
            Union[AI_Mazedonian.RecruitmentOption, AI_Mazedonian.RaiseArmyOption]] = self.evaluate_move_recruitment(
            ai_stat)
        scouting_options: List[AI_Mazedonian.ScoutingOption] = self.evaluate_move_scouting(ai_stat)
        # TODO army movement
        self.evaluate_army_movement(ai_stat, move)
        all_options: List[AI_Mazedonian.Option] = []
        all_options.extend(build_options)
        all_options.extend(recruitment_options)
        # all_options.extend(scouting_options)
        all_options.append(scouting_options[0])  # reducing complexity - just consider the best scouting option
        all_options.append(AI_Mazedonian.WaitOption(Priority.P_MEDIUM))  # do nothing is an option
        self.weight_options(all_options, ai_stat, move)

        self.set_counters(ai_stat)

    def evaluate_army_movement(self, ai_stat: AI_GameStatus, move: AI_Move):
        if self.state == AI_Mazedonian.AI_State.PASSIVE:
            # for now, just move it out of the way.
            army_is_on_field = False
            for b in ai_stat.own_buildings:
                if b.type == BuildingType.FARM:
                    if len(b.associated_tiles) > 0:
                        for a in b.associated_tiles:
                            if ai_stat.armies[0].offset_coordinates == a.offset_coordinates:
                                army_is_on_field = True
                                break
                if army_is_on_field:
                    break
            if not army_is_on_field:
                for i in range(2):              # try for each field :/ semi safe
                    field = None
                    for b in ai_stat.own_buildings:
                        if b.type == BuildingType.FARM:
                            if len(b.associated_tiles) > 0 and len(b.associated_tiles) > i: # found a farm with a field
                                field = b.associated_tiles[i]
                                break
                    if field:    # is not None
                        army_tile = AI_Toolkit.get_tile_by_xy(ai_stat.armies[0].offset_coordinates, ai_stat.tiles_walkable)
                        target_tile = AI_Toolkit.get_tile_by_xy(field.offset_coordinates, ai_stat.tiles_walkable)
                        path = []
                        AI_Toolkit.dijkstra(army_tile, target_tile, ai_stat.tiles_walkable, path)
                        if len(path) > 1:
                            move.move_army_to = path[1].offset_coordinates
                            move.doMoveArmy = True
                            break

        else:
            error("army movement lacks implementation")

    def set_vars(self, ai_stat: AI_GameStatus):
        if self.previous_food > ai_stat.player_food:
            hint("AI detected that it is loosing food")
            self.is_loosing_food = True

    def create_heat_maps(self, ai_stat: AI_GameStatus, move: AI_Move):
        cond = lambda n: AI_Toolkit.is_obj_in_list(n, ai_stat.tiles_walkable)
        heat_map = AI_Toolkit.simple_heat_map(ai_stat.own_buildings, ai_stat.tiles_walkable, cond)
        for d, s in heat_map:
            if d <= self.claiming_distance:
                self.claimed_tiles.add(s)
        # for d, s in heat_map:
        #    move.info_at_tile.append((s.offset_coordinates, str(d)))

    def update_diplo_events(self, ai_stat: AI_GameStatus):
        # for ai_stat.aggressions:

        for e_b in ai_stat.enemy_buildings:
            if AI_Toolkit.is_obj_in_list(e_b, self.claimed_tiles):
                debug("New Event: ENEMY_BUILDING_IN_CLAIMED_ZONE")
                self.diplomacy.add_event(e_b.owner, e_b.offset_coordinates,
                                         DiploEventType.ENEMY_BUILDING_IN_CLAIMED_ZONE, -2, 3, self.name)
        for e_a in ai_stat.enemy_armies:
            if AI_Toolkit.is_obj_in_list(e_a, self.claimed_tiles):
                debug("New Event: ENEMY_ARMY_INVADING_CLAIMED_ZONE")
                self.diplomacy.add_event(e_a.owner, e_a.offset_coordinates,
                                         DiploEventType.ENEMY_ARMY_INVADING_CLAIMED_ZONE, -2, 3, self.name)

    def evaluate_hostile_players(self):
        for other_p_id in self.other_players:
            if self.diplomacy.get_diplomatic_value_of_player(other_p_id) <= self.threshold_considered_hostile:
                if other_p_id not in self.hostile_player:
                    hint("Player id: {} got added to hostile players.".format(other_p_id))
                    self.hostile_player.add(other_p_id)
            if self.diplomacy.get_diplomatic_value_of_player(other_p_id) >= self.threshold_considered_neutral:
                if other_p_id in self.hostile_player:
                    hint("Player id: {} got removed from hostile players.".format(other_p_id))
                    self.hostile_player.remove(other_p_id)

    def estimate_opponent_strength(self, ai_stat: AI_GameStatus):
        """AI tries to estimate opponent's strength. Currently solely based on army population"""
        for other_p_id in self.other_players:
            for e_a in ai_stat.enemy_armies:
                if e_a.owner == other_p_id:
                    if abs(e_a.population - ai_stat.armies[0].population) < self.threshold_considered_equal:
                        self.__update_estimated_strength(other_p_id, AI_Mazedonian.EQUAL)
                    elif e_a.population > ai_stat.armies[0].population:
                        self.__update_estimated_strength(other_p_id, AI_Mazedonian.STRONGER)
                    elif e_a.population < ai_stat.armies[0].population:
                        self.__update_estimated_strength(other_p_id, AI_Mazedonian.WEAKER)

    def evaluate_state(self, ai_stat: AI_GameStatus):
        old_state = self.state
        if self.state == AI_Mazedonian.AI_State.PASSIVE:
            if len(self.hostile_player) > 0:
                def_count = 0
                agg_count = 0
                for h_p in self.hostile_player:
                    opp_s = self.__check_opp_strength(h_p)
                    if opp_s == AI_Mazedonian.EQUAL:
                        if self.equal_strength_defencive:
                            def_count = def_count + 1
                        else:
                            agg_count = agg_count + 1
                    elif opp_s == AI_Mazedonian.WEAKER:
                        agg_count = agg_count + 1
                    elif opp_s == AI_Mazedonian.STRONGER:
                        def_count = def_count + 1
                    elif opp_s == AI_Mazedonian.UNKNOWN:
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
            if len(ai_stat.own_buildings) < self.previous_amount_of_buildings:  # we got attacked
                if len(self.hostile_player) == 0:
                    hint("Problem with AI, we got attacked but no hostile players?!")
                else:
                    self.state = AI_Mazedonian.AI_State.AGGRESSIVE
            if len(self.hostile_player) == 0:
                self.state = AI_Mazedonian.AI_State.PASSIVE
        hint(f"State: {old_state} -> {self.state}")

    # def weight_options_rule_based(self, options: List[Option], ai_stat: AI_GameStatus, move: AI_Move):
    #     options.sort(key=lambda x: x.weighted_score, reverse=True)
    #     for opt in options:
    #

    def weight_options(self, options: List[Option], ai_stat: AI_GameStatus, move: AI_Move):
        for opt in options:
            opt.weighted_score = opt.score.value
            if opt.score == Priority.P_NO:          # no option (should not depend on weights) -> contain invalid info
                continue
            for w in self.weights:
                if w.condition(opt, ai_stat):
                    if DETAILED_DEBUG:
                        hint(f"Weight condition fullfiled w: {w.weight} applied on score: {opt.weighted_score} of {type(opt)} ")
                    opt.weighted_score = opt.weighted_score + w.weight
        options.sort(key=lambda x: x.weighted_score, reverse=True)
        hint("All options after they have been weighted: ")
        for opt in options:
            s = f"\tOption of type: {type(opt)}, score: {opt.weighted_score}"
            if type(opt) == AI_Mazedonian.RecruitmentOption or type(opt) == AI_Mazedonian.BuildOption:
                s = s + f", type {opt.type}"
            if type(opt) == AI_Mazedonian.ScoutingOption:
                s = s + f", site: {opt.site}"
            s = s + f", former priority: {opt.score}"
            hint(s)
        # translate this into move
        best_option: AI_Mazedonian.Option = options[0]
        if type(best_option) == AI_Mazedonian.WaitOption:
            move.doNothing = True
            move.str_rep_of_action = "waiting"
        elif type(best_option) == AI_Mazedonian.BuildOption:
            move.doBuild = True
            move.loc = best_option.site
            move.type = best_option.type
            for at in best_option.associated_tiles:
                move.info.append(at)
            move.str_rep_of_action = f"building a {best_option.type} at " + str(move.loc)
        elif type(best_option) == AI_Mazedonian.RecruitmentOption:
            move.doRecruitUnit = True
            move.type = best_option.type
            move.str_rep_of_action = f"recruiting a {best_option.type}"
        elif type(best_option) == AI_Mazedonian.ScoutingOption:
            move.doScout = True
            move.loc = best_option.site
            move.str_rep_of_action = "scouting at" + str(move.loc)
        else:
            error("unexpected type")
        hint(f"DECISION: {move.str_rep_of_action}")

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

        # current_bo = None
        # offset_to_bo = None
        # for bo in self.build_orders:
        #     c, p = self.__compare_to_bo(bo, ai_stat)
        #     for t, v in c:
        #         if v > 0:
        #             current_bo = bo
        #             offset_to_bo = c
        #     if current_bo:
        #         break

        if current_bo != None:
            hint("Currently active build order: {}".format(current_bo.name))
            # value_farm = -1
            prio_racks = Priority.P_NO
            value_hut = -1
            # site_farm = (-1, -1)
            farm_opt = AI_Mazedonian.BuildOption(BuildingType.FARM, (-1, -1), [], Priority.P_NO)
            site_racks = (-1, -1)
            site_hut = (-1, -1)
            for t, v in offset_to_bo:
                # hint(f"for type: {t}, v: {v}")
                if v > 0:  # only check this building type if it is part of the bo
                    if t == BuildingType.FARM:
                        farm_opt: AI_Mazedonian.BuildOption = self.__best_building_site_farm(ai_stat)
                        # value_farm = value_farm + v
                    elif t == BuildingType.HUT:
                        value_hut, site_hut = self.__best_building_site_hut(ai_stat)
                        # value_hut = value_hut + v
                    elif t == BuildingType.BARRACKS:
                        prio_racks, site_racks = self.__best_building_site_barracks(ai_stat)
                        # value_racks = value_racks + v
                    else:
                        hint("Build order contains unknown building type -> " + str(t))

            if ai_stat.player_food < self.food_lower_limit:
                if farm_opt is None:  # we force to look for a site even if the BO does not allow for it
                    farm_opt = value_farm, site_farm = self.__best_building_site_farm(ai_stat)

            if farm_opt:
                hint(f"amount of fields {len(farm_opt.associated_tiles)}")

            return [farm_opt,
                    AI_Mazedonian.BuildOption(BuildingType.HUT, site_hut, [], normalize(value_hut)),
                    AI_Mazedonian.BuildOption(BuildingType.BARRACKS, site_racks, [], prio_racks)]
        else:
            hint("No building order found. This is not supported so far. Need guidance")
            return []

    def __best_building_site_farm(self, ai_stat: AI_GameStatus) -> BuildOption:
        """building sites get scored by how many buildable fields there are next to it"""
        best_score = -1
        best_site = (-1, -1)
        fields = []
        p = Priority.P_NO
        is_next_to_res = False      # just for printing
        if ai_stat.player_resources >= ai_stat.costBuildFarm:
            for ai_t in ai_stat.tiles_buildable:
                tmp = False # just for printing
                possible_fields = AI_Toolkit.getListDistanceOne(ai_t, ai_stat.tiles_buildable)
                bad_candidates = set()
                for d in possible_fields:    # check if this field has a resource field next to it (which would be bad)
                    # this is also a very dramatic approach, should be replaced by values based
                    # (to enable placing a field next to a resource in an emergency) for now i'll do, though
                    adjacent = AI_Toolkit.getListDistanceOne(d, ai_stat.tiles_discovered)
                    for a in adjacent:
                        if AI_Toolkit.is_obj_in_list(a, ai_stat.resources):
                            bad_candidates.add(d)
                # can_field = [x.offset_coordinates for x in possible_fields if x not in bad_candidates] # very pythonic :)
                for bad_ca in bad_candidates:
                    possible_fields.remove(bad_ca)
                score = len(possible_fields)
                amount_of_fields = min(3, len(possible_fields))
                sampled = random.sample(possible_fields, amount_of_fields)
                # if build site is next to a resource --> reduce value by 1 for each resource field
                all_sourroundings = AI_Toolkit.getListDistanceOne(ai_t, ai_stat.tiles_discovered)
                for adjacent in all_sourroundings:
                    if AI_Toolkit.is_obj_in_list(adjacent, ai_stat.resources):
                        tmp = True
                        score = score - 1
                if best_score < score:
                    best_score = score
                    is_next_to_res = tmp
                    best_site = ai_t.offset_coordinates
                    fields.clear()
                    for s in sampled:
                        fields.append(s.offset_coordinates)

        if is_next_to_res:
            hint("The farm will be next to a resource (apparently there is no better spot)")

        # translate score to priority (normalization step)
        if len(fields) >= 3:
            p = Priority.P_HIGH
        elif len(fields) >= 2:
            p = Priority.P_MEDIUM
        elif len(fields) >= 1:
            p = Priority.P_LOW
        # hint(f"                            type eval: {type(p)}")
        return AI_Mazedonian.BuildOption(BuildingType.FARM, best_site, fields, p)

    def __best_building_site_hut(self, ai_stat: AI_GameStatus) -> Tuple[int, Tuple[int, int]]:
        """building sites get scored by their number of resource fields next to them"""
        best_score = -1
        best_site = (-1, -1)
        if ai_stat.player_resources >= ai_stat.costBuildS1:
            for ai_t in ai_stat.tiles_buildable:
                score = 0
                dist1 = AI_Toolkit.getListDistanceOne(ai_t, ai_stat.tiles_discovered)
                for t_at_dist_1 in dist1:
                    for res in ai_stat.resources:
                        if res.offset_coordinates == t_at_dist_1.offset_coordinates:
                            score = score + 1
                if best_score < score:
                    best_score = score
                    best_site = ai_t.offset_coordinates
        return best_score, best_site

    def __best_building_site_barracks(self, ai_stat: AI_GameStatus) -> Tuple[Priority, Tuple[int, int]]:
        """building sites should be a claimed tile and not next to a resource"""
        if ai_stat.player_resources >= ai_stat.costBuildRacks:
            candidates = []
            for c in self.claimed_tiles:
                if not AI_Toolkit.is_obj_in_list(c, ai_stat.tiles_buildable):   # if tile is not buildable, forget it
                    continue
                res_next_to_can = 0
                dist1 = AI_Toolkit.getListDistanceOne(c, ai_stat.tiles_discovered)
                for d in dist1:
                    if AI_Toolkit.is_obj_in_list(d, ai_stat.resources):
                        res_next_to_can = res_next_to_can + 1

                if res_next_to_can == 0:        # very hard constraint (go by value would be better)
                    candidates.append(c)

            # hint(f"possible candidates for a barracks: {len(candidates)}")
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
        if ai_stat.population >= ai_stat.population_limit:
            return options
        if len(ai_stat.armies) == 0:
            options.append(AI_Mazedonian.RaiseArmyOption(Priority.P_HIGH))
            return options  # cannot recruit if no army available
        # calculate offset to desired population by build order
        prio_merc = Priority.P_LOW
        prio_knight = Priority.P_LOW
        offset = self.build_order.population - ai_stat.population
        if offset > 0:
            prio_merc = Priority.increase(prio_merc)
            prio_knight = Priority.increase(prio_knight)
        else:
            prio_merc = Priority.decrease(prio_merc)
            prio_knight = Priority.decrease(prio_knight)
        # compare to desired army composition:
        army = ai_stat.armies[0]
        percentage_merc_wanted = self.army_comp.ac[0] / (self.army_comp.ac[0] + self.army_comp.ac[0])
        percentage_merc_actual = army.mercenaries / (army.mercenaries + army.knights)
        percentage_knig_wanted = self.army_comp.ac[1] / (self.army_comp.ac[0] + self.army_comp.ac[0])
        percentage_knig_actual = army.knights / (army.mercenaries + army.knights)
        hint(f"merc: {percentage_merc_wanted} - {percentage_merc_actual} | knight: {percentage_knig_wanted} - {percentage_knig_actual}")
        if (percentage_knig_wanted - percentage_knig_actual) < (percentage_merc_wanted - percentage_merc_actual):
            prio_merc = Priority.increase(prio_merc)
        else:
            prio_knight = Priority.increase(prio_knight)
        # mercenary
        if ai_stat.population + ai_stat.costUnitMe[2] <= ai_stat.population_limit:
            if ai_stat.player_resources >= ai_stat.costUnitMe[0]:
                if ai_stat.player_culture >= ai_stat.costUnitMe[1]:
                    options.append(AI_Mazedonian.RecruitmentOption(UnitType.MERCENARY, prio_merc))
                else:
                    hint("not enough culture to recruit a mercenary. actual: {} required: {}".format(
                        ai_stat.player_culture, ai_stat.costUnitMe[2]))
            else:
                hint("not enough resources to recruit a mercenary. actual: {} required: {}".format(
                    ai_stat.player_resources, ai_stat.costUnitMe[0]))
        else:
            hint("not enough free population to recruit a mercenary")
        # knight
        if ai_stat.population + ai_stat.costUnitKn[2] <= ai_stat.population_limit:
            if ai_stat.player_resources >= ai_stat.costUnitKn[0]:
                if ai_stat.player_culture >= ai_stat.costUnitKn[1]:
                    options.append(AI_Mazedonian.RecruitmentOption(UnitType.KNIGHT, prio_knight))
                else:
                    hint("not enough culture to recruit a knight. actual: {} required: {}".format(
                        ai_stat.player_culture, ai_stat.costUnitKn[2]))
            else:
                hint("not enough resources to recruit a knight. actual: {} required: {}".format(
                    ai_stat.player_resources, ai_stat.costUnitKn[0]))
        else:
            hint("not enough free population to recruit a knight")
        return options

    def evaluate_move_scouting(self, ai_stat: AI_GameStatus) -> List[ScoutingOption]:
        """scores the scouting options, currently by the distance to a own building
        (want to make sure that all claimable tiles are scouted) and by the proximity to a resource fieled"""
        options: List[AI_Mazedonian.ScoutingOption] = []
        if ai_stat.player_resources < ai_stat.costScout:
            return options

        for s in ai_stat.tiles_scoutable:
            options.append(AI_Mazedonian.ScoutingOption(s.offset_coordinates, Priority.P_NO))

        for so in options:
            value = 0
            tmp_tile = AI_Tile()
            tmp_tile.offset_coordinates = so.site
            dist1 = AI_Toolkit.getListDistanceOne(tmp_tile, ai_stat.tiles_discovered)
            # 1. increase value by resources nearby
            num_of_tiles_with_res = 0
            for t_at_dist_1 in dist1:
                if AI_Toolkit.is_obj_in_list(t_at_dist_1, ai_stat.resources):
                    num_of_tiles_with_res = num_of_tiles_with_res + 1
            value = value + (num_of_tiles_with_res * self.w_scouting_resource)
            # 2. increase value by proximity to claimed tiles
            num_of_claimed_tiles = 0
            for t_at_dist_1 in dist1:
                if AI_Toolkit.is_obj_in_list(t_at_dist_1, self.claimed_tiles):
                    num_of_claimed_tiles = num_of_claimed_tiles + 1
            value = value + (num_of_claimed_tiles * self.w_scouting_claimed)
            # 3. try to smooth out border
            # value = value + (len(dist1) * self.w_scouting_smooth_border)

            # Normalize
            high = max(4 * self.w_scouting_resource, 4 * self.w_scouting_claimed, 4 * self.w_scouting_smooth_border)
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
        self.previous_amount_of_buildings = len(ai_stat.own_buildings)
        self.previous_army_population = ai_stat.armies[0].population
        self.previous_food = ai_stat.player_food

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
            hint (f"p_offset {p_offset}")
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
        elif  done_build_orders == 2:
            self.protocol = AI_Mazedonian.Protocol.LATE_GAME
        if self.state == AI_Mazedonian.AI_State.PASSIVE:
            self.army_comp = self.ac_passive
        if self.state == AI_Mazedonian.AI_State.DEFENSIVE:
            self.army_comp = self.ac_defencive
        if self.state == AI_Mazedonian.AI_State.AGGRESSIVE:
            self.army_comp = self.ac_aggressive
        hint(f"Active protocol: {self.protocol}, active build order: {self.build_order.name}, active army comp: {self.army_comp.name}")

    def __compare_to_bo(self, bo: BuildOrder, ai_stat: AI_GameStatus):
        """this will return a list of tuples, comparing every b type the with desired value according to the bo
        (b_type, value) -> if value < 0 there are x more buildings than wanted - otherwise > 0
        if all values are <= 0, the bo is complete"""
        tmp = []
        for b_type, value in bo.bo:
            tmp.append([b_type, value])
        for b in ai_stat.own_buildings:
            for t in tmp:
                if t[0] == b.type:
                    t[1] = t[1] - 1
        return (tmp, bo.population - ai_stat.population)

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
        for b in ai_stat.own_buildings:
            if b.type == t:
                value = value + 1
        return value

    def __get_attack_target(self, ai_stat: AI_GameStatus):
        """get's the best attack target
        currently only buildings and armies of hostile players are considered to be attackable"""
        targets: Set[Tuple[Union[AI_Building, AI_Army], bool]] = set()
        # priority_list: List[Tuple[int, Union[AI_Building, AI_Army]]]= []
        if len(ai_stat.armies) == 0:  # in case we don't have an army
            return
        for e_a in ai_stat.enemy_armies:
            targets.add((e_a, True))
        for e_b in ai_stat.enemy_buildings:
            targets.add((e_b, False))

        hint(f"Found {len(targets)} target(s) for our army")
        for target, is_army in targets:
            value = 0
            if target.owner in self.hostile_player:
                if self.__check_opp_strength(target.owner) == AI_Mazedonian.STRONGER:
                    value = 1 if is_army else 0
                elif self.__check_opp_strength(target.owner) == AI_Mazedonian.WEAKER:
                    value = 5 if is_army else 4
                else:  # opp has unknown strength or equal
                    value = 3 if is_army else 2

                if AI_Toolkit.is_obj_in_list(target, self.claimed_tiles):
                    value = value + 3 if is_army else 2
                if self.previous_amount_of_buildings > len(ai_stat.own_buildings):  # a building got destroyed
                    value = value + 3 if is_army else 0

            hint(f"Target @ {str(target.offset_coordinates)} ({'army' if is_army else 'building'}) has value {value}")
            self.priolist_targets.append((value, target, is_army))  # TODO transform this to a dataclass
        if len(self.priolist_targets) > 0:
            self.priolist_targets.sort(key=lambda x: x[0], reverse=True)
            hint("Best attack target: {} ({}) value:{}".format(str(self.priolist_targets[0][1].offset_coordinates),
                                                               'army' if self.priolist_targets[0][2] else 'building',
                                                               self.priolist_targets[0][0]))
        else:
            hint("No Targets found")

    def __print_situation(self, ai_stat: AI_GameStatus):
        # count_farms = 0
        # for b in ai_stat.own_buildings:
        #     if b.type == BuildingType.FARM:
        #         count_farms = count_farms + 1
        # hint(f"AI INFO: {count_farms} farms")
        hint(f"Res: {ai_stat.player_resources}, Cul: {ai_stat.player_culture}, Food: {ai_stat.player_food}"
             f", Pop: {ai_stat.population} / {ai_stat.population_limit}")

    def __update_estimated_strength(self, opponent_id, value):
        """checks if there is a guess, if not, adds it"""
        # This is a bit ugly. But a set cannot contain list and tuples cannot be updated.
        # Maybe use a sequence?
        rm = None
        for id, v in self.opponent_strength:
            if id == opponent_id:
                rm = (id, v)
        self.opponent_strength.remove(rm)
        self.opponent_strength.add((opponent_id, value))

    def __check_opp_strength(self, opponent_id: int) -> int:
        for id, v in self.opponent_strength:
            if id == opponent_id:
                return v
        return AI_Mazedonian.UNKNOWN

    def __setup_weights(self) -> List:
        w: List[Tuple[Callable, int]] = []

        def w1(elem: AI_Mazedonian.Option, ai_stat: AI_GameStatus) -> bool:
            """Idea: If AI looses food -> Make building a farm more important!"""
            if type(elem) is AI_Mazedonian.BuildOption:
                if elem.type == BuildingType.FARM:
                    return self.is_loosing_food
            return False
        w.append((w1, 3))

        def w2(elem: AI_Mazedonian.Option, ai_stat: AI_GameStatus) -> bool:
            """Idea: If AI is in aggressive state -> build offensive units"""
            if type(elem) is AI_Mazedonian.RecruitmentOption:
                if self.state == AI_Mazedonian.AI_State.AGGRESSIVE:
                    if elem.type == UnitType.MERCENARY:
                        return True
            return False
        w.append((w2, 3))

        def w3(elem: AI_Mazedonian.Option, ai_stat: AI_GameStatus) -> bool:
            """Idea: If AI has no army -> Recruiting an army is important"""
            if type(elem) is AI_Mazedonian.RaiseArmyOption:
                if len(ai_stat.armies) == 0:
                    return True
            return False
        w.append((w3, 3))

        def w4(elem: AI_Mazedonian.Option, ai_stat: AI_GameStatus) -> bool:
            """Idea, once we have enough resources (and is in passive/def state),
             make scouting slightly more important"""
            if type(elem) is AI_Mazedonian.ScoutingOption:
                if ai_stat.player_resources > 10:
                    if self.state == AI_Mazedonian.AI_State.PASSIVE or self.state == AI_Mazedonian.AI_State.DEFENSIVE:
                        return True
            return False
        w.append((w4, 1))

        def w5(elem: AI_Mazedonian.Option, ai_stat: AI_GameStatus) -> bool:
            """Idea: reduce significance of scouting in a low eco game"""
            if type(elem) is AI_Mazedonian.ScoutingOption:
                if ai_stat.player_resources < 10:
                    return True
            return False
        w.append((w5, -1))

        def w6(elem: AI_Mazedonian.Option, ai_stat: AI_GameStatus) -> bool:
            """Idea: If AI has more than 70 food, cut down on additional farms"""
            if type(elem) is AI_Mazedonian.BuildOption:
                if elem.type == BuildingType.FARM:
                    if ai_stat.player_food > 70:
                        return True
            return False
        w.append((w6, -3))

        def w7(elem: AI_Mazedonian.Option, ai_stat: AI_GameStatus) -> bool:
            """Idea: slightly decrease scouting and waiting if a lot of resources are available"""
            if type(elem) is AI_Mazedonian.ScoutingOption or type(elem) is AI_Mazedonian.WaitOption:
                if ai_stat.player_resources > 70:
                    return True
            return False
        w.append((w7, -1))

        def w8(elem: AI_Mazedonian.Option, ai_stat: AI_GameStatus) -> bool:
            """Idea: slightly decrease scouting in early game"""
            if type(elem) is AI_Mazedonian.ScoutingOption:
                if self.protocol == AI_Mazedonian.Protocol.EARLY_GAME:
                    return True
            return False
        w.append((w8, -1))

        def w9(elem: AI_Mazedonian.Option, ai_stat: AI_GameStatus) -> bool:
            """Idea: slightly increase building in early game"""
            if type(elem) is AI_Mazedonian.BuildOption:
                if self.protocol == AI_Mazedonian.Protocol.EARLY_GAME:
                    return True
            return False
        w.append((w9, 1))

        def w10(elem: AI_Mazedonian.Option, ai_stat: AI_GameStatus) -> bool:
            """Idea: if AI lacks population by twice the desired value -> double down"""
            if type(elem) is AI_Mazedonian.RecruitmentOption:
                if self.build_order.population / 2 > ai_stat.population:
                    return True
            return False
        w.append((w10, 0.9))

        def w11(elem: AI_Mazedonian.Option, ai_stat: AI_GameStatus) -> bool:
            """Idea: if AI doesn't have a farm -> highest prio (if it cannot build one -> wait)"""
            if type(elem) is AI_Mazedonian.BuildOption:
                if elem.type == BuildingType.FARM:
                    for b in ai_stat.own_buildings:
                        if b.type == BuildingType.FARM:
                            return False
                    return True # returns true if AI does not have a farm and building one is an option
            return False
        w.append((w11, 10))

        def w12(elem: AI_Mazedonian.Option, ai_stat: AI_GameStatus) -> bool:
            """Idea: extension to w11 (if it cannot build one -> wait)"""
            if type(elem) is AI_Mazedonian.WaitOption:
                for b in ai_stat.own_buildings:
                    if b.type == BuildingType.FARM:
                        return False
                return True # returns true if AI does not have a farm
            return False
        w.append((w12, 5))

        hint(f"AI has found {len(w)} weight functions.")
        return w
