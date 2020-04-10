##############
### Logger ###
##############
import sys


def hint(msg: str):
    print("[HINT] : " + msg)


ERRORS_ARE_FATAL = False


def error(msg: str):
    if ERRORS_ARE_FATAL:
        print("[FATAL]: " + msg)
        sys.exit(-1)
    else:
        print("[ERROR]: " + msg)


#####################
### TYPES ###########
#####################


# logs
class LogType:
    BATTLE_ARMY_VS_ARMY = 900
    BATTLE_ARMY_VS_BUILDING = 901
    DIPLO_ENEMY_BUILDING_SCOUTED = 902


# buildings
class BuildingType:
    HUT = 20
    FARM = 21
    CAMP_1 = 22
    CAMP_2 = 23
    CAMP_3 = 24
    VILLA = 25
    VILLAGE = 26

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

###############
### STATES ####
###############

class BuildingState:
    UNDER_CONSTRUCTION = 30
    ACTIVE = 31
    DESTROYED = 32
