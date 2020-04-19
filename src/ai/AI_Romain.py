# # fist primitive AI which can read from xml file
#
# import random
#
# from src.ai import AI_Toolkit
# from src.ai.ai_blueprint import AI
# from src.ai.AiFileReader import AiFileReader
#
#
# class AI_Romain(AI):
#     def __init__(self, name):
#         super().__init__(name)
#         xml_file = "../resources/ai_0.xml"
#         self.parser = AiFileReader(xml_file)
#         if self.parser.has_ai_data(name):
#             print("found AI data")
#         else:
#             print("AI data not found :/")
#
#         # char_dict = {}
#         # self.parser.get_characteristics(char_dict, name)
#
#     def evaluate_building(self, ai_stat):
#         highest = -1
#         best = None
#         for ai_t in ai_stat.tiles_buildable:
#             score = 0
#             dist1 = AI_Toolkit.getListDistanceOne(ai_t, ai_stat.tiles_discovered)
#             for t_at_dist_1 in dist1:
#                 for res in ai_stat.resources:
#                     if int(t_at_dist_1.x_grid) == int(res.x_grid):
#                         if int(t_at_dist_1.y_grid) == int(res.y_grid):
#                             score = score + 1
#             # s = ""
#             # for n in dist1:
#             #    s = s + str(n.x_grid) + "|" + str(n.y_grid) + ", "
#             """print("Tile: " + str(ai_t.x_grid) + "|" + str(ai_t.y_grid) +
#                   " score: " + str(score) +
#                   " neighbours dist 1: " + str(len(dist1)) +
#                   " len res: " + str(len(ai_stat.resources)) +
#                   " Neighbours: [" + s + "]")"""
#             if highest < score:
#                 highest = score
#                 best = ai_t
#         #print((best, highest))
#         return (best, highest)
#
#     def evaluate_scouting(self, ai_stat):
#         #print("evaluating scouting")
#         if len(ai_stat.tiles_scoutable) == 0:
#             return (None,-1)
#         scoutable_score = []
#         for scoutable in ai_stat.tiles_scoutable:
#             # get neighbours - if one is ares tile, this augments the priority
#             dist1 = AI_Toolkit.getListDistanceOne(scoutable, ai_stat.tiles_discovered)
#             num_tiles_with_res = 0
#             for nei in dist1:
#                 r = AI_Toolkit.get_resource_on_tile_xy(nei.x_grid, nei.y_grid, ai_stat.resources)
#                 if r is not None:
#                     num_tiles_with_res = num_tiles_with_res + 1
#             scoutable_score.append((scoutable, num_tiles_with_res))
#
#         best_s = None
#         best_value = -1
#         for s_v in scoutable_score:
#             if s_v[1] > best_value:
#                 best_s = s_v[0]
#                 best_value = s_v[1]
#         #print((best_s, best_value))
#         shuffle_list = []
#         for e in scoutable_score:
#             if e[1] == best_value:
#                 shuffle_list.append(e)
#         idx = random.randint(0, len(shuffle_list)-1)
#
#         return (shuffle_list[idx][0], shuffle_list[idx][1])
#
#     def evaluate_upgrading(self, ai_stat):
#         #print("evaluating upgrading")
#         score = 0
#         #if ai_stat.player_resources <= ai_stat.costBuildT2: # not enough resources to upgrade
#         #    return score
#         buildings_values = []  # contains tuple of (bld, amount of res tiles attached)
#         for bld in ai_stat.own_buildings:
#             num_tiles_with_res = 0
#             for tile in ai_stat.tiles_discovered:
#                 if AI_Toolkit.getDistance_xy(bld.offset_coordinates, tile.offset_coordinates) == 1:
#                     r = AI_Toolkit.get_resource_on_tile_xy(tile.offset_coordinates, ai_stat.resources)
#                     if r is not None:
#                         num_tiles_with_res = num_tiles_with_res + 1
#             buildings_values.append((bld, num_tiles_with_res))
#
#         best_bld = None
#         best_value = -1
#         for b_v in buildings_values:
#             if b_v[1] > best_value:
#                 best_bld = b_v[0]
#                 best_value = b_v[1]
#         #print((best_bld, best_value))
#         return (best_bld, best_value)
#
#     def perform_upgrading(self, move, x, y):
#         move.doUpgrade = True
#         move.loc = (x, y)
#         move.str_rep_of_action = "upgrading (" + str(move.loc) + ")"
#
#     def perform_building(self, move, x, y):
#         move.doBuild = True
#         move.loc = (x, y)
#         move.str_rep_of_action = "build (" + str(move.loc) + ")"
#
#     def perform_scouting(self, move, x, y):
#         move.doScout = True
#         move.loc = (x, y)
#         move.str_rep_of_action = "scout (" + str(move.loc) + ")"
#
#     def perform_noop(self, move):
#         move.doNothing = True
#         move.str_rep_of_action = "no action"
#
#     ## do a move from gen1
#     def do_move(self, ai_stat, move):
#         print("AI " + self.name + " calulates its move")
#         (best_u, score_u) = self.evaluate_upgrading(ai_stat)
#         (best_s, score_s) = self.evaluate_scouting(ai_stat)
#         (best_b, score_b) = self.evaluate_building(ai_stat)
#         print("Player Res: " + str(ai_stat.player_resources))
#         print("Best buildings place: " + str(best_b.x_grid) + "|" + str(best_b.y_grid) +
#               ", score: " + str(score_b))
#         print("Best scouting place:  " + str(best_s.x_grid) + "|" + str(best_s.y_grid) +
#               ", score: " + str(score_s))
#         print("Best upgrading place: " + str(best_u.x_grid) + "|" + str(best_u.y_grid) +
#               ", score: " + str(score_u))
#
#
#         # army movement
#         if len(ai_stat.enemy_buildings) > 0:
#             shortest_path_length = 100
#             best_path = None
#             for target in ai_stat.enemy_buildings:
#                 print("Found a enemy buildings @ " + str(target.x_grid) + "|" + str(target.y_grid) )
#                 target_tile = AI_Toolkit.get_tile_by_xy(target.x_grid, target.y_grid, ai_stat.tiles_walkable)
#                 army_tile = AI_Toolkit.get_tile_by_xy(ai_stat.army.x_grid, ai_stat.army.y_grid, ai_stat.tiles_walkable)
#                 path = []
#                 AI_Toolkit.dijkstra(army_tile, target_tile, ai_stat.tiles_walkable, path)
#                 #for p in path:
#                 #    print(str(p.x_grid) + "|" + str(p.y_grid))
#                 if len(path) == 1:
#                     print("NO PATH")
#                 else:
#                     for e in path:
#                         move.info_at_tile.append((e.x_grid, e.y_grid, "X"))
#                 if len(path) == 1: # no path to enemy building
#                     continue
#                 if len(path) < shortest_path_length:
#                     best_path = path
#                     shortest_path_length = len(path)
#
#             print("path to next buildings: length:  " + str(shortest_path_length))
#             if best_path:
#                 print("path:")
#                 for p in best_path:
#                     print(str(p.x_grid) + "|" + str(p.y_grid) + " ", end = "")
#                 print("")
#                 if len(best_path) > 1:
#                     move.move_army_to = (best_path[1].x_grid, best_path[1].y_grid)
#                     move.doMoveArmy = True
#
#         if ai_stat.costArmyUp <= ai_stat.player_culture:
#             print("up the army!")
#             move.doUpArmy = True
#             move.str_rep_of_action = "up the army"
#             return
#         """
#         #test
#         path = []
#         AI_Toolkit.dijkstra(ai_stat.tiles_buildable[0], ai_stat.tiles_buildable[5], ai_stat.tiles_walkable, path)
#         print(path)
#         if len(path) == 1:
#            print("NO PATH")
#         else:
#            for e in path:
#                move.info_at_tile.append((e.x_grid, e.y_grid, "X"))
#         """
#
#         if self.name == "expansionist":
#             print("calc expansionist move:")
#             if score_b >= 2 and ai_stat.player_resources >= ai_stat.costBuildT1:
#                 self.perform_building(move, best_b.x_grid, best_b.y_grid)
#             elif score_s >= 2 and ai_stat.player_resources >= ai_stat.costScout:
#                 self.perform_scouting(move, best_s.x_grid, best_s.y_grid)
#             elif score_b == 1 and ai_stat.player_resources >= ai_stat.costBuildT1:
#                 self.perform_building(move, best_b.x_grid, best_b.y_grid)
#             elif (score_s == 1 or score_s == 0) and \
#                     ai_stat.player_resources >= ai_stat.costScout:
#                 self.perform_scouting(move, best_s.x_grid, best_s.y_grid)
#             else:
#                 self.perform_noop(move)
#
#
#         elif self.name == "cultivated":
#             if score_u >= 1 and ai_stat.player_resources >= ai_stat.costBuildT2:
#                 self.perform_upgrading(move, best_u.x_grid, best_u.y_grid)
#             elif score_b >= 2 and ai_stat.player_resources >= ai_stat.costBuildT1:
#                 self.perform_building(move, best_b.x_grid, best_b.y_grid)
#             elif score_s >= 2 and ai_stat.player_resources >= ai_stat.costScout:
#                 self.perform_scouting(move, best_s.x_grid, best_s.y_grid)
#             elif ai_stat.player_resources > ai_stat.costBuildT2:
#                 if score_b == 1 and ai_stat.player_resources >= ai_stat.costBuildT1:
#                     self.perform_building(move, best_b.x_grid, best_b.y_grid)
#                 elif ai_stat.player_resources > ai_stat.costScout:
#                     self.perform_scouting(move, best_s.x_grid, best_s.y_grid)
#             else:
#                 self.perform_noop(move)
#
#         print("AI decision: " + move.str_rep_of_action)
#
#
#         #
#         # if ai_stat.player_resources > 40:   # upgrade
#         #     counter = 0
#         #     b = None
#         #     for bld in ai_stat.own_buildings:
#         #         if bld.type == "t1":
#         #             b = bld
#         #             break
#         #     move.loc = (b.x_grid, b.y_grid)
#         #     move.str_rep_of_action = "upgrading (" + str(move.loc) + ")"
#         #     move.doUpgrade = True
#         #
#         # if not move.doUpgrade and ai_stat.player_resources >= ai_stat.costBuildT1:
#         #     highest = -1
#         #     best = None
#         #     for ai_t in ai_stat.tiles_buildable:
#         #         score = 0
#         #         dist1 = AI_Toolkit.getListDistanceOne(ai_t, ai_stat.tiles_discovered)
#         #         for t_at_dist_1 in dist1:
#         #             for res in ai_stat.resources:
#         #                 if int(t_at_dist_1.x_grid) == int(res.x_grid):
#         #                     if int(t_at_dist_1.y_grid) == int(res.y_grid):
#         #                         score = score + 1
#         #         s = ""
#         #         for n in dist1:
#         #             s = s + str(n.x_grid) + "|" + str(n.y_grid) + ", "
#         #         """print("Tile: " + str(ai_t.x_grid) + "|" + str(ai_t.y_grid) +
#         #               " score: " + str(score) +
#         #               " neighbours dist 1: " + str(len(dist1)) +
#         #               " len res: " + str(len(ai_stat.resources)) +
#         #               " Neighbours: [" + s + "]")"""
#         #         if highest < score:
#         #             highest = score
#         #             best = ai_t
#         #     if highest > 0:
#         #         move.doBuild = True
#         #         move.loc = (best.x_grid, best.y_grid)
#         #         move.str_rep_of_action = "build (" + str(move.loc) + ")"
#         #
#         # if not move.doUpgrade and not move.doBuild and ai_stat.player_resources >= ai_stat.costScout:  # scouting
#         #     found_target = False
#         #     x_target = -1
#         #     y_target = -1
#         #     for t in ai_stat.tiles_scoutable:       # look for a tile with resources
#         #         for res in ai_stat.resources:
#         #             if int(t.x_grid) == int(res.x_grid):
#         #                 if int(t.y_grid) == int(res.y_grid):
#         #                     found_target = True
#         #                     x_target = t.x_grid
#         #                     y_target = t.y_grid
#         #
#         #     if not found_target:
#         #         for t in ai_stat.tiles_scoutable:       # look for a neighbour tile of a resource tile
#         #             dist1 = AI_Toolkit.getListDistanceOne(t, ai_stat.tiles_discovered)
#         #             for d1 in dist1:
#         #                 for res in ai_stat.resources:
#         #                     if int(d1.x_grid) == int(res.x_grid):
#         #                         if int(d1.y_grid) == int(res.y_grid):
#         #                             found_target = True
#         #                             x_target = t.x_grid
#         #                             y_target = t.y_grid
#         #
#         #     idx = 0
#         #     if not found_target:
#         #         max = len(ai_stat.tiles_scoutable) - 1
#         #         idx = random.randint(0, max)
#         #         x_target = ai_stat.tiles_scoutable[idx].x_grid
#         #         y_target = ai_stat.tiles_scoutable[idx].y_grid
#         #
#         #     move.doScout = True
#         #     move.loc = (x_target, y_target)
#         #     move.str_rep_of_action = "scout (" + str(move.loc) + ")"
#         #     move.info_at_tile.append((x_target, y_target, "S"))
#         #
#         # if not move.doBuild and not move.doScout and not move.doUpgrade:
#         #     move.doNothing = True
#         #     move.str_rep_of_action = "no action"
