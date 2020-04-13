from typing import Set
from src.game_accessoires import Army
from src.misc.building import Building
from src.hex_map import Hexagon
from src.misc.game_constants import BuildingType, PlayerColour, UnitType


class Player:

    tot_player = 0                  # keeps track of the total amount of players (redundant to the length of the player list)
    def __init__(self, name: str, id: int, colour_str: str, spawn_loc: (int, int), ai_str: str):
        self.name = name
        self.id: int = id
        self.colour: PlayerColour = PlayerColour.get_type_from_strcode(colour_str)
        self.colour_code: str = PlayerColour.get_colour_code(self.colour)
        self.spaw_loc: (int, int) = spawn_loc
        self.init_army_loc: (int, int) = (0,0)
        self.ai_str = ai_str
        Player.tot_player = Player.tot_player + 1
        self.amount_of_resources = 0
        self.food = 0
        self.income = 0
        self.culture = 0
        self.has_lost = False
        self.buildings: [Building] = []
        self.discovered_tiles: Set[Hexagon] = set()
        self.armies: [Army] = []
        self.is_barbaric = False
        self.is_villager = False
        self.attacked_set: Set[int] = set()     # contains a set of player ids and locations which attacked last round

    def get_initial_building_type(self):
        """returns the initial building the player will spawn with"""
        if self.is_barbaric:
            return BuildingType.CAMP_1
        elif self.is_villager:
            return BuildingType.VILLAGE
        return BuildingType.HUT

    def get_initial_unit_type(self):
        """returns the type of initial unit"""
        if self.is_barbaric:
            return UnitType.BABARIC_SOLDIER
        elif self.is_villager:
            return UnitType.KNIGHT
        return UnitType.MERCENARY

    def get_population_limit(self) -> int:
        value = 0
        for b in self.buildings:
            value = value + b.grant_pop
        return value

    def get_population(self) -> int:
        value = 0
        for a in self.armies:
            value = value + a.get_population()
        return value