from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Tuple, List, Union, Optional, Dict
from enum import Enum

from src.ai import AI_Toolkit
from src.ai.AI_MapRepresentation import AI_Building, AI_Army, Tile
from src.misc.game_constants import DiploEventType, error, Priority, UnitType, BuildingType, debug
from src.misc.game_logic_misc import Logger


class CardinalDirection(Enum):
    """Cardinal directions in a hexagonal system (6)"""
    North = 0
    NorthEast = 1
    SouthEast = 2
    South = 3
    SouthWest = 4
    NorthWest = 5



@dataclass
class WaitOption:
    score: Priority
    weighted_score: float = 0

@dataclass
class UpgradeOption:
    type: BuildingType
    site: Tuple[int, int]
    score: Priority
    weighted_score: float = 0


@dataclass
class BuildOption:
    type: BuildingType
    site: Tuple[int, int]
    associated_tiles: List[Tuple[int, int]]
    score: Priority
    cardinal_direction: Optional[List[CardinalDirection]] = None
    threat_level: Optional[ThreatLevel] = None
    weighted_score: float = 0


@dataclass
class RecruitmentOption:
    type: UnitType
    score: Priority
    weighted_score: float = 0


@dataclass
class RaiseArmyOption:
    site: Tuple[int, int]
    score: Priority
    weighted_score: float = 0


@dataclass
class ScoutingOption:
    site: Tuple[int, int]
    score: Priority             # Caution changed this to Priority!!
    weighted_score: float = 0


@dataclass()
class ArmyMovementOption:
    target: Union[AI_Building, AI_Army, Tile]
    score: Priority
    next_step: Tuple[int, int]
    weighted_score: float = 0


class ThreatLevel(Enum):
    SECURE = -1
    NO_RISK = 0
    LOW_RISK = 1
    MEDIUM_RISK = 2
    HIGH_RISK = 3

    @staticmethod
    def increase(t: ThreatLevel) -> ThreatLevel:
        """Increase the threat level by one"""
        return ThreatLevel(min(3, t.value + 1))

    @staticmethod
    def decrease(t: ThreatLevel) -> ThreatLevel:
        """Decrease the threat level by one"""
        return ThreatLevel(max(-1, t.value - 1))

    @staticmethod
    def avg(t1: ThreatLevel, t2: ThreatLevel) -> ThreatLevel:
        return ThreatLevel(round((t1.value + t2.value) / 2))


class Compass:
    def __init__(self, center_tile: Tile, book=None):
        self.center_tile: Tile = center_tile
        if book is None:
            self.book: Dict[CardinalDirection, ThreatLevel] = {}
            for cd in CardinalDirection:
                self.book[cd] = ThreatLevel.NO_RISK
        else:
            self.book = book

    def get_threat_level(self, t: Tile) -> ThreatLevel:
        cd = self.get_cardinal_direction_obj(t, self.center_tile)
        if len(cd) == 1:
            return self.book[cd[0]]
        elif len(cd) == 2:
            return ThreatLevel.avg(self.book[cd[0]], self.book[cd[1]])

    def raise_threat_level(self, t: Tile):
        for cd in self.get_cardinal_direction_obj(t, self.center_tile):
            self.book[cd] = ThreatLevel.increase(self.book[cd])

    def lower_threat_level(self, t: Tile):
        for cd in self.get_cardinal_direction_obj(t, self.center_tile):
            self.book[cd] = ThreatLevel.decrease(self.book[cd])

    @staticmethod
    def get_cardinal_direction_obj(tile: Tile, base: Tile) -> List[CardinalDirection]:
        """wrapper function for get_cardinal_direction(...)"""
        cc1 = AI_Toolkit.offset_to_cube_coord(tile)
        cc2 = AI_Toolkit.offset_to_cube_coord(base)
        return Compass.get_cardinal_direction(cc1, cc2)

    @staticmethod
    def get_cardinal_direction(tile: Tuple[int, int, int], base: Tuple[int, int, int]) -> List[CardinalDirection]:
        """get the cardinal direction of the cube coordinates of a tile with respect to a base
        function may return two adjacent CDs. IN This case, the tile is placed on the border"""
        x_normal = tile[0] - base[0]
        y_normal = tile[1] - base[1]
        z_normal = tile[2] - base[2]
        if x_normal + y_normal + z_normal != 0:
            error("error in CD")
        ret = []
        if x_normal <= 0 and y_normal > 0 and z_normal <= 0:
            ret.append(CardinalDirection.SouthWest)
        if x_normal >= 0 and y_normal >= 0 and z_normal < 0:
            ret.append(CardinalDirection.South)
        if x_normal > 0 and y_normal <= 0 and z_normal <= 0:
            ret.append(CardinalDirection.SouthEast)
        if x_normal >= 0 and y_normal < 0 and z_normal >= 0:
            ret.append(CardinalDirection.NorthEast)
        if x_normal <= 0 and y_normal <= 0 and z_normal > 0:
            ret.append(CardinalDirection.North)
        if x_normal < 0 and y_normal >= 0 and z_normal >= 0:
            ret.append(CardinalDirection.NorthWest)
        return ret

