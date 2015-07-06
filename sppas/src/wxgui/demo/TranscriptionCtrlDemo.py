# coding=UTF8
# Copyright (C) 2014  Brigitte Bigi
#
# This file is part of DataEditor.
#
# DataEditor is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# DataEditor is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with DataEditor.  If not, see <http://www.gnu.org/licenses/>.


# ---------------------------------------------------------------------------
import sys
import os.path
import random
import wx
import logging


# ----------------------------------------------------------------------------
import sys
import os.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
import annotationdata.io
from trsctrl import TranscriptionCtrl

# ---------------------------------------------------------------------------

class MyFrame(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title, wx.DefaultPosition, wx.Size(820, 550))
        self.SetBackgroundColour( wx.WHITE )

        t1 = annotationdata.io.read("/home/bigi/Grenelle-Phonetic.TextGrid")
        t2 = annotationdata.io.read("/home/bigi/Grenelle-Gestures.TextGrid")

        self.w1 = TranscriptionCtrl(self, id=-1, pos=wx.Point(10,50), size=wx.Size(800,250),trs=t1)
        self.w2 = TranscriptionCtrl(self, id=-1, pos=wx.Point(10,300), size=wx.Size(800,150),trs=t2)

        self.b1 = wx.Button(self, -1, "Colour", (10,0))
        self.b2 = wx.Button(self, -1, "Zoom/Scroll", (110, 0))

        self.Bind(wx.EVT_BUTTON, self.repaint1, self.b1)
        self.Bind(wx.EVT_BUTTON, self.repaint2, self.b2)
        self.Centre()

    def repaint1(self, event):
        (r,g,b) = random.sample(range(170,245),  3)
        #self.w1.SetTierBackgroundColour(wx.Colour(r,g,b))
        (a,b,c) = random.sample(range(5,160),  3)
        (q,r,s) = random.sample(range(5,160),  3)
        #self.w1.SetLabelColours(wx.Colour(r,g,b),wx.Colour(a,b,c),wx.Colour(q,r,s))
        (a,b,c) = random.sample(range(5,160),  3)
        #self.w1.SetPointColours(wx.Colour(r,g,b),wx.Colour(a,b,c))

    def repaint2(self, event):
        s = float(random.sample(range(0,600), 1)[0])
        d = float(random.sample(range(1,50), 1)[0])/10.
        logging.debug('New period: %f,%f'%(s,s+d))
        self.w1.SetTime(s,s+d)
        self.w2.SetTime(s,s+d)

        

class MyApp(wx.App):
    def OnInit(self):
        frame = MyFrame(None, -1, 'Test')
        frame.Show(True)
        return True


def setup_logging(log_level):
    """ 
    Setup default logger to log to stderr or and possible also to a file.
    
    The default logger is used like this:
        >>> import logging
        >>> logging.error(text message)
    """
    format= "%(asctime)s [%(levelname)s] %(message)s"
    # Setup logging to stderr
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(format))
    console_handler.setLevel(log_level)
    logging.getLogger().addHandler(console_handler)

    logging.getLogger().setLevel(log_level)
    logging.info("Logging set up with log level=%s", log_level)


if __name__ == '__main__':
    setup_logging(1)
    app = MyApp(0)
    app.MainLoop()

# ---------------------------------------------------------------------------