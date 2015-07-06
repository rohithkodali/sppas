#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
# ---------------------------------------------------------------------------
#            ___   __    __    __    ___
#           /     |  \  |  \  |  \  /        Automatic
#           \__   |__/  |__/  |___| \__      Annotation
#              \  |     |     |   |    \     of
#           ___/  |     |     |   | ___/     Speech
#           =============================
#
#           http://sldr.org/sldr000800/preview/
#
# ---------------------------------------------------------------------------
# developed at:
#
#       Laboratoire Parole et Langage
#
#       Copyright (C) 2011-2015  Brigitte Bigi
#
#       Use of this software is governed by the GPL, v3
#       This banner notice must not be removed
# ---------------------------------------------------------------------------
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
# ----------------------------------------------------------------------------
# File: singlefilter.py
# ----------------------------------------------------------------------------

__docformat__ = """epytext"""
__authors__   = """Brigitte Bigi"""
__copyright__ = """Copyright (C) 2011-2015  Brigitte Bigi"""


# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------

import os
import wx
import re
import operator
import logging

from annotationdata.filter.predicate import Rel

from wxgui.sp_icons import DATAFILTER_APP_ICON
from wxgui.sp_icons import FILTER_RELATION
from wxgui.sp_icons import APPLY_ICON
from wxgui.sp_icons import CANCEL_ICON

from wxgui.sp_consts import TB_ICONSIZE
from wxgui.sp_consts import TB_FONTSIZE

from wxgui.cutils.imageutils import spBitmap
from wxgui.cutils.ctrlutils import CreateGenButton
from wxgui.cutils.textutils import TextValidator

from wxgui.sp_consts import FRAME_STYLE
from wxgui.sp_consts import FRAME_TITLE

from wxgui.panels.relationstable import AllensRelationsTable

from sp_glob import ICONS_PATH

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------

DEFAULT_TIERNAME = "Filtered tier"


# ----------------------------------------------------------------------------
# class RelationFilterDialog
# ----------------------------------------------------------------------------

