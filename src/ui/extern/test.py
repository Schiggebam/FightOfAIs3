# import wx
# import wx.html as html
#
# class MainFrame(wx.Frame):
#     def __init__(self, parent, title):
#         wx.Frame.__init__(self, parent, -1, title)
#         panel = MainPanel(self)
#
# class MainPanel(wx.Panel):
#     def __init__(self, frame):
#         wx.Panel.__init__(self, frame)
#
#         txt_style = wx.VSCROLL|wx.HSCROLL|wx.TE_READONLY|wx.BORDER_SIMPLE
#         self.html = html.HtmlWindow(self, -1, size=(300, 150), style=txt_style)
#         self.html.SetPage(
#                     "Here is some <b>formatted</b>"
#                     "<i><u>text</u></i> "
#                     "loaded from a "
#                     "<font color=\"red\">string</font>.")
#
# app = wx.App()
# frm = MainFrame(None, "Screen layout")
# frm.Show()
# app.MainLoop()


import wx
import matplotlib
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure

class MainFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, wx.NewId(), "Main")
        panel = wx.Panel(self,1)
        #sizer = wx.BoxSizer(wx.HORIZONTAL)
        boxsizer = wx.BoxSizer(wx.VERTICAL)
        c1 = wx.CheckBox(panel, label="Text")
        c2 = wx.CheckBox(panel, label="HTML ")
        c3 = wx.CheckBox(panel, label="NLP")
        c1.Bind(wx.EVT_CHECKBOX, self.OntextMetric, c1)
        c2.Bind(wx.EVT_CHECKBOX, self.OntextMetric,c2)
        c3.Bind(wx.EVT_CHECKBOX, self.OntextMetric,c3)
        self.abt_Metric= wx.StaticText(panel, label='')
        boxsizer.Add(c1,flag=wx.LEFT, border=5)
        boxsizer.Add(c2,flag=wx.LEFT, border=5)
        boxsizer.Add(c3,flag=wx.LEFT, border=5)

        boxsizer.Add(self.abt_Metric, flag = wx.LEFT)
        panel.SetSizer(boxsizer)

    def OntextMetric(self,event):
        if event.IsChecked():
            self.abt_Metric.SetLabel(event.GetEventObject().GetLabel() + "collected")

class MyApp(wx.App):
    def OnInit(self):
        frame = MainFrame()
        frame.Show(True)
        self.SetTopWindow(frame)
        return True

app = MyApp(0)
app.MainLoop()