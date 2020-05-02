from typing import Optional

from src.game_accessoires import Army, Unit, Resource
from src.misc.building import Building
from src.misc.game_constants import PlayerColour
from src.misc.game_logic_misc import Logger, IncomeCalculator
from src.player import Player
from src.texture_store import TextureStore
from src.ui.lang_en import *
from src.ui.ui_accessoires import UI_Texture
from src.ui.ui_panel_templates import SimplePanel, ClosablePanel, BasicPanel

ls = "    "
ts = "  "

class PanelInfo(SimplePanel):
    def __init__(self, center_x, center_y, header: str, gl):
        super().__init__(center_x, center_y, header, scale=2)
        self.text = "Please read the GameDesignDoc.txt / Documentation for general information!\n"
        self.text += "Buildings: \n"
        self.sprites = []
        offset_y = 0
        for t_b in [BuildingType.HUT, BuildingType.VILLA, BuildingType.BARRACKS, BuildingType.FARM]:
            s = arcade.Sprite(center_x=self.text_box_x-20, center_y=self.text_box_y - offset_y)
            s.append_texture(TextureStore.instance().get_texture(Building.building_info[t_b]['tex_code']))
            s.set_texture(0)
            self.sprites.append(s)
            self.text += ts + building_type_conversion(t_b) + "\n"
            self.text += ls + Building.building_info[t_b]['description'] + "\n"
            self.text += ls + f"Construction cost: {Building.get_construction_cost(t_b)},"
            self.text += f" defencive value: {Building.building_info[t_b]['defensive_value']}\n"
            if t_b is BuildingType.HUT:
                self.text += ls + f"Income per adjacent resource field: {Building.building_info[t_b]['resource_per_field']}"
                self.text += f", culture per turn: {Building.building_info[t_b]['culture_per_turn']} \n"
                self.text += ls + f"Food consumption: {Building.building_info[t_b]['food_consumption']} \n"
            if t_b is BuildingType.BARRACKS:
                self.text += ls + f"Increases population by: {Building.building_info[t_b]['grant_pop']}\n"
            if t_b is BuildingType.FARM:
                self.text += ls + f"Food per corn field: 1 \n"
            if t_b is BuildingType.VILLA:
                self.text += ls + f"Resource per turn by itself: {Building.building_info[t_b]['resource_per_turn']}\n"
            offset_y += 70

    def draw(self):
        super().draw()
        if len(self.text) > 0:
            arcade.draw_text(self.text, self.text_box_x+15, self.text_box_y-250,
                             arcade.color.WHITE, font_size=10, font_name='verdana')
        for s in self.sprites:
            s.draw()


class PanelAI(SimplePanel):
    def __init__(self, center_x, center_y, header: str, gl):
        super().__init__(center_x, center_y, header)
        self.text = ""
        self.gl = gl


    def update(self):
        self.text = ""
        for p in self.gl.player_list:
            if p.player_type != PlayerType.HUMAN:
                self.text = self.text + p.name + ": \n"
                self.text = self.text + self.gl.ai_interface.query_ai('state', None, p.id) + "\n"

    def draw(self):
        super().draw()
        if len(self.text) > 0:
            arcade.draw_text(self.text, self.text_box_x, self.text_box_y - 135,
                             arcade.color.WHITE, font_size=15, font_name='verdana')


