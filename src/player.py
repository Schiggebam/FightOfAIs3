import arcade
from typing import Set
from src.game_accessoires import Army
from src.misc.building import Building
from src.hex_map import Hexagon
from src.misc.game_constants import BuildingType


class Player:
    class Player_Colour:
        YELLOW = 0
        TEAL = 1
        RED = 2

        @staticmethod
        def get_type_from_strcode(str_code: str):
            if str_code == "yellow":
                return Player.Player_Colour.YELLOW
            elif str_code == "red":
                return Player.Player_Colour.RED
            elif str_code == "teal":
                return Player.Player_Colour.TEAL
            return -1

        @staticmethod
        def player_colour_to_arcade_colour(colour: int) -> arcade.Color:
            if colour == Player.Player_Colour.YELLOW:
                return arcade.color.YELLOW
            elif colour == Player.Player_Colour.TEAL:
                return arcade.color.PALE_BLUE
            elif colour == Player.Player_Colour.RED:
                return arcade.color.RED

        @staticmethod
        def get_colour_code(colour: int) -> str:
            if colour == Player.Player_Colour.YELLOW:
                return 'y'
            elif colour == Player.Player_Colour.TEAL:
                return 't'
            elif colour == Player.Player_Colour.RED:
                return 'r'
            return 'no_colour'

    tot_player = 0                  # keeps track of the total amount of players (redundant to the length of the player list)
    def __init__(self, name: str, id: int, colour_str: str, spawn_loc: (int, int), ai_str: str):
        self.name = name
        self.id: int = id
        self.colour = Player.Player_Colour.get_type_from_strcode(colour_str)
        self.colour_code = Player.Player_Colour.get_colour_code(self.colour)
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
        # self.army = None
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