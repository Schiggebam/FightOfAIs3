import arcade
import os
import timeit

from src.console import Console
from src.game_logic import GameLogic
from src.ui.ui import UI

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
SCREEN_TITLE = "Fight of AIs"

DEBUG = True
NUM_Z_LEVELS = 4

GAME_XML_FILE = "../resources/smooth_game.xml"
SETUP_COMMANDS = "../resources/initial_commands.txt"


class ZlvlRenderer:
    def __init__(self, num_levels):
        self.z_levels: [arcade.SpriteList] = []
        for i in range(num_levels):
            self.z_levels.append(arcade.SpriteList())
        self.ui = None

    def render(self):
        for z in self.z_levels:
            z.draw()
        self.ui.draw()



class Game(arcade.Window):
    def __init__(self, width, height, title):
        super().__init__(width, height, title)

        file_path = os.path.dirname(os.path.abspath(__file__))
        os.chdir(file_path)

        self.z_level_renderer: ZlvlRenderer = ZlvlRenderer(NUM_Z_LEVELS)
        self.game_logic: GameLogic = GameLogic(GAME_XML_FILE, self.z_level_renderer.z_levels)
        self.console: Console = Console()
        self.ui = UI(self.game_logic, SCREEN_WIDTH, SCREEN_HEIGHT)
        self.z_level_renderer.ui = self.ui


        self.commands: [(str, str)] = []

        # for performance measurement
        self.draw_time: float = .0
        self.max_update_time: float = .0
        self.frame_count = 0
        self.fps_start_timer = None
        self.fps = None
        self.num_of_sprites: int = 0

    def setup(self):
        arcade.set_background_color(arcade.color.DARK_BLUE)
        self.commands.extend(self.console.initial_commands(SETUP_COMMANDS))
        self.game_logic.setup()

    def on_update(self, delta_time):
        timestamp_start = timeit.default_timer()
        self.commands.extend(self.console.get())
        self.game_logic.update(delta_time, self.commands)
        self.ui.update()
        self.commands.clear()

        self.num_of_sprites = 0
        for zl in self.z_level_renderer.z_levels:
            self.num_of_sprites = self.num_of_sprites + len(zl)
        update_time = timeit.default_timer() - timestamp_start
        self.max_update_time = max(update_time, self.max_update_time)

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
        output_update = f"Max Update time: {self.max_update_time:.3f}"
        arcade.draw_text(output, 20, SCREEN_HEIGHT - 40, arcade.color.WHITE, 16)
        arcade.draw_text(output_update, 20, SCREEN_HEIGHT - 60, arcade.color.WHITE, 16)
        if self.fps is not None:
            output = f"FPS: {self.fps:.0f}"
            arcade.draw_text(output, 20, SCREEN_HEIGHT - 80, arcade.color.WHITE, 16)
        self.draw_time = timeit.default_timer() - timestamp_start

    def on_mouse_press(self, x, y, button, key_modifiers):
        found = self.ui.check_mouse_press_for_buttons(x, y)
        #if not found:
        self.ui.hl_pressed_tile(x, y)

    def on_mouse_release(self, x, y, button, key_modifiers):
        self.ui.check_mouse_release_for_buttons(x, y)

    def on_key_press(self, key, modifiers):
        if key == arcade.key.UP:
            self.ZR.update_camera(0, 10)
        if key == arcade.key.DOWN:
            self.ZR.update_camera(0, -10)
        if key == arcade.key.LEFT:
            self.ZR.update_camera(-10, 0)
        if key == arcade.key.RIGHT:
            self.ZR.update_camera(10, 0)


def main():
    window = Game(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    window.setup()
    arcade.finish_render()
    arcade.run()


if __name__ == "__main__":
    main()
