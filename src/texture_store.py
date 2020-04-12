

import arcade

from src.misc.game_constants import start_progress, progress, end_progress


class TextureStore:

    def __init__(self):
        # this dictionary contains all textures
        # key is a str_code
        self.textures = {}

    def load_textures(self, dict_requested):
        start_progress("loading textures")
        total = float(len(dict_requested))
        prog = 0
        for elem in dict_requested:
            if elem not in self.textures:
                self.textures[elem] = (arcade.load_texture(dict_requested[elem][0]),
                                       dict_requested[elem][1],  # offsetX
                                       dict_requested[elem][2],  # offsetY
                                       dict_requested[elem][3])  # scale
                # print("tex loaded for : " + elem)
            prog = prog + 1
            progress(float(prog)/total)
        end_progress()

    def get_texture(self, key):
        if key in self.textures:
            return self.textures[key][0]
        print("TextureStore: Unable to find texture: " + key)

    def get_tex_offest(self, key: str) -> (int, int):
        """returns offset of texture in pixels"""
        if key in self.textures:
            return self.textures[key][1], self.textures[key][2]
        print("TextureStore: Unable to find texture: " + key)

    def get_tex_scale(self, key: str) -> float:
        """returns scale of texture """
        if key in self.textures:
            return self.textures[key][3]
        print("TextureStore: Unable to find texture: " + key)
