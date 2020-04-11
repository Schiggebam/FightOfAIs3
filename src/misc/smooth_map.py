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

                inner = ""
                if current_hex.ground.tex_code == "xx":
                    inner = "gc"
                elif current_hex.ground.tex_code == "yy":
                    inner = "whatever"
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

                if sum(edge) == 2:           # in place replacement would not work -> store reference
                    if edge[0] and edge[2]:
                        adjusted_tiles.append((current_hex, SmoothMap.__1_TO_3))
                    elif edge[0] and edge[3]:
                        adjusted_tiles.append((current_hex, SmoothMap.__1_TO_4))
                    elif edge[0] and edge[4]:
                        adjusted_tiles.append((current_hex, SmoothMap.__1_TO_5))
                    elif edge[1] and edge[3]:
                        adjusted_tiles.append((current_hex, SmoothMap.__2_TO_4))
                    elif edge[1] and edge[4]:
                        adjusted_tiles.append((current_hex, SmoothMap.__2_TO_5))
                    elif edge[1] and edge[5]:
                        adjusted_tiles.append((current_hex, SmoothMap.__2_TO_6))
                    elif edge[2] and edge[4]:
                        adjusted_tiles.append((current_hex, SmoothMap.__3_TO_5))
                    elif edge[2] and edge[5]:
                        adjusted_tiles.append((current_hex, SmoothMap.__3_TO_6))
                    elif edge[3] and edge[5]:
                        adjusted_tiles.append((current_hex, SmoothMap.__4_TO_6))
                else:
                    error("Smooth Map. Lines may not split.")
                    print(edge)
                    for n in nei:
                        print(n.ground.tex_code)

        for h, m in adjusted_tiles:
                h.ground.tex_code = "dg_lg_{}var_0".format(m)