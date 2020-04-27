# import wx
#
#
# class Mywin(wx.Frame):
#     def __init__(self, parent, title):
#         super(Mywin, self).__init__(parent, title=title, size=(300, 200))
#
#         panel = wx.Panel(self)
#         box = wx.BoxSizer(wx.VERTICAL)
#         self.label = wx.StaticText(panel, label="Your choice:", style=wx.ALIGN_CENTRE)
#         box.Add(self.label, 0, wx.EXPAND | wx.ALL, 20)
#         cblbl = wx.StaticText(panel, label="Combo box", style=wx.ALIGN_CENTRE)
#
#         box.Add(cblbl, 0, wx.EXPAND | wx.ALL, 5)
#         languages = ['C', 'C++', 'Python', 'Java', 'Perl']
#         self.combo = wx.ComboBox(panel, choices=languages)
#
#         box.Add(self.combo, 1, wx.EXPAND | wx.ALL, 5)
#         chlbl = wx.StaticText(panel, label="Choice control", style=wx.ALIGN_CENTRE)
#
#         box.Add(chlbl, 0, wx.EXPAND | wx.ALL, 5)
#         self.choice = wx.Choice(panel, choices=languages)
#         box.Add(self.choice, 1, wx.EXPAND | wx.ALL, 5)
#
#         box.AddStretchSpacer()
#         self.combo.Bind(wx.EVT_COMBOBOX, self.OnCombo)
#         self.choice.Bind(wx.EVT_CHOICE, self.OnChoice)
#
#         panel.SetSizer(box)
#         self.Centre()
#         self.Show()
#
#     def OnCombo(self, event):
#         self.label.SetLabel("You selected" + self.combo.GetValue() + " from Combobox")
#
#     def OnChoice(self, event):
#         self.label.SetLabel("You selected " + self.choice.GetString
#         (self.choice.GetSelection()) + " from Choice")
#
#
# app = wx.App()
# Mywin(None, 'ComboBox and Choice demo')
# app.MainLoop()













import wx

class TreeExample(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, title='Tree Example', size=(200, 130))
        self.tree = wx.TreeCtrl(self, size=(200, 100))

        root = self.tree.AddRoot('root')
        for item in ['item1', 'item2', 'item3']:
            self.tree.AppendItem(root, item)
        self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.OnActivated, self.tree)
        self.tree.Expand(root)

    def OnActivated(self, evt):
        print( 'Double clicked on', self.tree.GetItemText(evt.GetItem()))

app = wx.App(None)
TreeExample().Show()
app.MainLoop()


