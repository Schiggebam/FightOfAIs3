import importlib
import random
from enum import Enum
from typing import Set, Optional, Union, List, Any, Dict

from src.ai.AI_GameStatus import AI_Move, AI_GameStatus
from src.ai.AI_MapRepresentation import AI_Building, AI_Army, Tile
from src.ai.ai_blueprint import AI
from src.ai.toolkit import essentials
from src.ai.toolkit.basic import Weight, BuildOption, RecruitmentOption, RaiseArmyOption, ArmyMovementOption, \
    WaitOption, UpgradeOption
from src.misc.game_constants import error, MoveType, Priority


class AI_NPC(AI):
    """
    Base class for NPCs
    """
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


    def __init__(self, name: str,  other_players: List[int], script):
        super().__init__(name, other_players)
        self.personality = "militant"
        # self.personality = "temperate"
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
        self._reset_dump()
        self._dump(f"Turn: {ai_stat.turn_nr}")
        self.update_diplo_events(ai_stat)
        self.update_hostile_players()
        self.diplomacy.calc_round()
        self.evaluate_state(ai_stat)
        self.calculate_heatmaps(ai_stat)
        self._dump("Barbaric AI: hostile players: " + str(self.hostile_player))

        # self.calculate_heatmaps()
        all_options = [self.evaluate_move_building(ai_stat),
                       self.evaluate_move_upgrade(ai_stat),
                       self.evaluate_move_recruit_unit(ai_stat),
                       WaitOption(Priority.P_MEDIUM)]
        all_options = list(filter(None, all_options))
        movement_options = []
        movement_options.extend(self.calculate_army_movement(ai_stat))

        self.weight_options(ai_stat, move, all_options, movement_options)


        # keep values
        if len(ai_stat.map.army_list) > 0:
            self.previous_army_strength = ai_stat.map.army_list[0].population
        else:
            self.previous_army_strength = 0
        self.previous_amount_of_buildings = len(ai_stat.map.building_list)
        self.hostile_player.clear()
        self.claimed_tiles.clear()

    def calculate_army_movement(self, ai_stat: AI_GameStatus) -> List[ArmyMovementOption]:
        pass

    def update_diplo_events(self, ai_stat: AI_GameStatus):
        pass

    def evaluate_state(self, ai_stat: AI_GameStatus):
        pass

    def weight_options(self, ai_stat: AI_GameStatus, move: AI_Move,
                       all_options: List[Union[BuildOption, RecruitmentOption, RaiseArmyOption, WaitOption]],
                       movement_options: List[ArmyMovementOption]):
        used_weights: List[str] = []
        for opt in all_options:             # --------------------- Action options ----------
            if opt.score == Priority.P_NO:
                continue
            opt.weighted_score = opt.score.value
            for w in self.weights:
                if w.condition(opt, ai_stat):
                    used_weights.append(w.condition.__name__)
                    opt.weighted_score = opt.weighted_score + w.weight

        used_weights.append(" | ")

        for opt in movement_options:        # --------------------- Movement options ----------
            if opt.score == Priority.P_NO:
                continue
            opt.weighted_score = opt.score.value
            for w in self.m_weights:
                if w.condition(opt, ai_stat):
                    used_weights.append(w.condition.__name__)
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
                move.str_rep_of_action = f"upgrading building to {move.type}"
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


        for opt in all_options:
            s = f"Option of type {type(opt)}, score: {opt.weighted_score} ({opt.score})"
            if not (type(opt) == WaitOption or type(opt) == RaiseArmyOption):
                s = s + f" -> Type: {opt.type}"
            self._dump(s)
        for m_opt in movement_options:
            stmp = 'army' if type(m_opt.target) is AI_Army else ''
            stmp = 'building' if type(m_opt.target) is AI_Building else ''
            s = f"M-Option target: {type(m_opt)} target({stmp}), score: {m_opt.weighted_score} ({m_opt.score})"
            self._dump(s)

        s = f"DECISION: {move.str_rep_of_action}"
        if move.doMoveArmy:
            s += f" moving army to {move.move_army_to}"
        self._dump(s)

    def calculate_heatmaps(self, ai_stat: AI_GameStatus):
        heat_map = essentials.simple_heat_map(ai_stat.map.building_list, ai_stat.map.walkable_tiles,
                                              lambda n: essentials.is_obj_in_list(n, ai_stat.map.walkable_tiles))
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
                nei = essentials.get_neighbours_on_set(b, ai_stat.map.walkable_tiles)  # buildable -> to avoid opp armies
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

    def update_hostile_players(self):
        for other_p_id in self.other_players:
            if self.diplomacy.get_diplomatic_value_of_player(other_p_id) < self.properties['diplo_aggressive_threshold']:
                if other_p_id not in self.hostile_player:
                    self.hostile_player.add(other_p_id)
            if self.diplomacy.get_diplomatic_value_of_player(other_p_id) > self.properties['diplo_aggressive_threshold']:
                if other_p_id in self.hostile_player:
                    self.hostile_player.remove(other_p_id)
        self._dump(f"hostile players: {str(self.hostile_player)}")


    def has_been_attacked(self, ai_stat: AI_GameStatus):
        for opp in ai_stat.opponents:
            if opp.has_attacked:
                self.hostile_player.add(opp.id)
                self._dump("aggression found!")
                return True
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
