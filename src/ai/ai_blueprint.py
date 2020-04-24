from dataclasses import dataclass
from typing import Callable, Tuple, List, Union

from src.ai.AI_MapRepresentation import AI_Building, AI_Army, Tile
from src.misc.game_constants import DiploEventType, error, Priority, UnitType, BuildingType
from src.misc.game_logic_misc import Logger


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
    def __init__(self, name, other_players_ids: [int]):
        self.name = name
        self.diplomacy: AI_Diplo = AI_Diplo(other_players_ids)
        print("AI (" + str(name) + ") is running")

    def do_move(self, ai_state, move):
        raise NotImplementedError("Please Implement this method")




#class NonPlayerAI(AI):
#    def __init__(self, name: str, other_players_ids: [int]):
#        super().__init__(name, other_players_ids)
#