from src.game_accessoires import Army, Unit
from src.misc.game_logic_misc import Logger
from src.player import Player
from src.ui.SimplePanel import SimplePanel
from src.ui.lang_en import *
from src.misc.game_constants import PlayerColour

ls = "    "
ts = "  "

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
    def __init__(self, center_x, center_y, army: Army):
        super().__init__(center_x, center_y, "", panel_tex="../resources/other/panel_army.png", no_header=True)
        u = army.get_units_as_tuple()
        a = (Unit.get_unit_stats(UnitType.KNIGHT))
        b = (Unit.get_unit_stats(UnitType.MERCENARY))
        c = (Unit.get_unit_stats(UnitType.BABARIC_SOLDIER))
        self.units = f"{u[1]} {ls} {ls}{ts}{u[0]} {ls}{ls}{ts}{u[2]}"
        self.m_value = f"{a[0]}{ls}{ls}{ls}{b[0]}{ls}{ls}{ls}{c[0]}\n{a[1]}{ls}{ls}{ls}{b[1]}{ls}{ls}{ls}{c[1]}\n{a[2]}{ls}{ls}{ls}{b[2]}{ls}{ls}{ls}{c[2]}"

    def draw(self):
        super().draw()
        arcade.draw_text(self.units, self.text_box_x + 125, self.text_box_y - 75,
                         arcade.color.WHITE, font_size=15, font_name='verdana')
        arcade.draw_text(self.m_value, self.text_box_x + 125, self.text_box_y - 152,
                         arcade.color.GRAY, font_size=14, font_name='verdana')

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
    def __init__(self, center_x, center_y, log: Logger.BattleLog):
        if log.log_type == LogType.BATTLE_ARMY_VS_ARMY:
            super().__init__(center_x, center_y, "", panel_tex="../resources/other/attack_vs_army.png", no_header=True)
            att_kia = (log.pre_att_units[0] - log.post_att_units[0],
                       log.pre_att_units[1] - log.post_att_units[1],
                       log.pre_att_units[2] - log.post_att_units[2])
            def_kia = (log.pre_def_units[0] - log.post_def_units[0],
                       log.pre_def_units[1] - log.post_def_units[1],
                       log.pre_def_units[2] - log.post_def_units[2])

            self.in_action = f"{log.pre_att_units[1]} {ls} {log.pre_att_units[0]} {ls}{log.pre_att_units[2]}                     {log.pre_def_units[1]} {ls} {log.pre_def_units[0]} {ls} {log.pre_def_units[2]}"
            self.kia = f"{att_kia[1]} {ls} {att_kia[0]} {ls}{att_kia[2]}                     {def_kia[1]} {ls} {def_kia[0]} {ls} {def_kia[2]}"
            self.remaining = f"{log.post_att_units[1]} {ls} {log.post_att_units[0]} {ls}{log.post_att_units[2]}                     {log.post_def_units[1]} {ls} {log.post_def_units[0]} {ls} {log.post_def_units[2]}"
        elif log.log_type == LogType.BATTLE_ARMY_VS_BUILDING:
            super().__init__(center_x, center_y, "", panel_tex="../resources/other/attack_vs_building.png", no_header=True)
            att_kia = (log.pre_att_units[0] - log.post_att_units[0],
                       log.pre_att_units[1] - log.post_att_units[1],
                       log.pre_att_units[2] - log.post_att_units[2])
            def_kia = log.pre_def_units[0] - log.post_def_units[0]

            self.in_action = f"{log.pre_att_units[1]} {ls} {log.pre_att_units[0]} {ls}{log.pre_att_units[2]}   {ls}{ls}                 {log.pre_def_units[0]}"
            self.kia = f"{att_kia[1]} {ls} {att_kia[0]} {ls}{att_kia[2]}{ls}{ls}                    {def_kia}"
            self.remaining = f"{log.post_att_units[1]} {ls} {log.post_att_units[0]} {ls}{log.post_att_units[2]} {ls}{ls}                   {log.post_def_units[0]}"

    def draw(self):
        super().draw()
        arcade.draw_text(self.in_action, self.text_box_x + 15, self.text_box_y - 48,
                         arcade.color.WHITE, font_size=13, font_name='verdana')
        arcade.draw_text(self.kia, self.text_box_x + 15, self.text_box_y - 90,
                         arcade.color.RED, font_size=13, font_name='verdana')
        arcade.draw_text(self.remaining, self.text_box_x + 15, self.text_box_y - 137,
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
        self.colour: arcade.color = PlayerColour.player_colour_to_arcade_colour(winner.colour)

    def draw(self):
        super().draw()
        arcade.draw_text(self.text1, self.text_box_x+240, self.text_box_y,
                         self.colour, font_size=20, font_name='verdana', anchor_x="center")
        arcade.draw_text(self.text2, self.text_box_x, self.text_box_y - 220,
                         arcade.color.WHITE, font_size=12, font_name='verdana')

