from math import sqrt

import arcade

from src.ai import AI_Toolkit
from src.game_accessoires import Unit
from src.game_logic import GameLogic, Army
from src.hex_map import *
from src.ai.AI_GameStatus import AI_Move, AI_GameStatus
from src.misc.building import Building
from src.misc.game_constants import MoveType, BuildingType, UnitType


class HI_State(Enum):
    INACTIVE = 0
    SELECTION = 1
    GRIDMODE = 2
    SPECIFY_FIELDS = 3
    SPECIFY_MOVEMENT = 4

class Action(Enum):
    BUILD_HUT = 70
    BUILD_FARM = 71
    BUILD_RACKS = 72
    RECRUIT_KNIGHT = 73
    RECRUIT_MERC = 74
    SCOUT = 75
    ARMY_MOVEMENT = 76
    NONE = 79


class SelectionTool(arcade.Sprite):
    def __init__(self):
        super().__init__(center_x=0, center_y=0)
        tex = arcade.load_texture("../resources/objects/selection_far.png")
        self.append_texture(tex)
        self.alpha = 200
        self.set_texture(0)

class SelectionIcon(arcade.Sprite):
    def __init__(self, center_x, center_y, textures: Tuple[arcade.Texture, arcade.Texture, arcade.Texture],
                 action: Action, hexagon: Hexagon, width=76, height=66, is_active=True, scale=0.75):
        super().__init__(scale=scale, center_x=center_x, center_y=center_y)
        self.append_texture(textures[1])
        self.append_texture(textures[0])
        self.append_texture(textures[2])
        self.width = width
        self.height = height

        self.action = action
        self.hex = hexagon
        self.highlighted = False
        self.is_active = is_active
        if not self.is_active:
            self.set_texture(2)
        else:
            self.set_texture(1)

    def highlight(self):
        if self.is_active:
            self.highlighted = True
            self.set_texture(0)

    def normal(self):
        if self.is_active:
            self.highlighted = False
            self.set_texture(1)

    def gray_out(self):
        self.is_active = False
        self.set_texture(2)


