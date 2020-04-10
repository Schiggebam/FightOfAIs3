import arcade

class IconButton:
    def __init__(self, center_x, center_y, tex_pressed: str, tex_unpressed: str, width=48, height=48, scale=1.0):
        self.center_x = center_x
        self.center_y = center_y
        self.width = width * scale
        self.height = height * scale
        self.sprite = arcade.Sprite()
        self.sprite.append_texture(arcade.load_texture(tex_unpressed))
        self.sprite.append_texture(arcade.load_texture(tex_pressed))
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