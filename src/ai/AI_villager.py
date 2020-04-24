# from enum import Enum
#
# from typing import Set, Optional, Union, List, Any, Dict, Tuple
#
# from src.ai.AI_GameStatus import AI_GameStatus, AI_Move
# from src.ai.ai_blueprint import AI, Weight, BuildOption, RecruitmentOption, RaiseArmyOption, ArmyMovementOption, \
#     WaitOption, UpgradeOption
# from src.misc.game_constants import DiploEventType, hint
#
#
# class AI_Villager(AI):
#     class AI_State(Enum):
#         PASSIVE = 0
#         AGGRESSIVE = 1
#         DEFENSIVE = 2
#
#     def __init__(self, own_id: int, other_players: [int]):
#         super().__init__("Villager", other_players)
#         self.own_id = own_id
#         self.state = AI_Villager.AI_State.PASSIVE
#         self.other_player = other_players
#         self.previous_army_strength = -1
#         self.previous_amount_of_buildings = -1
#         self.hostile_player: Set[int] = set()
#
#         #calling out to the script
#         from src.ai.scripts.villager_basic import on_setup, setup_weights, setup_movement_weights
#         self.properties: Dict[str, Any] = {}
#         on_setup(self.properties)
#         self.weights: List[Weight] = []
#         self.m_weights: List[Weight] = []
#         for c, v in setup_weights(self):
#             self.weights.append(Weight(c, v))
#         for c, v in setup_movement_weights(self):
#             self.m_weights.append(Weight(c, v))
#
#     def do_move(self, ai_stat: AI_GameStatus, move: AI_Move):
#         self.update_diplo_events(ai_stat)
#         self.diplomacy.calc_round()
#         self.evaluate_state(ai_stat)
#
#
#     def evaluate_state(self, ai_stat: AI_GameStatus):
#         if self.state == AI_Villager.AI_State.PASSIVE:
#             if len(self.hostile_player) > 0 and (len(ai_stat.map.opp_army_list) > 0 or len(ai_stat.map.opp_building_list) > 0):
#                 hint("Barbaric AI: Passive -> Aggressive")
#                 self.state = AI_Villager.AI_State.AGGRESSIVE
#             if len(ai_stat.map.opp_army_list) > 0:
#                 hint("Barbaric AI: Passive -> Defensive")
#                 self.state = AI_Villager.AI_State.DEFENSIVE
#         elif self.state == AI_Villager.AI_State.DEFENSIVE:
#             if len(ai_stat.map.opp_army_list) == 0:
#                 hint("Barbaric AI: Defensive -> Passive")
#                 self.state = AI_Villager.AI_State.PASSIVE
#             if self.has_been_attacked(ai_stat):
#                 hint("Barbaric AI: Notices an attack! Defensive -> Aggressive")
#                 self.state = AI_Villager.AI_State.AGGRESSIVE
#         elif self.state == AI_Villager.AI_State.AGGRESSIVE:
#             if len(self.hostile_player) == 0 or len(ai_stat.map.army_list) == 0:       # become defensive if army is lost or no more hostile players
#                 hint("Barbaric AI: Aggressive -> Defensive")
#                 self.state = AI_Villager.AI_State.DEFENSIVE
#             if len(ai_stat.map.opp_army_list) == 0 and len(ai_stat.map.opp_building_list) == 0:
#                 hint("Barbaric AI: Aggressive -> Passive")
#                 self.state = AI_Villager.AI_State.PASSIVE
#     def update_diplo_events(self, ai_stat: AI_GameStatus):
#         """Idea: for each opponent building in the visible area of the barbaric, reduce diplo value by 2"""
#         for e_b in ai_stat.map.opp_building_list:
#             if e_b.visible:
#                 self.diplomacy.add_event(e_b.owner, e_b.offset_coordinates,
#                                          DiploEventType.TYPE_ENEMY_BUILDING_SCOUTED, -2.0, 5, self.name)
#
#         """Idea, for each opponent army movement in the visible area of the barbaric, reduce diplo value by 1
#         Note: if the army moves, this gets triggered again, thus the lifetime of this event is only 1"""
#         for e_a in ai_stat.map.opp_army_list:
#             self.diplomacy.add_event(e_a.owner, e_a.offset_coordinates,
#                                      DiploEventType.ENEMY_ARMY_INVADING_CLAIMED_ZONE, -1.0, 1, self.name)
#
#         for other_p_id in self.other_players:
#             if self.diplomacy.get_diplomatic_value_of_player(other_p_id) < self.properties[
#                 'diplo_aggressive_threshold']:
#                 if other_p_id not in self.hostile_player:
#                     hint("Barbaric AI: Player id: " + str(other_p_id) + " got added to hostile players.")
#                     self.hostile_player.add(other_p_id)