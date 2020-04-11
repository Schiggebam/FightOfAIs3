from enum import Enum

import arcade

from src.hex_map import Hexagon
from src.misc.game_constants import ResourceType, error, hint, GroundType


class Drawable:
    def __init__(self):
        self.sprite: arcade.Sprite = arcade.Sprite()
        self.tex_counter = -1                       # this variable is supposed to count the number of textures
        self.__active_tex = -1
        self.tex_code = ""
        self.offset = (0, 0)

    def set_sprite_pos(self, pos_pixel: (int, int)):
        self.sprite.center_x = pos_pixel[0] + self.offset[0]
        self.sprite.center_y = pos_pixel[1] + self.offset[1]

    def add_texture(self, tex: arcade.Texture):
        if self.__active_tex == -1:
            self.__active_tex = 0
        self.sprite.append_texture(tex)
        self.tex_counter = self.tex_counter + 1
        self.sprite.set_texture(self.__active_tex)            # preserve the idx

    def set_tex_offset(self, offset: (int, int)):
        self.offset = offset
        self.sprite.center_x = self.sprite.center_x + offset[0]
        self.sprite.center_y = self.sprite.center_y + offset[1]

    def set_tex_scale(self, scale: float):
        self.sprite.scale = scale

    def set_active_texture(self, idx: int):
        if self.tex_counter >= idx:
            self.sprite.set_texture(idx)
            self.__active_tex = idx
        else:
            error("Drawable: No texture at index: " + str(idx))


class Ground(Drawable):

    def __init__(self, str_code: str):
        super().__init__()
        self.walkable: bool = False
        self.buildable: bool = False
        self.ground_type: GroundType = GroundType.get_type_from_strcode(str_code)

class Resource(Drawable):
    """class ResourceType(Enum):
        ROCK = 10
        GOLD = 11
        FOREST = 12

        @staticmethod
        def get_type_from_strcode(str_code:str):
            if str_code == "r1":
                return Resource.ResourceType.ROCK
            elif str_code == "g1":
                return Resource.ResourceType.GOLD
            elif str_code == "f1":
                return Resource.ResourceType.GOLD
            return -1"""
    # end of class ResourceType

    # e.g. ('Resource.ResourceType.GOLD', {amount: 150, ...}
    resource_info: [(int, {})] = [] # a dict containing all information about the resources

    def __init__(self, tile: Hexagon, res_type: int):
        super().__init__()
        self.tile: Hexagon = tile
        self.remaining_amount: int = int(0)
        self.resource_type: ResourceType = res_type
        for r_info in Resource.resource_info:
            if r_info[0] == res_type:
                self.remaining_amount = r_info[1]['amount']

    def demand_res(self, request):
        if request <= self.remaining_amount:
            self.remaining_amount = self.remaining_amount - request
            return request
        else:
            remaining = self.remaining_amount
            self.remaining_amount = 0
            return remaining




class Army(Drawable):
    def __init__(self, tile: Hexagon, owner_id):
        super().__init__()
        self.tile: Hexagon = tile
        self.strength: int = 1
        self.owner_id: int = owner_id
        self.is_barbaric: bool = False

    def upgrade(self):
        self.strength = self.strength + 1

    def get_upgrade_cost(self):
        if not self.is_barbaric:
            return int(self.strength * 3)           # culture
        else:
            return int(self.strength * 2)       # resources


class Scenario():
    def __init__(self):
        self.resource_list: [Resource] = []
        self.aux_sprites: [(Hexagon, Drawable)] = []

