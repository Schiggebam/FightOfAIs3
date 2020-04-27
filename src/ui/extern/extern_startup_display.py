import os
from dataclasses import dataclass
from enum import Enum
from threading import Thread
from typing import Optional

from os import listdir
from os.path import isfile, join

import wx
from wx import App

import untangle

class DecisionType(Enum):
    DCN_READ_DOCUMENTATION = 0
    DCN_START_GAME = 1
    DCN_EXIT_GAME = 2


@dataclass
class Decision:
    decision: DecisionType
    xml_file_location: str
    show_ai_control: bool = False
    show_stats_on_exit: bool = False
    allow_command_line_input: bool = False
    enable_debug_mode: bool = False



class StartupFrame(wx.Frame):
    def __init__(self, resource_dir: str, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        #---------------------- START ---------------------------
        self.SetSize((700, 800))
        self.panel_1 = wx.Panel(self, wx.ID_ANY)
        self.panel_9 = wx.Panel(self.panel_1, wx.ID_ANY)
        self.combo_box_1 = wx.ComboBox(self.panel_9, wx.ID_ANY, choices=[], style=wx.CB_DROPDOWN)
        self.button_load_xml = wx.Button(self.panel_9, wx.ID_ANY, "Load")
        self.panel_2 = wx.Panel(self.panel_1, wx.ID_ANY)
        self.tree_ctrl_1 = wx.TreeCtrl(self.panel_2, wx.ID_ANY)
        self.panel_5 = wx.ScrolledWindow(self.panel_2, wx.ID_ANY, style=wx.BORDER_SUNKEN)
        self.text_details = wx.StaticText(self.panel_5, wx.ID_ANY,
                                          "Please select an element in the tree (double click)")
        self.panel_6 = wx.Panel(self.panel_1, wx.ID_ANY)
        self.text_information = wx.StaticText(self.panel_6, wx.ID_ANY, "Please select the game XML file.")
        self.panel_7 = wx.Panel(self.panel_1, wx.ID_ANY)
        self.panel_8 = wx.Panel(self.panel_7, wx.ID_ANY)
        self.checkbox_show_ai_ctrl = wx.CheckBox(self.panel_8, wx.ID_ANY, "Show AI CTRL Frame")
        self.checkbox_show_stats = wx.CheckBox(self.panel_8, wx.ID_ANY, "Show Statistics Upon Exit")
        self.checkbox_allow_cmd_input = wx.CheckBox(self.panel_8, wx.ID_ANY, "Allow Command Line Input")
        self.checkbox_enable_debug = wx.CheckBox(self.panel_8, wx.ID_ANY, "Enable Debug Mode")
        self.button_read_docu = wx.Button(self.panel_1, wx.ID_ANY, "Read Documentation")
        self.button_exit = wx.Button(self.panel_1, wx.ID_ANY, "Exit")
        self.button_start_game = wx.Button(self.panel_1, wx.ID_ANY, "Start Game")
        # ---------------------- END ------------------------------
        self.checkbox_enable_debug.SetForegroundColour(wx.Colour(100, 100, 100))
        self.button_start_game.Disable()
        self.Bind(wx.EVT_CLOSE, self.on_close_window)

        # init frame variables:
        self.decision: Optional[Decision] = None
        self.resource_dir = resource_dir
        self.xml_parser = None

        self.__set_properties()
        self.__do_layout()
        self.__setup_combo_box()
        self.__bind_callback_functions()

    def __set_properties(self):
        self.SetTitle("Welcome Frame")
        _icon = wx.NullIcon
        _icon.CopyFromBitmap(wx.Bitmap("..\\resources\\objects\\flag_red.png", wx.BITMAP_TYPE_ANY))
        self.SetIcon(_icon)
        self.combo_box_1.SetMinSize((150, 23))
        self.panel_5.SetFocus()
        self.panel_5.SetScrollRate(10, 10)
        self.checkbox_show_ai_ctrl.SetValue(1)
        self.checkbox_show_stats.SetValue(1)
        self.checkbox_allow_cmd_input.SetValue(1)
        self.checkbox_enable_debug.SetValue(1)

    def __do_layout(self):
        # ---------------------- START ---------------------------
        sizer_3 = wx.BoxSizer(wx.VERTICAL)
        sizer_4 = wx.BoxSizer(wx.VERTICAL)
        sizer_10 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_13 = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_1 = wx.GridSizer(3, 3, 0, 0)
        sizer_12 = wx.BoxSizer(wx.VERTICAL)
        sizer_7 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_15 = wx.BoxSizer(wx.VERTICAL)
        sizer_11 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_9 = wx.BoxSizer(wx.VERTICAL)
        sizer_14 = wx.BoxSizer(wx.VERTICAL)
        sizer_6 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_5 = wx.BoxSizer(wx.HORIZONTAL)
        InfoText = wx.StaticText(self.panel_1, wx.ID_ANY, "Welcome to [pre-alpha] WarOfTribes aka. FightOfAIs aka. let's do some coding and see where it takes us")
        sizer_5.Add(InfoText, 0, wx.BOTTOM | wx.RIGHT | wx.TOP, 10)
        sizer_4.Add(sizer_5, 0, wx.EXPAND | wx.LEFT, 4)
        label_1 = wx.StaticText(self.panel_9, wx.ID_ANY, "Select the XML input file: ")
        sizer_6.Add(label_1, 0, wx.RIGHT | wx.TOP, 10)
        sizer_6.Add(self.combo_box_1, 1, wx.ALL, 5)
        sizer_6.Add(self.button_load_xml, 0, wx.LEFT | wx.RIGHT | wx.TOP, 5)
        sizer_14.Add(sizer_6, 0, wx.EXPAND | wx.RIGHT, 10)
        label_6 = wx.StaticText(self.panel_9, wx.ID_ANY, "Note: The search direction for game.xml files is <root>/resources/")
        label_6.SetForegroundColour(wx.Colour(128, 128, 128))
        sizer_14.Add(label_6, 0, wx.TOP, 5)
        self.panel_9.SetSizer(sizer_14)
        sizer_4.Add(self.panel_9, 1, wx.EXPAND | wx.LEFT, 4)
        label_2 = wx.StaticText(self.panel_2, wx.ID_ANY, "XML Structure")
        label_2.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, "Segoe UI"))
        sizer_9.Add(label_2, 0, wx.ALL, 5)
        sizer_9.Add(self.tree_ctrl_1, 1, wx.EXPAND, 0)
        sizer_7.Add(sizer_9, 1, wx.EXPAND, 0)
        label_3 = wx.StaticText(self.panel_2, wx.ID_ANY, "Properties")
        label_3.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, "Segoe UI"))
        sizer_15.Add(label_3, 0, wx.ALL, 5)
        sizer_11.Add(self.text_details, 0, 0, 5)
        self.panel_5.SetSizer(sizer_11)
        sizer_15.Add(self.panel_5, 2, wx.ALL | wx.EXPAND, 7)
        sizer_7.Add(sizer_15, 2, wx.EXPAND, 0)
        self.panel_2.SetSizer(sizer_7)
        sizer_4.Add(self.panel_2, 5, wx.EXPAND | wx.LEFT | wx.TOP, 4)
        label_4 = wx.StaticText(self.panel_6, wx.ID_ANY, "Information: ")
        label_4.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, "Segoe UI"))
        sizer_12.Add(label_4, 0, wx.ALL, 5)
        static_line_1 = wx.StaticLine(self.panel_6, wx.ID_ANY)
        sizer_12.Add(static_line_1, 0, wx.EXPAND, 0)
        sizer_12.Add(self.text_information, 0, wx.ALL, 5)
        self.panel_6.SetSizer(sizer_12)
        sizer_4.Add(self.panel_6, 2, wx.EXPAND | wx.LEFT, 4)
        label_5 = wx.StaticText(self.panel_7, wx.ID_ANY, "Settings: ")
        label_5.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, "Segoe UI"))
        sizer_13.Add(label_5, 0, wx.ALL, 5)
        static_line_3 = wx.StaticLine(self.panel_7, wx.ID_ANY)
        sizer_13.Add(static_line_3, 0, wx.EXPAND, 0)
        grid_sizer_1.Add(self.checkbox_show_ai_ctrl, 0, wx.ALL, 10)
        grid_sizer_1.Add((0, 0), 0, 0, 0)
        grid_sizer_1.Add((0, 0), 0, 0, 0)
        grid_sizer_1.Add(self.checkbox_show_stats, 0, wx.ALL, 10)
        grid_sizer_1.Add((0, 0), 0, 0, 0)
        grid_sizer_1.Add(self.checkbox_allow_cmd_input, 0, wx.ALL, 10)
        grid_sizer_1.Add((0, 0), 0, 0, 0)
        grid_sizer_1.Add((0, 0), 0, 0, 0)
        grid_sizer_1.Add(self.checkbox_enable_debug, 0, wx.ALL, 10)
        self.panel_8.SetSizer(grid_sizer_1)
        sizer_13.Add(self.panel_8, 1, wx.EXPAND, 0)
        self.panel_7.SetSizer(sizer_13)
        sizer_4.Add(self.panel_7, 2, wx.EXPAND | wx.LEFT, 4)
        static_line_2 = wx.StaticLine(self.panel_1, wx.ID_ANY)
        sizer_4.Add(static_line_2, 0, wx.EXPAND, 0)
        sizer_10.Add(self.button_read_docu, 1, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, 20)
        sizer_10.Add(self.button_exit, 1, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.LEFT | wx.RIGHT, 20)
        sizer_10.Add(self.button_start_game, 1, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, 20)
        sizer_4.Add(sizer_10, 0, wx.ALL | wx.EXPAND, 10)
        self.panel_1.SetSizer(sizer_4)
        sizer_3.Add(self.panel_1, 1, wx.EXPAND, 0)
        self.SetSizer(sizer_3)
        self.Layout()
        # ---------------------- END ---------------------------
        font = wx.Font(10, wx.DECORATIVE, wx.NORMAL, wx.BOLD)
        InfoText.SetFont(font)

    def __bind_callback_functions(self):
        self.button_exit.Bind(wx.EVT_BUTTON, self.on_close_window)
        self.button_start_game.Bind(wx.EVT_BUTTON, self.on_button_start_game)
        self.button_read_docu.Bind(wx.EVT_BUTTON, self.on_button_read_docu)
        self.button_load_xml.Bind(wx.EVT_BUTTON, self.on_button_load_xml)
        self.tree_ctrl_1.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.on_tree_item_select)


    def __setup_combo_box(self):
        choices = [f for f in listdir(self.resource_dir) if isfile(join(self.resource_dir, f))]
        for c in choices:
            if c.endswith(".xml"):
                self.combo_box_1.Append(c)
        self.combo_box_1.SetValue("game_2.xml")

    def on_button_load_xml(self, event):
        xml_file = self.resource_dir + self.combo_box_1.GetValue()
        if len(xml_file) == 0:
            return
        if not os.path.isfile(xml_file):
            self.text_information.SetLabel("Invalid File!")
            self.text_information.SetForegroundColour(wx.RED)
            return
        if not xml_file.endswith(".xml"):
            self.text_information.SetLabel("File has to be in XML format!")
            self.text_information.SetForegroundColour(wx.RED)
            return
        self.button_start_game.Enable()
        self.root = self.tree_ctrl_1.AddRoot('game')
        self.xml_parser = untangle.parse(xml_file)
        for elem in self.xml_parser.game.children:
            cur = self.tree_ctrl_1.AppendItem(self.root, elem._name)
            for child in elem.children:
                self.tree_ctrl_1.AppendItem(cur, child._name)

        # check for human controlled player
        has_human = False
        for elem in self.xml_parser.game.players:
            if elem.get_attribute('ai') == "human":
                has_human = True
        if has_human:
            self.text_information.SetLabel("At least one player found, which is controlled by a human player")
        else:
            self.text_information.SetLabel("All players are controlled by AIs. No 'human' player found in xml data")
            self.text_information.SetForegroundColour(wx.RED)
        self.tree_ctrl_1.Expand(self.root)


    def on_button_read_docu(self, event):
        osCommandString = "notepad.exe ../Documentation_v0.1.txt"
        os.system(osCommandString)

    def on_button_start_game(self, event):
        xml_file = self.combo_box_1.GetValue()
        self.decision = Decision(DecisionType.DCN_START_GAME, self.resource_dir + xml_file)
        self.decision.allow_command_line_input = self.checkbox_allow_cmd_input.GetValue()
        self.decision.enable_debug_mode = self.checkbox_enable_debug.GetValue()
        self.decision.show_ai_control = self.checkbox_show_ai_ctrl.GetValue()
        self.decision.show_stats_on_exit = self.checkbox_show_stats.GetValue()
        self.Destroy()

    def on_close_window(self, event):
        self.decision = Decision(DecisionType.DCN_EXIT_GAME, "")
        self.Destroy()

    def on_tree_item_select(self, event):
        path = []
        item = self.tree_ctrl_1.GetSelection()
        while self.tree_ctrl_1.GetItemParent(item):
            piece = self.tree_ctrl_1.GetItemText(item)
            path.insert(0, piece)
            item = self.tree_ctrl_1.GetItemParent(item)
        cur = self.xml_parser.game
        for p in path:
            for c in cur.children:
                if c._name == p:
                    cur = c
                    break
        s_buf = ""
        for key, value in cur._attributes.items():
            s_buf += f"{key} -> {value} \n"
        s_buf += cur.cdata
        self.text_details.SetLabel(s_buf)



class StartUp(Thread):
    def __init__(self, resouce_dir: str):
        Thread.__init__(self)
        self.app: Optional[App] = None
        self.frame: Optional[StartupFrame] = None
        self.resource_dir = resouce_dir

    def run(self):
        self.app = wx.App(False)
        self.app.SetAssertMode(wx.APP_ASSERT_SUPPRESS)
        self.frame = StartupFrame(self.resource_dir, None)
        self.frame.Show()
        self.app.MainLoop()

    def has_decision(self):
        return self.frame.decision

    def close(self):
        pass
