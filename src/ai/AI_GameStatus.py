from typing import Set, Tuple, Optional, Union, List, Any, Dict

from src.ai.AI_MapRepresentation import Map, AI_Player, AI_Opponent
from src.misc.game_constants import error, UnitType, BuildingType, MoveType, UnitCost


"""This file (together with AI_map_representation) handles the interaction between game and AI/HI"""


class AI_Move:
    """
    Wrapper class to return the information the AI / HI can give to the game_logic.
    It is not necessary to set all fields, it depends on the move_type
    -> refer to class MoveType for hints on which move_type requires what fields to be set
    """
    def __init__(self):
        """specifies the nature of the move"""
        self.move_type: Optional[MoveType] = None
        """if set to True, the army should be moved"""
        self.doMoveArmy: bool = False
        """is only necessary if doMoveArmy == True.
         If so, this field should load the offset coordiantes of the destination hexagon"""
        self.move_army_to: Tuple[int, int] = (-1, -1)
        """For move_types like DoBuild, DoUpgrade.. one has to specify the game_obj.
        Since there can only be one game obecjt (army, building etc.) per hexagon,
         it is identified by the offset coordinates, given by this field"""
        self.loc: Tuple[int, int] = (0, 0)
        """In case of recruiting a unit or building, this field holds the Unit/BuildingType"""
        self.type: Union[BuildingType, UnitType, None] = None
        """addidional args, currently only used to transfer a list of offset_c. to specify 
        where to put the fields in case a farm has to be built"""
        self.info: List[Any] = []  # currently only for the associated tiles

        """Debug/UI"""
        self.str_rep_of_action: str = ""  # just for printing
        """Debug"""
        self.info_at_tile: List[Tuple[Tuple[int, int], str]] = []  # a list of tuples ((x, y), "str")



class AI_GameStatus:
    """Wrapper Class. It conains all information which is available to the AI for a move"""
    def __init__(self):
        """Current turn number"""
        self.turn_nr: int = -1
        """cost in resources of scouting a hexagon"""
        self.costScout: int = -1
        """cost in resouces to build a hut """
        self.costBuildS1: int = -1
        """cost in resources to build a villa (currently not in use)"""
        self.costBuildS2: int = -1
        """cost in resources to build a farm"""
        self.costBuildFarm: int = -1
        """cost in resouces to build a barracks"""
        self.costBuildRacks: int = -1
        """cost in rescoures to build a 'camp level 1'"""
        self.costBuildC1: int = -1
        """cost in rescoures to build a 'camp level 2'"""
        self.costBuildC2: int = -1
        """cost in rescoures to build a 'camp level 3'"""
        self.costBuildC3: int = -1
        """cost in UnitCost to build a 'barbaric soldier'"""
        self.costUnitBS: Optional[UnitCost] = None  # cost in resources, culture and population
        """cost in UnitCost to build a 'knight'"""
        self.costUnitKn: Optional[UnitCost] = None
        """cost in UnitCost to build a 'mercenary'"""
        self.costUnitMe: Optional[UnitCost] = None
        """holds the construction cost of all building types in a Dict"""
        self.cost_building_construction: Dict[BuildingType, int] = {}
        """holds the unitcost of all unit types in a Dict"""
        self.cost_unit_recruitment: Dict[UnitType, UnitCost] = {}
        """contains an object from type Map. This hold all information about the current map-view:
         buildings, armies, scouted tiles, scoutable tiles, buildable tiles etc.
         in easy-to-access lists"""
        self.map: Optional[Map] = None
        """information about the player, like current resouces, culture, poplation etc."""
        self.me: Optional[AI_Player] = None
        """the information which is available to the AI of their opponents"""
        self.opponents: Optional[List[AI_Opponent]] = None

    def clear(self):
        pass


class AI_GameInterface:
    def __init__(self):
        from src.ai.ai_blueprint import AI
        self.dict_of_ais: Dict[int, AI] = {}
        print("AI Game interface has been initialized")

    def launch_AI(self, id: int, ai_str: str, other_players: [int]):
        from src.ai.ai_npc import AI_NPC
        from src.ai.AI_Macedon import AI_Mazedonian
        if ai_str == "cultivated":
            self.dict_of_ais[id] = AI_Mazedonian(ai_str, id, other_players)
        elif ai_str == "expansionist":
            self.dict_of_ais[id] = AI_Mazedonian(ai_str, id, other_players)
        elif ai_str == "barbaric":
            self.dict_of_ais[id] = AI_NPC(id, other_players, AI_NPC.Script.BARBARIC_HOSTILE)
        elif ai_str == "villager":
            self.dict_of_ais[id] = AI_NPC(id, other_players, AI_NPC.Script.VILLAGER)


    @staticmethod
    def create_ai_status(ai_stat: AI_GameStatus, turn_nr,
                         costs, ai_map: Map, me: AI_Player, opponents: List[AI_Opponent],
                         building_costs: Dict[BuildingType, int],
                         unit_cost: Dict[UnitType, UnitCost]):
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
        # TODO costs to dict:
        ai_stat.cost_building_construction = building_costs
        ai_stat.cost_unit_recruitment = unit_cost


    def do_a_move(self, ai_stat: AI_GameStatus, move: AI_Move, player_id):
        self.dict_of_ais[player_id].do_move(ai_stat, move)
        # performance logging
        from src.ai.performance import ScoreSpentResources
        score = ScoreSpentResources.evaluate(ai_stat.map)
        from src.ai.performance import PerformanceLogger
        PerformanceLogger.log_performance_file(ai_stat.turn_nr, ai_stat.me.id, score)

    def query_ai(self, query, arg, player_id) -> str:
        if query == "diplo":
            return str(self.dict_of_ais[player_id].diplomacy.get_diplomatic_value_of_player(arg))
        elif query == "state":
            return self.dict_of_ais[player_id].get_state_as_str()
        else:
            error("WRONG QUERY")

    def get_dump(self, player_id) -> str:
        return self.dict_of_ais[player_id].get_dump()
