from __future__ import annotations

import copy
import queue
from dataclasses import dataclass
from typing import List, Union, Tuple, Callable, Set, Optional

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


def bfs(start: Tile, target: Tile, domain: List[Tile]) -> List[Tile]:
    """

    :param start:
    :param target:
    :param domain:
    :return:
    """
    path: List[Tile] = []
    tmp = queue.Queue()
    tmp.put((0, start))
    discovered = set()
    path_endpoint = None
    for d in domain:
        d.pre = None
        d.dist = -1

    while not tmp.empty():
        d, s = tmp.get()
        if s in discovered:
            continue
        discovered.add(s)
        if s.offset_coordinates == target.offset_coordinates:
            path_endpoint = s
            break
        nei = get_neighbours_on_set(s, domain)
        for n in nei:
            if n not in discovered:
                n.dist = d + 1
                n.pre = s
                tmp.put((d + 1, n))

    if path_endpoint:
        cur = path_endpoint
        while cur.pre is not None:
            path.append(cur)
            cur = cur.pre

    for p in path:
        print(p.offset_coordinates, end="")
    print(" ")
    return path


class AStarNode:
    """Node for path finding (a star)"""
    def __init__(self, tile: Tile, parent=None):
        self.base_tile = tile
        self.parent = parent
        self.g = 0
        self.h = 0
        self.f = 0

    def __eq__(self, other: AStarNode):
        return self.base_tile.offset_coordinates == other.base_tile.offset_coordinates


def a_star(start: Tile, target: Tile, domain: List[Tile]) -> List[Tile]:
    """
    A* path finding routine, in sparse hexagonal maps a relatively fast way of finding the shortest path
    from start to target
    As heuristic, I use the distance between two nodes

    :param start: start tile
    :param target: target tile
    :param domain: search domain which as to be explored. This has to be a connected graph. Also, start and finish
    should be part of the domain
    :return: a path, including the start and finish tile
    """
    if target not in domain or start not in domain:
        print("no pathfinding possible")
        return [start]

    start_node = AStarNode(start)
    end_node = AStarNode(target)

    open_list = []
    closed_list = []

    open_list.append(start_node)
    while len(open_list) > 0:
        current_node = open_list[0]
        current_index = 0
        for index, item in enumerate(open_list):
            if item.f < current_node.f:
                current_node = item
                current_index = index

        open_list.pop(current_index)
        closed_list.append(current_node)

        if current_node == end_node:
            path = []
            current = current_node
            while current is not None:
                path.append(current.base_tile)
                current = current.parent
            return path[::-1]   # is this the same as [::-1] <-> reverse?

        children = []
        for child in get_neighbours_on_set(current_node, domain):
            children.append(AStarNode(child, parent=current_node))

        for child in children:
            for c in closed_list:
                if child == c:
                    continue

            child.g = current_node.g + 1
            child.h = get_distance(end_node.base_tile, child.base_tile)
            child.f = child.g + child.h

            for open_node in open_list:
                if child == open_node and child.g > open_node.g:
                    continue

            open_list.append(child)


def dijkstra_pq(start: Tile, target: Tile, domain: List[Tile]) -> List[Tile]:
    """
    simple path-finding routine, based on dijkstra's algorithm
    This algorithm is inferior to a_star

    :param start: start Tile from where to start the search
    :param target: target Tile, search will abort upon reaching it
    :param domain: the search domain, start and target tile have to be part of the domain (!)
    :return: a sequence of connected tiles, which represent the path
    """
    pass
    # return bfs(start, target, domain)
    # path: List[Tile] = []
    # Q = []
    # for d in domain:
    #     d.dist = 1000
    #     d.pre = None
    #     Q.append(Item(d, 1000, None))
    # start.dist = 0
    # while len(Q) > 0:
    #     Q.sort(key=lambda x: x.dist, reverse=False)
    #     u = Q.pop(0)
    #     for v in get_neighbours_on_set(u.tile, domain):
    #         if v.has_army():
    #             print("attacking!!!!!!{}".format(v.offset_coordinates))
    #         if is_obj_in_list(v, domain) and v in Q:
    #             alt = u.dist + 1
    #             if alt < v.dist:
    #                 v.dist = alt
    #                 v.pre = u
    # x = target
    # path.append(x)
    # while x.offset_coordinates != start.offset_coordinates:
    #     x = x.pre
    #     path.append(x)
    #     if x is None:  # this is a bit weird in conjunction with the while condition.
    #         break
    #
    # for p in path:
    #     if p not in Q:
    #         print(f"PROBLEM {p.offset_coordinates}")
    # for d in domain:
    #     print(d.offset_coordinates, end = "")
    # print("")
    # # path.append(start)
    # path.reverse()
    # # check validity of path.
    # # problem = False
    # # for i in range(len(path) - 1):
    # #     if getDistance(path[i].offset_coordinates, path[i+1].offset_coordinates) != 1:
    # #         error("Problem in pathfinding")
    # #         problem = True
    # # if problem:
    # #     for p in path:
    # #         print(p.offset_coordinates, end=" ")
    # #     print("")
    # if start.offset_coordinates == path[0].offset_coordinates and\
    #         target.offset_coordinates == path[len(path) - 1].offset_coordinates:
    #     return path
    # else:
    #     debug("Found path is incomplete")
    #     for p in path:
    #         print(p.offset_coordinates, end="")
    #     print(" ")
    #     return [start]


def create_subset_by_cond(orig: Union[List[Tile], Set[Tile]], cond: Callable[[Tile], bool]) -> List[Tile]:
    """
    create a subset, where each element satisfies the condition
    wrapper function for a python list comprehension
    :param orig: original set
    :param cond: condition which has to be satisfied
    :return: subset
    """
    return [x for x in orig if cond(x)]


def get_tile_by_xy(coords, discovered_tiles: []):
    for e in discovered_tiles:
        if coords == e.offset_coordinates:
            return e
    return None


def get_neighbours_on_set(tile: Union[AI_OBJ, AStarNode], working_set: List[Tile]) -> List[Tile]:
    """

    :param tile:
    :param working_set: the domain, in which the neighbors are searched
    :return: a list of all neighbors of the tile, which are also in the working list
    """
    # return [x for x in get_neighbours(tile) if x in working_set]
    ret = []
    for x in get_neighbours(tile):
        for w in working_set:
            if x.offset_coordinates == w.offset_coordinates:
                ret.append(x)
    return ret


def get_neighbours(e: Union[AI_OBJ, AStarNode]) -> List[Tile]:
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


