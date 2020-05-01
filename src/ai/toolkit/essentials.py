import copy
import queue
from typing import List, Union, Tuple, Callable

from src.ai.AI_MapRepresentation import Tile, AI_Element
from src.hex_map import Hexagon
from src.misc.game_constants import debug

# ------------------------ Essential TOOLKIT FUNCTIONS: ------------------------

AI_OBJ = Union[AI_Element, Tile]


def simple_heat_map(initial_set: List[AI_OBJ], working_set: List[AI_OBJ],
                    condition: Callable[[AI_OBJ], bool]) -> List[Tuple[int, AI_OBJ]]:
    """
    create simple heat map.
    Essentially, this performs a breadth first search, starting from a set, instead of a single point.
    Example: if you'd like to get the minimum distance from any tile in a set to a building, the call would
    look something like this:

    simple_heat_map(building_list, discovered_tiles, lambda function)

    The lambda function allows for an additional selection on which tiles get included into the search.
    For instance, one might want to exclude all tiles, which have a resource

    :param initial_set: list from where to start the search
    :param working_set: only neighbors, which are in this list will be considered for the search
    :param condition: additional condition, see above
    :return: heat map, a tuple containing an integer value which is the distance to the closest object in initial list plus the object itself
    """

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
        nei = get_neighbours_on_set(s, working_set)
        for n in nei:
            if n not in discovered and condition(n):
                tmp.put((d + 1, n))
    return heat_map


def dijkstra_pq(start: Tile, target: Tile, domain: List[Tile]) -> List[Tile]:
    """
    simple path-finding routine, based on dijkstra's algorithm

    :param start: start Tile from where to start the search
    :param target: target Tile, search will abort upon reaching it
    :param domain: the search domain
    :return: a sequence of connected tiles, which represent the path
    """

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
    path.append(x)
    while x.offset_coordinates != start.offset_coordinates:
        x = x.pre
        path.append(x)
        if x is None:  # this is a bit weird in conjunction with the while condition.
            break
    # path.append(start)
    path.reverse()
    # check validity of path.
    # problem = False
    # for i in range(len(path) - 1):
    #     if getDistance(path[i].offset_coordinates, path[i+1].offset_coordinates) != 1:
    #         error("Problem in pathfinding")
    #         problem = True
    # if problem:
    #     for p in path:
    #         print(p.offset_coordinates, end=" ")
    #     print("")
    if start == path[0] and target == path[len(path) - 1]:
        return path
    else:
        debug("Found path is incomplete")
        return [start]


def get_tile_by_xy(coords, discovered_tiles: []):
    for e in discovered_tiles:
        if coords == e.offset_coordinates:
            return e
    return None


def get_neighbours_on_set(tile: AI_OBJ, working_set: List[Tile]) -> List[Tile]:
    """


    :param tile:
    :param working_set: the domain, in which the neighbors are searched
    :return: a list of all neighbors of the tile, which are also in the working list
    """
    nei = get_neighbours(tile)
    filtered = [x for x in nei if x in working_set]
    return filtered


def get_neighbours(e: AI_OBJ) -> List[Tile]:
    """
    returns all the available neighbours of a tile
    (!) If you are interested in all neighbors which share also a list, use:
    get_neighbours_on_set(...)

    :param e: center tile
    :return: list, containing all valid (non- None) neighbours
    """
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


def is_obj_in_list(obj: Union[AI_OBJ, Hexagon], domain: List[Union[AI_OBJ, Hexagon]]) -> bool:
    """
    check whether a the offset coordinates of an object match the ones of an element in the list
    comparison is done via the coordinates of the element

    :param obj: any object, which has offset_coordinates AI_Object or Hexagon
    :param domain: comparison list
    :return: True, if the object is in the list, else False
    """

    for e in domain:
        if e.offset_coordinates == obj.offset_coordinates:
            return True
    return False


def deep_copy_list(src):
    return copy.deepcopy(src)


