from enum import Enum
from typing import Optional, Tuple

TILE_HIGHT = 52 * 1
TILE_WIDTH = 66 * 1
TILEMAP_ORIGIN_X = 40
TILEMAP_ORIGIN_Y = 0
LEFT_MARGIN = 0
BOTTOM_MARGIN = 130

class Hexagon:
    def __init__(self, grid_pos: (int, int)):
        self.offset_coordinates: (int, int) = grid_pos
        self.cube_coordinates: (int, int, int) = HexMap.offset_to_cube_coords(grid_pos)
        self.ground = None
        self.debug_msg = ""



class MapStyle(Enum):
    S_V_C = 0   # bottom side horizontal, each row has equal amount of elements


class HexMap:
    def __init__(self, map_dim: (int, int), style: MapStyle):
        if style != MapStyle.S_V_C:
            print("HexMap: Only supported style so far: S_V_C")
        self.map_dim = map_dim
        self.map: [Hexagon] = []       # linear storage of all hexagons in the map
        for y in range(map_dim[1]):
            for x in range(map_dim[0]):
                self.map.append(Hexagon((x, y)))

    def get_hex_by_cube(self, cube_c: (int, int, int)) -> Optional[Hexagon]:
        x, y = HexMap.cube_to_offset_coords(cube_c)
        if (0 <= x < self.map_dim[0]) and (0 <= y < self.map_dim[1]):
            return self.map[self.offset_to_linear_mapping(HexMap.cube_to_offset_coords(cube_c))]
        return None

    def get_hex_by_offset(self, offset_c: (int, int)) -> Optional[Hexagon]:
        if (0 <= offset_c[0] < self.map_dim[0]) and (0 <= offset_c[1] < self.map_dim[1]):
            return self.map[self.offset_to_linear_mapping(offset_c)]
        return None

    def offset_to_linear_mapping(self, offset_c: (int, int)) -> int:
        return offset_c[0] + offset_c[1] * self.map_dim[0]

    @staticmethod
    def get_cc_east(cc: (int, int, int)) -> Tuple[int, int, int]:
        x, y, z = cc
        x = x + 1
        y = y - 1
        return x, y, z

    def get_hex_east(self, h: Hexagon) -> Hexagon:
        x, y, z = h.cube_coordinates
        x = x + 1
        y = y - 1
        return self.get_hex_by_cube((x, y, z))

    @staticmethod
    def get_cc_west(cc: (int, int, int)) -> Tuple[int, int, int]:
        x, y, z = cc
        x = x - 1
        y = y + 1
        return x, y, z

    def get_hex_west(self, h: Hexagon) -> Hexagon:
        x, y, z = h.cube_coordinates
        x = x - 1
        y = y + 1
        return self.get_hex_by_cube((x, y, z))

    @staticmethod
    def get_cc_northwest(cc: (int, int, int)) -> Tuple[int, int, int]:
        x, y, z = cc
        x = x - 1
        z = z + 1
        return x, y, z

    def get_hex_northwest(self, h: Hexagon) -> Hexagon:
        x, y, z = h.cube_coordinates
        x = x - 1
        z = z + 1
        return self.get_hex_by_cube((x, y, z))

    @staticmethod
    def get_cc_northeast(cc: (int, int, int)) -> Tuple[int, int, int]:
        x, y, z = cc
        y = y - 1
        z = z + 1
        return x, y, z

    def get_hex_northeast(self, h: Hexagon) -> Hexagon:
        x, y, z = h.cube_coordinates
        y = y - 1
        z = z + 1
        return self.get_hex_by_cube((x, y, z))

    @staticmethod
    def get_cc_southwest(cc: (int, int, int)) -> Tuple[int, int, int]:
        x, y, z = cc
        y = y + 1
        z = z - 1
        return x, y, z

    def get_hex_southwest(self, h: Hexagon) -> Hexagon:
        x, y, z = h.cube_coordinates
        y = y + 1
        z = z - 1
        return self.get_hex_by_cube((x, y, z))

    @staticmethod
    def get_cc_southeast(cc: (int, int, int)) -> Tuple[int, int, int]:
        x, y, z = cc
        x = x + 1
        z = z - 1
        return x, y, z

    def get_hex_southeast(self, h: Hexagon) -> Hexagon:
        x, y, z = h.cube_coordinates
        x = x + 1
        z = z - 1
        return self.get_hex_by_cube((x, y, z))

    def get_neighbours(self, h: Hexagon) -> [Hexagon]:
        nei = [self.get_hex_northeast(h),
                self.get_hex_east(h),
                self.get_hex_southeast(h),
                self.get_hex_southwest(h),
                self.get_hex_west(h),
                self.get_hex_northwest(h)]
        return list(filter(None, nei))

    def get_neighbours_dist2(self, h:Hexagon) -> [Hexagon]:
        x, y ,z = h.cube_coordinates
        dist_2 = [(x, y+2, z-2), (x+1, y+1, z-2), (x+2, y, z-2),
         (x+2, y-1, z-1), (x+2, y-2, z), (x+1, y-2, z+1),
         (x, y-2, z+2), (x-1, y-1, z+2), (x-2, y, z+2),
         (x-2, y+1, z+1), (x-2, y+2, z), (x-1, y+2, z-1)]
        nei = []
        for tpl in dist_2:
            nei.append(self.get_hex_by_cube(tpl))
        nei.extend(self.get_neighbours(h))
        return list(filter(None, nei))

    def get_neighbours_dist(self, h: Hexagon, dist: int):
        if dist < 0:
            print("HexMap: negative distance?")
            return None
        elif dist == 0:
            return h
        elif dist == 1:
            return self.get_neighbours(h)
        elif dist == 2:
            return self.get_neighbours_dist2(h)
        else:
            nei = []
            for hex in self.map:
                if HexMap.hex_distance(h, hex) <= dist:
                    nei.append(hex)
            return list(filter(None, nei))

    @staticmethod
    def hex_distance(hex_a: Hexagon, hex_b: Hexagon) -> int:
        return HexMap.cube_distance(hex_a.cube_coordinates, hex_b.cube_coordinates)

    @staticmethod
    def cube_distance(a: (int, int, int), b: (int, int, int)) -> int:
        return (abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])) / 2

    @staticmethod
    def offset_to_cube_coords(offset_c: (int, int)) -> (int, int, int):
        x = offset_c[0] - (offset_c[1] - (offset_c[1] & 1)) / 2
        z = offset_c[1]
        y = -x - z
        return x, y, z

    @staticmethod
    def cube_to_offset_coords(cube_c: (int, int, int)) -> (int, int):
        x = cube_c[0] + (cube_c[2] - (cube_c[2] & 1)) / 2
        y = cube_c[2]
        return int(x), int(y)

    @staticmethod
    def offset_to_pixel_coords(offset_c: (int, int)) -> (int, int):
        y_pix = offset_c[1] * TILE_HIGHT / 2 + BOTTOM_MARGIN + TILEMAP_ORIGIN_Y
        x_pix = offset_c[0] * TILE_WIDTH + LEFT_MARGIN + TILEMAP_ORIGIN_X
        if offset_c[1] % 2 != 0:
            x_pix = x_pix + TILE_WIDTH / 2
        return x_pix, y_pix
