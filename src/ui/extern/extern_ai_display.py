import time
from threading import Thread
from typing import Optional, Dict, List
#import wx.html as html

import wx
from wx import App



class SelfUpdatePanel(wx.Panel):
    def __init__(self, parent, interval, ai_ctrl, pid: int):
        wx.Panel.__init__(self, parent)
        self.updateMsg = ""
        self.textCtrl = None
        self.interval = interval
        self.ai_ctrl = ai_ctrl
        self.pid = pid
        self.halt = False
        # txt_style = wx.VSCROLL | wx.HSCROLL | wx.TE_READONLY | wx.BORDER_SIMPLE
        # self.html = html.HtmlWindow(self, -1, size=(300, 150), style=txt_style)
        # self.html.SetPage(
        #     "Here is some <b>formatted</b>"
        #     "<i><u>text</u></i> "
        #     "loaded from a "
        #     "<font color=\"red\">string</font>.")

    def set_text_ctrl(self, text):
        self.textCtrl = text

    def update_panel(self):
        self.textCtrl.SetLabel(self.updateMsg)
        # self.Refresh()

    def lifecycle(self):
        while True:
            if self.halt:
                break
            time.sleep(self.interval)
            self.updateMsg = self.ai_ctrl.get_dump(self.pid)
            self.update_panel()

    def run(self):
        thread = Thread(target=self.lifecycle)
        thread.start()


class ExternAIFrame(wx.Frame):
    def __init__(self, parent, ai_ctrl, ids_of_ais):
        wx.Frame.__init__(self, parent, size=wx.Size(1500, 500))
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
        self.main_panel = wx.Panel(self)
        self.nb = wx.Notebook(self.main_panel)

        self.ai_tab: Dict[int, SelfUpdatePanel] = {}
        for pid in ids_of_ais:
            p_temp = SelfUpdatePanel(self.nb, .5, ai_ctrl, pid)
            txt = wx.StaticText(p_temp, pos=wx.Point(20, 10))
            p_temp.set_text_ctrl(txt)
            p_temp.run()
            self.ai_tab[pid] = p_temp
            self.nb.AddPage(p_temp, "ID: " + str(pid))

        sizer = wx.BoxSizer()
        sizer.Add(self.nb, 1, wx.EXPAND)
        self.main_panel.SetSizer(sizer)

    def halt(self):
        for key, panel in self.ai_tab.items():
            panel.halt = True

    def OnCloseWindow(self, event):
        self.halt()
        time.sleep(.75)  # make sure the thread had time to halt.
        self.Destroy()

    # @staticmethod
    # def raw_html():
    #     html = ('<p><font color="#4C4C4C", size=2>What do we want: '
    #             '<font color="#FF0000">all</font>'
    #             '</p>')
    #     return html


class AIControl(Thread):
    def __init__(self, ids_of_ai: List[int]):
        Thread.__init__(self)
        self.app: Optional[App] = None
        self.frame: Optional[ExternAIFrame] = None
        self.dump: Dict[int, str] = {}
        self.ids_of_ai = ids_of_ai

    def run(self):
        self.app = wx.App(False)
        self.app.SetAssertMode(wx.APP_ASSERT_SUPPRESS)
        self.frame = ExternAIFrame(None, self, self.ids_of_ai)
        self.frame.Show()
        self.app.MainLoop()

    def update(self, dump: str, pid: int):
        self.dump[pid] = dump

    def get_dump(self, pid: int):
        if pid in self.dump:
            return self.dump[pid]
        return "no data for pid " + str(pid)

    def close(self):
        self.frame.halt()
        time.sleep(.75)  # make sure the thread had time to halt.
        self.app.Destroy()
