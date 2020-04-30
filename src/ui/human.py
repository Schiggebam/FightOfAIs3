from math import sqrt

import arcade

from src.ai import AI_Toolkit
from src.game_accessoires import Unit
from src.game_logic import GameLogic, Army
from src.hex_map import *
from src.ai.AI_GameStatus import AI_Move, AI_GameStatus
from src.misc.building import Building
from src.misc.game_constants import MoveType, BuildingType, UnitType, PlayerType
from src.misc.game_logic_misc import Logger
from src.ui.ui_accessoires import CustomCursor
from src.ui.ui_panels import CostPanel


class HI_State(Enum):
    INACTIVE = 0
    SELECTION = 1
    GRIDMODE = 2
    SPECIFY_FIELDS = 3
    SPECIFY_MOVEMENT = 4


class MoveState(Enum):
    WAIT = 0
    READY = 1
    USED = 2


class Action(Enum):
    BUILD_HUT = 70
    BUILD_FARM = 71
    BUILD_RACKS = 72
    RECRUIT_KNIGHT = 73
    RECRUIT_MERC = 74
    SCOUT = 75
    ARMY_MOVEMENT = 76
    RAISE_ARMY = 77
    NONE = 79


class SelectionTool(arcade.Sprite):
    """Represents the tool which is draged along the mouse to select a tile"""
    def __init__(self):
        super().__init__(center_x=0, center_y=0)
        tex = arcade.load_texture("../resources/objects/selection_far.png")
        self.append_texture(tex)
        self.alpha = 200
        self.set_texture(0)


class SelectionIcon(arcade.Sprite):
    """Class represents an icon to select an action, may be bound to a hex, an action is taking 3 texture, to display
    the icon in highlighted, neutral and disabled mode"""
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
        self.info_text: str = ""
        if not self.is_active:
            self.gray_out()
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
        if self.action == Action.BUILD_RACKS:
            self.info_text = "Not enough resources to build a barracks"
        elif self.action == Action.BUILD_HUT:
            self.info_text = "Not enough resources to build a hut"
        elif self.action == Action.BUILD_FARM:
            self.info_text = "Not enough resources to build a farm"
        elif self.action == Action.RECRUIT_KNIGHT:
            self.info_text = "Not enough resources/culture/population to recruit a knight"
        elif self.action == Action.RECRUIT_MERC:
            self.info_text = "Not enough resource/culture/population to recruit a mercenary"
        elif self.action == Action.RAISE_ARMY:
            self.info_text = "Cannot raise an army if there is already a existing army"
        elif self.action == Action.SCOUT:
            self.info_text = "You need at least 1 resource to scout"
        elif self.action == Action.ARMY_MOVEMENT:
            self.info_text = "Army has to have at least 1 unit so it can move."
        else:
            self.info_text = ""


