import timeit
# from threading import Thread

from src.ai.AI_GameStatus import AI_GameStatus, AI_Move, AI_GameInterface

from src.misc.animation import Animator
from src.misc.game_constants import *
from src.game_accessoires import Scenario, Ground, Resource, Drawable, Flag, Unit
from src.game_file_reader import GameFileReader
from src.hex_map import HexMap, MapStyle, Hexagon
from src.texture_store import TextureStore
from src.misc.game_logic_misc import *
from typing import Optional, List, Set, Dict

from src.ui.extern.extern_ai_display import AIControl


class GameLogic:
    def __init__(self, game_xml_file: str, z_levels: [arcade.SpriteList]):
        self.texture_store: TextureStore = TextureStore.instance()
        self.game_file_reader: GameFileReader = GameFileReader(game_xml_file)
        self.z_levels: [arcade.SpriteList] = z_levels               # reference to the sprite lists
        self.hex_map: Optional[HexMap] = None
        from src.ui.human import HumanInteraction
        self.human_interface: Optional[HumanInteraction] = None
        self.ai_interface: AI_GameInterface = AI_GameInterface()
        self.scenario: Scenario = Scenario()
        self.income_calc: IncomeCalculator = IncomeCalculator(self.hex_map, self.scenario)
        self.animator: Animator = Animator()

        tex_dict = {}
        self.game_file_reader.read_textures_to_dict(tex_dict)
        self.texture_store.load_textures(tex_dict)

        self.__camera_pos: (int, int) = (0, 0)

        self.player_list: [Player] = []
        self.map_view: [bool] = []              # true if we show the players view, otherwise false
        self.change_in_map_view = MAP_HACK_ENABLE_AT_STARTUP
        self.map_hack = MAP_HACK_ENABLE_AT_STARTUP
        self.winner: Optional[Player] = None

        # read game data
        self.game_file_reader.read_resource_info(Resource.resource_info)
        self.game_file_reader.read_building_info(Building.building_info)
        self.game_file_reader.read_unit_info(Unit.unit_info)

        # read player data
        player_info: [(str, {})] = []                           # a tuple per player, first element is player's name
        self.game_file_reader.read_player_info(player_info)
        pid = 0
        for p_info in player_info:          # -> Tuple pid and info
            p = Player(p_info[0], pid, p_info[1]['colour'],
                       (int(p_info[1]['spawn_x']), int(p_info[1]['spawn_y'])),
                       p_info[1]['ai'])
            p.is_barbaric = p_info[1]['ai'] == "barbaric"
            p.is_villager = p_info[1]['ai'] == "villager"
            p.player_type = PlayerType.get_type_from_strcode(p_info[1]['ai'])

            p.init_army_loc = (p.spaw_loc[0] + p_info[1]['army_rel_to_spawn_x'],
                               p.spaw_loc[1] + p_info[1]['army_rel_to_spawn_y'])
            self.player_list.append(p)
            self.map_view.append(False)
            pid = pid + 1

        # load textures which depend on player
        for p in self.player_list:
            c = p.colour_code
            self.texture_store.load_animated_texture("{}_flag".format(c), 10, lambda i: (0, 100 * i), 108, 100,
                                                     "../resources/objects/animated/flag_100_sprite_{}.png".format(c))

        # self.ai_running = False
        # game status
        self.playNextTurn: bool = False
        self.current_player: int = 0
        self.turn_nr: int = 0
        self.automatic: bool = False

        # self.test = None
        self.total_time: float = 0
        # self.animator_time = 0
        # self.wait_for_human = False
        self.has_human_player: bool = False

        self.ai_ctrl_frame: Optional[AIControl] = None
        self.show_key_frame_animation: bool = ENABLE_KEYFRAME_ANIMATIONS
        self.logic_state: GameLogicState = GameLogicState.NOT_READY
        self.nextPlayerButtonPressed: bool = False
        self.elapsed: float = float(0)

    def setup(self):
        """ load the game """
        map_data: [[str]] = []
        self.game_file_reader.read_map(map_data)
        map_obj_data: [(str, int, int)] = []
        self.game_file_reader.read_map_obj(map_obj_data)

        # setup hex map
        self.hex_map = HexMap((len(map_data[0]), len(map_data)), MapStyle.S_V_C)
        self.income_calc.hex_map = self.hex_map         # TODO make sure to set the hex_map everywhere. Ugly!

        #TODO do this somewhere else

        # background: List[Drawable] = []
        # x_off = 213
        # y_off = 165
        # for x in range(6):
        #     for y in range(5):
        #         d = Drawable()
        #         d.set_sprite_pos((x_off * x + 100, y_off * y), self.__camera_pos)
        #         self.__set_sprite(d, "ocean")
        #         self.z_levels[0].append(d.sprite)

        #map
        for y in range(len(map_data)-1, -1, -1):
            for x in range(len(map_data[y])):
                hex: Hexagon = self.hex_map.get_hex_by_offset((x, y))
                ground: Ground = Ground(map_data[y][x])
                hex.ground = ground
                ground.set_sprite_pos(HexMap.offset_to_pixel_coords((x, y)), self.__camera_pos)
                ground.add_texture(self.texture_store.get_texture("fw"))
                ground.tex_code = map_data[y][x]
                self.z_levels[Z_MAP].append(ground.sprite)

        from src.misc.smooth_map import SmoothMap
        SmoothMap.smooth_map(self.hex_map)
        #SmoothMap.adjust_elevation(self.hex_map)

        # assign textures
        for hexagon in self.hex_map.map:
            self.__set_sprite(hexagon.ground, hexagon.ground.tex_code)

        for map_obj in map_obj_data:
            hex: Hexagon = self.hex_map.get_hex_by_offset((map_obj[1], map_obj[2]))
            if map_obj[0] == "f2":
                # get str_code with variance
                import random
                var = random.randint(0, 6)
                r: Resource = Resource(hex, ResourceType.FOREST)
                r.tex_code = "forest_3_var{}".format(var)
                self.add_resource(r)

            elif map_obj[0] == "r1" or map_obj[0] == "g1" or map_obj[0] == "f1":                    # TODO if resource
                r: Resource = Resource(hex, ResourceType.get_type_from_strcode(map_obj[0]))
                r.tex_code = map_obj[0]
                self.add_resource(r)
        player_ids: List[Tuple[int, str]] = []
        for player in self.player_list:
            other_players_ids: List[int] = []
            for p in self.player_list:
                if p != player:
                    other_players_ids.append(p.id)
            self.ai_interface.launch_AI(player.id, player.ai_str, "AI_" + player.name, other_players_ids)
            base_hex: Hexagon = self.hex_map.get_hex_by_offset(player.spaw_loc)
            player.discovered_tiles.add(base_hex)
            player.food = 35
            player.amount_of_resources = 10
            b_type = player.get_initial_building_type()
            b: Building = Building(base_hex, b_type, player.id)
            self.add_building(b, player)
            b.construction_time = 0
            b.set_state_active()
            tmp = self.hex_map.get_neighbours_dist(base_hex, b.sight_range)
            player.discovered_tiles.update(tmp)
            if player.player_type is PlayerType.HUMAN:
                self.has_human_player = True
            if not player.is_barbaric:
                unit = Unit(player.get_initial_unit_type())
                army = Army(self.hex_map.get_hex_by_offset(player.init_army_loc), player.id)
                army.add_unit(unit)
                self.add_army(army, player)
            player_ids.append((player.id, player.colour_code))

        self.__reorder_spritelist(self.z_levels[Z_GAME_OBJ])
        self.toggle_fog_of_war_lw(self.hex_map.map)

        from src.ai.performance import PerformanceLogger
        PerformanceLogger.setup(player_ids)
        self.logic_state = GameLogicState.READY_FOR_TURN

        if self.player_list[0].player_type is PlayerType.HUMAN:
            # in case the first player is the human, we already gather his/her resources
            self.playNextTurn = True
            self.nextPlayerButtonPressed = True

    def set_ai_ctrl_frame(self, ai_ctrl_frame: Optional[AIControl]):
        self.ai_ctrl_frame = ai_ctrl_frame

    def update(self, delta_time: float, commands :[], wall_clock_time: float):
        timestamp_start = timeit.default_timer()
        self.__exec_command(commands)
        self.elapsed = self.elapsed + delta_time
        if self.show_key_frame_animation:
            for k_f in self.animator.key_frame_animations:
                k_f.next_frame(delta_time)
        # self.animator_time = timestamp_start - timeit.default_timer()
        if self.elapsed > float(GAME_LOGIC_CLK_SPEED if self.turn_nr < 80 else 1) and self.automatic:
            self.playNextTurn = True
            self.elapsed = float(0)

        if self.playNextTurn:
            t1 = timeit.default_timer()
            self.handle_turn()
            t2 = timeit.default_timer()
            debug(f"update loop took: {(t2 - t1) * 1000:.0} ms")
        if self.show_key_frame_animation:
            for s in self.z_levels[Z_FLYING]:
                s.update_animation()

        if self.change_in_map_view:
            t1 = timeit.default_timer()
            self.toggle_fog_of_war_lw(self.hex_map.map, show_update_bar=True)
            self.change_in_map_view = False
            t2 = timeit.default_timer()
            debug(f"change map view routine took: {(t2 - t1) :.6} s")

        self.animator.update(wall_clock_time)
        self.total_time = timestamp_start - timeit.default_timer()
        # debug("update loop took: {} s []".format(self.total_time))

    def handle_turn(self):
        """handles the turn for a player (human, ai or npc), extends the main update loop"""
        if self.logic_state is GameLogicState.NOT_READY:
            error(f"game logic not ready, logic state: {self.logic_state}")
            self.playNextTurn = False
            return

        if len(self.player_list) <= 0:
            self.playNextTurn = False
            return

        player = self.player_list[self.current_player]

        if player.player_type is PlayerType.HUMAN:

            if self.logic_state is GameLogicState.READY_FOR_TURN:
                self.play_players_turn(player)
                self.logic_state = GameLogicState.WAITING_FOR_AGENT
                self.nextPlayerButtonPressed = False

            elif self.logic_state is GameLogicState.WAITING_FOR_AGENT:
                h_move = self.human_interface.get_partial_move()
                if h_move is not None:
                    self.exec_ai_move(h_move, player)
                    new_ai_stat = AI_GameStatus()
                    self.construct_game_status(player, new_ai_stat)
                    self.human_interface.update_game_status(new_ai_stat)

                if self.human_interface.is_move_complete() or self.nextPlayerButtonPressed:
                    self.logic_state = GameLogicState.TURN_COMPLETE
        else:   # handle AI agent

            if self.logic_state is GameLogicState.READY_FOR_TURN:
                self.play_players_turn(player)
                self.logic_state = GameLogicState.WAITING_FOR_AGENT

            elif self.logic_state is GameLogicState.WAITING_FOR_AGENT:
                if self.ai_interface.has_finished():
                    ai_move = self.ai_interface.ref_to_move
                    debug("AI took {} ms".format(self.ai_interface.get_ai_execution_time()))
                    if ai_move:  # player might have lost
                        self.exec_ai_move(ai_move, player)
                    if Definitions.SHOW_AI_CTRL:
                        self.ai_ctrl_frame.update(self.ai_interface.get_dump(player.id), player.id)
                    self.logic_state = GameLogicState.TURN_COMPLETE

        if self.logic_state is GameLogicState.TURN_COMPLETE:
            self.nextPlayerButtonPressed = False
            if self.current_player == 0:  # next time player 0 plays -> new turn
                self.turn_nr = self.turn_nr + 1
            self.current_player = (self.current_player + 1) % len(self.player_list)
            if self.player_list[self.current_player].player_type is PlayerType.HUMAN:
                self.playNextTurn = True
            else:
                self.playNextTurn = False
            hint("                              SUCCESSFULLY PLAYED TURN")
            self.logic_state = GameLogicState.READY_FOR_TURN


    def play_players_turn(self, player: Player):
        """wrapper function, extends the main update loop"""
        debug(f"Play move of player {player.name} [pid: {player.id}]")
        self.updata_map()
        if self.check_win_condition(player):
            self.winner = player
        self.update_player_properties(player)
        player.has_lost = self.check_lose_condition(player)
        if player.has_lost:
            self.destroy_player(player)
            return
        ai_game_status = AI_GameStatus()
        self.construct_game_status(player, ai_game_status)

        ai_move = AI_Move()
        if player.player_type == PlayerType.HUMAN:
            self.human_interface.request_move(ai_game_status, ai_move, player.id)
        else:
            self.ai_interface.do_a_move(ai_game_status, ai_move, player.id)

    def update_player_properties(self, player):
        """calculate income, new culture level, food, etc."""
        # continue build buildings
        for b in player.buildings:
            if b.building_state == BuildingState.UNDER_CONSTRUCTION:
                if b.construction_time == 0:
                    b.set_state_active()
                else:
                    b.construction_time = b.construction_time - 1
            if b.building_state == BuildingState.DESTROYED:
                self.del_building(b, player)

        player.income = self.income_calc.calculate_income(player)
        player.amount_of_resources = player.amount_of_resources + player.income
        player.food = player.food + self.income_calc.calculate_food(player)
        player.culture = player.culture + self.income_calc.calculate_culture(player)

    def construct_game_status(self, player: Player, ai_game_status: AI_GameStatus):
        """constructs an object, which holds the current view of the game out of a players perspective"""
        scoutable_tiles = self.get_scoutable_tiles(player)
        buildable_tiles = self.get_buildable_tiles(player)
        known_resources = self.get_known_resources(player)
        walkable_tiles = self.get_walkable_tiles(player)
        enemy_buildings = self.get_enemy_buildings(player, scoutable_tiles)  # tuple set((bld, owner_id))
        enemy_armies = self.get_enemy_armies(player)        # tuple set((army, owner_id))

        # build the map representation for the AI
        # all tiles is the union of scoutable and known tiles
        from src.ai.AI_MapRepresentation import Map
        ai_map: Map = Map()
        for s in scoutable_tiles:
            ai_map.add_tile(s.offset_coordinates, s.ground.ground_type)
        for s in player.discovered_tiles:
            ai_map.add_tile(s.offset_coordinates, s.ground.ground_type)
        ai_map.connect_graph()

        # TODO speed up (iterate only once over the map) by doing the scoutables, one can get all others "for free"
        for h in scoutable_tiles:
            ai_map.set_scoutable_tile(h.offset_coordinates)
        for h in walkable_tiles:
            ai_map.set_walkable_tile(h.offset_coordinates)
        for h in buildable_tiles:
            ai_map.set_buildable_tile(h.offset_coordinates)
        for h in player.discovered_tiles:
            ai_map.set_discovered_tile(h.offset_coordinates)

        for r in known_resources:
            ai_map.add_resource(r.tile.offset_coordinates, r)
        for b in player.buildings:
            ai_map.add_own_building(b.tile.offset_coordinates, b)
        for b, id in enemy_buildings:
            ai_map.add_opp_building(b.tile.offset_coordinates, b, id)
        for a in player.armies:
            ai_map.add_own_army(a.tile.offset_coordinates, a)
        for a, id in enemy_armies:
            ai_map.add_opp_army(a.tile.offset_coordinates, a, id)
        # ai_map.print_map()
        from src.ai.AI_MapRepresentation import AI_Player, AI_Opponent
        me = AI_Player(player.id, player.name, player.player_type, player.amount_of_resources,
                       player.culture, player.food, player.get_population(), player.get_population_limit())
        opponents = []
        for p in self.player_list:
            if p.id != player.id:
                tmp = AI_Opponent(p.id, p.name, p.player_type)
                tmp.has_lost = p.has_lost
                opponents.append(tmp)
                for pid, loc in player.attacked_set:
                    if pid == p.id:
                        tmp.has_attacked = True
                        # tmp.attack_loc.append((pid, loc))

        scout_cost = 1
        b_costs: Dict[BuildingType, int] = {}
        for t_b in BuildingType:
            if t_b != BuildingType.OTHER_BUILDING:
                b_costs[t_b] = Building.get_construction_cost(t_b)
        u_costs: Dict[UnitType, UnitCost] = {}
        for t_u in UnitType:
            u_costs[t_u] = Unit.get_unit_cost(t_u)

        AI_GameInterface.create_ai_status(ai_game_status, self.turn_nr, scout_cost,
                                          ai_map, me, opponents, b_costs, u_costs)
        player.attacked_set.clear()




    def destroy_player(self, player):
        """cleans up the board, if a player has lost"""
        for army in player.armies:
            self.del_army(army, player)
        for b in player.buildings:
            self.del_building(b, player)
        # still log its performance
        # (also to keep the arrays in the logger of equal length which helps for drawing the diagram)
        from src.ai.performance import PerformanceLogger
        PerformanceLogger.log_performance_file(self.turn_nr, player.id, 0)

    def updata_map(self):
        """this function makes sure that the map remains well defined"""
        for hex in self.hex_map.map:
            if hex.ground.ground_type == GroundType.OTHER:
                error("Unknown ground type is a problem! {}".format(hex.offset_coordinates))
            if hex.ground.ground_type == GroundType.GRASS or\
                    hex.ground.ground_type == GroundType.STONE or\
                    hex.ground.ground_type == GroundType.MIXED:
                hex.ground.walkable = True
                hex.ground.buildable = True
            elif hex.ground.ground_type == GroundType.WATER_DEEP:
                hex.ground.walkable = False
                hex.ground.buildable = False
            else:
                hint("GameLogic cannot update map! Unknown ground type")

        for player in self.player_list:
            for building in player.buildings:
                for ass in building.associated_tiles:
                    ass.ground.buildable = False
                building.tile.ground.buildable = False
                if building.building_state == BuildingState.UNDER_CONSTRUCTION or \
                        building.building_state == BuildingState.ACTIVE:
                    building.tile.ground.walkable = False
            # self.update_fog_of_war(player)

        for res in self.scenario.resource_list:
            if res.remaining_amount <= 0:
                self.del_resource(res)
                continue
            res.tile.ground.walkable = False
            res.tile.ground.buildable = False

        for p in self.player_list:
            for a in p.armies:
                pix_loc = HexMap.offset_to_pixel_coords(a.tile.offset_coordinates)
                a.set_sprite_pos(pix_loc, self.__camera_pos)

        # This is a bit of brute force approach and not really necessary. However, animations made it hard
        # to track when updates are necessary, however the method is still very fast
        self.__reorder_spritelist(self.z_levels[Z_GAME_OBJ])

    def exec_ai_move(self, ai_move: AI_Move, player: Player):
        t1 = timeit.default_timer()
        self.__check_validity(ai_move)
        for d in self.hex_map.map:
            d.debug_msg = ""
        for d in ai_move.info_at_tile:
            hex = self.hex_map.get_hex_by_offset(d[0])
            hex.debug_msg = d[1]

        print_move = False
        if print_move:
            s = str(ai_move.move_type)
            s = s + f"Loc: {ai_move.loc}, army_move: {ai_move.move_army_to}, move: {ai_move.doMoveArmy}"
            s = s + ai_move.str_rep_of_action
            debug(s)

        if ai_move.move_type == MoveType.DO_RAISE_ARMY:
            if len(player.armies) == 0:
                hint(f"spawning army at {ai_move.loc}")
                base_hex = self.hex_map.get_hex_by_offset(ai_move.loc)
                army = Army(base_hex, player.id)
                self.add_army(army, player)
            else:
                error("Not more than one armies allowed")

        if ai_move.move_type == MoveType.DO_RECRUIT_UNIT:
            if len(player.armies) == 1:             #FIXME has support for only 1 army here
                t_u = ai_move.type
                cost = Unit.get_unit_cost(t_u)
                if player.amount_of_resources < cost.resources:
                    error("Not enough resources to recruit unit: " + str(t_u))
                elif player.culture < cost.culture:
                    error("Not enough culture to recruit unit: " + str(t_u))
                elif player.get_population_limit() < player.get_population() + cost.population:
                    error("Not enough free population to recruit " + str(t_u))
                else:
                    player.amount_of_resources = player.amount_of_resources - cost.resources
                    player.culture = player.culture - cost.culture
                    u: Unit = Unit(t_u)
                    player.armies[0].add_unit(u)
            else:
                error("No army. Recruit new army first!")

        if ai_move.move_type == MoveType.DO_BUILD:
            if not self.hex_map.get_hex_by_offset(ai_move.loc).ground.buildable:
                error("Exec AI Move: Location is not buildable!")
                return
            b_type = 0
            if player.is_barbaric:
                b_type = BuildingType.CAMP_1        # not very good to hard-code this here
            else:
                b_type = ai_move.type
            if Building.get_construction_cost(b_type) <= player.amount_of_resources:
                # hint("building: @" + str(ai_move.loc))
                base_hex = self.hex_map.get_hex_by_offset(ai_move.loc)
                b = Building(base_hex, b_type, player.id)
                if not player.is_barbaric:
                    if ai_move.type == BuildingType.FARM:
                        for loc in ai_move.info:
                            # hint(f"adding Associated Tile at location: {loc}")
                            b.associated_tiles.append(self.hex_map.get_hex_by_offset(loc))
                        # b.associated_tiles.append(self.hex_map.get_hex_by_offset(ai_move.info[1]))
                        # b.associated_tiles.append(self.hex_map.get_hex_by_offset(ai_move.info[2]))
                if not player.is_barbaric:
                    tmp = self.hex_map.get_neighbours_dist(base_hex, b.sight_range)
                    player.discovered_tiles.update(tmp)
                self.add_building(b, player)
                player.amount_of_resources = player.amount_of_resources - Building.get_construction_cost(b_type)
                # The sight range is only extended with the player is not barbaric

            else:
                error("Exec AI Move: Cannot build building! BuildingType:" + str(b_type))
        if ai_move.move_type == MoveType.DO_SCOUT:
            #FIXME cost of scouting is hardcoded
            if player.amount_of_resources >= 1:
                player.discovered_tiles.add(self.hex_map.get_hex_by_offset(ai_move.loc))
                player.amount_of_resources = player.amount_of_resources - 1
                self.toggle_fog_of_war_lw(player.discovered_tiles)

        elif ai_move.move_type == MoveType.DO_UPGRADE_BUILDING:
            b_old: Optional[Building] = None
            for upgradable in player.buildings:
                if upgradable.tile.offset_coordinates == ai_move.loc:
                    b_old = upgradable
            if not b_old:
                print("Exec AI Move: No building found at location to upgrade!")
                return
            b_type = ai_move.type
            if player.amount_of_resources >= Building.get_construction_cost(b_type):
                player.amount_of_resources = player.amount_of_resources - Building.get_construction_cost(b_type)
                self.del_building(b_old, player)
                base_hex = self.hex_map.get_hex_by_offset(ai_move.loc)
                b_new = Building(base_hex, b_type, player.id)
                # print(b_new.tex_code)
                self.add_building(b_new, player)
            else:
                error(f"Exec AI Move: Not enough resources to upgrade type{b_old.building_type} to {b_type}")

        if ai_move.doMoveArmy:
            if len(player.armies) == 1:             #FIXME has support for only 1 army here
                if self.hex_map.get_hex_by_offset(ai_move.move_army_to) is not None:
                    #if self.hex_map.get_hex_by_offset(ai_move.move_army_to).ground.walkable:
                    ok = True
                    for b in player.buildings:
                        if b.tile.offset_coordinates == ai_move.move_army_to:
                            ok = False
                    if ok:
                        self.move_army(player.armies[0], player, ai_move.move_army_to)
                    else:
                        error("Cannot move army, it appears a building has been built on this tile")
                else:
                    error(f"Invalid target for army movement: {ai_move.move_army_to}")
            else:
                error("No army available")
        t_tot = timeit.default_timer() - t1
        debug("exec_ai_move took {} s".format(t_tot))


    def __check_validity(self, ai_move: AI_Move):
        """prints warning message if AI_Move object is faulty"""
        if not ai_move.from_human_interaction:
            if ai_move.move_type is None:
                error("AI must specify type of move")
            if ai_move.move_type is MoveType.DO_RAISE_ARMY:
                if ai_move.loc == (-1, -1):
                    error("AI must specify location where to raise the army")
            if ai_move.move_type == MoveType.DO_BUILD:
                if ai_move.loc == (-1, -1):
                    error("AI must specify the location of the building site")
        else:
            if ai_move.move_type is None:
                if ai_move.doMoveArmy is False:
                    error("The move object comes from human interaction and is faulty! This is a problem!")

    def check_win_condition(self, player: Player):
        for p in self.player_list:
            if p != player:
                if not p.has_lost:
                    return False
        return True

    def check_lose_condition(self, player: Player) -> bool :
        """in case the player lost, this function returns True, otherwise False"""
        has_active_building = False
        has_food = False
        for b in player.buildings:
            if b.building_state == BuildingState.ACTIVE or b.building_state == BuildingState.UNDER_CONSTRUCTION:
                has_active_building = True
        has_food = player.food > 0
        return not (has_food and has_active_building)


    def get_scoutable_tiles(self, player: Player) -> set:
        s_set = set()
        for hex in self.hex_map.map:
            if hex in player.discovered_tiles and hex.ground.walkable:
                for h in self.hex_map.get_neighbours(hex):
                    if h not in player.discovered_tiles:
                        s_set.add(h)
        return set(filter(None, s_set))

    def get_buildable_tiles(self, player: Player) -> Set[Hexagon]:
        b_set = set()
        for hex in player.discovered_tiles:
            if hex.ground.buildable:
                b_set.add(hex)
        for p in self.player_list:          # army may block
            for army in p.armies:
                if army.tile in b_set:
                    b_set.remove(army.tile)
        return b_set

    def get_walkable_tiles(self, player):
        b_set = set()
        for hex in player.discovered_tiles:
            if hex.ground.walkable:
                b_set.add(hex)
        for p in self.player_list:      # enemy buildings are walkable (to attack them) if they are scouted
            if p.id != player.id:
                for b in p.buildings:
                    if b.tile in player.discovered_tiles:
                        b_set.add(b.tile)
        return b_set

    def get_known_resources(self, player: Player) -> set:
        r_set = set()
        for res in self.scenario.resource_list:
            if res.tile in player.discovered_tiles:
                r_set.add(res)
        return r_set

    def get_enemy_buildings(self, player: Player, scoutable_tiles: Set[Hexagon]) -> set:
        e_set = set()
        for other_player in self.player_list:
            if other_player.id != player.id:
                for o_b in other_player.buildings:
                    for my_dis in set().union(player.discovered_tiles, scoutable_tiles):
                        if o_b.tile.offset_coordinates == my_dis.offset_coordinates:
                            e_set.add((o_b, other_player.id))
        return e_set

    def get_enemy_armies(self, player:  Player) -> set:
        e_set = set()
        for other_player in self.player_list:
            if other_player != player:
                for army in other_player.armies:
                    if army.tile in player.discovered_tiles:
                        e_set.add((army, other_player.id))
        return e_set

    def update_fog_of_war(self, player):
        if self.map_hack:
            return
        if self.map_view[player.id]:
            for hex in player.discovered_tiles:
                hex.ground.set_active_texture(1)
                # hex.ground.sprite.alpha = 255
            for res in self.scenario.resource_list:
                if res.tile in player.discovered_tiles:
                    res.sprite.alpha = 255
            for p in self.player_list:
                for a in p.armies:
                    if a.tile in player.discovered_tiles:
                        a.sprite.alpha = 255
                for b in p.buildings:
                    if b.tile in player.discovered_tiles:
                        b.sprite.alpha = 255
                        b.flag.alpha = 255
                        for a in b.associated_drawables:
                            a.sprite.alpha = 255
        self.__reorder_spritelist(self.z_levels[Z_GAME_OBJ])

    def toggle_fog_of_war_lw(self, tile_list: Set[Hexagon], show_update_bar=False):
        t1 = timeit.default_timer()
        v = 255 if self.map_hack else 0
        for res in self.scenario.resource_list:
            res.sprite.alpha = v
        tot = len(tile_list)
        counter = 0
        if show_update_bar:
            start_progress("Updating map view")
        if self.change_in_map_view:
            for hex in tile_list:
                if counter % 5 == 0 and show_update_bar:
                    progress(counter)
                counter = counter + 1
                hex.ground.set_active_texture(1 if self.map_hack else 0)
                # hex.ground.sprite.alpha = 255 if self.map_hack else 0
        if show_update_bar:
            end_progress()
        for player in self.player_list:
            for a in player.armies:
                a.sprite.alpha = v
            for b in player.buildings:
                b.sprite.alpha = v
                b.flag.alpha = v
                for a in b.associated_drawables:
                    a.sprite.alpha = v
        t2 = timeit.default_timer()
        for player in self.player_list:
            self.update_fog_of_war(player)
        t3 = timeit.default_timer()
        debug("Toggeling the map took: {} s (fog of war update: {})".format(t3 - t1, t3 - t2))

    def add_resource(self, resource: Resource):
        self.scenario.resource_list.append(resource)
        resource.set_sprite_pos(HexMap.offset_to_pixel_coords(resource.tile.offset_coordinates), self.__camera_pos)
        self.__set_sprite(resource, resource.tex_code)
        self.z_levels[Z_GAME_OBJ].append(resource.sprite)

    def del_resource(self, resource: Resource):
        self.scenario.resource_list.remove(resource)
        self.z_levels[Z_GAME_OBJ].remove(resource.sprite)

    def add_animated_flag(self, colour_code: str, pos: Tuple[int, int]) -> Flag:
        a_tex = self.texture_store.get_animated_texture('{}_flag'.format(colour_code))
        flag = Flag(pos, a_tex, 0.2)
        self.z_levels[Z_FLYING].append(flag)
        return flag

    # def add_flag(self, flag: Flag, colour_code: str):
    #     a_tex = self.texture_store.get_animated_texture('{}_flag'.format(colour_code))
    #     for tex in a_tex:
    #         flag.add_texture(tex)
    #     flag.set_sprite_pos(flag.position, self.__camera_pos)
    #     flag.set_tex_scale(0.20)
    #     flag.update_interval = 0.1
    #     flag.sprite.set_texture(0)
    #     self.animator.key_frame_animations.append(flag)
    #     self.z_levels[2].append(flag.sprite)

    def del_flag(self, flag: Flag):
        self.z_levels[Z_FLYING].remove(flag)

    def add_building(self, building: Building, player: Player):
        # hint("adding a building")
        player.buildings.append(building)
        position = HexMap.offset_to_pixel_coords(building.tile.offset_coordinates)
        building.set_sprite_pos(position, self.__camera_pos)
        self.__set_sprite(building, building.tex_code)
        building.set_state_active()
        if building.construction_time > 0:
            building.add_tex_construction(self.texture_store.get_texture("cs"))
            building.set_state_construction()
        building.add_tex_destruction(self.texture_store.get_texture("ds"))
        self.z_levels[Z_GAME_OBJ].append(building.sprite)
        # add the flag:
        # flag = Flag((position[0] + building.flag_offset[0], position[1] + building.flag_offset[1]),
        #            player.colour)
        #self.add_flag(flag, player.colour_code)
        pos = (position[0] + building.flag_offset[0] + self.__camera_pos[0],
               position[1] + building.flag_offset[1] + self.__camera_pos[1])
        flag = self.add_animated_flag(player.colour_code, pos)
        building.flag = flag
        if building.building_type == BuildingType.FARM:
            for a in building.associated_tiles:
                self.extend_building(building, a, "cf")
        if building.building_type == BuildingType.VILLAGE_1:
            for n in self.hex_map.get_neighbours(building.tile):
                building.associated_tiles.append(n)
        building.tile.ground.walkable = False
        building.tile.ground.buildable = False
        self.toggle_fog_of_war_lw(player.discovered_tiles)
        self.__reorder_spritelist(self.z_levels[Z_GAME_OBJ])


    def extend_building(self, building: Building, tile: Hexagon, tex_code: str):
        # building.associated_tiles.append(tile)
        drawable = Drawable()
        drawable.set_sprite_pos(HexMap.offset_to_pixel_coords(tile.offset_coordinates), self.__camera_pos)
        building.associated_drawables.append(drawable)
        drawable.sprite.alpha = 100
        self.__set_sprite(drawable, tex_code)
        self.z_levels[Z_GAME_OBJ].append(drawable.sprite)

    def del_building(self, building: Building, player: Player):
        self.del_flag(building.flag)
        for drawable in building.associated_drawables:
            self.z_levels[Z_GAME_OBJ].remove(drawable.sprite)
        player.buildings.remove(building)
        self.z_levels[Z_GAME_OBJ].remove(building.sprite)

    def add_army(self, army: Army, player: Player):
        player.armies.append(army)
        army.set_sprite_pos(HexMap.offset_to_pixel_coords(army.tile.offset_coordinates), self.__camera_pos)
        army.is_barbaric = player.is_barbaric
        self.__set_sprite(army, "f1_" + player.colour_code)
        self.toggle_fog_of_war_lw(player.discovered_tiles)
        self.z_levels[Z_GAME_OBJ].append(army.sprite)

    def move_army(self, army: Army, player: Player, pos: (int, int)):
        is_moving = True
        new_hex = self.hex_map.get_hex_by_offset(pos)
        if new_hex is None:
            error("Error in army movment: ->" + str(pos))
            return
        if self.hex_map.hex_distance(new_hex, army.tile) != 1:
            error("Army cannot 'fly'. AI tries to move more than 1 tile. strange..!?!?!?!")
            hint(str(new_hex.offset_coordinates))
            hint(str(army.tile.offset_coordinates))
            return          # try to recover from there.
        # make sure the new hex is empty
        if player.armies[0].get_population() == 0:
            hint("army has population 0 and cannot be moved")
            return
        for p in self.player_list:
            if p != player:
                for hostile_army in p.armies:
                    if hostile_army.tile.offset_coordinates == new_hex.offset_coordinates:
                        if hostile_army.get_population() > 0:
                            pre_att_u = army.get_units_as_tuple()
                            pre_def_u = hostile_army.get_units_as_tuple()
                            outcome: BattleAfterMath = FightCalculator.army_vs_army(army, hostile_army)
                            post_att_u = army.get_units_as_tuple()
                            post_def_u = hostile_army.get_units_as_tuple()
                            Logger.log_battle_army_vs_army_log(pre_att_u, pre_def_u, post_att_u, post_def_u,
                                                               outcome, player.name, p.name)
                            p.attacked_set.add((player.id, hostile_army.tile.offset_coordinates))
                            if hostile_army.get_population() == 0:
                                self.del_army(hostile_army, p)
                            if army.get_population() == 0:
                                self.del_army(army, player)
                            # does not execute moving the army
                            is_moving = False
                        else:
                            self.del_army(hostile_army, p)
                            is_moving = False
                for b in p.buildings:
                    if b.tile.offset_coordinates == new_hex.offset_coordinates:
                        pre_att_u = army.get_units_as_tuple()
                        pre_b = b.defensive_value
                        outcome: BattleAfterMath = FightCalculator.army_vs_building(army, b)
                        print(outcome)
                        post_att_u = army.get_units_as_tuple()
                        post_b = b.defensive_value
                        Logger.log_battle_army_vs_building(pre_att_u, post_att_u, pre_b, post_b,
                                                           outcome, player.name, p.name)
                        p.attacked_set.add((player.id, b.tile.offset_coordinates))
                        if b.defensive_value == -1:
                            b.set_state_destruction()
                        if army.get_population() == 0:
                            self.del_army(army, player)
                            is_moving = False
        if is_moving:
            if self.hex_map.hex_distance(new_hex, army.tile) == 1:
                self.animator.add_move_animation(army, new_hex.offset_coordinates, float(.4))
                army.tile = new_hex
                hint('army is moving to ' + str(army.tile.offset_coordinates))
                #army.set_sprite_pos(HexMap.offset_to_pixel_coords(new_hex.offset_coordinates))
                self.__reorder_spritelist(self.z_levels[Z_GAME_OBJ])
                self.toggle_fog_of_war_lw(player.discovered_tiles)
            else:
                error(f"Army cannot move that far: {self.hex_map.hex_distance(new_hex, army.tile)}")




    def del_army(self, army: Army, player: Player):
        hint("Game Logic: deleting army of player " + str(player.name))
        self.animator.stop_animation(army)
        self.z_levels[Z_GAME_OBJ].remove(army.sprite)
        player.armies.remove(army)

    def __set_sprite(self, drawable: Drawable, tex_code: str):
        drawable.add_texture(self.texture_store.get_texture(tex_code))
        drawable.set_tex_offset(self.texture_store.get_tex_offest(tex_code))
        drawable.set_tex_scale(self.texture_store.get_tex_scale(tex_code))

    def __reorder_spritelist(self, sl: arcade.SpriteList):          #TODO ugly
        li = []
        for s in sl:
            li.append(s)
        for s in li:
            sl.remove(s)
        # TODO: BAD:to make the army appear on top of fields I substract by height. That must be a better solution
        # li.sort(key=lambda x: x.center_y - (x._height - 30), reverse=True)
        li.sort(key=lambda x: x.center_y, reverse=True)
        for s in li:
            sl.append(s)

    def set_camera_pos(self, pos_x, pos_y):
        self.__camera_pos = (pos_x, pos_y)

    def get_map_element(self, offset_coords):
        # do this in zlvl order
        for res in self.scenario.resource_list:
            if res.tile.offset_coordinates == offset_coords:
                return res, Resource
        for p in self.player_list:
            for b in p.buildings:
                if b.tile.offset_coordinates == offset_coords:
                    return b, Building
            for a in p.armies:
                if a.tile.offset_coordinates == offset_coords:
                    return a, Army
        return None, None

    def add_aux_sprite(self, hex, tex_code):              # TODO ugly method duplicated
        self.__add_aux_sprite(hex, tex_code)

    def __add_aux_sprite(self, hex: Hexagon, tex_code: str):
        aux = Drawable()
        self.scenario.aux_sprites.append((hex, aux))
        aux.set_sprite_pos(HexMap.offset_to_pixel_coords(hex.offset_coordinates), self.__camera_pos)
        self.__set_sprite(aux, tex_code)
        self.z_levels[Z_AUX].append(aux.sprite)
        self.__reorder_spritelist(self.z_levels[Z_AUX])

    def __clear_aux_sprites(self):
        to_be_del: List[(Hexagon, Drawable)] = []
        for aux in self.scenario.aux_sprites:
            to_be_del.append(aux)
        for tbd in to_be_del:
            if tbd:
                self.__rmv_aux_sprite(tbd[1].sprite)
                self.scenario.aux_sprites.remove(tbd)

    def __rmv_aux_sprite(self, sprite: arcade.Sprite):
        self.z_levels[Z_AUX].remove(sprite)

    def __exec_command(self, c_list):
        if not Definitions.ALLOW_CONSOLE_CMDS:
            return
        for c in c_list:
            cmd = c[0]
            if cmd == "mark_tile":
                hex = self.hex_map.get_hex_by_offset((int(c[1]), int(c[2])))
                self.__add_aux_sprite(hex, "ou")
            elif cmd == "set_res":
                for p in self.player_list:
                    if p.id == int(c[1]):
                        p.amount_of_resources = int(c[2])
            #elif cmd == "set_scouted":
                #for p in self.player_list:
                    #if p.id == int(c[1]):
                        #p.discovedTiles.add(self.tile_map.get_tile(int(c[2]), int(c[3])))
            elif cmd == "hl_scouted":
                for p in self.player_list:
                    if p.id == int(c[1]):
                        for dt in p.discovered_tiles:
                            self.__add_aux_sprite(dt, "ou")
            elif cmd == "hl_walkable":
                for hex in self.hex_map.map:
                    if hex.ground.walkable:
                        self.__add_aux_sprite(hex, "ou")
            elif cmd == "clear_aux":
                self.__clear_aux_sprites()
            elif cmd == "switch_ka":
                self.show_key_frame_animation = not self.show_key_frame_animation
                debug(f"keyframes are {'enabled' if self.show_key_frame_animation else 'disabled'}")
