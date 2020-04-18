from typing import Set, Tuple, Optional, Union

from src.ai.AI_MapRepresentation import Map
from src.misc.game_constants import error, UnitType, BuildingType


class AI_Move:
    def __init__(self):
        self.doNothing = False
        self.doBuild = False
        self.doScout = False
        self.doUpgrade = False
        self.doUpArmy = False  # TODO get rid of this field -> doRecruitUnit
        # TODO (also: should be same field as recruitArmy)
        self.doMoveArmy = False
        self.doRecruitArmy = False
        self.doRecruitUnit = False
        self.loc = (0, 0)
        self.type: Union[BuildingType, UnitType, None] = None
        self.info = []  # currently only for the associated tiles
        self.move_army_to = (-1, -1)
        self.str_rep_of_action = ""  # just for printing
        self.info_at_tile = []  # a list of tuples ((x, y), "str")

    def check_validity(self):
        return self.doBuild + self.doNothing + self.doScout == 1



class AI_GameStatus:
    def __init__(self):
        self.turn_nr: int = -1
        self.player_id: int = -1
        self.player_food: int = 0
        self.player_resources = 0
        self.player_culture = 0
        # self.tiles_buildable: List[AI_Tile] = []
        # self.tiles_scoutable: List[AI_Tile] = []
        # self.tiles_discovered: List[AI_Tile] = []
        # self.tiles_walkable: List[AI_Tile] = []
        self.costScout: int = -1
        self.costBuildS1: int = -1
        self.costBuildS2: int = -1
        self.costBuildFarm: int = -1
        self.costBuildRacks: int = -1
        self.costBuildC1: int = -1
        self.costBuildC2: int = -1
        self.costBuildC3: int = -1
        self.costUnitBS: Tuple[int, int, int] = (-1, -1, -1)  # cost in resources, culture and population
        self.costUnitKn: Tuple[int, int, int] = (-1, -1, -1)  # TODO: transform this to a dataclass
        self.costUnitMe: Tuple[int, int, int] = (-1, -1, -1)
        # self.resources: List[AI_Resource] = []
        # self.own_buildings: List[AI_Building] = []
        # self.other_players: List[int] = []
        # self.enemy_buildings: List[AI_Building] = []
        # self.enemy_armies: List[AI_Army] = []
        self.num_of_enemies: int = -1
        # self.armies: List[AI_Army] = []
        self.aggressions: Set[int] = set()
        self.population = 0
        self.population_limit = 0
        self.map: Optional[Map] = None

    def clear(self):
        pass


class AI_GameInterface:
    def __init__(self):
        self.dict_of_ais = {}
        print("AI Game interface has been initialized")

    def launch_AI(self, id: int, ai_str: str, other_players: [int]):
        from src.ai.AI_Barbaric import AI_Barbaric
        from src.ai.AI_Macedon import AI_Mazedonian
        if ai_str == "cultivated":
            self.dict_of_ais[id] = AI_Mazedonian(ai_str, id, other_players)
        elif ai_str == "expansionist":
            self.dict_of_ais[id] = AI_Mazedonian(ai_str, id, other_players)
        elif ai_str == "barbaric":
            self.dict_of_ais[id] = AI_Barbaric(id, other_players)

    # def copy_tile_to_ai_tile(self, t: Hexagon, ai_t: AI_Tile):
    #     ai_t.offset_coordinates = t.offset_coordinates
    #     ai_t.str_code = t.ground.tex_code
    #
    # def copy_res_to_ai_res(self, r: Resource, ai_r: AI_Resource):
    #     ai_r.offset_coordinates = r.tile.offset_coordinates
    #     ai_r.resource_type = r.resource_type
    #     ai_r.amount = r.remaining_amount
    #
    # def copy_building_to_ai_building(self, b: Building, ai_b: AI_Building):
    #     ai_b.offset_coordinates = b.tile.offset_coordinates
    #     ai_b.type = b.building_type
    #     for a in b.associated_tiles:
    #         t = AI_Tile()
    #         self.copy_tile_to_ai_tile(a, t)
    #         ai_b.associated_tiles.append(t)
    #
    # def copy_army_to_ai_army(self, a: Army, ai_a: AI_Army):
    #     ai_a.offset_coordinates = a.tile.offset_coordinates
    #     ai_a.population = a.get_population()
    #     ai_a.knights = a.get_population_by_unit(UnitType.KNIGHT)
    #     ai_a.mercenaries = a.get_population_by_unit(UnitType.MERCENARY)
    #     ai_a.barbaric_soldiers = a.get_population_by_unit(UnitType.BABARIC_SOLDIER)

    def create_ai_status(self, ai_stat: AI_GameStatus, turn_nr,
                         p_id, p_food, p_res, p_cult,
                         costs, num_of_enemies, aggressions: Set[int],
                         pop, pop_limit, ai_map: Map):
        ai_stat.turn_nr = turn_nr
        ai_stat.player_id = p_id
        ai_stat.player_food = p_food
        ai_stat.player_resources = p_res
        ai_stat.player_culture = p_cult
        ai_stat.num_of_enemies = num_of_enemies
        ai_stat.population = pop
        ai_stat.population_limit = pop_limit
        ai_stat.map = ai_map

        ai_stat.costScout = costs['scout']
        ai_stat.costBuildS1 = costs['s1']
        ai_stat.costBuildC1 = costs['c1']
        ai_stat.costBuildC2 = costs['c2']
        ai_stat.costBuildC3 = costs['c3']
        ai_stat.costBuildS2 = costs['s2']
        ai_stat.costBuildRacks = costs['br']
        ai_stat.costBuildFarm = costs['fa']
        ai_stat.costUnitBS = costs['bs']
        ai_stat.costUnitKn = costs['knight']
        ai_stat.costUnitMe = costs['mercenary']

        for a in aggressions:
            ai_stat.aggressions.add(a)

    def do_a_move(self, ai_stat: AI_GameStatus, move: AI_Move, player_id):
        self.dict_of_ais[player_id].do_move(ai_stat, move)

    def query_ai(self, query, arg, player_id) -> str:
        if query == "diplo":
            return self.dict_of_ais[player_id].diplomacy.get_diplomatic_value_of_player(arg)
        elif query == "state":
            return self.dict_of_ais[player_id].get_state_as_str()
        else:
            error("WRONG QUERY")
