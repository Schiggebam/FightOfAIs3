import arcade
import os
from os import sys, path
import timeit

from src.ai import human

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
# print(os.getcwd())

from src.console import Console
from src.game_logic import GameLogic
from src.misc.game_constants import CAMERA_SENSITIVITY
from src.ui.ui import UI

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
SCREEN_TITLE = "Fight of AIs"


NUM_Z_LEVELS = 4

GAME_XML_FILE = "../resources/game_2.xml"
SETUP_COMMANDS = "../resources/initial_commands.txt"


class ZlvlRenderer:
    def __init__(self, num_levels):
        self.camera_x = 0
        self.camera_y = 0
        self.rel_x = 0
        self.rel_y = 0
        self.camera_has_moved = False
        self.z_levels: [arcade.SpriteList] = []
        for i in range(num_levels):
            self.z_levels.append(arcade.SpriteList())
        self.ui = None
        self.gl = None
        self.up_key = False
        self.down_key = False
        self.left_key = False
        self.right_key = False

    def render(self):
        for z in self.z_levels:
            z.draw()
        self.ui.draw()

    def update_camera(self, rel_x, rel_y):
        #self.rel_x = rel_x
        #self.rel_y = rel_y
        #self.camera_has_moved = True
        pass

    def update(self, delta_t: float):
        rel = int(float(CAMERA_SENSITIVITY) * delta_t)
        if self.up_key:
            self.camera_has_moved = True
            self.rel_y = - rel
            self.camera_y = self.camera_y + self.rel_y
        elif self.down_key:
            self.camera_has_moved = True
            self.rel_y = rel
            self.camera_y = self.camera_y + self.rel_y
        if self.left_key:
            self.camera_has_moved = True
            self.rel_x = rel
            self.camera_x = self.camera_x + self.rel_x
        elif self.right_key:
            self.camera_has_moved = True
            self.rel_x = - rel
            self.camera_x = self.camera_x + self.rel_x

        if self.camera_has_moved:
            for s_list in self.z_levels:
                for sp in s_list:
                    sp.center_x = sp.center_x + self.rel_x
                    sp.center_y = sp.center_y + self.rel_y
            self.gl.set_camera_pos(self.camera_x, self.camera_y)
            self.gl.animator.camera_pos = (self.camera_x, self.camera_y)
            self.ui.camera_pos = (self.camera_x, self.camera_y)
            self.camera_has_moved = False
            self.rel_x = 0
            self.rel_y = 0


class Game(arcade.Window):
    def __init__(self, width, height, title):
        super().__init__(width, height, title)

        file_path = os.path.dirname(os.path.abspath(__file__))
        os.chdir(file_path)
        sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
        #print(os.getcwd())

        self.z_level_renderer: ZlvlRenderer = ZlvlRenderer(NUM_Z_LEVELS)
        self.game_logic: GameLogic = GameLogic(GAME_XML_FILE, self.z_level_renderer.z_levels)
        self.console: Console = Console()
        self.ui = UI(self.game_logic, SCREEN_WIDTH, SCREEN_HEIGHT)
        self.z_level_renderer.ui = self.ui
        self.z_level_renderer.gl = self.game_logic

        self.commands: [(str, str)] = []

        # for performance measurement
        self.draw_time: float = .0
        self.max_update_time: float = .0
        self.frame_count = 0
        self.fps_start_timer = None
        self.fps = None
        self.num_of_sprites: int = 0
        self.fps_colour = arcade.color.WHITE
        self.draw_time_colour = arcade.color.WHITE

    def setup(self):
        # arcade.set_background_color(arcade.color.DARK_BLUE)
        arcade.set_background_color(arcade.color.BLACK)
        self.commands.extend(self.console.initial_commands(SETUP_COMMANDS))
        self.game_logic.setup()
        self.ui.setup()

    def on_update(self, delta_time):
        # pr.enable()
        timestamp_start = timeit.default_timer()
        self.commands.extend(self.console.get())
        self.game_logic.update(delta_time, self.commands)
        self.ui.update()
        self.z_level_renderer.update(delta_time)
        self.commands.clear()

        self.num_of_sprites = 0
        for zl in self.z_level_renderer.z_levels:
            self.num_of_sprites = self.num_of_sprites + len(zl)
        update_time = timeit.default_timer() - timestamp_start
        # self.max_update_time = max(update_time, self.max_update_time)
        self.max_update_time = update_time

        # set colour for framerate
        if self.fps:
            self.fps_colour = arcade.color.WHITE
            if 30 < self.fps < 45:
                self.fps_colour = arcade.color.ORANGE
            if self.fps <= 30:
                self.fps_colour = arcade.color.RED
        self.draw_time_colour = arcade.color.WHITE
        if 0.15 < self.draw_time < 0.2:
            self.draw_time_colour = arcade.color.ORANGE
        if self.draw_time >= 0.2:
            self.draw_time_colour = arcade.color.RED
        # pr.disable()

    def on_draw(self):
        timestamp_start = timeit.default_timer()
        if self.frame_count % 60 == 0:
            if self.fps_start_timer is not None:
                total_time = timeit.default_timer() - self.fps_start_timer
                self.fps = 60 / total_time
            self.fps_start_timer = timeit.default_timer()
        self.frame_count += 1
        arcade.start_render()

        self.z_level_renderer.render()  # call the z-level Renderer

        output = f"Drawing time: {self.draw_time:.3f} #sprites: {self.num_of_sprites}"
        output_update = f"Update time: {self.max_update_time:.3f}"
        # other_times = f"A: {self.game_logic.animator_time:.3f}  T: {self.game_logic.total_time:.3f}"
        arcade.draw_text(output, 20, SCREEN_HEIGHT - 40, self.draw_time_colour, 16)
        arcade.draw_text(output_update, 20, SCREEN_HEIGHT - 60, arcade.color.WHITE, 16)
#        arcade.draw_text(other_times, 20, SCREEN_HEIGHT - 100, arcade.color.WHITE, 16)
        if self.fps is not None:
            output = f"FPS: {self.fps:.0f}"
            arcade.draw_text(output, 20, SCREEN_HEIGHT - 80, self.fps_colour, 16)
        self.draw_time = timeit.default_timer() - timestamp_start

    def on_mouse_press(self, x, y, button, key_modifiers):
        found = self.ui.check_mouse_press_for_buttons(x, y)
        #if not found:
        self.ui.hl_pressed_tile(x, y)

    def on_mouse_release(self, x, y, button, key_modifiers):
        self.ui.check_mouse_release_for_buttons(x, y)

    def on_key_press(self, key: int, modifiers: int):
        if key == arcade.key.UP:
            self.z_level_renderer.up_key = True
        if key == arcade.key.DOWN:
            self.z_level_renderer.down_key = True
        if key == arcade.key.LEFT:
            self.z_level_renderer.left_key = True
        if key == arcade.key.RIGHT:
            self.z_level_renderer.right_key = True


    def on_key_release(self, key: int, modifiers: int):
        if key == arcade.key.UP:
            self.z_level_renderer.up_key = False
        if key == arcade.key.DOWN:
            self.z_level_renderer.down_key = False
        if key == arcade.key.LEFT:
            self.z_level_renderer.left_key = False
        if key == arcade.key.RIGHT:
            self.z_level_renderer.right_key = False

    # def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):
    #     human.set_flag()

def main():
    window = Game(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    window.setup()
    window.set_update_rate(1/60)
    arcade.finish_render()
    arcade.run()


if __name__ == "__main__":
    main()