class HumanInteraction:
    """defines the interaction between a human player and the game"""
    def __init__(self, gl: GameLogic,  zlvl_selection_tool: arcade.SpriteList, zlvl_icons):
        self.is_active = True
        self.movement_specified: MoveState = MoveState.WAIT
        self.action_specified: MoveState = MoveState.WAIT
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
        self.cursor: Optional[CustomCursor] = None
        self.set_cost_panel = None
        self.cost_panel: Optional[CostPanel] = None

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
                                        arcade.load_texture(res + 'hi_specify_2.png')),
                         'hi_raise_army': (arcade.load_texture(res + 'hi_raise_army_np.png'),
                                           arcade.load_texture(res + 'hi_raise_army_p.png'),
                                           arcade.load_texture(res + 'hi_raise_army_gray.png'))}

    def set_ui_references(self, cursor: CustomCursor, cost_panel_callback):
        self.cursor = cursor
        self.set_cost_panel = cost_panel_callback

    def get_icon_coordinates(self, pos: Tuple[int, int], num: int) -> List[Tuple[int, int]] :
        """the location of the icons (up to 4) is hardcoded"""
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

    def handle_mouse_motin(self, mouse_x: int, mouse_y: int):
        # CODE TO COMPUTE "snapping to grid" explicitly. Keep this for now
        # !!!!!!!!!!!!!!!!!!!!!!!!
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
            active_icon = None
            for icon in self.active_selection:
                if self.__check_icon_boudning_box(mouse_x, mouse_y, icon):
                    active_icon = icon
                    if not icon.highlighted:
                        icon.highlight()
                else:
                    if icon.highlighted:
                        icon.normal()

            if active_icon is not None:
                self.show_cost_panel(active_icon, mouse_x, mouse_y)
            else:
                if self.cost_panel.show:
                    self.hide_cost_panel()

        elif self.state == HI_State.SPECIFY_MOVEMENT or self.state == HI_State.SPECIFY_FIELDS:
            for icon in self.candidates:
                if self.__check_icon_boudning_box(mouse_x, mouse_y, icon):
                    if not icon.highlighted:
                        icon.highlight()
                else:
                    if icon.highlighted:
                        icon.normal()

            if self.cursor:
                if self.state is HI_State.SPECIFY_MOVEMENT:
                    for icon in self.candidates:
                        if self.__check_icon_boudning_box(mouse_x, mouse_y, icon):
                            for opp_b in self.game_status.map.opp_building_list:
                                if opp_b.visible:
                                    if opp_b.base_tile.offset_coordinates == icon.hex.offset_coordinates:
                                        self.cursor.set_cursor_to_combat()
                            for opp_a in self.game_status.map.opp_army_list:
                                if opp_a.base_tile.offset_coordinates == icon.hex.offset_coordinates:
                                    self.cursor.set_cursor_to_combat()
                        else:
                            self.cursor.set_cursor_to_normal()

    def handle_mouse_press(self, mouse_x: int, mouse_y: int, button):
        """core function forwards mouse click to be interpreted by the respective function, depending on the state.
        Does only accept left or right mouse-button clicks"""
        if button == 4:     # Right click on mouse
            self.set_state(HI_State.GRIDMODE)
            return
        if self.gl.player_list[self.gl.current_player].player_type is PlayerType.HUMAN:
            if self.state == HI_State.SPECIFY_FIELDS:
                self.__handle_state_specify_fields(mouse_x, mouse_y)

            elif self.state == HI_State.SPECIFY_MOVEMENT:
                self.__handle_state_specify_movement(mouse_x, mouse_y)

            elif self.state == HI_State.SELECTION:
                self.__handle_state_selection(mouse_x, mouse_y)

            elif self.state == HI_State.GRIDMODE:
                self.__handle_state_gridmode(mouse_x, mouse_y)
        else:
            pass

    def set_state(self, state: HI_State):
        if self.cost_panel:
            if self.cost_panel.show:
                self.hide_cost_panel()
        if state == HI_State.GRIDMODE:
            for c in self.candidates:
                self.zlvl_icons.remove(c)
            for a in self.active_selection:
                self.zlvl_icons.remove(a)
            self.active_selection.clear()
            self.candidates.clear()
            self.cursor.set_cursor_to_normal()
            self.selection_tool.alpha = 200
            self.selection_tool.center_x = -50
            self.selection_tool.center_y = -50      # small hack to make it appear only on first mouse move
        else:
            self.selection_tool.alpha = 0
        self.state = state

    def request_move(self, status: AI_GameStatus, move: AI_Move, pid: int):
        """initial call, the game logic asks the HI to fill the move obj with the user input"""
        self.set_state(HI_State.GRIDMODE)
        self.action_specified = MoveState.WAIT
        self.movement_specified = MoveState.WAIT
        self.move = move
        self.move.from_human_interaction = True
        self.game_status = status

    def update_game_status(self, status: AI_GameStatus):
        """the game logic might update the game_status of the human interaction
        Example: The human moves the army, but hasn't built yet. To ensure that the map view remains consistent,
        the game logic has to create a new map_status object. So for instance, the tile where the has moved in,
        isn't buildable anymore, whereas the free tile where the army moved away, is now in the buildable_list.
        Technically, this gives a small advantage to a human player, because this allows for moves, the AI can't perform
        Such as: move the army away from a tile and build on the same tile. For now, this is not to big of a deal:)"""
        self.game_status = status

    def is_move_complete(self):
        return self.movement_specified is MoveState.USED and self.action_specified is MoveState.USED

    def get_partial_move(self) -> Optional[AI_Move]:
        """if part of the move has been specified yet, it does return it anyway"""
        if self.movement_specified is MoveState.READY:
            self.movement_specified = MoveState.USED
            if self.action_specified is MoveState.USED:
                self.move.move_type = MoveType.DO_NOTHING
            return self.move
        if self.action_specified is MoveState.READY:
            if self.movement_specified is MoveState.USED:
                self.move.doMoveArmy = False
            self.action_specified = MoveState.USED
            return self.move
        return None

    def __check_icon_boudning_box(self, x, y, icon: SelectionIcon, use_elliptic_bounding_box=True) -> bool:
        if use_elliptic_bounding_box:
            # Elliptical bounding box
            dist = sqrt(((x - icon.center_x)*0.5 * (x - icon.center_x)*0.5) +
                        ((y - icon.center_y) * (y - icon.center_y)))
            if dist < 15:
                return True
            return False
        else:
            # Rectangular Bounding Box
            if (icon.center_x - icon.width / 2) < x < (icon.center_x + icon.width / 2):
                if (icon.center_y - icon.height / 2) < y < (icon.center_y + icon.height / 2):
                    return True
            return False

    def __handle_state_gridmode(self, mouse_x: int, mouse_y: int):
        """If in gridmode and the player clicks on a tile, this function decides what options are available"""
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
                has_res_for_hut = Building.building_info[BuildingType.HUT][
                                      'construction_cost'] <= self.game_status.me.resources
                has_res_for_farm = Building.building_info[BuildingType.FARM][
                                       'construction_cost'] <= self.game_status.me.resources
                has_res_for_racks = Building.building_info[BuildingType.BARRACKS][
                                        'construction_cost'] <= self.game_status.me.resources
                can_raise_army = len(self.game_status.map.army_list) == 0
                pos_list = self.get_icon_coordinates((mouse_x, mouse_y), 4)
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
                idx += 1
                self.active_selection.append(SelectionIcon(pos_list[idx][0], pos_list[idx][1],
                                                           self.textures['hi_raise_army'],
                                                           Action.RAISE_ARMY, h, is_active=can_raise_army))

            else:
                # at this point it is not scoutable nor buildable
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
                army_pop = self.game_status.map.army_list[0].population and self.movement_specified is not MoveState.USED
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
                                                           Action.ARMY_MOVEMENT, h, is_active=(army_pop > 0)))
        for ai in self.active_selection:
            self.zlvl_icons.append(ai)
        self.set_state(HI_State.SELECTION)

    def __handle_state_selection(self, mouse_x: int, mouse_y: int):
        """Lets the player select an icon and translates this to the move object.
         If necessary, the state is set to await additional input (e.g. for army movement)"""
        action = None
        active_icon = None
        candidates = []
        for icon in self.active_selection:
            if self.__check_icon_boudning_box(mouse_x, mouse_y, icon):
                if icon.is_active:
                    action = icon.action
                    active_icon = icon
                else:
                    if len(icon.info_text) > 0:
                        Logger.log_notification(icon.info_text)
                    else:
                        Logger.log_notification("Invalid option")
        if action:
            if action == Action.ARMY_MOVEMENT:
                if not (self.movement_specified is MoveState.USED):
                    self.move.doMoveArmy = True
                    self.active_hexagon = active_icon.hex
                    candidates = [x for x in self.gl.hex_map.get_neighbours(self.active_hexagon) if
                                  AI_Toolkit.is_obj_in_list(x, self.game_status.map.walkable_tiles)]
                    self.set_state(HI_State.SPECIFY_MOVEMENT)
                else:
                    Logger.log_notification("you already moved the army.")
                    self.set_state(HI_State.GRIDMODE)
            else:
                if not (self.action_specified is MoveState.USED):
                    if action == Action.BUILD_FARM:
                        self.move.type = BuildingType.FARM
                        self.move.move_type = MoveType.DO_BUILD
                        self.move.loc = active_icon.hex.offset_coordinates
                        self.active_hexagon = active_icon.hex
                        candidates = [x for x in self.gl.hex_map.get_neighbours(self.active_hexagon) if
                                      AI_Toolkit.is_obj_in_list(x, self.game_status.map.buildable_tiles)]
                        self.set_state(HI_State.SPECIFY_FIELDS)
                    elif action == Action.BUILD_HUT:
                        self.move.type = BuildingType.HUT
                        self.move.move_type = MoveType.DO_BUILD
                        self.move.loc = active_icon.hex.offset_coordinates
                        self.action_specified = MoveState.READY
                        self.set_state(HI_State.GRIDMODE)
                    elif action == Action.BUILD_RACKS:
                        self.move.type = BuildingType.BARRACKS
                        self.move.move_type = MoveType.DO_BUILD
                        self.move.loc = active_icon.hex.offset_coordinates
                        self.action_specified = MoveState.READY
                        self.set_state(HI_State.GRIDMODE)
                    elif action == Action.RECRUIT_KNIGHT:
                        self.move.type = UnitType.KNIGHT
                        self.move.move_type = MoveType.DO_RECRUIT_UNIT
                        self.action_specified = MoveState.READY
                        self.set_state(HI_State.GRIDMODE)
                    elif action == Action.RECRUIT_MERC:
                        self.move.type = UnitType.MERCENARY
                        self.move.move_type = MoveType.DO_RECRUIT_UNIT
                        self.action_specified = MoveState.READY
                        self.set_state(HI_State.GRIDMODE)
                    elif action == Action.SCOUT:
                        self.move.move_type = MoveType.DO_SCOUT
                        self.move.loc = active_icon.hex.offset_coordinates
                        self.action_specified = MoveState.READY
                        self.set_state(HI_State.GRIDMODE)
                    elif action == Action.RAISE_ARMY:
                        self.move.move_type = MoveType.DO_RAISE_ARMY
                        self.move.loc = active_icon.hex.offset_coordinates
                        self.action_specified = MoveState.READY
                        self.set_state(HI_State.GRIDMODE)
                else:
                    Logger.log_notification("you already used up the action, wait until next turn")
                    self.set_state(HI_State.GRIDMODE)

            ######
            for c in candidates:
                pix_c = HexMap.offset_to_pixel_coords(c.offset_coordinates)
                si = SelectionIcon(pix_c[0] + self.camera_pos[0], pix_c[1] + self.camera_pos[1],
                                   self.textures['hi_specify'], Action.NONE, c, scale=0.9)
                self.zlvl_icons.append(si)
                self.candidates.append(si)
        else:
            self.set_state(HI_State.GRIDMODE)
        for icon in self.active_selection:
            self.zlvl_icons.remove(icon)
        self.active_selection.clear()

    def __handle_state_specify_movement(self, mouse_x: int, mouse_y: int):
        """Lets the player select a walkable field next to the army"""
        if self.active_hexagon:
            for n in self.candidates:
                if self.__check_icon_boudning_box(mouse_x, mouse_y, n):
                    self.move.move_army_to = n.hex.offset_coordinates
                    self.active_hexagon = None
                    self.movement_specified = MoveState.READY
                    self.set_state(HI_State.GRIDMODE)
                    n.gray_out()
        else:
            error("this is a problem 1")

    def __handle_state_specify_fields(self, mouse_x: int, mouse_y: int):
        """Lets the player select up to 3 fields which are placed next to the farm"""
        if self.active_hexagon:
            for n in self.candidates:
                if self.__check_icon_boudning_box(mouse_x, mouse_y, n):
                    if n.is_active:
                        self.move.info.append(n.hex.offset_coordinates)
                        n.gray_out()
            has_valid_can = False
            for n in self.candidates:
                if n.is_active:
                    has_valid_can = True

            if len(self.move.info) == 3 or not has_valid_can:
                self.active_hexagon = None
                self.action_specified = MoveState.READY
                self.set_state(HI_State.GRIDMODE)

        else:
            error("this is a problem 0")

    def show_cost_panel(self, icon: SelectionIcon, x, y):
        if self.cost_panel:
            if self.cost_panel.show:
                return
        txt = ""
        player = self.gl.player_list[self.gl.current_player]
        j = 0 if self.action_specified is MoveState.USED else 1
        if icon.action is Action.BUILD_RACKS:
            txt += f"Action ({j}/1) \n"
            txt += f"Resources: {player.amount_of_resources}/{Building.get_construction_cost(BuildingType.BARRACKS)} \n"
        elif icon.action is Action.BUILD_HUT:
            txt += f"Action ({j}/1) \n"
            txt += f"Resources: {player.amount_of_resources}/{Building.get_construction_cost(BuildingType.HUT)} \n"
        elif icon.action is Action.BUILD_FARM:
            txt += f"Action ({j}/1) \n"
            txt += f"Resources: {player.amount_of_resources}/{Building.get_construction_cost(BuildingType.FARM)} \n"
        elif icon.action is Action.RECRUIT_KNIGHT:
            cost = Unit.get_unit_cost(UnitType.KNIGHT)
            txt += f"Action ({j}/1) \n"
            txt += f"Resources: {player.amount_of_resources}/{cost.resources} \n"
            txt += f"Culture: {player.culture}/{cost.culture} \n"
            txt += f"Population: {cost.population}"
        elif icon.action is Action.RECRUIT_MERC:
            cost = Unit.get_unit_cost(UnitType.MERCENARY)
            txt += f"Action ({j}/1) \n"
            txt += f"Resources: {player.amount_of_resources}/{cost.resources} \n"
            txt += f"Culture: {player.culture}/{cost.culture} \n"
            txt += f"Population: {cost.population}"
        elif icon.action is Action.RAISE_ARMY:
            txt += f"Action ({j}/1) \n \n"
        elif icon.action is Action.SCOUT:
            txt += f"Action ({j}/1) \n"
            txt += f"Resources: {player.amount_of_resources}/1 \n"
        elif icon.action is Action.ARMY_MOVEMENT:
            i = 0 if self.movement_specified is MoveState.USED else 1
            txt += f"Movement ({i}/1) \n \n"
        else:
            txt = "free \n \n"

        c = arcade.color.WHITE if icon.is_active else arcade.color.RED

        self.cost_panel = CostPanel(x + 100, y + 60, txt, c)
        self.zlvl_icons.append(self.cost_panel.sprite)
        self.set_cost_panel(self.cost_panel)
        self.cost_panel.show = True

    def hide_cost_panel(self):
        self.zlvl_icons.remove(self.cost_panel.sprite)
        self.cost_panel.show = False

