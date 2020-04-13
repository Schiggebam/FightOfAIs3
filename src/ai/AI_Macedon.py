from enum import Enum
from typing import Set

from src.ai.AI_GameStatus import AI_GameStatus, AI_Move
from src.ai.ai_blueprint import AI


class AI_Mazedon(AI):
    class AI_State(Enum):
        PASSIVE = 0
        AGGRESSIVE = 1
        DEFENSIVE = 2


    def __init__(self, own_id: int, other_players: [int]):
        super().__init__("Barbaric", other_players)
        self.personality = "militant"
        self.own_id = own_id
        self.state = AI_Mazedon.AI_State.PASSIVE
        self.other_players = other_players
        self.hostile_player: Set[int] = set()
        self.previous_army_strength = -1
        self.previous_amount_of_buildings = -1

    def do_move(self, ai_stat: AI_GameStatus, move: AI_Move):

        self.diplomacy.calc_round()