from math import sqrt
from typing import List, Optional, Tuple, Union, Dict

from src.ui.human import HumanInteraction
from src.game_logic import GameLogic
from src.ui.IconButton import IconButton
from src.ui.SimpleButton import TextButton
from src.ui.ui_accessoires import CustomCursor
from src.ui.ui_panels import *
from dataclasses import dataclass


@dataclass
class Notification:
    text: str
    duration: float


class NextTurnButton(TextButton):
    def __init__(self, center_x, center_y, action_function):
        super().__init__(center_x, center_y, 100, 30, "Next Player", 16, "Arial")
        self.action_function = action_function

    def on_release(self):
        super().on_release()
        self.action_function()


class AutomaticButton(TextButton):
    def __init__(self, center_x, center_y, action_function):
        super().__init__(center_x, center_y, 100, 30, "Play Auto", 16, "Arial")
        self.action_function = action_function
        self.active = False

    def on_press(self):
        self.active = not self.active
        if not self.active:
            super().on_release()
        else:
            super().on_press()
        self.action_function(self.active)

    def on_release(self):
        # super().on_release()
        # self.action_function()
        pass


class AutomaticIconButton(IconButton):
    def __init__(self, center_x, center_y, action_function, tex_pressed: str, tex_unpressed: str, scale=1.0):
        super().__init__(center_x, center_y, tex_pressed, tex_unpressed, scale=scale)
        self.action_function = action_function
        self.active = False
        self.args: [] = []

    def on_press(self):
        self.active = not self.active
        if not self.active:
            super().on_release()
        else:
            super().on_press()
        self.action_function(self.active, self.args)

    def on_release(self):
        pass


Panels = Union[PanelAI, PanelDiplo, PanelArmy, PanelResource, PanelBuilding]


