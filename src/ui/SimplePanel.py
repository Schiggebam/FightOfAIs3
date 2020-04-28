import arcade

class SimplePanel:
    def __init__(self, center_x, center_y, header: str, scale=1.25, panel_tex="../resources/other/game_panel.png",
                 no_header=False):
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

    def update(self):
        pass

    def draw(self):
        if not self.no_header:
            arcade.draw_text(self.header, self.header_x, self.header_y,
                             arcade.color.WHITE, font_size=17, align="center",
                             anchor_x="center", anchor_y="center", font_name='verdana')