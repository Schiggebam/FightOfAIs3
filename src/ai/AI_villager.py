# from enum import Enum
#
# from src.ai.AI_GameStatus import AI_GameStatus, AI_Move
# from src.ai.ai_blueprint import AI
#
#
# class AI_Villager(AI):
#     class AI_State(Enum):
#         PASSIVE = 0
#         AGGRESSIVE = 1
#         DEFENSIVE = 2
#
#     def __init__(self, own_id: int, other_players: [int]):
#         super().__init__("Barbaric", other_players)
#         self.own_id = own_id
#         self.state = AI_Villager.AI_State.PASSIVE
#         self.other_player = other_players
#         self.previous_army_strength = -1
#         self.previous_amount_of_buildings = -1
#
#     def do_move(self, ai_stat: AI_GameStatus, move: AI_Move):
#         self.update_diplo_events(ai_stat)
#         self.diplomacy.calc_round()
#
#
#
#     def update_diplo_events(self, ai_stat: AI_GameStatus):
#         pass