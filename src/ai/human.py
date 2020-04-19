# from typing import Dict, Any, Tuple
#
# import arcade
#
# from src.ai.AI_GameStatus import AI_Move
#
#
# class SelectionTool(arcade.Sprite):
#     def __init__(self):
#         super().__init__()
#         tex = arcade.load_texture("../resources/objects/selection_far.png")
#         self.append_texture(tex)
#         self.center_x = 400
#         self.center_y = 400
#         self.set_texture(0)
#
#
# class HumanInteraction:
#
#     def __init__(self, zlvl_top):
#         self.is_active = True
#         self.selection_tool = SelectionTool()
#         zlvl_top.append(self.selection_tool)
#
#     def show_selection_tool(self, mouse_x: int, mouse_y: int):
#         if self.is_active:
#             self.selection_tool.center_x = mouse_x
#             self.selection_tool.center_y = mouse_y
