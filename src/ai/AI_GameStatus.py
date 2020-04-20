from typing import Set, Tuple, Optional, Union, List, Any

from src.ai.AI_MapRepresentation import Map, AI_Player, AI_Opponent
from src.misc.game_constants import error, UnitType, BuildingType, MoveType, UnitCost


class AI_Move:
    def __init__(self):
        self.move_type: Optional[MoveType] = None
        self.doMoveArmy: bool = False
        self.loc: Tuple[int, int] = (0, 0)
        self.type: Union[BuildingType, UnitType, None] = None
        self.info: List[Any] = []  # currently only for the associated tiles
        self.move_army_to: Tuple[int, int] = (-1, -1)
        self.str_rep_of_action: str = ""  # just for printing
        self.info_at_tile: List[Tuple[Tuple[int, int], str]] = []  # a list of tuples ((x, y), "str")



class AI_GameStatus:
    def __init__(self):
        self.turn_nr: int = -1
        self.costScout: int = -1
        self.costBuildS1: int = -1
        self.costBuildS2: int = -1
        self.costBuildFarm: int = -1
        self.costBuildRacks: int = -1
        self.costBuildC1: int = -1
        self.costBuildC2: int = -1
        self.costBuildC3: int = -1
        self.costUnitBS: Optional[UnitCost] = None  # cost in resources, culture and population
        self.costUnitKn: Optional[UnitCost] = None
        self.costUnitMe: Optional[UnitCost] = None
        self.aggressions: Set[int] = set()
        self.map: Optional[Map] = None
        self.me: Optional[AI_Player] = None
        self.opponents: Optional[List[AI_Opponent]] = None

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


    def create_ai_status(self, ai_stat: AI_GameStatus, turn_nr,
                         costs, ai_map: Map, me: AI_Player, opponents: List[AI_Opponent]):
        ai_stat.turn_nr = turn_nr
        ai_stat.map = ai_map
        ai_stat.me = me
        ai_stat.opponents = opponents

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

    def do_a_move(self, ai_stat: AI_GameStatus, move: AI_Move, player_id):
        self.dict_of_ais[player_id].do_move(ai_stat, move)

    def query_ai(self, query, arg, player_id) -> str:
        if query == "diplo":
            return self.dict_of_ais[player_id].diplomacy.get_diplomatic_value_of_player(arg)
        elif query == "state":
            return self.dict_of_ais[player_id].get_state_as_str()
        else:
            error("WRONG QUERY")
