from __future__ import annotations

import inspect
import sys

######################
### Game Constants ###
######################
from dataclasses import dataclass
from enum import Enum

import arcade

#####################
### Game Settings ###
#####################

CAMERA_SENSITIVITY = 250
NUM_Z_LEVELS = 5

Z_MAP = 1
Z_AUX = 2
Z_FLYING = 4
Z_GAME_OBJ = 3

ERRORS_ARE_FATAL = False
DEBUG = True
DETAILED_DEBUG_INFO = 1     # 0: no info, 1: includes calling class, 2: includes calling method
ENABLE_KEYFRAME_ANIMATIONS = False

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


########################
### Helper functions ###
########################
def get_caller() -> str:
    stack = inspect.stack()
    the_class = stack[2][0].f_locals["self"].__class__.__name__
    the_method = stack[2][0].f_code.co_name
    if DETAILED_DEBUG_INFO == 2:
        return "(Class: {} Function: {})".format(the_class, the_method)
    elif DETAILED_DEBUG_INFO == 1:
        return "(Class: {})".format(the_class)


def debug(msg: str, colour=0):
    if not DEBUG:
        return
    caller = ""
    if DETAILED_DEBUG_INFO != 0:
        caller = get_caller()
    c = bcolors.OKBLUE
    if colour == 1:
        c = bcolors.OKGREEN
    print("[DEBUG]{} : {}{}{}".format(caller, c, str(msg), bcolors.ENDC))


def hint(msg: str):
    caller = ""
    if DETAILED_DEBUG_INFO:
        caller = get_caller()
    print("[HINT]{} : {}{}{}".format(caller, bcolors.WARNING, str(msg), bcolors.ENDC))


def error(msg: str):
    caller = ""
    if DETAILED_DEBUG_INFO:
        try:
            caller = get_caller()
        except KeyError:
            print("unable to get caller object - possible if it is called from 'self'")
    if ERRORS_ARE_FATAL:
        print("[FATAL]{} : {}{}{}".format(caller, bcolors.FAIL, str(msg), bcolors.ENDC))
        sys.exit(-1)
    else:
        print("[ERROR]{} : {}{}{}".format(caller, bcolors.FAIL, str(msg), bcolors.ENDC))


def start_progress(title):
    global progress_x
    sys.stdout.write(title + ": [" + "-" * 10 + "]" + chr(8) * 11)
    sys.stdout.flush()
    progress_x = 0


