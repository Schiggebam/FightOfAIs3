from typing import Set
from src.game_accessoires import Resource, Army
from src.misc.building import Building
from src.hex_map import Hexagon
from src.misc.game_constants import error


class AI_Move:
    def __init__(self):
        self.doNothing = False
        self.doBuild = False
        self.doScout = False
        self.doUpgrade = False
        self.doUpArmy = False
        self.doMoveArmy = False
        self.doRecruitArmy = False
        self.loc = (0,0)
        self.info = []
        self.move_army_to = (-1, -1)
        self.str_rep_of_action = "" #just for printing
        self.info_at_tile = [] #a list of tuples ((x, y), "str")

    def check_validity(self):
        return self.doBuild + self.doNothing + self.doScout == 1

class AI_Element:
    def __init__(self):
        self.offset_coordinates: (int, int) = (-1, -1)


class AI_Tile(AI_Element):
    def __init__(self):
        super().__init__()
        self.str_code = "--"

        self.pre = None # for pathfinding
        self.dist = 0

class AI_Army(AI_Element):
    def __init__(self):
        super().__init__()
        self.strength = -1
        self.owner = -1

class AI_Resource(AI_Element):
    def __init__(self):
        super().__init__()
        self.type = -1
        self.amount = -1

class AI_Building(AI_Element):
    def __init__(self):
        super().__init__()
        self.type = "--"
        self.owner = -1 #if this is -1, it means that this is not a enemy building. Otherwise the player_id is stored here
        self.associated_tiles = []


class AI_GameStatus:
    def __init__(self):
        self.turn_nr: int = -1
        self.player_id: int = -1
        self.player_food: int = 0
        self.player_resources = 0
        self.player_culture = 0
        self.tiles_buildable: [AI_Tile] = []
        self.tiles_scoutable: [AI_Tile] = []
        self.tiles_discovered: [AI_Tile] = []
        self.tiles_walkable: [AI_Tile] = []
        self.costScout: int = -1
        self.costBuildS1: int = -1
        self.costBuildS2: int = -1
        self.costBuildFarm: int = -1
        self.costBuildC1: int = -1
        self.costBuildC2: int = -1
        self.costBuildC3: int = -1
        self.costArmyUp: int = -1
        self.resources: [AI_Resource] = []
        self.own_buildings: [AI_Building] = []
        self.other_players = []
        self.enemy_buildings: [AI_Building] = []
        self.enemy_armies: [AI_Army] = []
        self.num_of_enemies: int = -1
        self.armies: [AI_Army] = []
        self.aggressions: Set[int] = set()


    def clear(self):
        for e in self.tiles_buildable:
            del e
        for e in self.tiles_scoutable:
            del e
        for e in self.resources:
            del e
        for e in self.tiles_discovered:
            del e
        for e in self.own_buildings:
            del e


