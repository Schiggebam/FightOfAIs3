from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Tuple, List, Union, Optional, Dict
from enum import Enum

from src.ai.toolkit import essentials
from src.ai.AI_GameStatus import AI_GameStatus, AI_Move
from src.ai.AI_MapRepresentation import AI_Building, AI_Army, Tile
from src.misc.game_constants import DiploEventType, error, Priority, UnitType, BuildingType, debug, hint, Definitions
from src.misc.game_logic_misc import Logger


class AI_Diplo:
    """
    Example class for inter-player diplomatics. Events are defined in the constants.
    In principle, events have a lifetime, they will last at least this time.
    If the cause of the event persists, the event will also remain active (its lifetime is set to its
    original lifetime. Diplomacy is one-dimensional for now. Thus, an event has a value (rel_change)
    to change the current diplomatic value.
    For future iteration, a multidimensional setup can be imagined for more complex relations
    An event is defined by its location. If the cause of the event moves, it will be triggered again.
    Example a hostile army invades the claimed territory, one can throw an event with lifetime one to track
    the army and to make sure, that no events are accumulated for the same cause.

    IMPORTANT (!): If diplomacy is used, one has to call AI_Diplo.calc_round() per turn (do_move) to update the
    events
    """
    DIPLO_BASE_VALUE = float(5)
    LOGGED_EVENTS = (DiploEventType.ENEMY_BUILDING_IN_CLAIMED_ZONE,
                     DiploEventType.ENEMY_ARMY_INVADING_CLAIMED_ZONE)

    class AI_DiploEvent:
        """ Intern class to handle Events. They are broadcasted to the Logger"""
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

    def __init__(self, other_players: [int], player_name: str):
        self.diplomacy: [[int, float]] = []
        self.events: [AI_Diplo.AI_DiploEvent] = []
        self.name = player_name
        for o_p in other_players:
            self.diplomacy.append([o_p, float(AI_Diplo.DIPLO_BASE_VALUE)])

    def add_event(self, target_id: int, loc: (int, int), event: DiploEventType, rel_change: float, lifetime: int):
        """
        add an event. For more details read class description

        :param target_id: id of the owner of the cause of the event. For instance, the owner id of the hostile army
        :param loc: location of the event. This will be used to identify if a event for this cause exists already
        :param event: The type of the event, defined in constants
        :param rel_change: relative change in one-dimensional diplomacy
        :param lifetime: the lifetime of the event, for how long the effect persists
        :return:
        """
        # check if this exists already:
        for e in self.events:
            if e.target_id == target_id and e.event == event and e.loc == loc:
                e.lifetime = e.lifetime_max
                return
        # otherwise, if event does not exist, yet
        event_str = DiploEventType.get_event_description(event, loc)
        ai_event = AI_Diplo.AI_DiploEvent(target_id, rel_change, lifetime, event, event_str)
        ai_event.add_loc(loc)
        self.events.append(ai_event)
        if event in AI_Diplo.LOGGED_EVENTS:
            Logger.log_diplomatic_event(event, rel_change, loc, lifetime, self.name)

    def calc_round(self):
        """
        If diplomacy is used, this method has to be called every round, to adjust the lifetime of all events
        :return:
        """
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
        """
        returns a one-dimensional scalar, which represents the current relation to this player
        :param player_id: opponent player id
        :return:
        """
        for d in self.diplomacy:
            if d[0] == player_id:
                return d[1]

    def get_player_with_lowest_dv(self) -> int:
        """

        :return: the player with the lowest diplomatic value. Useful for aggressive moves against least valued player
        """
        lowest_value = float(100)
        lowest_pid = -1
        for pid, value in self.diplomacy:
            if lowest_value > value:
                lowest_value = value
                lowest_pid = pid
        return lowest_pid




class AI:
    """Superclass to a AI. Any AI must implement at least do_move and fill the move object"""

    def __init__(self, name, other_players_ids: [int]):
        """the name of the ai"""
        self.name = name
        """each ai can do (not required) diplomacy"""
        self.diplomacy: AI_Diplo = AI_Diplo(other_players_ids, self.name)
        """this is used for development.
        instead of printing all AI info to the console, one can use the dump to display stats in-game"""
        self.__dump: str = ""
        debug("AI (" + str(name) + ") is running")

    def do_move(self, ai_state: AI_GameStatus, move: AI_Move):
        """upon completion of this method, the AI should have decided on its move"""
        raise NotImplementedError("Please Implement this method")

    def get_state_as_str(self) -> str:
        """used by the UI to display some basic information which is displayed in-game. For complex output, use _dump"""
        pass

    def _dump(self, d: str):
        """Depending on the game settings, this will either dump the output to:
        - [if SHOW_AI_CTRL]the external AI ctrl window
        - [if DEBUG_MODE]the console (should not be the first choice, very slow)
        - [else]nowhere."""
        if Definitions.SHOW_AI_CTRL:
            self.__dump += d + "\n"
        elif Definitions.DEBUG_MODE:
            hint(d)
        else:
            pass

    def dump_diplomacy(self):
        """method dumps active events in diplomacy. (with its lifetime and rel. change)"""
        self._dump("Events: -------------------")
        for event in self.diplomacy.events:
            self._dump(f"    {event.description} [lifetime: {event.lifetime}, rel. change: {event.rel_change}]")

    def _reset_dump(self):
        """most likely, the AI should call this upon being called each turn. It will reset the string buffer"""
        self.__dump = ""

    def get_dump(self):
        return self.__dump