class HumanInteraction:

    def __init__(self, gl: GameLogic, zlvl_selection_tool: arcade.SpriteList, zlvl_icons):
        self.is_active = True
        self.camera_pos: Tuple[int, int] = (0, 0)
        self.selection_tool = SelectionTool()
        self.zlvl_icons: arcade.SpriteList = zlvl_icons
        zlvl_selection_tool.append(self.selection_tool)
        self.gl: GameLogic = gl
        self.state: HI_State = HI_State.INACTIVE
        self.move: Optional[AI_Move] = None
        self.game_status: Optional[AI_GameStatus] = None
        self.active_selection: List[SelectionIcon] = []
        self.active_hexagon: Optional[Hexagon] = None
        self.candidates: Optional[List[SelectionIcon]] = []

        res = '../resources/other/hi/'
        #FIXME let the texture store do this
        self.textures = {'hi_build_farm': (arcade.load_texture(res + 'hi_build_farm_np.png'),
                                           arcade.load_texture(res + 'hi_build_farm_p.png'),
                                           arcade.load_texture(res + 'hi_build_farm_gray.png')),
                         'hi_build_hut': (arcade.load_texture(res + 'hi_build_hut_np.png'),
                                          arcade.load_texture(res + 'hi_build_hut_p.png'),
                                          arcade.load_texture(res + 'hi_build_hut_gray.png')),
                         'hi_build_racks': (arcade.load_texture(res + 'hi_build_racks_np.png'),
                                            arcade.load_texture(res + 'hi_build_racks_p.png'),
                                            arcade.load_texture(res + 'hi_build_racks_gray.png')),
                         'hi_move_army': (arcade.load_texture(res + 'hi_move_army_np.png'),
                                          arcade.load_texture(res + 'hi_move_army_p.png'),
                                          arcade.load_texture(res + 'hi_move_army_gray.png')),
                         'hi_recruit_merc': (arcade.load_texture(res + 'hi_recruit_merc_np.png'),
                                             arcade.load_texture(res + 'hi_recruit_merc_p.png'),
                                             arcade.load_texture(res + 'hi_recruit_merc_gray.png')),
                         'hi_recruit_knight': (arcade.load_texture(res + 'hi_recruit_knight_np.png'),
                                               arcade.load_texture(res + 'hi_recruit_knight_p.png'),
                                               arcade.load_texture(res + 'hi_recruit_knight_gray.png')),
                         'hi_scout': (arcade.load_texture(res + 'hi_scout_np.png'),
                                      arcade.load_texture(res + 'hi_scout_p.png'),
                                      arcade.load_texture(res + 'hi_scout_gray.png')),
                         'hi_specify': (arcade.load_texture(res + 'hi_specify_1.png'),
                                        arcade.load_texture(res + 'hi_specify_2.png'),
                                        arcade.load_texture(res + 'hi_specify_2.png'))}


    def get_icon_coordinates(self, pos: Tuple[int, int], num: int) -> List[Tuple[int, int]] :
        if num == 1:
            return [(pos[0], pos[1] + 35)]
        elif num == 2:
            return [(pos[0]- 30, pos[1] + 25), (pos[0] + 30, pos[1] + 25)]
        elif num == 3:
            return [(pos[0], pos[1] + 50), (pos[0], pos[1] - 50),
                    (pos[0] + 50, pos[1])]
        elif num == 4:
            return [(pos[0], pos[1] + 50), (pos[0], pos[1] - 50),
                    (pos[0] + 50, pos[1]), (pos[0] - 50, pos[1])]
        return []

    def show_selection_tool(self, mouse_x: int, mouse_y: int):
        # CODE TO COMPUTE "snapping to grid" explicitly. Keep this for now
        # This variant should be a bit faster (because we don't have to go via the hexmap),
        # but the second option allows to respect the height of the hexagon (sea-level - vs land-level)
        # also we get a reference to the hex for free, which is handy
        # idx_x = 0
        # idx_aligned_x = 0
        # idx_y = round((mouse_y - BOTTOM_MARGIN - self.camera_pos[1]) / (TILE_HIGHT / 2))
        # if idx_y % 2 != 0:
        #     idx_x = round((mouse_x - TILEMAP_ORIGIN_X - TILE_WIDTH/2 - self.camera_pos[0]) / TILE_WIDTH)
        #     idx_aligned_x = idx_x + 0.5
        # else:
        #     idx_x = round((mouse_x - TILEMAP_ORIGIN_X - self.camera_pos[0]) / TILE_WIDTH)
        #     idx_aligned_x = idx_x
        # xx = idx_aligned_x * TILE_WIDTH + TILEMAP_ORIGIN_X + self.camera_pos[0]
        # yy = idx_y * (TILE_HIGHT/2) + BOTTOM_MARGIN + self.camera_pos[1] - 4  # -4 is due to the texture offset
        if self.state == HI_State.GRIDMODE:
            h = self.gl.hex_map.get_hex_by_pixel((mouse_x, mouse_y), self.camera_pos)
            xx = h.ground.sprite.center_x
            yy = h.ground.sprite.center_y - 4

            self.selection_tool.center_x = xx
            self.selection_tool.center_y = yy
        if self.state == HI_State.SELECTION:
            for icon in self.active_selection:
                if self.__check_icon_boudning_box(mouse_x, mouse_y, icon):
                    if not icon.highlighted:
                        icon.highlight()
                else:
                    if icon.highlighted:
                        icon.normal()
        elif self.state == HI_State.SPECIFY_MOVEMENT or self.state == HI_State.SPECIFY_FIELDS:
            for icon in self.candidates:
                if self.__check_icon_boudning_box(mouse_x, mouse_y, icon):
                    if not icon.highlighted:
                        icon.highlight()
                else:
                    if icon.highlighted:
                        icon.normal()

    def handle_click(self, mouse_x: int, mouse_y: int):
        if self.state == HI_State.SPECIFY_FIELDS:
            if self.active_hexagon:
                for n in self.candidates:
                    if self.__check_icon_boudning_box(mouse_x, mouse_y, n):
                        if n.is_active:
                            self.move.info.append(n.hex.offset_coordinates)
                            n.gray_out()

                if len(self.move.info) == 3:
                    self.active_hexagon = None
                    self.set_state(HI_State.GRIDMODE)

            else:
                error("this is a problem 0")
        elif self.state == HI_State.SPECIFY_MOVEMENT:
            if self.active_hexagon:
                for n in self.candidates:
                    if self.__check_icon_boudning_box(mouse_x, mouse_y, n):
                        self.move.move_army_to = n.hex.offset_coordinates
                        self.active_hexagon = None
                        self.set_state(HI_State.GRIDMODE)
                        n.gray_out()
            else:
                error("this is a problem 1")
        elif self.state == HI_State.SELECTION:
            action = None
            active_icon = None
            candidates = []
            for icon in self.active_selection:
                if self.__check_icon_boudning_box(mouse_x, mouse_y, icon):
                    action = icon.action
                    active_icon = icon
            if action:
                if action == Action.BUILD_FARM:
                    self.move.type = BuildingType.FARM
                    self.move.move_type = MoveType.DO_BUILD
                    self.move.loc = active_icon.hex.offset_coordinates
                    self.active_hexagon = active_icon.hex
                    candidates = [x for x in self.gl.hex_map.get_neighbours(self.active_hexagon) if x.ground.buildable
                                  and AI_Toolkit.is_obj_in_list(x, self.game_status.map.discovered_tiles)]
                    self.set_state(HI_State.SPECIFY_FIELDS)
                elif action == Action.BUILD_HUT:
                    self.move.type = BuildingType.HUT
                    self.move.move_type = MoveType.DO_BUILD
                    self.move.loc = active_icon.hex.offset_coordinates
                    self.set_state(HI_State.GRIDMODE)
                elif action == Action.BUILD_RACKS:
                    self.move.type = BuildingType.BARRACKS
                    self.move.move_type = MoveType.DO_BUILD
                    self.move.loc = active_icon.hex.offset_coordinates
                    self.set_state(HI_State.GRIDMODE)
                elif action == Action.RECRUIT_KNIGHT:
                    self.move.type = UnitType.KNIGHT
                    self.move.move_type = MoveType.DO_RECRUIT_UNIT
                    self.set_state(HI_State.GRIDMODE)
                elif action == Action.RECRUIT_MERC:
                    self.move.type = UnitType.MERCENARY
                    self.move.move_type = MoveType.DO_RECRUIT_UNIT
                    self.set_state(HI_State.GRIDMODE)
                elif action == Action.SCOUT:
                    self.move.move_type = MoveType.DO_SCOUT
                    self.move.loc = active_icon.hex.offset_coordinates
                    self.set_state(HI_State.GRIDMODE)
                elif action == Action.ARMY_MOVEMENT:
                    self.move.doMoveArmy = True
                    self.active_hexagon = active_icon.hex
                    candidates = [x for x in self.gl.hex_map.get_neighbours(self.active_hexagon) if x.ground.walkable
                                  and AI_Toolkit.is_obj_in_list(x, self.game_status.map.discovered_tiles)]
                    self.set_state(HI_State.SPECIFY_MOVEMENT)
                    ######
                for c in candidates:
                    pix_c = HexMap.offset_to_pixel_coords(c.offset_coordinates)
                    si = SelectionIcon(pix_c[0], pix_c[1], self.textures['hi_specify'], Action.NONE, c, scale=0.9)
                    self.zlvl_icons.append(si)
                    self.candidates.append(si)
            else:
                self.set_state(HI_State.GRIDMODE)
            for icon in self.active_selection:
                self.zlvl_icons.remove(icon)
            self.active_selection.clear()

        elif self.state == HI_State.GRIDMODE:
            h = self.gl.hex_map.get_hex_by_pixel((mouse_x, mouse_y), self.camera_pos)
            obj, obj_class = self.gl.get_map_element(h.offset_coordinates)

            # tiles is scoutable
            if AI_Toolkit.is_obj_in_list(h, self.game_status.map.scoutable_tiles):
                has_res_for_scouting = self.game_status.me.resources >= 1
                pos_list = self.get_icon_coordinates((mouse_x, mouse_y), 1)
                self.active_selection.append(SelectionIcon(pos_list[0][0], pos_list[0][1],
                                                           self.textures['hi_scout'],
                                                           Action.SCOUT, h, is_active=has_res_for_scouting))
            # tile is buildable
            elif obj is None and h is not None:
                if AI_Toolkit.is_obj_in_list(h, self.game_status.map.buildable_tiles):
                    has_res_for_hut = Building.building_info[BuildingType.HUT]['construction_cost'] <= self.game_status.me.resources
                    has_res_for_farm = Building.building_info[BuildingType.FARM]['construction_cost'] <= self.game_status.me.resources
                    has_res_for_racks = Building.building_info[BuildingType.BARRACKS]['construction_cost'] <= self.game_status.me.resources
                    pos_list = self.get_icon_coordinates((mouse_x, mouse_y), 3)
                    idx = 0
                    self.active_selection.append(SelectionIcon(pos_list[idx][0], pos_list[idx][1],
                                                 self.textures['hi_build_farm'],
                                                 Action.BUILD_FARM, h, is_active=has_res_for_farm))
                    idx += 1
                    self.active_selection.append(SelectionIcon(pos_list[idx][0], pos_list[idx][1],
                                                 self.textures['hi_build_hut'],
                                                 Action.BUILD_HUT, h, is_active=has_res_for_hut))
                    idx += 1
                    self.active_selection.append(SelectionIcon(pos_list[idx][0], pos_list[idx][1],
                                                 self.textures['hi_build_racks'],
                                                 Action.BUILD_RACKS, h, is_active=has_res_for_racks))

                else:
                    # at this point it is not scoutable nor buildable
                    print("hello")
                    return

            elif obj_class is Army:
                if AI_Toolkit.is_obj_in_list(obj.tile, self.game_status.map.army_list):
                    merc_cost = Unit.get_unit_cost(UnitType.MERCENARY)
                    knight_cost = Unit.get_unit_cost(UnitType.KNIGHT)
                    has_res_for_merc = self.game_status.me.resources >= merc_cost.resources and \
                        self.game_status.me.culture >= merc_cost.culture and \
                        self.game_status.me.population + merc_cost.population <= self.game_status.me.population_limit
                    has_res_for_knight = self.game_status.me.resources >= knight_cost.resources and \
                        self.game_status.me.culture >= knight_cost.culture and \
                        self.game_status.me.population + knight_cost.population <= self.game_status.me.population_limit
                    pos_list = self.get_icon_coordinates((mouse_x, mouse_y), 3)
                    idx = 0
                    self.active_selection.append(SelectionIcon(pos_list[idx][0], pos_list[idx][1],
                                                               self.textures['hi_recruit_merc'],
                                                               Action.RECRUIT_MERC, h, is_active=has_res_for_merc))
                    idx += 1
                    self.active_selection.append(SelectionIcon(pos_list[idx][0], pos_list[idx][1],
                                                               self.textures['hi_recruit_knight'],
                                                               Action.RECRUIT_KNIGHT, h, is_active=has_res_for_knight))
                    idx += 1
                    self.active_selection.append(SelectionIcon(pos_list[idx][0], pos_list[idx][1],
                                                               self.textures['hi_move_army'],
                                                               Action.ARMY_MOVEMENT, h, is_active=True))
            for ai in self.active_selection:
                self.zlvl_icons.append(ai)
            self.set_state(HI_State.SELECTION)


    def set_state(self, state: HI_State):
        if state == HI_State.GRIDMODE:
            for c in self.candidates:
                self.zlvl_icons.remove(c)
            self.candidates.clear()
            self.selection_tool.alpha = 200
            self.selection_tool.center_x = -50
            self.selection_tool.center_y = -50      # small hack to make it appear only on first mouse move
        else:
            self.selection_tool.alpha = 0
        self.state = state

    def request_move(self, status: AI_GameStatus, move: AI_Move, pid: int):
        self.set_state(HI_State.GRIDMODE)
        self.move = move
        self.game_status = status


    def get_move(self):
        if self.move.move_type is None:
            self.move.move_type = MoveType.DO_NOTHING
        self.set_state(HI_State.INACTIVE)
        return self.move

    def __check_icon_boudning_box(self, x, y, icon: SelectionIcon) -> bool:
        # Elliptical bounding box
        dist = sqrt(((x - icon.center_x)*0.5 * (x - icon.center_x)*0.5) +
                    ((y - icon.center_y) * (y - icon.center_y)))
        if dist < 15:
            return True
        return False

        # Rectangular Bounding Box
        # if (icon.center_x - icon.width / 2) < x < (icon.center_x + icon.width / 2):
        #     if (icon.center_y - icon.height / 2) < y < (icon.center_y + icon.height / 2):
        #         return True
        # return False