def progress(x):
    global progress_x
    x = int(x * 10 // 100)
    sys.stdout.write("#" * (x - progress_x))
    sys.stdout.flush()
    progress_x = x


def end_progress():
    sys.stdout.write("#" * (10 - progress_x) + "]\n")
    sys.stdout.flush()


#####################
### TYPES ###########
#####################

class Priority(Enum):
    P_NO = 0
    P_LOW = 1
    P_MEDIUM = 2
    P_HIGH = 3
    P_CRITICAL = 4

    @staticmethod
    def increase(p: Priority):
        if p == Priority.P_NO:
            return Priority.P_LOW
        elif p == Priority.P_LOW:
            return Priority.P_MEDIUM
        elif p == Priority.P_MEDIUM:
            return Priority.P_HIGH
        return Priority.P_CRITICAL

    @staticmethod
    def decrease(p: Priority):
        if p == Priority.P_CRITICAL:
            return Priority.P_HIGH
        elif p == Priority.P_HIGH:
            return Priority.P_MEDIUM
        elif p == Priority.P_MEDIUM:
            return Priority.P_LOW
        return Priority.P_NO

class PlayerType(Enum):
    AI = 0
    BARBARIC = 1
    VILLAGER = 2
    HUMAN = 3

    @staticmethod
    def get_type_from_strcode(str_code: str) -> PlayerType:
        if str_code == "barbaric":
            return PlayerType.BARBARIC
        elif str_code == "villager":
            return PlayerType.VILLAGER
        elif str_code == "human":
            return PlayerType.HUMAN
        else:
            return PlayerType.AI

# logs
class LogType(Enum):
    BATTLE_ARMY_VS_ARMY = 900
    BATTLE_ARMY_VS_BUILDING = 901
    DIPLO_ENEMY_BUILDING_SCOUTED = 902
    NOTIFICATION = 903


# ground
class GroundType(Enum):
    GRASS = 0
    WATER_DEEP = 1
    STONE = 2
    OTHER = 3
    MIXED = 4  # currently a workaround for mixed tiles which are walkable and buildable

    # (they have no associated str_code)

    @staticmethod
    def get_type_from_strcode(str_code: str) -> GroundType:
        if str_code == "gr" or str_code == "gc":
            return GroundType.GRASS
        elif str_code == "st":
            return GroundType.STONE
        elif str_code == "wd":
            return GroundType.WATER_DEEP
        return GroundType.OTHER


# buildings
class BuildingType(Enum):
    HUT = 20
    FARM = 21
    CAMP_1 = 22
    CAMP_2 = 23
    CAMP_3 = 24
    VILLA = 25
    VILLAGE = 26
    BARRACKS = 27
    OTHER_BUILDING = 29

    @staticmethod
    def get_type_from_strcode(str_code: str) -> BuildingType:
        if str_code == "s1":
            return BuildingType.HUT
        elif str_code == "s2":
            return BuildingType.VILLA
        elif str_code == "fa":
            return BuildingType.FARM
        elif str_code == "c1":
            return BuildingType.CAMP_1
        elif str_code == "c2":
            return BuildingType.CAMP_2
        elif str_code == "c3":
            return BuildingType.CAMP_3
        elif str_code == "v1":
            return BuildingType.VILLAGE
        elif str_code == "br":
            return BuildingType.BARRACKS
        return BuildingType.OTHER_BUILDING


class ResourceType(Enum):
    ROCK = 10
    GOLD = 11
    FOREST = 12
    OTHER_RESOURCE = 19

    @staticmethod
    def get_type_from_strcode(str_code: str) -> ResourceType:
        if str_code == "r1":
            return ResourceType.ROCK
        elif str_code == "g1":
            return ResourceType.GOLD
        elif str_code == "f1":
            return ResourceType.FOREST
        return ResourceType.OTHER_RESOURCE


class DiploEventType(Enum):
    TYPE_ENEMY_ARMY_INVADING = 100
    TYPE_ENEMY_BUILDING_SCOUTED = 101
    ENEMY_BUILDING_IN_CLAIMED_ZONE = 102
    ENEMY_ARMY_INVADING_CLAIMED_ZONE = 103


class UnitType(Enum):
    KNIGHT = 0
    MERCENARY = 1
    BABARIC_SOLDIER = 2

    @staticmethod
    def get_type_from_strcode(str_code: str):
        if str_code == "unit_a":
            return UnitType.MERCENARY
        elif str_code == "unit_b":
            return UnitType.KNIGHT
        elif str_code == "unit_c":
            return UnitType.BABARIC_SOLDIER
        return -1


class PlayerColour(Enum):
    YELLOW = 60
    TEAL = 61
    RED = 62
    BLUE = 63
    GREEN = 64
    PINK = 65
    NO_COLOUR = 69

    @staticmethod
    def get_type_from_strcode(str_code: str) -> PlayerColour:
        if str_code == "yellow":
            return PlayerColour.YELLOW
        elif str_code == "red":
            return PlayerColour.RED
        elif str_code == "teal":
            return PlayerColour.TEAL
        elif str_code == "pink":
            return PlayerColour.PINK
        elif str_code == "green":
            return PlayerColour.GREEN
        elif str_code == "blue":
            return PlayerColour.BLUE
        return PlayerColour.NO_COLOUR

    @staticmethod
    def player_colour_to_arcade_colour(colour: PlayerColour) -> arcade.Color:
        if colour == PlayerColour.YELLOW:
            return arcade.color.YELLOW
        elif colour == PlayerColour.TEAL:
            return arcade.color.PALE_BLUE
        elif colour == PlayerColour.RED:
            return arcade.color.RED
        elif colour == PlayerColour.PINK:
            return arcade.color.PINK
        elif colour == PlayerColour.BLUE:
            return arcade.color.BLUE
        elif colour == PlayerColour.GREEN:
            return arcade.color.GREEN

    @staticmethod
    def get_colour_code(colour: PlayerColour) -> str:
        if colour == PlayerColour.YELLOW:
            return 'yellow'
        elif colour == PlayerColour.TEAL:
            return 'teal'
        elif colour == PlayerColour.RED:
            return 'red'
        elif colour == PlayerColour.PINK:
            return 'pink'
        elif colour == PlayerColour.BLUE:
            return 'blue'
        elif colour == PlayerColour.GREEN:
            return 'green'
        return 'no_colour'


class MoveType(Enum):
    """ does not required any additional fields to be set"""
    DO_NOTHING = 230
    """requires the 'loc' field to be set, indicating the location of the hexagon to be scouted"""
    DO_SCOUT = 231
    """requires the 'loc' field to be set, indicating the location of the building to be upgraded"""
    DO_UPGRADE_BUILDING = 232
    """requires the 'loc' field to be set, indicating the location of the building site
    also, requires the 'type' field to specify the Type of the building"""
    DO_BUILD = 233
    """requires the 'type' field to be set, indicating the UnitType"""
    DO_RECRUIT_UNIT = 234
    """requires the 'loc' field to be set, indicating the hexagon were the new army should appear"""
    DO_RAISE_ARMY = 235

###################
### Dataclasses ###
###################
@dataclass
class UnitCost:
    resources: int
    culture: int
    population: int


###############
### STATES ####
###############

class BuildingState(Enum):
    UNDER_CONSTRUCTION = 30
    ACTIVE = 31
    DESTROYED = 32