class PanelDiplo(SimplePanel):
    def __init__(self, center_x, center_y, header: str, gl):
        super().__init__(center_x, center_y, header)
        self.gl = gl
        self.text = ""

    def update(self):
        self.text = ""
        for p in self.gl.player_list:
            self.text += ls + ls + str(p.id)
        self.text += "\n \n"
        for i in range(len(self.gl.player_list)):
            self.text += str(self.gl.player_list[i].id) + ls
            for j in range(len(self.gl.player_list)):
                if i == j:
                    self.text += '---' + ls + ts
                else:
                    if not self.gl.player_list[i].player_type == PlayerType.HUMAN:
                        self.text += str(self.gl.ai_interface.query_ai("diplo", j, i)) + ls + ts
                    else:
                        self.text += '---' + ls + ts
            self.text += "\n \n"

    def draw(self):
        super().draw()
        x_offset = 50
        y_offset = 30
        it = 0
        if len(self.text) > 0:
            arcade.draw_text(self.text, self.text_box_x, self.text_box_y - 180,
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
    def __init__(self, center_x, center_y, building: Building):
        super().__init__(center_x, center_y, "Building", scale=1)
        self.building = building
        self.text = ""

    def update(self):
        self.text = building_type_conversion(self.building.building_type) + "\n"
        self.text += "State: " + building_state_conversion(self.building.building_state) + "\n"
        if IncomeCalculator.building_population_influence(self.building) != 0:
            self.text += "Population: " + str(IncomeCalculator.building_population_influence(self.building)) + "\n"
        if IncomeCalculator.building_food_influence(self.building) != 0:
            self.text += "Food: " + str(IncomeCalculator.building_food_influence(self.building)) + "\n"
        if IncomeCalculator.building_culture_influce(self.building) != 0:
            self.text += "Culture: " + str(IncomeCalculator.building_culture_influce(self.building)) + "\n"
        self.text += "Defence: " + str(self.building.defensive_value) + "\n"
        if self.building.building_type == BuildingType.HUT:
            self.text += "Resource per adjacent field: " + str(self.building.resource_per_field)

    def draw(self):
        super().draw()
        if len(self.text) > 0:
            arcade.draw_text(self.text, self.text_box_x, self.text_box_y-100,
                             arcade.color.WHITE, font_size=14, font_name='verdana')


class PanelResource(SimplePanel):
    def __init__(self, center_x, center_y, resource: Resource):
        super().__init__(center_x, center_y, "Resource", scale=1)
        self.test = ""
        self.resource = resource

    def update(self):
        self.text = resource_type_conversion(self.resource.resource_type) + "\n"
        self.text += "Resources remaining: " + str(self.resource.remaining_amount)

    def draw(self):
        super().draw()
        if len(self.text) > 0:
            arcade.draw_text(self.text, self.text_box_x, self.text_box_y-20,
                             arcade.color.WHITE, font_size=14, font_name='verdana')


class PanelLogBattle(ClosablePanel):
    def __init__(self, center_x, center_y, log: Logger.BattleLog, texture_store: TextureStore):
        panel_tex: Optional[UI_Texture] = None
        header = ""
        if log.log_type == LogType.BATTLE_ARMY_VS_ARMY:
            if log.outcome is BattleAfterMath.ATTACKER_WON:
                panel_tex = UI_Texture.PANEL_BATTLE_AvsA_A_WON
                header = "Attacker won"
                self.text = "Attacker won, all defending units are wiped out"
            elif log.outcome is BattleAfterMath.DEFENDER_WON:
                panel_tex = UI_Texture.PANEL_BATTLE_AvsA_D_WON
                header = "Defender won"
                self.text = "Defender won, all attacking units are defeated"
            else:
                panel_tex = UI_Texture.PANEL_BATTLE_AvsA_DRAW
                header = "Draw!"
            super().__init__(center_x, center_y, texture_store.get_ui_texture(panel_tex), scale=1.25)
            att_kia = (log.pre_att_units[0] - log.post_att_units[0],
                       log.pre_att_units[1] - log.post_att_units[1],
                       log.pre_att_units[2] - log.post_att_units[2])
            def_kia = (log.pre_def_units[0] - log.post_def_units[0],
                       log.pre_def_units[1] - log.post_def_units[1],
                       log.pre_def_units[2] - log.post_def_units[2])

            self.att_name = str(log.att_name)
            self.def_name = str(log.def_name)
            self.in_action = f"{log.pre_att_units[1]} {ls} {log.pre_att_units[0]} {ls}{log.pre_att_units[2]}                    {ls}{log.pre_def_units[1]} {ls} {log.pre_def_units[0]} {ls} {log.pre_def_units[2]}"
            self.kia = f"{att_kia[1]} {ls} {att_kia[0]} {ls}{att_kia[2]}                    {ls}{def_kia[1]} {ls} {def_kia[0]} {ls} {def_kia[2]}"
            self.remaining = f"{log.post_att_units[1]} {ls} {log.post_att_units[0]} {ls}{log.post_att_units[2]}                    {ls}{log.post_def_units[1]} {ls} {log.post_def_units[0]} {ls} {log.post_def_units[2]}"
        # -------------------------------------------------------
        elif log.log_type == LogType.BATTLE_ARMY_VS_BUILDING:
            if log.outcome is BattleAfterMath.ATTACKER_WON:
                panel_tex = UI_Texture.PANEL_BATTLE_AvsB_A_WON
                self.text = "Building destroyed"
                header = "Army won"
            elif log.outcome is BattleAfterMath.DEFENDER_WON:
                panel_tex = UI_Texture.PANEL_BATTLE_AvsB_B_WON
                self.text = "Army suffered catastrophic losses. Building defended"
                header = "Building defended"
            else:
                panel_tex = UI_Texture.PANEL_BATTLE_AvsB_DRAW
                self.text = "Army destroyed, but not before the building burst into flames"
                header = "Draw!"
            super().__init__(center_x, center_y, texture_store.get_ui_texture(panel_tex), scale=1.25)
            att_kia = (log.pre_att_units[0] - log.post_att_units[0],
                       log.pre_att_units[1] - log.post_att_units[1],
                       log.pre_att_units[2] - log.post_att_units[2])
            def_kia = log.pre_def_units[0] - log.post_def_units[0]

            self.att_name = log.att_name
            self.def_name = log.def_name
            self.in_action = f"{log.pre_att_units[1]} {ls} {log.pre_att_units[0]} {ls}{log.pre_att_units[2]}  {ls}{ls}{ls}                 {log.pre_def_units[0]}"
            self.kia = f"{att_kia[1]} {ls} {att_kia[0]} {ls}{att_kia[2]}{ls}{ls}                   {ls}{def_kia}"
            self.remaining = f"{log.post_att_units[1]} {ls} {log.post_att_units[0]} {ls}{log.post_att_units[2]}{ls}{ls}{ls}                   {log.post_def_units[0]}"

    def draw(self):
        super().draw()
        x_offset = 5
        if len(self.att_name) > 0 and len(self.def_name) > 0:
            arcade.draw_text(self.att_name, self.text_box_x + 10, self.text_box_y + 10,
                             arcade.color.WHITE, font_size=15, font_name='verdana')
            arcade.draw_text(self.def_name, self.text_box_x + 220, self.text_box_y + 10,
                             arcade.color.WHITE, font_size=15, font_name='verdana')
        arcade.draw_text(self.in_action, self.text_box_x + x_offset, self.text_box_y - 110,
                         arcade.color.WHITE, font_size=13, font_name='verdana')
        arcade.draw_text(self.kia, self.text_box_x + x_offset, self.text_box_y - 137,
                         arcade.color.RED, font_size=13, font_name='verdana')
        arcade.draw_text(self.remaining, self.text_box_x + x_offset, self.text_box_y - 170,
                         arcade.color.WHITE, font_size=13, font_name='verdana')
        if len(self.text) > 0:
            arcade.draw_text(self.text, self.text_box_x + x_offset, self.text_box_y - 202,
                             arcade.color.WHITE, font_size=11, font_name='verdana')


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


class CostPanel(BasicPanel):
    def __init__(self, center_x, center_y, text: str, c: arcade.color):
        super().__init__(center_x, center_y, alpha=160)
        self.text = text
        self.c = c

    def draw(self):
        arcade.draw_text(self.text, self.text_box_x + 5, self.text_box_y + 5,
                         self.c, font_size=10, font_name='verdana')


class MainPanel(arcade.Sprite):
    def __init__(self, screen_width: int, y=102):
        super().__init__()
        self.append_texture(TextureStore.instance().get_ui_texture(UI_Texture.PANEL_MAIN))
        self.set_position(screen_width/2, y)
        self.set_texture(0)
