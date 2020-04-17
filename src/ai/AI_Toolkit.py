import copy
import queue
from typing import List, Union, Tuple, Optional

from src.ai.AI_GameStatus import AI_GameStatus
from src.ai.AI_MapRepresentation import Tile, AI_Element
from src.misc.game_constants import error, BuildingType, BuildingState

AI_OBJ = Union[AI_Element, Tile]


def simple_heat_map(initial_set: List[AI_OBJ], working_set: List[AI_OBJ],
                    condition) -> List[Tuple[int, AI_OBJ]]:
    heat_map: List[Tuple[int, AI_OBJ]] = []
    tmp = queue.Queue()
    discovered = set()
    for i in initial_set:
        tmp.put((-1, i))
    while not tmp.empty():
        d, s = tmp.get()
        if s in discovered:
            continue
        discovered.add(s)
        if d >= 0:
            heat_map.append((d, s))
        nei = get_neibours_on_set(s, working_set)
        for n in nei:
            if n not in discovered and condition(n):
                tmp.put((d + 1, n))
    return heat_map


def estimate_income(list_buildings):
    pass


def dijkstra_pq(start, target, domain: List[Tile]) -> List[Tile]:
    # print("DIJ: {} -> {}".format(start.offset_coordinates, target.offset_coordinates))
    path: List[Tile] = []
    Q = []
    for d in domain:
        d.dist = 1000
        d.pre = None
        Q.append(d)
    start.dist = 0
    while len(Q) > 0:
        Q.sort(key=lambda x: x.dist, reverse=False)
        u = Q.pop(0)
        for v in get_neighbours(u):
            if v in domain and v in Q:
                alt = u.dist + 1
                if alt < v.dist:
                    v.dist = alt
                    v.pre = u
    x = target
    while x.offset_coordinates != start.offset_coordinates:
        path.append(x)
        x = x.pre
    path.append(start)
    path.reverse()
    return path

    # print("path: ")
    x = target
    while x is not None:
        #    print(" " + str(x.x_grid) + "|" + str(x.y_grid) + " ", end="")
        path.append(x)
        x = x.pre
    # print(" ")
    path.reverse()
    # if path[0].x_grid == target.x_grid and path[0].y_grid == target.y_grid:
    #    path = None


def get_tile_by_xy(coords, discovered_tiles: []):
    for e in discovered_tiles:
        if coords == e.offset_coordinates:
            return e
    return None


def get_neibours_on_set(tile: AI_OBJ, working_set: List) -> List:
    nei = get_neighbours(tile)
    filtered = [x for x in nei if x in working_set]
    return filtered


def get_neighbours(e: AI_OBJ) -> List[Tile]:
    nei = []
    if type(e) is Tile:
        nei = [e.tile_ne, e.tile_e, e.tile_se, e.tile_sw, e.tile_w, e.tile_nw]
    else:
        nei = [e.base_tile.tile_ne, e.base_tile.tile_e, e.base_tile.tile_se,
               e.base_tile.tile_sw, e.base_tile.tile_w, e.base_tile.tile_nw]
    return list(filter(None, nei))


def get_distance(a: AI_OBJ, b: AI_OBJ) -> int:
    cc1 = offset_to_cube_xy(a.offset_coordinates[0], a.offset_coordinates[1])
    cc2 = offset_to_cube_xy(b.offset_coordinates[0], b.offset_coordinates[1])
    return cube_distance(cc1, cc2)


# def getListDistanceOne(t1, li):     # get neighbours
#     res = []
#     for t2 in li:
#         if getDistance(t1, t2) == int(1):
#             res.append(t2)
#     return list(filter(None, res))


def getDistance(off1: Tuple[int, int], off2: Tuple[int, int]) -> int:
    # dy = float(abs(t1.y_grid - t2.y_grid))
    # dx = float(abs(t1.x_grid - t2.x_grid))
    # return int(dy + max(math.ceil(dx - dy / float(2)), float(0)))
    cube_coords_t1 = offset_to_cube_xy(off1[0], off1[1])
    cube_coords_t2 = offset_to_cube_xy(off2[0], off2[1])
    dist = cube_distance(cube_coords_t1, cube_coords_t2)
    return dist


# def getDistance_xy(a:(int, int), b:(int, int)):
#     cube_coords_1 = offset_to_cube_xy(a[0], a[1])
#     cube_coords_2 = offset_to_cube_xy(b[0], b[1])
#     return cube_distance(cube_coords_1, cube_coords_2)


# def cube_to_offset_coord(cube):
#    col = cube.x + (cube.z - (cube.z&1)) / 2
#    row = cube.z
#    return row, col

def offset_to_cube_xy(x, y):
    c_x = x - (y - (y & 1)) / 2
    c_z = y
    c_y = -c_x - c_z
    return c_x, c_y, c_z


# def get_resource_on_tile_xy(offset_c: (int, int), res_list):
#     for r in res_list:
#         if r.offset_coordinates == offset_c:
#             return r
#     return None


def offset_to_cube_coord(hex):
    x = hex.offset_coordinates[0] - (hex.offset_coordinates[1] - (hex.offset_coordinates[1] & 1)) / 2
    z = hex.offset_coordinates[1]
    y = -x - z
    return x, y, z


def cube_distance(a, b):
    return (abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])) / 2


def is_obj_in_list(obj: AI_OBJ, list) -> bool:
    """check whether a the offset coordinates of an object match the ones of an element in the list"""
    for e in list:
        if e.offset_coordinates == obj.offset_coordinates:
            return True
    return False


def deep_copy_list(src):
    return copy.deepcopy(src)


############## NEWER TOOLKIT FUNCTIONS: ########################################
def num_resources_on_adjacent(obj: AI_OBJ) -> int:
    tile: Tile = get_tile_from_ai_obj(obj)  # assuming this is not none
    value = 0
    for n in get_neighbours(tile):
        if n.has_resource():
            value = value + 1
    return value


def get_tile_from_ai_obj(obj: AI_OBJ) -> Optional[Tile]:
    tile: Optional[Tile] = None
    if type(obj) is Tile:
        tile = obj
    else:
        tile = obj.base_tile
    if tile is None:  # is None
        error("Unable to get Tile from AI_Obj")
    return tile


def num_buidling(building_type: BuildingType, ai_stat: AI_GameStatus, count_under_construction=False):
    value = 0
    for b in ai_stat.map.building_list:
        if b.type == building_type:
            if count_under_construction:
                if b.state == BuildingState.UNDER_CONSTRUCTION or b.state == BuildingState.ACTIVE:
                    value = value + 1
            else:
                if b.state == BuildingState.ACTIVE:
                    value = value + 1
    return value


def has_building_under_construction(building_type: BuildingType, ai_stat: AI_GameStatus):
    for b in ai_stat.map.building_list:
        if b.type == building_type:
            if b.state == BuildingState.UNDER_CONSTRUCTION:
                return True
    return False
