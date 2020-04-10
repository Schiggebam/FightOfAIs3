import arcade

from src.player import Player
from src.ui.SimplePanel import SimplePanel
from src.ui.lang_en import *


class PanelAI(SimplePanel):
    def __init__(self, center_x, center_y, header: str, gl):
        super().__init__(center_x, center_y, header)
        self.gl = gl

    def draw(self):
        super().draw()
        y_offset = 0
        for player in self.gl.player_list:
            arcade.draw_text(str(player.name), self.text_box_x, self.text_box_y + y_offset,
                             arcade.color.WHITE, font_size=15, font_name='verdana')
            arcade.draw_text(self.gl.ai_interface.query_ai("state", None, player.id), self.text_box_x + 150, self.text_box_y + y_offset,
                             arcade.color.WHITE, font_size=15, font_name='verdana')
            y_offset = y_offset - 25


class PanelDiplo(SimplePanel):
    def __init__(self, center_x, center_y, header: str, gl):
        super().__init__(center_x, center_y, header)
        self.gl = gl

    def draw(self):
        super().draw()
        x_offset = 50
        y_offset = 30
        it = 0
        for p in self.gl.player_list:
            it = it + 1
            arcade.draw_text(str(p.id), self.text_box_x + it * x_offset, self.text_box_y, arcade.color.WHITE, font_size=14, font_name='verdana')
        it = 0
        for p in self.gl.player_list:
            it = it + 1
            arcade.draw_text(str(p.id), self.text_box_x, self.text_box_y - it * y_offset, arcade.color.WHITE, font_size=14, font_name='verdana')
        for i in range(len(self.gl.player_list)):
            for j in range(len(self.gl.player_list)):
                diplo_value = "---"
                if (j != i):
                    diplo_value = str(self.gl.ai_interface.query_ai("diplo", j, i))
                arcade.draw_text(diplo_value, self.text_box_x + x_offset * (j+1), self.text_box_y - y_offset * (i+1),
                                 arcade.color.WHITE, font_size=14, font_name='verdana')


class PanelArmy(SimplePanel):
    def __init__(self, center_x, center_y, army_strength, army_owner):
        super().__init__(center_x, center_y, "Army", scale=1)
        self.army_owner =  "Owner   : " + str(army_owner)
        self.army_strength = "Strength: " + str(army_strength)

    def draw(self):
        super().draw()
        arcade.draw_text(self.army_owner, self.text_box_x, self.text_box_y,
                         arcade.color.WHITE, font_size=15, font_name='verdana')
        arcade.draw_text(self.army_strength, self.text_box_x, self.text_box_y-20,
                         arcade.color.WHITE, font_size=15, font_name='verdana')


class PanelBuilding(SimplePanel):
    def __init__(self, center_x, center_y, building_type, building_owner, building_state):
        super().__init__(center_x, center_y, "Building", scale=1)
        self.building_type =  "Type:  " + building_type_conversion(building_type)
        self.building_owner = "Owner: " + str(building_owner)
        self.building_state = "State: " + building_state_conversion(building_state)

    def draw(self):
        super().draw()
        arcade.draw_text(self.building_type, self.text_box_x, self.text_box_y,
                         arcade.color.WHITE, font_size=15, font_name='verdana')
        arcade.draw_text(self.building_owner, self.text_box_x, self.text_box_y-20,
                         arcade.color.WHITE, font_size=15, font_name='verdana')
        arcade.draw_text(self.building_state, self.text_box_x, self.text_box_y - 40,
                         arcade.color.WHITE, font_size=15, font_name='verdana')


class PanelResource(SimplePanel):
    def __init__(self, center_x, center_y, resource_type, resource_amount):
        super().__init__(center_x, center_y, "Resource", scale=1)
        self.resource_type =  "Type:  " + str(resource_type)
        self.resource_owner = "Resources remaining: " + str(resource_amount)

    def draw(self):
        super().draw()
        arcade.draw_text(self.resource_type, self.text_box_x, self.text_box_y,
                         arcade.color.WHITE, font_size=15, font_name='verdana')
        arcade.draw_text(self.resource_owner, self.text_box_x, self.text_box_y-20,
                         arcade.color.WHITE, font_size=15, font_name='verdana')

