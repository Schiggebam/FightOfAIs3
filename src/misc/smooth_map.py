from typing import List

#      /  \
#    /6    1\
#  |          |
#  |5        2|
#  |          |
#    \4    3/
#      \  /
#
from src.hex_map import Hexagon, HexMap
from src.misc.game_constants import GroundType, error


class SmoothMap:
    ignore_list = [GroundType.WATER_DEEP]
    __1_TO_3 = "1_3_"
    __1_TO_4 = "1_4_"
    __1_TO_5 = "1_5_"
    __2_TO_4 = "2_4_"
    __2_TO_5 = "2_5_"
    __2_TO_6 = "2_6_"
    __3_TO_5 = "3_5_"
    __3_TO_6 = "3_6_"
    __4_TO_6 = "4_6_"

    def __init__(self):
        pass

    @staticmethod
    def smooth_map(hex_map: HexMap):
        x_max = hex_map.map_dim[0]
        y_max = hex_map.map_dim[1]

        adjusted_tiles: List[(Hexagon, str)] = []

        for y in range(y_max):
            for x in range(x_max):
                current_hex = hex_map.get_hex_by_offset((x, y))
                if current_hex.ground.ground_type in SmoothMap.ignore_list:
                    continue

                inner = ""      # tex_code of the "inner" texture how it is written on the map!
                inv = False
                outer_tex = ''      # tex_code of the texture of the inner!!! tex       # TODO this is bad!
                inner_tex = ''      # tex_code of the texture of the outer!!! tex
                if current_hex.ground.tex_code == "xx":
                    inner = "gc"
                    outer_tex = 'lg'
                    inner_tex = 'dg'
                elif current_hex.ground.tex_code == "yy":
                    inner = "gr"
                    # inv = False
                    outer_tex = 'dg'
                    inner_tex = 'lg'
                elif current_hex.ground.tex_code == "zz":
                    inner = "st"
                    outer_tex = 'st'
                    inner_tex = 'lg'
                elif current_hex.ground.tex_code == "ww":
                    # inv = False
                    inner = "gr"
                    outer_tex = 'lg'
                    inner_tex = 'st'
                elif current_hex.ground.tex_code == "vv":
                    inner = "gc"
                    outer_tex = "dg"
                    inner_tex = "st"
                    inv = True
                elif current_hex.ground.tex_code == "uu":
                    inner = "gr"
                    outer_tex = "lg"
                    inner_tex = "st"
                    inv = True
                else:
                    continue

                # gather neighbours
                edge = [False, False, False, False, False, False]   # true if this side of the hexagon gets smoothed out
                nei = [hex_map.get_hex_northeast(current_hex).ground.tex_code,      # the order is important, better do it explicitly
                       hex_map.get_hex_east(current_hex).ground.tex_code,
                       hex_map.get_hex_southeast(current_hex).ground.tex_code,
                       hex_map.get_hex_southwest(current_hex).ground.tex_code,
                       hex_map.get_hex_west(current_hex).ground.tex_code,
                       hex_map.get_hex_northwest(current_hex).ground.tex_code]

                for i in range(6):
                    edge[i] = nei[i] == current_hex.ground.tex_code

                mode = -1
                orientation = False
                if sum(edge) == 2 or sum(edge) == 1 or sum(edge) == 0:           # in-place replacement would not work -> store reference
                    if sum(edge) == 1 or sum(edge) == 0:
                        for i in range(6):
                            edge[i] = nei[i] == "wd" or nei[i] == "xx" or nei[i] == "ww" or nei[i] == "vv" or nei[i] == "uu"

                    if edge[0] and edge[2]:         # 1_3
                        mode = SmoothMap.__1_TO_3
                        orientation = (edge[1] == inner)
                        if inv:
                            orientation = not orientation
                    elif edge[0] and edge[3]:       # 1_4
                        mode = SmoothMap.__1_TO_4
                        if nei[1] == inner:
                            orientation = True
                        else:
                            orientation = False
                    elif edge[0] and edge[4]:       # 1_5
                        mode = SmoothMap.__1_TO_5
                        orientation = nei[1] == inner
                    elif edge[1] and edge[3]:       # 2_4
                        mode = SmoothMap.__2_TO_4
                        if nei[2] == inner:
                            orientation = False
                        else:
                            orientation = True
                    elif edge[1] and edge[4]:       # 2_5
                        mode = SmoothMap.__2_TO_5
                        if nei[2] == inner:
                            orientation = False
                        else:
                            orientation = True
                    elif edge[1] and edge[5]:       # 2_6
                        mode = SmoothMap.__2_TO_6
                        orientation = nei[2] == inner
                    elif edge[2] and edge[4]:       # 3_5
                        mode = SmoothMap.__3_TO_5
                        if nei[3] == inner:
                            orientation = False
                        else:
                            orientation = True
                    elif edge[2] and edge[5]:       # 3_6
                        mode = SmoothMap.__3_TO_6
                        if nei[3] == inner:
                            orientation = True
                        else:
                            orientation = False
                    elif edge[3] and edge[5]:       # 4_6
                        mode = SmoothMap.__4_TO_6
                        if nei[4] == inner:
                            orientation = False
                        else:
                            orientation = True

                    if orientation:
                        adjusted_tiles.append((current_hex, "{}_{}_{}var_0".format(outer_tex, inner_tex, mode)))
                    else:
                        adjusted_tiles.append((current_hex, "{}_{}_{}var_0".format(inner_tex, outer_tex, mode)))
                # elif sum(edge) == 1:
                #     # this is okay if one side is water
                #     for i in range(6)
                #         edge[i] = nei[i] == "wd"
                #     mode = SmoothMap.__2_TO_5
                #     orientation = False
                #     if orientation:
                #         adjusted_tiles.append((current_hex, "{}_{}_{}var_0".format(outer_tex, inner_tex, mode)))
                #     else:
                #         adjusted_tiles.append((current_hex, "{}_{}_{}var_0".format(inner_tex, outer_tex, mode)))
                else:
                    error("Smooth Map. Lines may not split.")

        # set the tex_code
        for h, s in adjusted_tiles:
            h.ground.tex_code = s
            h.ground.ground_type = GroundType.MIXED

    @staticmethod
    def adjust_elevation(hex_map: HexMap):
        for hex in hex_map.map:
            ground = hex.ground
            if ground.ground_type == GroundType.WATER_DEEP:
                continue
            nei = hex_map.get_neighbours(hex)
            count = 0
            for n in nei:
                if n.ground.ground_type != GroundType.WATER_DEEP:
                    count = count + 1
            if count == 6:
                ground.sprite.center_y = ground.sprite.center_y + 10