class AI_GameInterface:
    def __init__(self):
        #self.gen1 = AI_Romain("Expansionist")
        self.dict_of_ais = {}
        print("AI Game interface has been initialized")

    def launch_AI(self, id: int, ai_str:str, other_players: [int]):
        from src.ai.AI_Hellenic import AI_Hellenic
        from src.ai.AI_Barbaric import AI_Barbaric
        if ai_str == "cultivated":
            self.dict_of_ais[id] = AI_Hellenic(ai_str, other_players)
        elif ai_str == "expansionist":
            self.dict_of_ais[id] = AI_Hellenic(ai_str, other_players)
        elif ai_str == "barbaric":
            self.dict_of_ais[id] = AI_Barbaric(id, other_players)


    def copy_tile_to_ai_tile(self, t:Hexagon, ai_t:AI_Tile):
        ai_t.offset_coordinates = t.offset_coordinates
        ai_t.str_code = t.ground.tex_code

    def copy_res_to_ai_res(self, r:Resource, ai_r:AI_Resource):
        ai_r.offset_coordinates = r.tile.offset_coordinates
        ai_r.resource_type = r.resource_type
        ai_r.amount = r.remaining_amount

    def copy_building_to_ai_building(self, b:Building, ai_b:AI_Building):
        ai_b.offset_coordinates = b.tile.offset_coordinates
        ai_b.type = b.building_type
        for a in b.associated_tiles:
            t = AI_Tile()
            self.copy_tile_to_ai_tile(a, t)
            ai_b.associated_tiles.append(t)

    def copy_army_to_ai_army(self, a:Army, ai_a: AI_Army):
        ai_a.offset_coordinates = a.tile.offset_coordinates
        ai_a.strength = a.strength

    def create_ai_status(self, ai_stat : AI_GameStatus, turn_nr,
                         p_id, p_food, p_res, p_cult,
                         t_build, t_scout, costs,
                         res_list, t_discovered, own_buildings,
                         num_of_enemies, t_walkable, own_armies,
                         enemy_buildings, enemy_armies, aggressions:  Set[int]):
        ai_stat.turn_nr = turn_nr
        ai_stat.player_id = p_id
        ai_stat.player_food = p_food
        ai_stat.player_resources = p_res
        ai_stat.player_culture = p_cult
        ai_stat.num_of_enemies = num_of_enemies
        for e_b in t_build:
            ai_tile = AI_Tile()
            self.copy_tile_to_ai_tile(e_b, ai_tile)
            ai_stat.tiles_buildable.append(ai_tile)

        for e_s in t_scout:
            ai_tile = AI_Tile()
            self.copy_tile_to_ai_tile(e_s, ai_tile)
            ai_stat.tiles_scoutable.append(ai_tile)

        ai_stat.costScout = costs['scout']
        ai_stat.costBuildS1 = costs['s1']
        ai_stat.costBuildC1 = costs['c1']
        ai_stat.costBuildC2 = costs['c2']
        ai_stat.costBuildC3 = costs['c3']
        ai_stat.costBuildS2 = costs['s2']
        ai_stat.costBuildFarm = costs['fa']
        ai_stat.costArmyUp = costs['army']

        for army in own_armies:
            ai_my_army = AI_Army()
            self.copy_army_to_ai_army(army, ai_my_army)
            ai_stat.armies.append(ai_my_army)

        for res in res_list:
            ai_r = AI_Resource()
            self.copy_res_to_ai_res(res, ai_r)
            ai_stat.resources.append(ai_r)

        for sc in t_discovered:
            ai_tile = AI_Tile()
            self.copy_tile_to_ai_tile(sc, ai_tile)
            ai_stat.tiles_discovered.append(ai_tile)

        for w in t_walkable:
            ai_tile = AI_Tile()
            self.copy_tile_to_ai_tile(w, ai_tile)
            ai_stat.tiles_walkable.append(ai_tile)

        for b in own_buildings:
            ai_bld = AI_Building()
            self.copy_building_to_ai_building(b, ai_bld)
            ai_stat.own_buildings.append(ai_bld)

        for e_b in enemy_buildings:
            ai_bld = AI_Building()
            self.copy_building_to_ai_building(e_b[0], ai_bld)
            ai_bld.owner = e_b[1]
            ai_stat.enemy_buildings.append(ai_bld)

        for e_a in enemy_armies:
            ai_e = AI_Army()
            self.copy_army_to_ai_army(e_a[0], ai_e)
            ai_e.owner = e_a[1]
            ai_stat.enemy_armies.append(ai_e)

        for a in aggressions:
            ai_stat.aggressions.add(a)

    def do_a_move(self, ai_stat: AI_GameStatus, move:AI_Move, player_id):
        self.dict_of_ais[player_id].do_move(ai_stat, move)

    def query_ai(self, query, arg, player_id) -> str:
        if query == "diplo":
            return self.dict_of_ais[player_id].diplomacy.get_diplomatic_value_of_player(arg)
        elif query == "state":
            return self.dict_of_ais[player_id].get_state_as_str()
        else:
            error("WRONG QUERY")