class PanelLogBattle(SimplePanel):
    def __init__(self, center_x, center_y, log):
        super().__init__(center_x, center_y, "Battle", scale=1)
        if log.log_type == LogType.BATTLE_ARMY_VS_ARMY:
            self.attacker = "Attacker (army): " + str(log.init_strength_attacker) + \
                            " > " + str(log.after_attacker_strength)
            self.defender = "Defender (army): " + str(log.init_strength_defender) + \
                            " > " + str(log.after_defender_strength)
        elif log.log_type == LogType.BATTLE_ARMY_VS_BUILDING:
            self.attacker = "Attacker (army): " + str(log.init_strength_attacker) + \
                            " > " + str(log.after_attacker_strength)
            self.defender = "Defender (building): " + str(log.init_strength_defender) + \
                            " > " + str(log.after_defender_strength)

    def draw(self):
        super().draw()
        arcade.draw_text("A battle took place:", self.text_box_x, self.text_box_y,
                         arcade.color.WHITE, font_size=15, font_name='verdana')
        arcade.draw_text(self.attacker, self.text_box_x+10, self.text_box_y-20,
                         arcade.color.WHITE, font_size=13, font_name='verdana')
        arcade.draw_text(self.defender, self.text_box_x+10, self.text_box_y-35,
                         arcade.color.WHITE, font_size=13, font_name='verdana')


class PanelLogDiplo(SimplePanel):
    def __init__(self, center_x, center_y, log):
        super().__init__(center_x, center_y, "Diplomatics", scale=1)
        self.text1 = str(log.player_name) + " reports the following diplomatic incident:"
        if log.event_type == DiploEventType.TYPE_ENEMY_ARMY_INVADING:
            self.text2 = "An enemy army was scouted at " + str(log.loc) + "."
        elif log.event_type == DiploEventType.TYPE_ENEMY_BUILDING_SCOUTED:
            self.text2 = "A enemy building was scouted at " + str(log.loc) + "."
        if log.relative_change < 0:
            self.text3 = "This will decrease the diplomatic favour by " + str(log.relative_change) + \
                         " for " + str(log.lifetime) + " rounds."

    def draw(self):
        super().draw()
        arcade.draw_text("A diplomatic event occurred!", self.text_box_x, self.text_box_y,
                         arcade.color.WHITE, font_size=10, font_name='verdana')
        arcade.draw_text(self.text1, self.text_box_x, self.text_box_y - 15,
                         arcade.color.WHITE, font_size=10, font_name='verdana')
        arcade.draw_text(self.text2, self.text_box_x, self.text_box_y - 30,
                         arcade.color.WHITE, font_size=10, font_name='verdana')
        arcade.draw_text(self.text3, self.text_box_x, self.text_box_y - 45,
                         arcade.color.WHITE, font_size=10, font_name='verdana')

class PanelGameWon(SimplePanel):
    def __init__(self, center_x, center_y, winner: Player):
        super().__init__(center_x, center_y, "END", scale=2)
        self.text1 = "CONGRATULATIONS: " + winner.name + " won!"
        self.text2 = "However, you can continue playing.. "
        self.colour: arcade.color = Player.Player_Colour.player_colour_to_arcade_colour(winner.colour)

    def draw(self):
        super().draw()
        arcade.draw_text(self.text1, self.text_box_x+240, self.text_box_y,
                         self.colour, font_size=20, font_name='verdana', anchor_x="center")
        arcade.draw_text(self.text2, self.text_box_x, self.text_box_y - 220,
                         arcade.color.WHITE, font_size=12, font_name='verdana')