class RelationFilterDialog( wx.Dialog ):
    """
    @author:  Brigitte Bigi
    @contact: brigitte.bigi@gmail.com
    @license: GPL, v3
    @summary: This class is used to fix a set of filters for a tier.

    Dialog for the user to fix a set of filters to be applied to a tier, thanks
    to the predicate Rel.

    """

    def __init__(self, parent, prefsIO, tierX=[], tierY=[]):
        """
        Create a new dialog.

        """
        wx.Dialog.__init__(self, parent, title=FRAME_TITLE+" - RelationFilter", style=FRAME_STYLE)

        # Members
        self.preferences = prefsIO
        self.tierX = tierX
        self.tierY = tierY

        self._create_gui()

        # Events of this frame
        wx.EVT_CLOSE(self, self.onClose)

    # End __init__
    # ------------------------------------------------------------------------


    # ------------------------------------------------------------------------
    # Create the GUI
    # ------------------------------------------------------------------------


    def _create_gui(self):
        self._init_infos()
        self._create_title_label()
        self._create_content()
        self._create_cancel_button()
        self._create_apply_button()
        self._layout_components()
        self._set_focus_component()


    def _init_infos( self ):
        wx.GetApp().SetAppName( "relationfilter" )
        # icon
        _icon = wx.EmptyIcon()
        _icon.CopyFromBitmap( spBitmap(DATAFILTER_APP_ICON) )
        self.SetIcon(_icon)
        # colors
        self.SetBackgroundColour( self.preferences.GetValue('M_BG_COLOUR'))
        self.SetForegroundColour( self.preferences.GetValue('M_FG_COLOUR'))
        self.SetFont( self.preferences.GetValue('M_FONT'))


    def _create_title_label(self):
        self.title_layout = wx.BoxSizer(wx.HORIZONTAL)
        bmp = wx.BitmapButton(self, bitmap=spBitmap(FILTER_RELATION, 32, theme=self.preferences.GetValue('M_ICON_THEME')), style=wx.NO_BORDER)
        font = self.preferences.GetValue('M_FONT')
        font.SetWeight(wx.BOLD)
        font.SetPointSize(font.GetPointSize() + 2)
        self.title_label = wx.StaticText(self, label="Filter a tier X, depending on time-relations with a tier Y", style=wx.ALIGN_CENTER)
        self.title_label.SetFont( font )
        self.title_layout.Add(bmp,  flag=wx.TOP|wx.RIGHT|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, border=5)
        self.title_layout.Add(self.title_label, flag=wx.EXPAND|wx.ALL|wx.ALIGN_CENTER_VERTICAL, border=5)


    def _create_content(self):
        self.xy_layout       = self._create_xy_layout()
        self.filterpanel     = RelationFilterPanel(self, self.preferences)
        self.tiername_layout = self._create_tiername_layout()


    def _create_tiername_layout(self):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        title_tiername = wx.StaticText(self, label="Name of filtered tier: ", style=wx.ALIGN_CENTER)
        title_tiername.SetFont( self.preferences.GetValue('M_FONT') )
        self.text_outtiername = wx.TextCtrl(self, size=(250, -1), validator=TextValidator())
        self.text_outtiername.SetBackgroundColour(wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW))
        self.text_outtiername.SetForegroundColour(wx.Colour(128,128,128))
        self.text_outtiername.SetValue(DEFAULT_TIERNAME)
        self.text_outtiername.Bind(wx.EVT_TEXT, self.OnTextChanged)
        self.text_outtiername.Bind(wx.EVT_SET_FOCUS, self.OnTextClick)
        sizer.Add(title_tiername,  flag=wx.ALL|wx.wx.ALIGN_CENTER_VERTICAL, border=5)
        sizer.Add(self.text_outtiername, flag=wx.EXPAND|wx.ALL|wx.wx.ALIGN_CENTER_VERTICAL, border=5)
        return  sizer


    def _create_xy_layout(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        x = self._createX()
        y = self._createY()
        sizer.Add(x, proportion=1, flag=wx.EXPAND|wx.RIGHT|wx.LEFT, border=5)
        sizer.Add(y, proportion=1, flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)
        return sizer

    def _createX(self):
        textX = wx.StaticText(self, -1, label="Tier X: ")
        tiersX = wx.TextCtrl(self, -1, size=(250, 24), style=wx.TE_READONLY)
        tiersX.SetValue(", ".join(self.tierX))
        s = wx.BoxSizer(wx.HORIZONTAL)
        s.Add( textX,  0, wx.ALIGN_CENTER_VERTICAL|wx.BOTTOM, border=4)
        s.Add( tiersX, 1, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, border=0)
        return s

    def _createY(self):
        textY = wx.StaticText(self, -1, label="Tier Y: ")
        self.texttierY = wx.TextCtrl(self, size=(250, 24), validator=TextValidator())
        self.texttierY.SetBackgroundColour(wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW))
        self.texttierY.SetForegroundColour(wx.Colour(128,128,128))
        self.texttierY.SetValue('')
        self.texttierY.Bind(wx.EVT_TEXT, self.OnTextChanged)
        self.texttierY.Bind(wx.EVT_SET_FOCUS, self.OnTextClick)
        btn = wx.Button(self, 1, 'Fix name', (50, 24))
        s = wx.BoxSizer(wx.HORIZONTAL)
        s.Add( textY,      0, wx.ALIGN_CENTER_VERTICAL,   border=0)
        s.Add( self.texttierY, 1, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, border=0)
        s.Add( btn, 0, wx.ALIGN_CENTER_VERTICAL, border=0)
        btn.Bind(wx.EVT_BUTTON, self.OnChooseY)
        return s


    def _create_cancel_button(self):
        bmp = spBitmap(CANCEL_ICON, theme=self.preferences.GetValue('M_ICON_THEME'))
        color = self.preferences.GetValue('M_BG_COLOUR')
        self.btn_cancel = CreateGenButton(self, wx.ID_CLOSE, bmp, text=" Cancel ", tooltip="Close this frame", colour=color)
        self.btn_cancel.SetFont( self.preferences.GetValue('M_FONT'))
        self.SetEscapeId(wx.ID_CLOSE)


    def _create_apply_button(self):
        bmp = spBitmap(APPLY_ICON, theme=self.preferences.GetValue('M_ICON_THEME'))
        color = self.preferences.GetValue('M_BG_COLOUR')
        self.btn_apply = CreateGenButton(self, wx.ID_OK, bmp, text=" Apply ", tooltip="Apply all filters and close the frame", colour=color)
        self.btn_apply.SetFont( self.preferences.GetValue('M_FONT'))
        self.btn_apply.SetDefault()
        self.btn_apply.SetFocus()


    def _create_button_box(self):
        button_box = wx.BoxSizer(wx.HORIZONTAL)
        button_box.Add(self.btn_cancel,   flag=wx.LEFT,  border=5)
        button_box.AddStretchSpacer()
        button_box.Add(self.btn_apply, flag=wx.RIGHT, border=5)
        return button_box


    def _layout_components(self):
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self.title_layout,    0, flag=wx.ALL|wx.EXPAND, border=5)
        vbox.Add(self.xy_layout,       0, flag=wx.ALL|wx.EXPAND, border=5)
        vbox.Add(self.filterpanel,     1, flag=wx.ALL|wx.EXPAND, border=10)
        vbox.Add(self.tiername_layout, 0, flag=wx.ALL|wx.EXPAND, border=5)
        vbox.Add(self._create_button_box(), 0, flag=wx.ALL|wx.EXPAND, border=5)
        self.SetSizerAndFit(vbox)


    def _set_focus_component(self):
        self.filterpanel.SetFocus()


    #-------------------------------------------------------------------------
    # Callbacks
    #-------------------------------------------------------------------------

    def onClose(self, event):
        self.SetEscapeId( wx.ID_CANCEL )

    def OnChooseY(self, event):
        logging.debug("choices are: %s"%self.tierY)
        dlg = wx.SingleChoiceDialog( self,
                                   "Fix Y tier from this list:",
                                   "RelationFilter", self.tierY)

        if dlg.ShowModal() == wx.ID_OK:
            selection = dlg.GetSelection()
            self.texttierY.SetValue( self.tierY[selection] )

        dlg.Destroy()

    def OnTextClick(self, event):
        text = event.GetEventObject()
        text.SetForegroundColour( wx.BLACK )
        contenttext = text.GetValue().strip()
        if contenttext == "":
            self.OnTextErase(event)
        event.Skip()

    def OnTextChanged(self, event):
        text = event.GetEventObject()
        text.SetFocus()
        text.SetBackgroundColour(wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW))
        text.Refresh()

    def OnTextErase(self, event):
        text = event.GetEventObject()
        text.SetValue('')
        text.SetFocus()
        text.SetBackgroundColour( wx.Colour(245,220,240) )
        text.Refresh()

    #-------------------------------------------------------------------------


    #-------------------------------------------------------------------------
    # Getters...
    #-------------------------------------------------------------------------


    def GetPredicate(self):
        """
        Convert the content of the checklist in a list of Sel predicates and return it.
        """
        return self.filterpanel.GetPredicate()


    def GetFiltererdTierName(self):
        """
        Return the future name for the filtered tier.
        """
        return self.text_outtiername.GetValue().strip()


    def GetRelationTierName(self):
        """
        Return the future name for the filtered tier.
        """
        return self.texttierY.GetValue().strip()


