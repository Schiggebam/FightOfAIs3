import traceback
from typing import List, Tuple, Optional, Dict

from src.game_accessoires import Resource, Army
from src.hex_map import HexMap
from src.misc.building import Building
from src.misc.game_constants import GroundType, error, UnitType, ResourceType, BuildingType, BuildingState


class Tile:
    def __init__(self, o_c: Tuple[int, int], gt: GroundType):
        self.offset_coordinates: Tuple[int, int] = o_c
        self.ground_type: Optional[GroundType] = gt
        self.building: Optional[AI_Building] = None
        self.resource: Optional[AI_Resource] = None
        self.army: Optional[AI_Army] = None
        self.is_scoutable = False
        self.is_walkable = False
        self.is_buildable = False
        self.is_discovered = False

        self.tile_ne: Optional[Tile] = None
        self.tile_e: Optional[Tile] = None
        self.tile_se: Optional[Tile] = None
        self.tile_sw: Optional[Tile] = None
        self.tile_w: Optional[Tile] = None
        self.tile_nw: Optional[Tile] = None

        self.cube_coordinates = HexMap.offset_to_cube_coords(self.offset_coordinates)
        # for pathfinding:
        self.pre: Optional[Tile] = None
        self.dist: int = 0

    def has_resource(self):
        return self.resource is not None

    def has_building(self):
        return self.building is not None

    def has_army(self):
        return self.army is not None

    def has_n_ne(self):
        return self.tile_ne is not None

    def has_n_e(self):
        return self.tile_e is not None

    def has_n_se(self):
        return self.tile_se is not None

    def has_n_sw(self):
        return self.tile_sw is not None

    def has_n_w(self):
        return self.tile_w is not None

    def has_n_nw(self):
        return self.tile_nw is not None

class AI_Element:
    def __init__(self, t: Tile):
        self.base_tile: Tile = t
        self.offset_coordinates: Tuple[int, int] = self.base_tile.offset_coordinates

class AI_Army(AI_Element):
    def __init__(self, t: Tile):
        super().__init__(t)
        self.owner: int = -1
        self.population: int = -1
        self.knights: int = -1
        self.mercenaries: int = -1
        self.barbaric_soldiers: int = -1


class AI_Resource(AI_Element):
    def __init__(self, t: Tile):
        super().__init__(t)
        self.type: Optional[ResourceType] = None
        self.amount = -1


class AI_Building(AI_Element):
    def __init__(self, t: Tile):
        super().__init__(t)
        self.type: Optional[BuildingType] = None
        self.state: Optional[BuildingState] = None
        self.owner: int = -1  # if this is -1, it means that this is not a enemy building. Otherwise the player_id is stored here
        self.associated_tiles: List[Tile] = []

