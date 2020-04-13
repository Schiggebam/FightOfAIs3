
import sys

######################
### Game Constants ###
######################
from enum import Enum, IntEnum
from typing import Union

import arcade

CAMERA_SENSITIVITY = 250

########################
### Helper functions ###
########################
def hint(msg: str):
    print("[HINT] : " + msg)


ERRORS_ARE_FATAL = False


def error(msg: str):
    if ERRORS_ARE_FATAL:
        print("[FATAL]: " + msg)
        sys.exit(-1)
    else:
        print("[ERROR]: " + msg)


def start_progress(title):
    global progress_x
    sys.stdout.write(title + ": [" + "-"*40 + "]" + chr(8)*41)
    sys.stdout.flush()
    progress_x = 0

def progress(x):
    global progress_x
    x = int(x * 40 // 100)
    sys.stdout.write("#" * (x - progress_x))
    sys.stdout.flush()
    progress_x = x

def end_progress():
    sys.stdout.write("#" * (40 - progress_x) + "]\n")
    sys.stdout.flush()



#####################
### TYPES ###########
#####################


# logs
class LogType:
    BATTLE_ARMY_VS_ARMY = 900
    BATTLE_ARMY_VS_BUILDING = 901
    DIPLO_ENEMY_BUILDING_SCOUTED = 902

#ground
class GroundType:
    GRASS = 0
    WATER_DEEP = 1
    STONE = 2
    OTHER = 3

    @staticmethod
    def get_type_from_strcode(str_code: str):
        if str_code == "gr" or str_code == "gc":
            return GroundType.GRASS
        elif str_code == "st":
            return GroundType.STONE
        elif str_code == "wd":
            return GroundType.WATER_DEEP
        return GroundType.OTHER


# buildings
class BuildingType:
    HUT = 20
    FARM = 21
    CAMP_1 = 22
    CAMP_2 = 23
    CAMP_3 = 24
    VILLA = 25
    VILLAGE = 26
    BARRACKS = 27

    @staticmethod
    def get_type_from_strcode(str_code: str) -> int:
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
        return -1


class ResourceType:
    ROCK = 10
    GOLD = 11
    FOREST = 12

    @staticmethod
    def get_type_from_strcode(str_code: str):
        if str_code == "r1":
            return ResourceType.ROCK
        elif str_code == "g1":
            return ResourceType.GOLD
        elif str_code == "f1":
            return ResourceType.FOREST
        return -1


class DiploEventType:
    TYPE_ENEMY_ARMY_INVADING = 100
    TYPE_ENEMY_BUILDING_SCOUTED = 101


class PlayerColour:
    YELLOW = 0
    TEAL = 1
    RED = 2
    BLUE = 3
    GREEN = 4
    PINK = 5

    @staticmethod
    def get_type_from_strcode(str_code: str):
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
        return -1

    @staticmethod
    def player_colour_to_arcade_colour(colour) -> arcade.Color:
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
    def get_colour_code(colour: int) -> str:
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

###############
### STATES ####
###############

class BuildingState:
    UNDER_CONSTRUCTION = 30
    ACTIVE = 31
    DESTROYED = 32