# ----------------------------------------------------------------------------


class RelationFilterPanel(wx.Panel):
    """
    @author:  Brigitte Bigi
    @contact: brigitte.bigi@gmail.com
    @license: GPL
    @summary: Panel to fix filters to be used with Rel predicate.

    """

    def __init__(self, parent, prefsIO):
        wx.Panel.__init__(self, parent, size=(580, 320))

        # Members
        self.preferences = prefsIO
        self.data = []

        self._create_gui()


    def _create_gui(self):

        self.relTable = AllensRelationsTable(self)
        self.opt = wx.CheckBox(self, label='Replace annotation label of X by the relation name.')

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.relTable, proportion=1, flag=wx.EXPAND|wx.BOTTOM, border=5)
        sizer.Add(self.opt, flag=wx.EXPAND|wx.TOP, border=5)
        self.SetSizer(sizer)
        self.SetMinSize((380, 280))
        self.Center()


    # ----------------------------------------------------------------------
    # Public Methods
    # ----------------------------------------------------------------------

    def GetPredicate(self):
        """
        Return a predicate, constructed from the data.

        """
        d = self.relTable.GetData()
        d['replace'] = self.opt.GetValue()

        return _genPredicateRel( **d ).generate()

    # -----------------------------------------------------------------------


# --------------------------------------------------------------------------


class _genPredicateRel(object):
    """
    Generate a Rel predicate.
    """
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def generate(self):
        pred = None
        for function,value in zip(self.function, self.value):
            if value is None:
                p = Rel(function)
            else:
                p = Rel(**{function:value})
            if pred:
                pred = pred | p
            else:
                pred = p
        return pred

# --------------------------------------------------------------------------