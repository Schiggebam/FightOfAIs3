from typing import Optional, Dict, Any

import arcade

from src.game_accessoires import Drawable, Flag
from src.hex_map import Hexagon
from src.misc.game_constants import BuildingType, BuildingState, error


class Building(Drawable):

    building_info: Dict[BuildingType, Dict[str, Any]] = {}
    def __init__(self, tile: Hexagon, bui_type: BuildingType, owner_id):
        super().__init__()
        self.tile: Hexagon = tile
        self.associated_tiles: [Hexagon] = []
        self.associated_drawables: [Drawable] = []
        self.building_type: BuildingType = bui_type
        self.owner_id = owner_id
        self.building_state: BuildingState = BuildingState.ACTIVE
        self.__idx_texture_construction: int = -1
        self.__idx_texture_destruction: int = -1
        self.flag: Optional[Flag] = None
        # values from xml file
        self.tex_code = Building.building_info[bui_type]['tex_code']
        self.construction_cost = Building.building_info[bui_type]['construction_cost']
        self.culture_per_turn = Building.building_info[bui_type]['culture_per_turn']
        self.resource_per_field = Building.building_info[bui_type]['resource_per_field']
        self.resource_per_turn = Building.building_info[bui_type]['resource_per_turn']
        self.sight_range = Building.building_info[bui_type]['sight_range']
        self.description = Building.building_info[bui_type]['description']
        self.food_consumption = Building.building_info[bui_type]['food_consumption']
        self.construction_time = Building.building_info[bui_type]['construction_time']
        self.defensive_value = Building.building_info[bui_type]['defensive_value']
        self.flag_offset = (Building.building_info[bui_type]['flag_x'], Building.building_info[bui_type]['flag_y'])
        self.grant_pop = Building.building_info[bui_type]['grant_pop']

    def has_texture_construction(self) -> bool:
        return not self.__idx_texture_construction == -1

    def has_texture_destruction(self) -> bool:
        return not self.__idx_texture_destruction == -1

    def add_tex_construction(self, tex: arcade.Texture):
        super().add_texture(tex)
        self.__idx_texture_construction = self.tex_counter

    def add_tex_destruction(self, tex: arcade.Texture):
        super().add_texture(tex)
        self.__idx_texture_destruction = self.tex_counter

    def set_state_construction(self):
        """set the state of the building to 'construction', also changes its texture"""
        self.building_state = BuildingState.UNDER_CONSTRUCTION
        if self.has_texture_construction():
            super().set_active_texture(self.__idx_texture_construction)
        else:
            error("Building does not have a construction texture!")

    def set_state_destruction(self):
        """set the state of the building to 'destruction', also changes its texture"""
        self.building_state = BuildingState.DESTROYED
        if self.has_texture_destruction():
            super().set_active_texture(self.__idx_texture_destruction)
        else:
            error("Building does not have a destruction texture!")

    def set_state_active(self):
        """set the state of the building to 'active', also changes its texture"""
        self.building_state = BuildingState.ACTIVE
        super().set_active_texture(0)

    @staticmethod
    def get_construction_cost(bui_type: BuildingType):
        """in case we want to know the construction cost before the building is instance"""
        return Building.building_info[bui_type]['construction_cost']

