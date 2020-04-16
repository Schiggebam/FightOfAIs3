import arcade
import timeit
# from threading import Thread

from src.ai.AI_GameStatus import AI_GameStatus, AI_Move, AI_GameInterface
from src.misc.animation import Animator
from src.misc.game_constants import ResourceType, error, GroundType, debug
from src.game_accessoires import Scenario, Ground, Resource, Drawable, Flag, Unit
from src.game_file_reader import GameFileReader
from src.hex_map import HexMap, MapStyle, Hexagon
from src.texture_store import TextureStore
from src.misc.game_logic_misc import *
from typing import Optional, List, Set


class GameLogic:
    def __init__(self, game_xml_file: str, z_levels: [arcade.SpriteList]):
        self.texture_store: TextureStore = TextureStore()
        self.game_file_reader: GameFileReader = GameFileReader(game_xml_file)
        self.z_levels: [arcade.SpriteList] = z_levels               # reference to the sprite lists
        self.hex_map: Optional[HexMap] = None
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
        self.change_in_map_view = False
        self.map_hack = True
        self.winner: Optional[Player] = None

        # read game data
        self.game_file_reader.read_resource_info(Resource.resource_info)
        self.game_file_reader.read_building_info(Building.building_info)
        self.game_file_reader.read_unit_info(Unit.unit_info)

        # read player data
        player_info: [(str, {})] = []                           # a tuple per player, first element is player's name
        self.game_file_reader.read_player_info(player_info)
        id = 0
        for p_info in player_info:
            p = Player(p_info[0], id, p_info[1]['colour'],
                       (int(p_info[1]['spawn_x']), int(p_info[1]['spawn_y'])),
                       p_info[1]['ai'])
            p.is_barbaric = p_info[1]['ai'] == "barbaric"
            p.is_villager = p_info[1]['ai'] == "villager"
            p.init_army_loc = (p.spaw_loc[0] + p_info[1]['army_rel_to_spawn_x'],
                               p.spaw_loc[1] + p_info[1]['army_rel_to_spawn_y'])
            self.player_list.append(p)
            self.map_view.append(False)
            id = id + 1

        # load textures which depend on player
        idx_fun = lambda i: (0, 100 * i)
        for p in self.player_list:
            c = p.colour_code
            self.texture_store.load_animated_texture("{}_flag".format(c), 10, idx_fun, 108, 100,
                                                     "../resources/objects/animated/flag_100_sprite_{}.png".format(c))

        self.ai_running = False
        # game status
        self.playNextTurn: bool = False
        self.current_player: int = 0
        self.turn_nr = 0
        self.automatic: bool = False

        self.test = None
        self.total_time = 0
        self.animator_time = 0

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
        background: List[Drawable] = []
        x_off = 213
        y_off = 165
        for x in range(6):
            for y in range(5):
                d = Drawable()
                d.set_sprite_pos((x_off * x + 100, y_off * y), self.__camera_pos)
                self.__set_sprite(d, "ocean")
                self.z_levels[0].append(d.sprite)

        #map
        for y in range(len(map_data)-1, -1, -1):
            for x in range(len(map_data[y])):
                hex: Hexagon = self.hex_map.get_hex_by_offset((x, y))
                ground: Ground = Ground(map_data[y][x])
                hex.ground = ground
                ground.set_sprite_pos(HexMap.offset_to_pixel_coords((x, y)), self.__camera_pos)
                ground.add_texture(self.texture_store.get_texture("fw"))
                ground.tex_code = map_data[y][x]
                self.z_levels[1].append(ground.sprite)

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

            elif map_obj[0] == "r1" or map_obj[0] == "g1" or map_obj[0] == "f1":                            # TODO if resource
                r: Resource = Resource(hex, ResourceType.get_type_from_strcode(map_obj[0]))
                r.tex_code = map_obj[0]
                self.add_resource(r)

        for player in self.player_list:
            other_players_ids = [int]
            for p in self.player_list:
                if p != player:
                    other_players_ids.append(p.id)
            self.ai_interface.launch_AI(player.id, player.ai_str, other_players_ids)
            base_hex: Hexagon = self.hex_map.get_hex_by_offset(player.spaw_loc)
            player.discovered_tiles.add(base_hex)
            player.food = 20
            b_type = player.get_initial_building_type()
            b: Building = Building(base_hex, b_type, player.id)
            self.add_building(b, player)
            b.construction_time = 0
            b.set_state_active()
            tmp = self.hex_map.get_neighbours_dist(base_hex, b.sight_range)
            player.discovered_tiles.update(tmp)
            unit = Unit(player.get_initial_unit_type())
            army = Army(self.hex_map.get_hex_by_offset(player.init_army_loc), player.id)
            army.add_unit(unit)
            self.add_army(army, player)

        self.__reorder_spritelist(self.z_levels[2])
        self.toggle_fog_of_war()
        # HexMap.hex_distance(self.hex_map.get_hex_by_offset((0,0)), self.hex_map.get_hex_by_offset((2,2)))

    elapsed = float(0)
    total_elapsed = float(0)
    ith_iteration = 0
    def update(self, delta_time: float, commands :[]):
        timestamp_start = timeit.default_timer()
        self.__exec_command(commands)
        GameLogic.elapsed = GameLogic.elapsed + delta_time
        GameLogic.total_elapsed = GameLogic.total_elapsed + delta_time
        #update animations
        # if self.animator.is_active():           # -> move this to own thread possibly
        #for p in self.player_list:
        #    for b in p.buildings:
        #        b.flag.next_frame(delta_time)
        GameLogic.ith_iteration = GameLogic.ith_iteration + 1
        if GameLogic.ith_iteration % 3 == 0:
            for k_f in self.animator.key_frame_animations:
                k_f.next_frame(delta_time)
        self.animator_time = timestamp_start - timeit.default_timer()
        if GameLogic.elapsed > float(1) and self.automatic:
            self.playNextTurn = True
            GameLogic.elapsed = float(0)
        if self.playNextTurn:
            #if not self.ai_running:
            if self.current_player == 0:  # next time player 0 plays -> new turn
                self.turn_nr = self.turn_nr + 1
            if len(self.player_list) > 0:
                self.play_players_turn()
                #thread = Thread(target= self.run_ai())
                self.current_player = (self.current_player + 1) % len(self.player_list)
            #else:
            #    debug("AI is still calculating move... ")

        self.playNextTurn = False
        if self.change_in_map_view:
            self.toggle_fog_of_war()
            self.change_in_map_view = False


        self.animator.update(GameLogic.total_elapsed)
        self.total_time = timestamp_start - timeit.default_timer()


    def play_players_turn(self):
        # self.__clear_aux_sprites(1)
        player = self.player_list[self.current_player]
        print("Play turn of: " + player.name)
        self.updata_map()
        # gather player data
        if self.check_win_condition(player):
            self.winner = player
        player.has_lost = self.check_lose_condition(player)

        # continue build buildings
        for b in player.buildings:
            if b.building_state == BuildingState.UNDER_CONSTRUCTION:
                if b.construction_time == 0:
                    b.set_state_active()
                else:
                    b.construction_time = b.construction_time - 1
            if b.building_state == BuildingState.DESTROYED:
                self.del_building(b, player)

        if player.has_lost:
            for army in player.armies:
                self.del_army(army, player)
            return

        player.income = self.income_calc.calculate_income(player)
        player.amount_of_resources = player.amount_of_resources + player.income
        player.food = player.food + self.income_calc.calculate_food(player)
        player.culture = player.culture + self.income_calc.calculate_culture(player)

        # gather data for ai
        scoutable_tiles = self.get_scoutable_tiles(player)
        buildable_tiles = self.get_buildable_tiles(player)
        known_resources = self.get_known_resources(player)
        walkable_tiles = self.get_walkable_tiles(player)
        enemy_buildings = self.get_enemy_buildings(player)  # tuple set((bld, owner_id))
        enemy_armies = self.get_enemy_armies(player)        # tuple set((army, owner_id))
        player_population = player.get_population()
        player_population_limit = player.get_population_limit()

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

        for r in known_resources:
            ai_map.add_resource(r.tile.offset_coordinates, r)
        for b in player.buildings:
            ai_map.add_own_building(b.tile.offset_coordinates, b)
        for b in enemy_buildings:
            ai_map.add_opp_building(b.tile.offset_coordinates, b)
        for a in player.armies:
            ai_map.add_own_army(a.tile.offset_coordinates, a)
        for a in enemy_armies:
            ai_map.add_opp_army(a.tile.offset_coordinates, a)
        # ai_map.print_map()

        costs = {'scout': int(1)}
        for b_info in Building.building_info:
            costs[b_info[1]['tex_code']] = b_info[1]['construction_cost']
        #if player.is_barbaric:
        costs['bs'] = Unit.get_unit_cost(UnitType.BABARIC_SOLDIER)
        #else:
        costs['knight'] = Unit.get_unit_cost(UnitType.KNIGHT)
        costs['mercenary'] = Unit.get_unit_cost(UnitType.MERCENARY)
        # print('costs: ', end="")
        # print(costs)

        # ask the AI of each player to do a move
        ai_status = AI_GameStatus()
        ai_move = AI_Move()

        self.ai_interface.create_ai_status(ai_status, self.turn_nr, player.id, player.food,
                                           player.amount_of_resources, player.culture,
                                           costs, len(self.player_list) - 1, player.attacked_set,
                                           player_population, player_population_limit, ai_map)
        player.attacked_set.clear()
        timestamp_start = timeit.default_timer()
        self.ai_interface.do_a_move(ai_status, ai_move, player.id)
        debug(f"AI took: {timeit.default_timer() - timestamp_start} s")

        self.exec_ai_move(ai_move, player, costs)
        ai_status.clear()
        del ai_status

        # if not player.is_barbaric:
        #     self.__add_aux_sprite(player.armies[0].tile, 1, "ou")

        hint("                          SUCCESSFULLY PLAYED TURN")

    def run_ai(self):
        self.ai_running = True
        self.play_players_turn()
        self.ai_running = False

    def updata_map(self):
        """this function makes sure that the map remains well defined"""
        for hex in self.hex_map.map:
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


    def exec_ai_move(self, ai_move: AI_Move, player: Player, costs):
        for d in self.hex_map.map:
            d.debug_msg = ""
        for d in ai_move.info_at_tile:
            hex = self.hex_map.get_hex_by_offset(d[0])
            hex.debug_msg = d[1]


        if ai_move.doMoveArmy:
            if len(player.armies) == 1:             #TODO support for only 1 army here
                self.move_army(player.armies[0], player, ai_move.move_army_to)
            else:
                print("No army available")

        if ai_move.doRecruitArmy:
            if len(player.armies) == 0:
                base_hex = self.hex_map.get_hex_by_offset(ai_move.loc)
                army = Army(base_hex, player.id)
                self.add_army(army, player)
            else:
                error("Not more than one armies allowed")

        if ai_move.doUpArmy or ai_move.doRecruitUnit:
            if len(player.armies) == 1:             #TODO support for only 1 army here
                if player.is_barbaric:
                    cost_bs = Unit.get_unit_cost(UnitType.BABARIC_SOLDIER)[0]
                    if player.amount_of_resources >= cost_bs:
                        player.amount_of_resources = player.amount_of_resources - cost_bs
                        u: Unit = Unit(UnitType.BABARIC_SOLDIER)
                        player.armies[0].add_unit(u)
                        hint("new unit recruited for barbric army")
                    else:
                        error("Not enough resources to upgrade the (barbaric) army")
                else:
                    if ai_move.type == UnitType.KNIGHT or ai_move.type == UnitType.MERCENARY:
                        type = ai_move.type
                        cost = Unit.get_unit_cost(type)
                        if player.amount_of_resources < cost[0]:
                            error("Not enough resources to recruit unit: " + str(type))
                        elif player.culture < cost[1]:
                            error("Not enough culture to recruit unit: " + str(type))
                        elif player.get_population_limit() < player.get_population() + cost[2]:
                            error("Not enough free population to recruit " + str(type))
                        else:
                            player.amount_of_resources = player.amount_of_resources - cost[0]
                            player.culture = player.culture - cost[1]
                            u: Unit = Unit(type)
                            player.armies[0].add_unit(u)
                            hint("new unit recruited - type: " + str(type))
                    else:
                        error("unknown unit type.")
            else:
                error("No army. Recruit new army first!")

        if ai_move.doBuild:
            if not self.hex_map.get_hex_by_offset(ai_move.loc).ground.buildable:
                error("Exec AI Move: Location is not buildable!")
                return
            b_type = 0
            if player.is_barbaric:
                b_type = BuildingType.CAMP_1        # not very good to hard-code this here
            else:
                b_type = ai_move.type
            if Building.get_construction_cost(b_type) <= player.amount_of_resources:
                base_hex = self.hex_map.get_hex_by_offset(ai_move.loc)
                b = Building(base_hex, b_type, player.id)
                if not player.is_barbaric:
                    if ai_move.type == BuildingType.FARM:
                        for loc in ai_move.info:
                            # hint(f"adding Associated Tile at location: {loc}")
                            b.associated_tiles.append(self.hex_map.get_hex_by_offset(loc))
                        # b.associated_tiles.append(self.hex_map.get_hex_by_offset(ai_move.info[1]))
                        # b.associated_tiles.append(self.hex_map.get_hex_by_offset(ai_move.info[2]))
                self.add_building(b, player)
                player.amount_of_resources = player.amount_of_resources - Building.get_construction_cost(b_type)
                # The sight range is only extended with the player is not barbaric
                if not player.is_barbaric:
                    tmp = self.hex_map.get_neighbours_dist(base_hex, b.sight_range)
                    player.discovered_tiles.update(tmp)
            else:
                error("Exec AI Move: Cannot build building! BuildingType:" + str(b_type))
        if ai_move.doScout:
            if player.amount_of_resources >= costs['scout']:
                player.discovered_tiles.add(self.hex_map.get_hex_by_offset(ai_move.loc))
                player.amount_of_resources = player.amount_of_resources - costs['scout']

        elif ai_move.doUpgrade:
            b_old: Optional[Building] = None
            for upgradable in player.buildings:
                if upgradable.tile.offset_coordinates == ai_move.loc:
                    b_old = upgradable
            if not b_old:
                print("Exec AI Move: No building found at location to upgrade!")
                return
            b_type = 0
            # self.__add_aux_sprite(b_old.tile, 1, "ou")
            if b_old.building_type == BuildingType.CAMP_1:
                b_type = BuildingType.CAMP_2
            elif b_old.building_type == BuildingType.CAMP_2:
                b_type = BuildingType.CAMP_3
            player.amount_of_resources = player.amount_of_resources - Building.get_construction_cost(b_type)
            self.del_building(b_old, player)
            base_hex = self.hex_map.get_hex_by_offset(ai_move.loc)
            b_new = Building(base_hex, b_type, player.id)
            print(b_new.tex_code)
            self.add_building(b_new, player)

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
        for p in self.player_list:          # enemy buildings are walkable (to attack them) if they are scouted
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

    def get_enemy_buildings(self, player: Player) -> set:
        e_set = set()
        for other_player in self.player_list:
            if other_player != player:
                for o_b in other_player.buildings:
                    if o_b.tile in player.discovered_tiles:
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
            for hex in self.hex_map.map:
                if hex in player.discovered_tiles:
                    hex.ground.set_active_texture(1)
            for res in self.scenario.resource_list:
                if res.tile in player.discovered_tiles:
                    res.sprite.alpha = 255
            for p in self.player_list:
                for b in p.buildings:
                    if b.tile in player.discovered_tiles:
                        b.sprite.alpha = 255
                        for a in b.associated_drawables:
                            a.sprite.alpha = 255
        self.__reorder_spritelist(self.z_levels[2])

    def toggle_fog_of_war(self):
        v = 255 if self.map_hack else 0
        for res in self.scenario.resource_list:
            res.sprite.alpha = v
        if len(self.player_list) == 0:
            for hex in self.hex_map.map:
                 hex.ground.set_active_texture(1 if self.map_hack else 0)
        else:
            for player in self.player_list:
                for hex in self.hex_map.map:
                     hex.ground.set_active_texture(1 if self.map_hack else 0)

            #for player in self.player_list:
                for b in player.buildings:
                    b.sprite.alpha = v
                    for a in b.associated_drawables:
                        a.sprite.alpha = v
                self.update_fog_of_war(player)

    def add_resource(self, resource: Resource):
        self.scenario.resource_list.append(resource)
        resource.set_sprite_pos(HexMap.offset_to_pixel_coords(resource.tile.offset_coordinates), self.__camera_pos)
        self.__set_sprite(resource, resource.tex_code)
        self.z_levels[2].append(resource.sprite)

    def del_resource(self, resource: Resource):
        self.scenario.resource_list.remove(resource)
        self.z_levels[2].remove(resource.sprite)

    def add_flag(self, flag: Flag, colour_code: str):
        a_tex = self.texture_store.get_animated_texture('{}_flag'.format(colour_code))
        for tex in a_tex:
            flag.add_texture(tex)
        flag.set_sprite_pos(flag.position, self.__camera_pos)
        flag.set_tex_scale(0.20)
        flag.update_interval = 0.1
        flag.sprite.set_texture(0)
        self.animator.key_frame_animations.append(flag)
        self.z_levels[2].append(flag.sprite)

    def add_building(self, building: Building, player: Player):
        hint("adding a building")
        player.buildings.append(building)
        position = HexMap.offset_to_pixel_coords(building.tile.offset_coordinates)
        building.set_sprite_pos(position, self.__camera_pos)
        self.__set_sprite(building, building.tex_code)
        building.set_state_active()
        if building.construction_time > 0:
            building.add_tex_construction(self.texture_store.get_texture("cs"))
            building.set_state_construction()
        building.add_tex_destruction(self.texture_store.get_texture("ds"))
        self.z_levels[2].append(building.sprite)
        # add the flag:
        flag = Flag((position[0] + building.flag_offset[0], position[1] + building.flag_offset[1]),
                    player.colour)
        self.add_flag(flag, player.colour_code)
        building.flag = flag
        if building.building_type == BuildingType.FARM:
            for a in building.associated_tiles:
                self.extend_building(building, a, "cf")
                #d = Drawable()
                #d.set_sprite_pos(HexMap.offset_to_pixel_coords(a.offset_coordinates))
                #building.associated_drawables.append(d)
                #self.__set_sprite(d, "cf")
                #self.z_levels[2].append(d.sprite)
        # if building.building_type == BuildingType.VILLAGE:
        #     mountain_tile = self.hex_map.get_hex_northeast(building.tile)
        #     mine_tile = self.hex_map.get_hex_northwest(building.tile)
        #     storage_tile = self.hex_map.get_hex_southwest(building.tile)
        #     church_tile = self.hex_map.get_hex_east(building.tile)
        #
            #TODO append tile as associated tiles

        #     self.extend_building(building, mountain_tile, "vmountain")
        #     self.extend_building(building, mine_tile, "vm_nw")
        #     self.extend_building(building, church_tile, "vk_e")
        #     self.extend_building(building, storage_tile, "vs_sw")
        self.toggle_fog_of_war()
        self.__reorder_spritelist(self.z_levels[2])


    def extend_building(self, building: Building, tile: Hexagon, tex_code: str):
        # building.associated_tiles.append(tile)
        drawable = Drawable()
        drawable.set_sprite_pos(HexMap.offset_to_pixel_coords(tile.offset_coordinates), self.__camera_pos)
        building.associated_drawables.append(drawable)
        self.__set_sprite(drawable, tex_code)
        self.z_levels[2].append(drawable.sprite)

    def del_building(self, building: Building, player: Player):
        for drawable in building.associated_drawables:
            self.z_levels[2].remove(drawable.sprite)
        player.buildings.remove(building)
        self.z_levels[2].remove(building.sprite)

    def add_army(self, army: Army, player: Player):
        player.armies.append(army)
        army.set_sprite_pos(HexMap.offset_to_pixel_coords(army.tile.offset_coordinates), self.__camera_pos)
        army.is_barbaric = player.is_barbaric
        self.__set_sprite(army, "f1_" + player.colour_code)
        self.z_levels[2].append(army.sprite)

    def move_army(self, army: Army, player: Player, pos: (int, int)):
        is_moving = True
        new_hex = self.hex_map.get_hex_by_offset(pos)
        # make sure the new hex is empty
        for p in self.player_list:
            if p != player:
                for hostile_army in p.armies:
                    if hostile_army.tile.offset_coordinates == new_hex.offset_coordinates:
                        army_population = army.get_population()
                        h_army_population = army.get_population()
                        FightCalculator.army_vs_army(army, hostile_army)
                        Logger.log_battle_army_vs_army_log(army, hostile_army, army_population, h_army_population)
                        p.attacked_set.add(player.id)
                        if hostile_army.get_population() == 0:
                            self.del_army(hostile_army, p)
                        # does not execute moving the army
                        is_moving = False
                for b in p.buildings:
                    if b.tile.offset_coordinates == new_hex.offset_coordinates:
                        b_strength = b.defensive_value
                        army_population = army.get_population()
                        FightCalculator.army_vs_building(army, b)
                        Logger.log_battle_army_vs_building(army, b, army_population, b_strength)
                        p.attacked_set.add(player.id)
                        if b.defensive_value == -1:
                            b.set_state_destruction()
        if is_moving:
            if self.hex_map.hex_distance(new_hex, army.tile) == 1:
                self.animator.add_move_animation(army, new_hex.offset_coordinates, float(.4))
                army.tile = new_hex
                #army.set_sprite_pos(HexMap.offset_to_pixel_coords(new_hex.offset_coordinates))
                self.__reorder_spritelist(self.z_levels[2])
            else:
                print("Army cannot move that far")

        if army.get_population() == 0:
            self.del_army(army, player)


    def del_army(self, army: Army, player: Player):
        hint("Game Logic: deleting army of player " + str(player.name))
        self.z_levels[2].remove(army.sprite)
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

    def add_aux_sprite(self, hex, zlvl, tex_code):              # TODO ugly method duplicated
        self.__add_aux_sprite(hex, zlvl, tex_code)

    def __add_aux_sprite(self, hex: Hexagon, zlvl: int, tex_code: str):
        aux = Drawable()
        self.scenario.aux_sprites.append((hex, aux))
        aux.set_sprite_pos(HexMap.offset_to_pixel_coords(hex.offset_coordinates), self.__camera_pos)
        self.__set_sprite(aux, tex_code)
        self.z_levels[zlvl].append(aux.sprite)
        self.__reorder_spritelist(self.z_levels[zlvl])

    def __clear_aux_sprites(self, zlvl):
        to_be_del: [arcade.Sprite] = []
        for aux in self.scenario.aux_sprites:
            to_be_del.append(aux)
        for tbd in to_be_del:
            if tbd:
                self.__rmv_aux_sprite(tbd[zlvl].sprite, 1)
                self.scenario.aux_sprites.remove(tbd)

    def __rmv_aux_sprite(self, sprite: arcade.Sprite, zlvl: int):
        self.z_levels[zlvl].remove(sprite)

    def __exec_command(self, c_list):
        for c in c_list:
            cmd = c[0]
            if cmd == "mark_tile":
                hex = self.hex_map.get_hex_by_offset((int(c[1]), int(c[2])))
                self.__add_aux_sprite(hex, 1, "ou")
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
                            self.__add_aux_sprite(dt, 1, "ou")
            elif cmd == "hl_walkable":
                for hex in self.hex_map.map:
                    if hex.ground.walkable:
                        self.__add_aux_sprite(hex, 1, "ou")
            elif cmd == "clear_aux":
                self.__clear_aux_sprites(1)
