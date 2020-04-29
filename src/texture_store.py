from typing import Dict

import arcade

from src.misc.game_constants import start_progress, progress, end_progress, Definitions



class TextureStore:

    def __init__(self):
        # this dictionary contains all textures
        # key is a str_code
        self.textures = {}
        self.animated_textures = {}
        from src.ui.ui_accessoires import UI_Texture
        self.ui_textures: Dict[UI_Texture, arcade.Texture] = {}

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

    def load_animated_texture(self, name: str, amount: int, index_function,
                              width, height, path: str):
        self.animated_textures[name] = []
        for i in range(amount):
            pixel_pos: (int, int) = index_function(i)
            tex: arcade.Texture = arcade.load_texture(path, x=pixel_pos[0], y=pixel_pos[1],
                                                      width=width, height=height)
            self.animated_textures[name].append(tex)

    def get_animated_texture(self, name: str):
        return self.animated_textures[name]

    def load_ui_textures(self):
        from src.ui.ui_accessoires import UI_Texture
        for ui_tex in UI_Texture:
            path = Definitions.UI_TEXTURE_PATH + ui_tex.value
            self.ui_textures[ui_tex] = arcade.load_texture(path)

    def get_ui_texture(self, key):
        """load a ui texture. The key must be of type UI_Texture"""
        return self.ui_textures[key]