class Map:
    def __init__(self):
        self.map: Dict[Tuple[int, int], Tile] = {}
        # additional list which contain subsets of map (only the reference on the actual tile) for fast reference
        self.resource_list: List[AI_Resource] = []
        self.army_list: List[AI_Army] = []
        self.opp_army_list: List[AI_Army] = []
        self.building_list: List[AI_Building] = []
        self.opp_building_list: List[AI_Building] = []
        self.scoutable_tiles: List[Tile] = []
        self.buildable_tiles: List[Tile] = []
        self.walkable_tiles: List[Tile] = []
        self.farm_field_tiles: List[Tile] = []
        self.discovered_tiles: List[Tile] = []

    def add_tile(self, offset_coordinates: Tuple[int, int], gt: GroundType):
        """after instantiation, fill the map. No tile with the same coordinates should be added twice"""
        self.map[offset_coordinates] = (Tile(offset_coordinates, gt))

    def connect_graph(self):
        """call this after all tiles have been added (or to recreate the bonds)"""
        for _, v in self.map.items():
            for _, o_v in self.map.items():
                other_cc = o_v.cube_coordinates
                if HexMap.get_cc_northeast(other_cc) == v.cube_coordinates:
                    v.tile_sw = o_v
                if HexMap.get_cc_east(other_cc) == v.cube_coordinates:
                    v.tile_w = o_v
                if HexMap.get_cc_southeast(other_cc) == v.cube_coordinates:
                    v.tile_nw = o_v
                if HexMap.get_cc_southwest(other_cc) == v.cube_coordinates:
                    v.tile_ne = o_v
                if HexMap.get_cc_west(other_cc) == v.cube_coordinates:
                    v.tile_e = o_v
                if HexMap.get_cc_northwest(other_cc) == v.cube_coordinates:
                    v.tile_se = o_v

    def add_resource(self, offset_coordinates: Tuple[int, int], res: Resource):
        tile = self.__get_tile(offset_coordinates)
        ai_r = AI_Resource(tile)
        ai_r.type = res.resource_type
        ai_r.amount = res.remaining_amount
        self.resource_list.append(ai_r)
        tile.resource = ai_r

    def add_own_army(self, offset_coordinates: Tuple[int, int], army: Army):
        army: AI_Army = self.__add_army(offset_coordinates, army)
        self.army_list.append(army)

    def add_opp_army(self, offset_coordinates: Tuple[int, int], army: Army, id: int):
        army: AI_Army = self.__add_army(offset_coordinates, army)
        army.owner = id
        self.opp_army_list.append(army)

    def add_own_building(self, offset_coordinates: Tuple[int, int], building: Building):
        b: AI_Building = self.__add_building(offset_coordinates, building)
        self.building_list.append(b)

    def add_opp_building(self, offset_coordinates: Tuple[int, int], building: Building, id: int):
        b: AI_Building = self.__add_building(offset_coordinates, building)
        b.owner = id
        self.opp_building_list.append(b)

    def set_scoutable_tile(self, offset_coordinates: Tuple[int, int]):
        tile: Tile = self.__get_tile(offset_coordinates)
        self.scoutable_tiles.append(tile)
        tile.is_scoutable = True

    def set_buildable_tile(self, offset_coordinates: Tuple[int, int]):
        tile: Tile = self.__get_tile(offset_coordinates)
        self.buildable_tiles.append(tile)
        tile.is_buildable = True

    def set_walkable_tile(self, offset_coordinates: Tuple[int, int]):
        tile: Tile = self.__get_tile(offset_coordinates)
        self.walkable_tiles.append(tile)
        tile.is_walkable = True

    def set_discovered_tile(self, offset_coordinates: Tuple[int, int]):
        tile: Tile = self.__get_tile(offset_coordinates)
        self.discovered_tiles.append(tile)
        tile.is_discovered = True

    def __add_army(self, offset_coordinates: Tuple[int, int], army: Army) -> AI_Army:
        tile = self.__get_tile(offset_coordinates)
        ai_a = AI_Army(tile)
        ai_a.population = army.get_population()
        ai_a.knights = army.get_population_by_unit(UnitType.KNIGHT)
        ai_a.mercenaries = army.get_population_by_unit(UnitType.MERCENARY)
        ai_a.barbaric_soldiers = army.get_population_by_unit(UnitType.BABARIC_SOLDIER)
        tile.army = ai_a
        return ai_a

    def __add_building(self, offset_coordinates: Tuple[int, int], building: Building) -> AI_Building:
        tile = self.__get_tile(offset_coordinates)
        ai_b = AI_Building(tile)
        ai_b.offset_coordinates = building.tile.offset_coordinates
        ai_b.type = building.building_type
        ai_b.state = building.building_state
        for a in building.associated_tiles:
            t = self.__get_tile(a.offset_coordinates)
            ai_b.associated_tiles.append(t)
            self.farm_field_tiles.append(t)
        return ai_b

    def get_tile(self, offset_coordinates: Tuple[int, int]) -> Tile:
        return self.__get_tile(offset_coordinates)

    def __get_tile(self, offset_coordinates) -> Optional[Tile]:
        try:
            tile = self.map[offset_coordinates]
            if not tile:
                error("Tile not part of the map -> dict key error")
                return None
            return tile
        except KeyError:
            error(f"Caught Key error for key {offset_coordinates}, available keys are:")
            for k, _ in self.map.items():
                print(str(k), end="")
            print("")
            traceback.print_exc()
            raise KeyError



    def print_map(self):
        for k, v in self.map.items():
            print(f" {v.tile_ne}  {v.tile_e} {v.tile_se} {v.tile_sw} {v.tile_w} {v.tile_nw}")
            print(v.tile_sw)
            print(v.tile_sw)
            print(v.tile_sw)
        # for v in self.discovered_tiles:
        #     if v.has_resource():
        #         print(f"{v.offset_coordinates} -> {v.tile_ne} {v.tile_e} {v.tile_se} {v.tile_sw} {v.tile_w} {v.tile_nw}")
        # print("more shit")
        # for k, v in self.map.items():
        #     if v.is_buildable:
        #         print(f"{v.offset_coordinates} -> {v.tile_ne} {v.tile_e} {v.tile_se} {v.tile_sw} {v.tile_w} {v.tile_nw}")
