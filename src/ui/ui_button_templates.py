import arcade

from src.texture_store import TextureStore
from src.ui.ui_accessoires import UI_Texture


class TextButton:
    def __init__(self, center_x, center_y, width, height, text, font_size=18, font_face="Arial", button_height=2):
        self.center_x = center_x
        self.center_y = center_y
        self.width = width
        self.height = height
        self.text = text
        self.font_size = font_size
        self.font_face = font_face
        self.pressed = False
        self.button_height = button_height
        self.sprite: arcade.Sprite = arcade.Sprite()
        self.sprite.append_texture(TextureStore.instance().get_ui_texture(UI_Texture.BUTTON_BASIC_UNPRESSED))
        self.sprite.append_texture(TextureStore.instance().get_ui_texture(UI_Texture.BUTTON_BASIC_PRESSED))
        #self.sprite.append_texture(arcade.load_texture("../resources/other/unpressed.png"))
        #self.sprite.append_texture(arcade.load_texture("../resources/other/pressed.png"))
        self.sprite.center_x = center_x
        self.sprite.center_y = center_y
        self.sprite.set_texture(0)

    def draw(self):
        arcade.draw_text(self.text, self.center_x, self.center_y,
                         arcade.color.BLACK, font_size=self.font_size,
                         width=self.width, align="center",
                         anchor_x="center", anchor_y="center")

    def on_press(self):
        self.pressed = True
        self.sprite.set_texture(1)

    def on_release(self):
        self.pressed = False
        self.sprite.set_texture(0)


class IconButton:
    def __init__(self, center_x, center_y, tex_pressed: UI_Texture, tex_unpressed: UI_Texture,
                 width=48, height=48, scale=1.0):
        self.center_x = center_x
        self.center_y = center_y
        self.width = width * scale
        self.height = height * scale
        self.sprite = arcade.Sprite()
        self.sprite.append_texture(TextureStore.instance().get_ui_texture(tex_unpressed))
        self.sprite.append_texture(TextureStore.instance().get_ui_texture(tex_pressed))
        # self.sprite.append_texture(arcade.load_texture(tex_unpressed))
        # self.sprite.append_texture(arcade.load_texture(tex_pressed))
        self.sprite.center_x = center_x
        self.sprite.center_y = center_y
        self.sprite.scale = scale
        self.sprite.set_texture(0)
        self.pressed = False

    def draw(self):
        pass

    def on_press(self):
        self.pressed = True
        self.sprite.set_texture(1)

    def on_release(self):
        self.pressed = False
        self.sprite.set_texture(0)
