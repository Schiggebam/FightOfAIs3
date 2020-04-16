import copy
import queue
from typing import List, Callable, Union, Tuple

from src.ai.AI_GameStatus import AI_Tile, AI_Element

AI_OBJ = Union[AI_Element, AI_Tile]

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
        nei = getListDistanceOne(s, working_set)
        for n in nei:
            if n not in discovered and condition(n):
                tmp.put((d + 1, n))
    return heat_map

def estimate_income(list_buildings):
    pass

def dijkstra(start, target, domain, path):
    if not start or not target:
        path = []
        return
    #print("Start: " + str(start.x_grid)  + "|" + str(start.y_grid))
    #print("target: " + str(target.x_grid)  + "|" + str(target.y_grid))
    #print("domain: ")
    #for d in domain:
    #    print(str(d.x_grid) + "|" + str(d.y_grid) + " ", end="")
    Q = domain.copy()
    for t in domain:
        t.dist = 100
        t.pre = None
    start.dist = 0
    while len(Q)>0:
        smallest = 1000
        u = None
        for q in Q:
            if q.dist < smallest:
                u = q
                smallest = q.dist
        if u is None:
            print("ERROR: " + str(len(Q)))
        Q.remove(u)
        nei = getListDistanceOne(u, Q)
        for v in nei:
            a = u.dist + 1
            if a < v.dist:
                v.dist = a
                v.pre = u

    #print("path: ")
    x = target
    while x is not None:
    #    print(" " + str(x.x_grid) + "|" + str(x.y_grid) + " ", end="")
        path.append(x)
        x = x.pre
    #print(" ")
    path.reverse()
    #if path[0].x_grid == target.x_grid and path[0].y_grid == target.y_grid:
    #    path = None


def get_tile_by_xy(coords, discovered_tiles : []):
    for e in discovered_tiles:
        if coords == e.offset_coordinates:
            return e
    return None


def getListDistanceOne(t1, li):     # get neighbours
    res = []
    for t2 in li:
        if getDistance(t1, t2) == int(1):
            res.append(t2)
    return list(filter(None, res))


def getDistance(t1, t2):
    # dy = float(abs(t1.y_grid - t2.y_grid))
    # dx = float(abs(t1.x_grid - t2.x_grid))
    # return int(dy + max(math.ceil(dx - dy / float(2)), float(0)))
    cube_coords_t1 = offset_to_cube_coord(t1)
    cube_coords_t2 = offset_to_cube_coord(t2)
    dist = cube_distance(cube_coords_t1, cube_coords_t2)
    return dist

def getDistance_xy(a:(int, int), b:(int, int)):
    cube_coords_1 = offset_to_cube_xy(a[0], a[1])
    cube_coords_2 = offset_to_cube_xy(b[0], b[1])
    return cube_distance(cube_coords_1, cube_coords_2)


#def cube_to_offset_coord(cube):
#    col = cube.x + (cube.z - (cube.z&1)) / 2
#    row = cube.z
#    return row, col

def offset_to_cube_xy(x,y):
    c_x = x - (y - (y & 1)) / 2
    c_z = y
    c_y = -c_x - c_z
    return c_x, c_y, c_z

def get_resource_on_tile_xy(offset_c: (int, int), res_list):
    for r in res_list:
        if r.offset_coordinates == offset_c:
            return r
    return None


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