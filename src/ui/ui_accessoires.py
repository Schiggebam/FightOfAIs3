from __future__ import annotations
from enum import Enum

import arcade

from src.misc.game_constants import CursorState
from src.texture_store import TextureStore


class CustomCursor(arcade.Sprite):
    def __init__(self, texture_store: TextureStore):
        super().__init__()
        self.append_texture(texture_store.get_ui_texture(UI_Texture.CURSOR_NORMAL))
        self.append_texture(texture_store.get_ui_texture(UI_Texture.CURSOR_COMBAT))
        self.set_texture(0)
        self.state: CursorState = CursorState.NORMAL

    def update_cursor(self, mouse_x: float, mouse_y: float):
        self.center_x = mouse_x + 15
        self.center_y = mouse_y - 15

    def set_cursor_to_combat(self):
        if self.state != CursorState.COMBAT:
            self.state = CursorState.COMBAT
            self.set_texture(1)

    def set_cursor_to_normal(self):
        if self.state != CursorState.NORMAL:
            self.state = CursorState.NORMAL
            self.set_texture(0)


class UI_Texture(Enum):
    """
    All textures in the class will be loaded at startup
    The path to the texture will be appended to UI_TEXTURE_PATH in Definitions
    """

    # ---------- Mouse cursors -------
    """default cursor texture"""
    CURSOR_NORMAL = "cursors/cursor_normal.png"

    """cursure texture for all combat action"""
    CURSOR_COMBAT = "cursors/cursor_fight.png"

    # ---------- Buttons -------------
    """basic text button"""
    BUTTON_BASIC_UNPRESSED = "unpressed.png"
    BUTTON_BASIC_PRESSED = "pressed.png"


    # ---------- Panels --------------
    """most basic, plain black panel"""
    PANEL_BASIC = "panels/basic_panel.png"

    """panel for battle 'army vs army' - attacker won"""
    PANEL_BATTLE_AvsA_A_WON = "panels/new_battle_panel_a_won.png"

    """panel for battle 'army vs army' - defender won"""
    PANEL_BATTLE_AvsA_D_WON = "panels/new_battle_panel_d_won.png"

    """panel for battle 'army vs army' - draw"""
    PANEL_BATTLE_AvsA_DRAW = "panels/new_battle_panel_draw.png"

    """panel for battle 'army vs building' - attacker won, building destroyed"""
    PANEL_BATTLE_AvsB_A_WON = "panels/army_vs_building_a_won.png"

    """panel for battle 'army vs building' - building defended"""
    PANEL_BATTLE_AvsB_B_WON = "panels/army_vs_building_b_won.png"

    """panel for battle 'army vs building' - draw"""
    PANEL_BATTLE_AvsB_DRAW = "panels/army_vs_building_draw.png"
