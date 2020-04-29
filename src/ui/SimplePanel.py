import arcade

from src.texture_store import TextureStore
from src.ui.ui_accessoires import UI_Texture


class SimplePanel:
    def __init__(self, center_x, center_y, header: str, scale=1.25, panel_tex="../resources/other/game_panel.png",
                 no_header=False, header_y=0):
        self.sprite = arcade.Sprite()
        self.sprite.append_texture(arcade.load_texture(panel_tex))
        self.sprite.center_x = center_x
        self.sprite.center_y = center_y
        self.sprite.scale = scale
        self.sprite.set_texture(0)
        self.header = header
        self.no_header = no_header
        if scale == 1.25:                       # TODO so hacky:)
            self.header_x = center_x
            self.header_y = (center_y + 95)
            self.text_box_x = center_x - 160
            self.text_box_y = center_y + 60
        elif scale == 1.0:
            self.header_x = center_x
            self.header_y = (center_y + 78)
            self.text_box_x = center_x - 130
            self.text_box_y = center_y + 40
        elif scale == 2.0:
            self.header_x = center_x
            self.header_y = (center_y + 150)
            self.text_box_x = center_x - 250
            self.text_box_y = center_y + 80
        else:
            print("SimplePanel: Unsupported scale set. Supported scales are 1.0, 1.25 and 2.0")
        self.show = False
        if header_y != 0:       # override header y
            self.header_y = center_y + header_y

    def update(self):
        pass

    def draw(self):
        if not self.no_header:
            arcade.draw_text(self.header, self.header_x, self.header_y,
                             arcade.color.WHITE, font_size=16, align="center",
                             anchor_x="center", anchor_y="center", font_name='verdana')


class ClosablePanel:
    def __init__(self, center_x, center_y, tex: arcade.Texture, scale=1):
        self.sprite = arcade.Sprite(center_x=center_x, center_y=center_y)
        self.sprite.scale = scale
        self.sprite.append_texture(tex)
        self.sprite.set_texture(0)
        self.show = False
        self.text_box_x = center_x - 160
        self.text_box_y = center_y + 60
        self.x_bb = ((self.sprite.center_x + self.sprite.width/2 - 30,
                      self.sprite.center_x + self.sprite.width/2),
                     (self.sprite.center_y + self.sprite.height/2 - 30,
                      self.sprite.center_y + self.sprite.height/2))

    def is_close_button_hit(self, x, y) -> bool:
        if self.x_bb[0][0] < x < self.x_bb[0][1]:
            if self.x_bb[1][0] < y < self.x_bb[1][1]:
                return True
        return False

    def update(self):
        pass

    def draw(self):
        pass


class BasicPanel:
    """Just a basic black background"""
    def __init__(self, center_x, center_y, width=150, height=72, alpha=255):
        self.sprite = arcade.Sprite(center_x=center_x, center_y=center_y,
                                    image_width=width, image_height=height)
        self.sprite.append_texture(TextureStore.instance().get_ui_texture(UI_Texture.PANEL_BASIC))
        self.sprite.set_texture(0)
        self.sprite.alpha = alpha
        self.text_box_x = center_x - width/2
        self.text_box_y = center_y - height/2
        self.show = False

    def update(self):
        pass

    def draw(self):
        pass