class UI:
    def __init__(self, gl, hi, screen_width, screen_height):
        self.camera_pos = (0, 0)
        self.gl: GameLogic = gl  # holds an instance of the game logic
        self.hi: HumanInteraction = hi
        self.buttonlist = []
        self.panel_list: List[Panels] = []
        self.next_turn_button = NextTurnButton(screen_width - 150, 70, self.callBack1)
        self.ba = AutomaticButton(screen_width - 150, 30, self.callBack_automatic)
        diplo_button = AutomaticIconButton(screen_width - 50, 200, self.callBack_diplo,
                                           "../resources/other/diplo_button_pressed.png",
                                           "../resources/other/diplo_button_unpressed.png")
        ai_button = AutomaticIconButton(screen_width - 50, 265, self.callBack_ai,
                                        "../resources/other/ai_button_pressed.png",
                                        "../resources/other/ai_button_unpressed.png")
        self.ai_panel: Optional[PanelAI] = None
        self.diplo_panel = None

        self.buttonlist.append(self.ba)
        self.buttonlist.append(self.next_turn_button)

        self.buttonlist.append(diplo_button)
        self.buttonlist.append(ai_button)
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.sprite_list = arcade.SpriteList()
        # TODO: move ui elements in this dict! This class is a mess!
        self.ui_elements: Dict[str, Union[AutomaticIconButton]] = {}
        self.playerinfo = {}
        self.volatile_panel = []
        self.closable_panels = []
        self.win_screen_shown = False
        self.status_text = ""
        self.notifications_text = ""
        self.notifications: List[Tuple[Notification, float]] = []
        x_offset = 40
        map_hack_button = AutomaticIconButton(self.screen_width - 50, 20, self.callBack_map_hack,
                                              "../resources/other/watch_button_pressed.png",
                                              "../resources/other/watch_button_unpressed.png", scale=0.75)
        # map_hack_button.on_press()
        self.buttonlist.append(map_hack_button)
        for p in self.gl.player_list:
            watch_button = AutomaticIconButton(10 + x_offset, 100, self.callBack_watch,
                                               "../resources/other/watch_button_pressed.png",
                                               "../resources/other/watch_button_unpressed.png", scale=0.5)
            watch_button.args.append(p.id)
            self.ui_elements[f"watch_id_{p.id}"] = watch_button
            # if p.player_type == PlayerType.HUMAN:
            #     watch_button.on_press()
            self.buttonlist.append(watch_button)
            x_offset = x_offset + 250

        self.main_panel: arcade.Sprite = arcade.Sprite()
        self.cursor: Optional[CustomCursor] = None
        self.cost_panel = None

    def setup(self):
        self.gl.texture_store.load_ui_textures()
        self.cursor = CustomCursor(self.gl.texture_store)
        self.hi.set_ui_references(self.cursor, self.cost_panel_callback)
        self.ai_panel = PanelAI(self.screen_width - 280, 500, "AI panel", self.gl)
        self.diplo_panel = PanelDiplo(self.screen_width - 280, 250, "Diplo panel", self.gl)
        self.panel_list.append(self.ai_panel)
        self.panel_list.append(self.diplo_panel)
        self.main_panel.append_texture(arcade.load_texture("../resources/objects/main_panel_2.png"))
        self.main_panel.set_position(self.screen_width / 2, 102)
        self.main_panel.set_texture(0)
        self.sprite_list.append(self.main_panel)
        for b in self.buttonlist:
            self.sprite_list.append(b.sprite)

        if not self.gl.has_human_player:
            if len(self.gl.player_list) > 0:
                pid = self.gl.player_list[0].id
                self.ui_elements[f"watch_id_{pid}"].on_press()
        else:
            for p in self.gl.player_list:
                if p.player_type == PlayerType.HUMAN:
                    self.ui_elements[f"watch_id_{p.id}"].on_press()

    def draw(self):
        for hex in self.gl.hex_map.map:
            if hex.debug_msg != "":
                from src.hex_map import HexMap
                (x, y) = HexMap.offset_to_pixel_coords(hex.offset_coordinates)
                arcade.draw_text(hex.debug_msg, x + self.camera_pos[0], y + self.camera_pos[1], arcade.color.BLACK)

        self.sprite_list.draw()

        # draw turn number
        arcade.draw_text("Turn: " + str(self.gl.turn_nr), self.screen_width - 80, 65, arcade.color.WHITE, 14)
        arcade.draw_text("Map Hack", self.screen_width - 85, 35, arcade.color.WHITE, 14)

        hl_x_off = self.gl.current_player * 250 + 140
        hl_y_off = 65
        arcade.draw_rectangle_filled(hl_x_off, hl_y_off, 120, 70, arcade.color.DARK_ORANGE)

        for p in self.panel_list:
            if p.show:
                p.draw()

        if self.cost_panel:
            if self.cost_panel.show:
                self.cost_panel.draw()

        for b in self.buttonlist:
            b.draw()

        # draw the player stats:
        x_offset = 70
        for p in self.gl.player_list:
            arcade.draw_text(str(p.name) + " [" + str(p.id) + "]", x_offset, 100, arcade.color.WHITE, 14)
            arcade.draw_text(self.playerinfo[p.id][0], x_offset + 10, 30, self.playerinfo[p.id][1],
                             self.playerinfo[p.id][2])
            x_offset = x_offset + 250


        # if self.gl.player_list[self.gl.current_player].player_type == PlayerType.HUMAN:
        #     arcade.draw_text("Your turn! Give orders and hit next turn.", self.screen_width - 600, 80,
        #                      arcade.color.WHITE, 16)
        #     c1 = arcade.color.GREEN
        #     s1 = "Army movement set"
        #     c2 = arcade.color.GREEN
        #     s2 = "Action set"
        #     if self.hi.move.move_army_to == (-1, -1):
        #         c1 = arcade.color.ORANGE
        #         s1 = "Awaiting orders to move the army"
        #     if self.hi.move.move_type is None or self.hi.move.move_type == MoveType.DO_NOTHING:
        #         c2 = arcade.color.ORANGE
        #         s2 = "Awaiting orders to build/scout/upgrade/recruit"
        #     arcade.draw_text(s1, self.screen_width - 570, 50, c1, 12)
        #     arcade.draw_text(s2, self.screen_width - 570, 30, c2, 12)

        # draw notifications
        if len(self.notifications_text) > 0:
            arcade.draw_text(self.notifications_text, self.screen_width / 2 - 100, 150, arcade.color.ORANGE, 16)

        self.cursor.draw()

    def update(self, wall_clock_time):
        # if self.ai_panel.show:
        #     self.ai_panel.update(self.gl)

        # build string for notifications
        self.notifications = [x for x in self.notifications if x[0].duration > wall_clock_time]
        self.notifications_text = ""
        for n, t in self.notifications:
            self.notifications_text += n.text + "\n"

        for p in self.panel_list:
            if p.show:
                p.update()

        if self.cost_panel:
            if self.cost_panel.show:
                self.cost_panel.draw()

        for player in self.gl.player_list:
            if not player.has_lost:
                s = f"Resources: {player.amount_of_resources} \n"
                s = s + f"Buildings: {len(player.buildings)} \n"
                s = s + f"Culture: {player.culture} \n"
                s = s + f"Food: {player.food} \n"
                s = s + f"Population {player.get_population()} / {player.get_population_limit()}"
                cond = self.gl.current_player == player.id
                self.playerinfo[player.id] = (s, arcade.color.BLACK if cond else arcade.color.WHITE, 12)
            else:
                self.playerinfo[player.id] = ("LOST", arcade.color.RED, 18)
        if self.gl.winner and not self.win_screen_shown:
            won_panel = PanelGameWon(self.screen_width / 2, self.screen_height / 2, self.gl.winner)
            self.show_volatile_panel(won_panel)
            self.win_screen_shown = True

        if not Logger.logs.empty():
            pos: [(int, int)] = []
            if Logger.logs.qsize() == 1:
                pos.append((self.screen_width / 2, self.screen_height / 2))
            elif Logger.logs.qsize() == 2:
                pos.append((1 * self.screen_width / 3, self.screen_height / 2))
                pos.append((2 * self.screen_width / 3, self.screen_height / 2))
            elif Logger.logs.qsize() == 3:
                pos.append((1 * self.screen_width / 4, self.screen_height / 2))
                pos.append((2 * self.screen_width / 4, self.screen_height / 2))
                pos.append((3 * self.screen_width / 4, self.screen_height / 2))
            elif Logger.logs.qsize() == 4:
                pos.append((1 * self.screen_width / 3, self.screen_height / 3))
                pos.append((2 * self.screen_width / 3, self.screen_height / 3))
                pos.append((1 * self.screen_width / 3, 2 * self.screen_height / 3))
                pos.append((2 * self.screen_width / 3, 2 * self.screen_height / 3))
            else:
                error("UI: cannot display more than 4 logged reports at once.")

            for i in range(Logger.logs.qsize()):
                log = Logger.logs.get()
                if log.log_type == LogType.BATTLE_ARMY_VS_ARMY or log.log_type == LogType.BATTLE_ARMY_VS_BUILDING:
                    panel_attack = PanelLogBattle(pos[i][0], pos[i][1], log, self.gl.texture_store)
                    self.show_closable_panel(panel_attack)

                if log.log_type == LogType.DIPLO_ENEMY_BUILDING_SCOUTED:
                    panel_diplo = PanelLogDiplo(pos[i][0], pos[i][1], log)
                    self.show_volatile_panel(panel_diplo)

                if log.log_type == LogType.NOTIFICATION:
                    self.notifications.append((Notification(log.text, wall_clock_time + 5), wall_clock_time))
            self.halt_progress()

    def callBack1(self):
        self.gl.playNextTurn = True
        self.gl.nextPlayerButtonPressed = True

    def callBack_automatic(self, active):
        self.gl.automatic = active

    def callBack_diplo(self, active, args):
        if self.diplo_panel.show:
            self.diplo_panel.sprite.remove_from_sprite_lists()
        else:
            self.sprite_list.append(self.diplo_panel.sprite)
        self.diplo_panel.show = not self.diplo_panel.show

    def callBack_ai(self, active, args):
        if self.ai_panel.show:
            self.ai_panel.sprite.remove_from_sprite_lists()
        else:
            self.sprite_list.append(self.ai_panel.sprite)
        self.ai_panel.show = not self.ai_panel.show

    def callBack_watch(self, active, args):
        self.gl.map_view[args[0]] = active
        self.gl.change_in_map_view = True

    def callBack_map_hack(self, active, args):
        self.gl.map_hack = active
        self.gl.change_in_map_view = True

    def cost_panel_callback(self, cost_panel):
        self.cost_panel = cost_panel

    def check_mouse_press_for_buttons(self, x, y) -> bool:
        """ Given an x, y, see if we need to register any button clicks. """
        for button in self.buttonlist:
            if x > button.center_x + button.width / 2:
                continue
            if x < button.center_x - button.width / 2:
                continue
            if y > button.center_y + button.height / 2:
                continue
            if y < button.center_y - button.height / 2:
                continue
            button.on_press()
            return True
        return False

    def handle_mouse_click(self, x, y):
        to_be_removed = None
        for panel in self.closable_panels:
            if panel.is_close_button_hit(x, y):
                self.panel_list.remove(panel)
                to_be_removed = panel
                self.sprite_list.remove(panel.sprite)
        if to_be_removed:
            self.closable_panels.remove(to_be_removed)

    def hl_pressed_tile(self, x, y, button):
        if len(self.volatile_panel) > 0 or button == 4:
            for p in self.volatile_panel:
                self.panel_list.remove(p)
                self.sprite_list.remove(p.sprite)
            self.volatile_panel.clear()
            return

        from src.hex_map import HexMap
        candidates = []
        for hex in self.gl.hex_map.map:  # FIXME should avoid looping over all elements. This is trash here
            hex_pix = tuple(map(sum, zip(HexMap.offset_to_pixel_coords(hex.offset_coordinates), self.camera_pos)))
            dist = sqrt(((x - hex_pix[0]) * 0.5 * (x - hex_pix[0]) * 0.5) + ((y - hex_pix[1]) * (y - hex_pix[1])))
            if dist < 30:
                candidates.append((dist, hex))
        if len(candidates) > 0:
            candidates.sort(key=lambda x: x[0], reverse=False)
            a, a_class = self.gl.get_map_element(candidates[0][1].offset_coordinates)
            from src.misc.building import Building
            from src.game_accessoires import Resource
            from src.game_accessoires import Army
            if a_class == Building:
                b_panel = PanelBuilding(x, y + 200 if y < self.screen_height / 2 else y - 200, a)
                self.show_volatile_panel(b_panel)
            elif a_class == Resource:
                r_panel = PanelResource(x, y + 200 if y < self.screen_height / 2 else y - 200, a)
                self.show_volatile_panel(r_panel)
            elif a_class == Army:
                a_panel = PanelArmy(x, y + 200 if y < self.screen_height / 2 else y - 200, a)
                self.show_volatile_panel(a_panel)
            return True
        return False

    def handle_mouse_motion(self, x, y):
        if self.cursor:
            self.cursor.update_cursor(x, y)

    def show_volatile_panel(self, panel):
        self.volatile_panel.append(panel)
        self.panel_list.append(panel)
        self.sprite_list.append(panel.sprite)
        panel.show = True

    def show_closable_panel(self, panel):
        self.closable_panels.append(panel)
        self.panel_list.append(panel)
        self.sprite_list.append(panel.sprite)
        panel.show = True

    def halt_progress(self):
        if self.ba.active:
            self.ba.on_press()
        self.gl.automatic = False

    def check_mouse_release_for_buttons(self, _x, _y):
        """ If a mouse button has been released, see if we need to process
            any release events. """
        for button in self.buttonlist:
            if button.pressed:
                button.on_release()
