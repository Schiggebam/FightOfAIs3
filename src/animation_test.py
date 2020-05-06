import random
import arcade
import os
import timeit
import time
import collections
import pyglet

# --- Constants ---
from arcade import AnimationKeyframe

SPRITE_SCALING_COIN = 0.25
SPRITE_NATIVE_SIZE = 128
SPRITE_SIZE = int(SPRITE_NATIVE_SIZE * SPRITE_SCALING_COIN)
COIN_COUNT_INCREMENT = 500

STOP_COUNT = 10000
RESULTS_FILE = "stress_test_draw_moving_arcade.csv"

SCREEN_WIDTH = 1080
SCREEN_HEIGHT = 720
SCREEN_TITLE = "Moving Sprite Stress Test"


class FPSCounter:
    def __init__(self):
        self.time = time.perf_counter()
        self.frame_times = collections.deque(maxlen=60)

    def tick(self):
        t1 = time.perf_counter()
        dt = t1 - self.time
        self.time = t1
        self.frame_times.append(dt)

    def get_fps(self):
        total_time = sum(self.frame_times)
        if total_time == 0:
            return 0
        else:
            return len(self.frame_times) / sum(self.frame_times)


class BadFlag(arcade.Sprite):
    def __init__(self, x, y):
        self.counter = 0
        self.current_tex = 0
        super().__init__()
        path = "../resources/objects/animated/flag_100_sprite_green.png"
        for i in range(10):
            tex: arcade.Texture = arcade.load_texture(path, x=0, y=i*100, width=108, height=100)
            self.append_texture(tex)
            self.counter = self.counter + 1
        self.set_texture(self.current_tex)
        self.center_x = x
        self.center_y = y
        self.scale = 0.25

    def update_a(self):
        self.set_texture(self.current_tex)


# class Flag(arcade.AnimatedTimeSprite):
#     def __init__(self, x, y):
#         super().__init__()
#         path = "../resources/objects/animated/flag_100_sprite_green.png"
#         for i in range(10):
#             tex: arcade.Texture = arcade.load_texture(path, x=0, y=i*100, width=108, height=100)
#             self.append_texture(tex)
#         self.set_texture(0)
#         self.center_x = x
#         self.center_y = y
#         self.scale = 0.25



class GoodFlag(arcade.AnimatedTimeBasedSprite):
    def __init__(self, x, y):
        super().__init__()
        path = "../resources/objects/animated/flag_100_sprite_green.png"
        for i in range(10):
            tex: arcade.Texture = arcade.load_texture(path, x=0, y=i*100, width=108, height=100)
            self.append_texture(tex)
            a = AnimationKeyframe(i, 50, tex)
            self.frames.append(a)
        self.update_animation()
        self.center_x = x
        self.center_y = y
        self.scale = 0.25


class MyGame(arcade.Window):
    """ Our custom Window Class"""

    def __init__(self):
        """ Initializer """
        # Call the parent class initializer
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)

        # Set the working directory (where we expect to find files) to the same
        # directory this .py file is in. You can leave this out of your own
        # code, but it is needed to easily run the examples using "python -m"
        # as mentioned at the top of this program.
        file_path = os.path.dirname(os.path.abspath(__file__))
        os.chdir(file_path)

        # Variables that will hold sprite lists
        self.flags = []

        self.processing_time = 0
        self.draw_time = 0
        self.program_start_time = timeit.default_timer()
        self.sprite_count_list = []
        self.fps_list = []
        self.processing_time_list = []
        self.drawing_time_list = []
        self.last_fps_reading = 0
        self.fps = FPSCounter()

        arcade.set_background_color(arcade.color.AMAZON)

        # Open file to save timings
        self.results_file = open(RESULTS_FILE, "w")
        self.tot_time = 10


    def setup(self):
        """ Set up the game and initialize the variables. """

        # Sprite lists
        self.flag_sl = arcade.SpriteList(use_spatial_hash=False, is_static=True)
        for i in range(10):
            for j in range(10):
                flag = BadFlag(50 + 50 * i, 100 + j * 75)
                self.flag_sl.append(flag)
                flag.set_texture(0)

    def on_draw(self):
        """ Draw everything """

        # Start timing how long this takes
        draw_start_time = timeit.default_timer()

        arcade.start_render()
        self.flag_sl.draw()

        output = f"Sprite count: {len(self.flag_sl):,}"
        arcade.draw_text(output, 20, SCREEN_HEIGHT - 20, arcade.color.BLACK, 16)

        # Display timings
        output = f"Processing time: {self.processing_time:.3f}"
        arcade.draw_text(output, 20, SCREEN_HEIGHT - 40, arcade.color.BLACK, 16)

        output = f"Drawing time: {self.draw_time:.3f}"
        arcade.draw_text(output, 20, SCREEN_HEIGHT - 60, arcade.color.BLACK, 16)

        fps = self.fps.get_fps()
        output = f"FPS: {fps:3.0f}"
        arcade.draw_text(output, 20, SCREEN_HEIGHT - 80, arcade.color.BLACK, 16)



        self.draw_time = timeit.default_timer() - draw_start_time



    def update(self, delta_time):
        self.tot_time += delta_time
        # Start update timer
        t1 = timeit.default_timer()

        # #if self.tot_time > 0.2:
        for s in self.flag_sl:
            s.update_animation()
            s.update_a()
        # self.tot_time = 0


        t2 = timeit.default_timer()
        self.processing_time = t2 - t1
        self.fps.tick()



def main():
    """ Main method """
    window = MyGame()
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()