# a = AI_Toolkit.offset_to_cube_xy(7, 10)
# b = AI_Toolkit.offset_to_cube_xy(10, 10)
# compass = Compass(None)
# print(compass.get_cardinal_direction(a, b))

Option = Union[BuildOption, RecruitmentOption, ScoutingOption, WaitOption, RaiseArmyOption, UpgradeOption]


@dataclass
class Weight:
    condition: Callable[..., bool]
    weight: float

class AI_Diplo:

    DIPLO_BASE_VALUE = float(5)
    LOGGED_EVENTS = (DiploEventType.ENEMY_BUILDING_IN_CLAIMED_ZONE,
                     DiploEventType.ENEMY_ARMY_INVADING_CLAIMED_ZONE)

    class AI_DiploEvent:


        def __init__(self, target_id: int, rel_change: float, lifetime: int, event: DiploEventType, description: str):
            self.rel_change = rel_change
            self.lifetime = lifetime
            self.lifetime_max = lifetime
            self.description = description
            self.loc = (-1, -1)
            self.event: DiploEventType = event
            self.target_id: int = target_id

        def add_loc(self, loc: (int, int)):
            self.loc = loc

    def __init__(self, other_players: [int]):
        self.diplomacy: [[int, float]] = []
        self.events: [AI_Diplo.AI_DiploEvent] = []
        for o_p in other_players:
            self.diplomacy.append([o_p, float(AI_Diplo.DIPLO_BASE_VALUE)])

    def add_event(self, target_id: int, loc: (int, int), event: DiploEventType, rel_change: float, lifetime: int,
                  player_name:str):
        # check if this exists already:
        for e in self.events:
            if e.target_id == target_id and e.event == event and e.loc == loc:
                e.lifetime = e.lifetime_max
                return
        # otherwise, if event does not exist, yet
        event_str = ""
        if event == DiploEventType.TYPE_ENEMY_BUILDING_SCOUTED:
            event_str = "Enemy building scouted at: " + str(loc)
        elif event == DiploEventType.TYPE_ENEMY_ARMY_INVADING:
            event_str = "Enemy army scouted at: " + str(loc)
        elif event == DiploEventType.ENEMY_BUILDING_IN_CLAIMED_ZONE:
            event_str = "Enemy building is located in claimed zone"
        elif event == DiploEventType.ENEMY_ARMY_INVADING_CLAIMED_ZONE:
            event_str = "Enemy army is invading claimed zone"
        elif event == DiploEventType.ATTACKED_BY_FACTION:
            event_str = "Attacked by Faction"
        else:
            error("Unknown event!")
        ai_event = AI_Diplo.AI_DiploEvent(target_id, rel_change, lifetime, event, event_str)
        ai_event.add_loc(loc)
        self.events.append(ai_event)
        if event in AI_Diplo.LOGGED_EVENTS:
            Logger.log_diplomatic_event(event, rel_change, loc, lifetime, player_name)

    def calc_round(self):
        for diplo in self.diplomacy:
            diplo[1] = AI_Diplo.DIPLO_BASE_VALUE
            for e in self.events:
                if e.target_id == diplo[0]:
                    diplo[1] = diplo[1] + e.rel_change
                    e.lifetime = e.lifetime - 1

        to_be_removed = []
        for e in self.events:
            if e.lifetime <= 0:
                to_be_removed.append(e)
        for tbr in to_be_removed:
            self.events.remove(tbr)

    def get_diplomatic_value_of_player(self, player_id: int) -> float:
        for d in self.diplomacy:
            if d[0] == player_id:
                return d[1]


class AI:
    """Superclass to a AI. Any AI must implement at least do_move and fill the move object"""

    def __init__(self, name, other_players_ids: [int]):
        """the name of the ai"""
        self.name = name
        """each ai can do (not required) diplomacy"""
        self.diplomacy: AI_Diplo = AI_Diplo(other_players_ids)
        """this is used for development.
        instead of printing all AI info to the console, one can use the dump to display stats in-game"""
        self.dump: str = ""
        debug("AI (" + str(name) + ") is running")

    def do_move(self, ai_state, move):
        """upon completion of this method, the AI should have decided on its move"""
        raise NotImplementedError("Please Implement this method")

    def get_state_as_str(self) -> str:
        pass

    def _dump(self, d: str):
        self.dump += d + "\n"
