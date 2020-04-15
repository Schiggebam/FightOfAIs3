from typing import Optional

import arcade

from src.game_accessoires import Drawable, Flag
from src.hex_map import Hexagon
from src.misc.game_constants import BuildingType, BuildingState, error, hint


class Building(Drawable):

    building_info: [(int, {})] = []
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
        for b_info in Building.building_info:
            if b_info[0] == bui_type:
                self.tex_code = b_info[1]['tex_code']
                self.construction_cost = b_info[1]['construction_cost']
                self.culture_per_turn = b_info[1]['culture_per_turn']
                self.resource_per_field = b_info[1]['resource_per_field']
                self.resource_per_turn = b_info[1]['resource_per_turn']
                self.sight_range = b_info[1]['sight_range']
                self.description = b_info[1]['description']
                self.food_consumption = b_info[1]['food_consumption']
                self.construction_time = b_info[1]['construction_time']
                self.defensive_value = b_info[1]['defensive_value']
                self.flag_offset = (b_info[1]['flag_x'], b_info[1]['flag_y'])
                self.grant_pop = b_info[1]['grant_pop']

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
        self.building_state = BuildingState.UNDER_CONSTRUCTION
        if self.has_texture_construction():
            super().set_active_texture(self.__idx_texture_construction)
            hint("Construction texture at: " + str(self.__idx_texture_construction))
        else:
            error("Building does not have a construction texture!")

    def set_state_destruction(self):
        self.building_state = BuildingState.DESTROYED
        if self.has_texture_destruction():
            super().set_active_texture(self.__idx_texture_destruction)
        else:
            error("Building does not have a destruction texture!")

    def set_state_active(self):
        self.building_state = BuildingState.ACTIVE
        super().set_active_texture(0)

    @staticmethod
    def get_construction_cost(bui_type: BuildingType):
        """in case we want to know the construction cost before the building is instance"""
        for b_info in Building.building_info:
            if b_info[0] == bui_type:
                return b_info[1]['construction_cost']