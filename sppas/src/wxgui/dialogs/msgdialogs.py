#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
# ---------------------------------------------------------------------------
#            ___   __    __    __    ___
#           /     |  \  |  \  |  \  /              Automatic
#           \__   |__/  |__/  |___| \__             Annotation
#              \  |     |     |   |    \             of
#           ___/  |     |     |   | ___/              Speech
#
#
#                           http://www.sppas.org/
#
# ---------------------------------------------------------------------------
#            Laboratoire Parole et Langage, Aix-en-Provence, France
#                   Copyright (C) 2011-2016  Brigitte Bigi
#
#                   This banner notice must not be removed
# ---------------------------------------------------------------------------
# Use of this software is governed by the GNU Public License, version 3.
#
# SPPAS is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SPPAS is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SPPAS. If not, see <http://www.gnu.org/licenses/>.
#
# ---------------------------------------------------------------------------
# File: msgdialogs.py
# ---------------------------------------------------------------------------
import sys
import os.path
sys.path.append(  os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) )

__docformat__ = """epytext"""
__authors__   = """Brigitte Bigi"""
__copyright__ = """Copyright (C) 2011-2016  Brigitte Bigi"""

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------

import wx
from basedialog import spBaseDialog

from wxgui.sp_icons import MESSAGE_ICON

from wxgui.sp_icons import DLG_INFO_ICON
from wxgui.sp_icons import DLG_WARN_ICON
from wxgui.sp_icons import DLG_ERR_ICON
from wxgui.sp_icons import DLG_QUEST_ICON

from wxgui.sp_consts import MAIN_FONTSIZE

# ----------------------------------------------------------------------------

class spBaseMessageDialog( spBaseDialog ):

    def __init__(self, parent, preferences, contentmsg, style=wx.ICON_INFORMATION):
        """
        Constructor.

        @param parent is the parent wx object.
        @param preferences (Preferences)
        @param filename (str) the file to display in this frame.
        @param style: ONE of wx.ICON_INFORMATION, wx.ICON_ERROR, wx.ICON_EXCLAMATION, wx.YES_NO

        """
        spBaseDialog.__init__(self, parent, preferences, title=" - Message")
        wx.GetApp().SetAppName( "question" )

        if style == wx.ICON_ERROR:
            titlebox = self.CreateTitle(DLG_ERR_ICON, "Error")
        elif style == wx.ICON_WARNING:
            titlebox = self.CreateTitle(DLG_WARN_ICON, "Warning")
        elif style == wx.YES_NO:
            titlebox = self.CreateTitle(DLG_QUEST_ICON, "Question")
        else:
            titlebox = self.CreateTitle(DLG_INFO_ICON, "Information")

        contentbox = self._create_content(contentmsg)
        buttonbox  = self._create_buttons()

        self.LayoutComponents( titlebox,
                               contentbox,
                               buttonbox )

    def _create_content(self,message):
        txt = self.CreateTextCtrl(message, style=wx.TE_READONLY|wx.TE_MULTILINE|wx.NO_BORDER)
        txt.SetMinSize((300,-1))
        return txt

    def _create_buttons(self):
        raise NotImplementedError

# ---------------------------------------------------------------------------

class YesNoQuestion( spBaseMessageDialog ):
    def __init__(self, parent, preferences, contentmsg):
        spBaseMessageDialog.__init__(self, parent, preferences, contentmsg, style=wx.YES_NO)

    def _create_buttons(self):
        yes = self.CreateYesButton()
        no  = self.CreateNoButton()
        no.Bind( wx.EVT_BUTTON, self._on_no, no )
        self.SetAffirmativeId( wx.ID_YES )
        return self.CreateButtonBox( [no],[yes] )

    def _on_no(self, evt):
        self.Destroy()
        self.SetReturnCode( wx.ID_NO )

# ---------------------------------------------------------------------------

class Information( spBaseMessageDialog ):
    def __init__(self, parent, preferences, contentmsg, style=wx.ICON_INFORMATION):
        spBaseMessageDialog.__init__(self, parent, preferences, contentmsg, style)

    def _create_buttons(self):
        okay = self.CreateOkayButton()
        self.SetAffirmativeId( wx.ID_OK )
        return self.CreateButtonBox( [],[okay] )

# ---------------------------------------------------------------------------

def ShowYesNoQuestion(parent, preferences, contentmsg):
    dlg = YesNoQuestion( parent, preferences, contentmsg)
    return dlg.ShowModal()

# ---------------------------------------------------------------------------

def ShowInformation(parent, preferences, contentmsg, style=wx.ICON_INFORMATION):
    dlg = Information( parent, preferences, contentmsg, style )
    return dlg.ShowModal()

# ---------------------------------------------------------------------------

def DemoBaseDialog(parent, preferences=None):
    """ A simple demonstration of SPPAS message dialogs."""
    def _on_yesno(evt):
        res = ShowYesNoQuestion( frame, preferences, "This is the message to show.")
        if res == wx.ID_YES:
            ShowInformation( frame, preferences, "You clicked the ""Yes"" button")
        elif res == wx.ID_NO:
            ShowInformation( frame, preferences, "You clicked the ""No"" button")
        else:
            print "there's a bug! return value is %s"%res
    def _on_info(evt):
        ShowInformation( frame, preferences, "This is an information message.", style=wx.ICON_INFORMATION)
    def _on_error(evt):
        ShowInformation( frame, preferences, "This is an error message.", style=wx.ICON_ERROR)
    def _on_warning(evt):
        ShowInformation( frame, preferences, "This is a warning message.", style=wx.ICON_WARNING)

    frame = spBaseDialog(parent, preferences)
    title = frame.CreateTitle(MESSAGE_ICON,"Message dialogs demonstration")
    btninfo   = frame.CreateButton(DLG_INFO_ICON,"Test info", "This is a tooltip!", btnid=wx.NewId())
    btnyesno  = frame.CreateButton(DLG_QUEST_ICON,"Test yes-no", "This is a tooltip!", btnid=wx.NewId())
    btnerror  = frame.CreateButton(DLG_ERR_ICON,"Test error", "This is a tooltip!", btnid=wx.NewId())
    btnwarn   = frame.CreateButton(DLG_WARN_ICON,"Test warning", "This is a tooltip!", btnid=wx.NewId())

    btnclose  = frame.CreateCloseButton()
    btnbox    = frame.CreateButtonBox( [btnyesno,btninfo,btnwarn,btnerror],[btnclose] )

    frame.LayoutComponents( title, wx.Panel(frame, -1, size=(320,200)), btnbox )

    btninfo.Bind( wx.EVT_BUTTON, _on_info )
    btnyesno.Bind( wx.EVT_BUTTON, _on_yesno )
    btnerror.Bind( wx.EVT_BUTTON, _on_error )
    btnwarn.Bind( wx.EVT_BUTTON, _on_warning )

    frame.ShowModal()
    frame.Destroy()

# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = wx.PySimpleApp()
    DemoBaseDialog(None)
    app.MainLoop()

# ---------------------------------------------------------------------------
