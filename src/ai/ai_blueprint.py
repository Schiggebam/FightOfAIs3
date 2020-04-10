from src.misc.game_constants import DiploEventType, hint
from src.misc.game_logic_misc import Logger


class AI_Diplo:

    DIPLO_BASE_VALUE = float(5)

    class AI_DiploEvent:


        def __init__(self, target_id: int, rel_change: float, lifetime: int, event: int, description: str):
            self.rel_change = rel_change
            self.lifetime = lifetime
            self.lifetime_max = lifetime
            self.description = description
            self.loc = (-1, -1)
            self.event: int = event
            self.target_id: int = target_id

        def add_loc(self, loc: (int, int)):
            self.loc = loc

    def __init__(self, other_players: [int]):
        self.diplomacy: [[int, float]] = []
        self.events: [AI_Diplo.AI_DiploEvent] = []
        for o_p in other_players:
            self.diplomacy.append([o_p, float(AI_Diplo.DIPLO_BASE_VALUE)])

    def add_event(self, target_id: int, loc: (int, int), event: int, rel_change: float, lifetime: int,
                  player_name:str):
        # check if this exists already:
        for e in self.events:
            if e.target_id == target_id and e.event == event and e.loc == loc:      #TODO armies move!
                e.lifetime = e.lifetime_max
                return
        # otherwise, if event does not exist, yet
        event_str = ""
        if event == DiploEventType.TYPE_ENEMY_BUILDING_SCOUTED:
            event_str = "Enemy building scouted at: " + str(loc)
        elif event == DiploEventType.TYPE_ENEMY_ARMY_INVADING:
            event_str = "Enemy army scouted at: " + str(loc)
        ai_event = AI_Diplo.AI_DiploEvent(target_id, rel_change, lifetime, event, event_str)
        ai_event.add_loc(loc)
        self.events.append(ai_event)
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

