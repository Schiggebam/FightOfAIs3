import random
import queue
from src.ai import AI_Toolkit
from src.ai.AI_GameStatus import AI_Tile, AI_GameStatus, AI_Move
from src.ai.ai_blueprint import AI


class AI_Hellenic(AI):
    STATE_DEFENSIVE = 99
    STATE_AGGRESSIVE = 98

    def __init__(self, name, other_players: [int]):
        super().__init__(name, other_players)
        self.build_order = []
        # self.build_order.append("s1")
        self.build_order.append("farm")
        self.build_order.append("s1")
        self.build_order.append("farm")
        # self.build_order.append("s2")
        self.state = AI_Hellenic.STATE_DEFENSIVE
        self.before_last_food = 0
        self.last_food = 0
        self.loosing_food = False
        self.need_more_culture = False

    def do_move(self, ai_stat: AI_GameStatus, move):
        if (ai_stat.turn_nr >= 5):
            self.generate_test_heapmap(ai_stat, move)
        print("AI " + self.name + " calculates its move")
        # handle some internal vars
        self.before_last_food = self.last_food
        self.last_food = ai_stat.player_food
        if self.last_food - self.before_last_food < 0:
            print("we are loosing food!")
            self.loosing_food = True
        else:
            self.loosing_food = False

        (best_building_pos, score_b, str_type) = self.evaluate_building(ai_stat)
        (best_scouting_pos, score_s) = self.evaluate_scouting(ai_stat)
        score_a = self.evaluate_army_upgrading(ai_stat)

        print("Building: Best tile @ " +
              str(best_building_pos.offset_coordinates) if best_building_pos else "-" + " score: " + str(score_b))
        print("Scouting: Best tile @ " + str(best_scouting_pos.offset_coordinates) + " score: " + str(score_s))
        print("Score to up the army: " + str(score_a))
        if score_a > score_b and score_a > score_s:
            move.doUpArmy = True

        elif score_b > 0:
            if len(self.build_order) == 0 or self.build_order[0] == str_type:
                move.doBuild = True
                move.info.append(str_type)
                move.loc = best_building_pos.offset_coordinates
                if str_type == "farm":              # say where to put the fields
                    sour = AI_Toolkit.getListDistanceOne(best_building_pos, ai_stat.tiles_buildable)
                    amount_of_fields = max(3, len(sour))
                    sampled = random.sample(sour, amount_of_fields)
                    for sample in sampled:              # 2 fields
                        move.info.append(sample.offset_coordinates)
                if len(self.build_order) > 0:
                    self.build_order.pop(0)
                print("new build order: ")
                print(self.build_order)

        elif ai_stat.player_resources > ai_stat.costBuildS1 and ai_stat.player_resources > ai_stat.costBuildFarm:
            move.doScout = True
            move.loc = best_scouting_pos.offset_coordinates
        else:
            move.doNothing = True

        # move army to attack another army
        if len(ai_stat.armies) > 0:
            attack = False
            target_tile = None
            if len(ai_stat.enemy_armies) > 0:
                if ai_stat.enemy_armies[0].strength > 0:
                    attack = True
                    target_tile = AI_Toolkit.get_tile_by_xy(ai_stat.enemy_armies[0].offset_coordinates, ai_stat.tiles_walkable)
            if len(ai_stat.enemy_buildings) > 0 and not attack:
                print("LETS ATTACK A BUILDING")
                attack = True
                target_tile = AI_Toolkit.get_tile_by_xy(ai_stat.enemy_buildings[0].offset_coordinates, ai_stat.tiles_walkable)

            if attack:
                army_tile = AI_Toolkit.get_tile_by_xy(ai_stat.armies[0].offset_coordinates, ai_stat.tiles_walkable)
                # calc path
                path = []
                if army_tile and target_tile:
                    AI_Toolkit.dijkstra(army_tile, target_tile, ai_stat.tiles_walkable, path)
                    if len(path) > 1:
                        # print("          PATH FOUND")
                        # for p in path:
                        #    print(str(p.offset_coordinates) + " ", end="")
                        # print("")
                        move.move_army_to = path[1].offset_coordinates
                        move.doMoveArmy = True
                    else:
                        print("          NO PATH")

    def evaluate_scouting(self, ai_stat) -> ((int, int), int):
        best_score = -1
        best_spot = None
        if len(ai_stat.tiles_scoutable) == 0:
            return best_spot, best_score
        scoutable_heatmap = []
        for scoutable in ai_stat.tiles_scoutable:
            dist1 = AI_Toolkit.getListDistanceOne(scoutable, ai_stat.tiles_discovered)
            num_of_tiles_with_res = 0
            for t_at_dist_1 in dist1:
                for res in ai_stat.resources:
                    if res.offset_coordinates == t_at_dist_1.offset_coordinates:
                        num_of_tiles_with_res = num_of_tiles_with_res + 1
            scoutable_heatmap.append((scoutable, num_of_tiles_with_res))

        for s_heat in scoutable_heatmap:
            if s_heat[1] > best_score:
                best_score = s_heat[1]
                best_spot = s_heat[0]
        shuffle_list = []
        for e in scoutable_heatmap:
            if e[1] == best_score:
                shuffle_list.append(e)
        idx = random.randint(0, len(shuffle_list) - 1)
        return shuffle_list[idx]


    def evaluate_building(self, ai_stat):
        best_score = -1
        best_spot = None
        building = ""
        prefered_building = ""
        if len(self.build_order) > 0:
            prefered_building = self.build_order[0]
        else:
            prefered_building = "s1" if not self.loosing_food else "farm"
        if prefered_building == "s1":
            building = "s1"
            """building spots get scored by how many resources they have close by"""
            if ai_stat.player_resources >= ai_stat.costBuildS1:
                for ai_t in ai_stat.tiles_buildable:
                    score = 0
                    dist1 = AI_Toolkit.getListDistanceOne(ai_t, ai_stat.tiles_discovered)
                    for t_at_dist_1 in dist1:
                        for res in ai_stat.resources:
                            if res.offset_coordinates == t_at_dist_1.offset_coordinates:
                                    score = score + 1
                    if best_score < score:
                        best_score = score
                        best_spot = ai_t


        if prefered_building == "farm":
            building = "farm"
            """building spots get scored by how many buildable fields there are next to it"""
            if ai_stat.player_resources >= ai_stat.costBuildFarm:
                for ai_t in ai_stat.tiles_buildable:
                    score = 0
                    dist1 = AI_Toolkit.getListDistanceOne(ai_t, ai_stat.tiles_buildable)
                    score = len(dist1)
                    if best_score < score:
                        best_score = score
                        best_spot = ai_t
        return best_spot, best_score, prefered_building


    def evaluate_army_upgrading(self, ai_stat):
        print("CULTURE: " + str(ai_stat.player_culture))
        print("UP COST: " + str(ai_stat.costArmyUp))
        if ai_stat.player_culture >= ai_stat.costArmyUp:
            self.need_more_culture = False
            if ai_stat.armies[0].strength < len(ai_stat.own_buildings):
                return len(ai_stat.own_buildings) - ai_stat.armies[0].strength
        # here I could set an internal var that I wand more culture.
        self.need_more_culture = True
        return 0

    def generate_test_heapmap(self, ai_stat: AI_GameStatus, move: AI_Move):
        print("heat_map:")
        heat_map: [(int, AI_Tile)] = []
        tmp = queue.Queue()
        discovered = set()
        #dis_plus_scout = []
        #for e in ai_stat.tiles_scoutable:
        #    dis_plus_scout.append(e)
        #for e in ai_stat.tiles_discovered:
        #    dis_plus_scout.append(e)
        #for s in ai_stat.tiles_scoutable:
        #for s in ai_stat.own_buildings:
        #    tmp.put((-1, s))
        for s in ai_stat.tiles_scoutable:
            tmp.put((-1, s))
        while not tmp.empty():
            d, s = tmp.get()
            if s in discovered:
                continue
            discovered.add(s)
            if d >= 0:
                heat_map.append((d, s))
           # nei = AI_Toolkit.getListDistanceOne(s, dis_plus_scout)
            nei = AI_Toolkit.getListDistanceOne(s, ai_stat.tiles_discovered)
            for n in nei:
                if n not in discovered and AI_Toolkit.is_tile_in_list(n, ai_stat.tiles_walkable):
                #if n not in discovered and (AI_Toolkit.is_tile_in_list(n, ai_stat.tiles_scoutable) or
                #                           AI_Toolkit.is_tile_in_list(n, ai_stat.tiles_discovered)):
                    tmp.put((d+1,n))

        #for (d, s) in heat_map:
        #    move.info_at_tile.append()

    def get_state_as_str(self):
        return "no state"