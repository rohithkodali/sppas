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
# File: filemanager.py
# ----------------------------------------------------------------------------

__docformat__ = """epytext"""
__authors__   = """Brigitte Bigi"""
__copyright__ = """Copyright (C) 2011-2015  Brigitte Bigi"""


# -------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import wx
import wx.lib.scrolledpanel
import logging

# Make sure that we can import various objects
import os.path

from wxgui.structs.files  import xFiles
from wxgui.structs.prefs  import Preferences
from wxgui.structs.themes import BaseTheme
import wxgui.ui.CustomCheckBox as CCB


from wxgui.ui.CustomEvents import FileWanderEvent, spEVT_FILE_WANDER
from wxgui.ui.CustomEvents import spEVT_FILE_CHECK
from wxgui.ui.CustomEvents import spEVT_SETTINGS

#-----------------------------------------------------------------------------


class FileManager( wx.lib.scrolledpanel.ScrolledPanel ):
    """
    @authors: Brigitte Bigi
    @contact: brigitte.bigi@gmail.com
    @license: GPL, v3
    @summary: Store a list of filenames and related objects.

    Allows to check/uncheck/add/remove files in single or multiple modes.

    """

    def __init__(self, parent, ID=0, pos=wx.DefaultPosition, size=wx.DefaultSize, style=0, prefsIO=None):

        wx.lib.scrolledpanel.ScrolledPanel.__init__(self, parent, -1, style=wx.TAB_TRAVERSAL|wx.SIMPLE_BORDER)

        # members
        self._xfiles  = xFiles()
        self._prefsIO = self._check_prefs(prefsIO)
        try:
            self._ccbmultiple = self._prefsIO.GetValue('F_CCB_MULTIPLE')
        except Exception:
            self._ccbmultiple = False

        # create the sizer items:

        # ... a text to introduce the panel
        self._text = wx.StaticText(self, -1, "List of files:", size=(150,-1), style=wx.TE_READONLY|wx.NO_BORDER)
        font = self._prefsIO.GetValue('M_FONT')
        font.SetWeight(wx.BOLD)
        self._text.SetFont( font )
        self._text.SetBackgroundColour( self._prefsIO.GetValue('M_BG_COLOUR') )
        self._text.SetForegroundColour( self._prefsIO.GetValue('M_FG_COLOUR') )

        # ... the list of files
        self._ccbsizer = wx.BoxSizer( wx.VERTICAL )

        # create the main sizer
        sizer = wx.BoxSizer( wx.VERTICAL )
        sizer.Add(self._text, proportion=0, flag=wx.ALL, border=5 )
        sizer.Add(self._ccbsizer, proportion=1, flag=wx.ALL, border=5 )
        self.SetSizer( sizer )

        spEVT_FILE_CHECK(self,  self.OnCheck)
        spEVT_FILE_WANDER(self, self.OnWander)
        spEVT_SETTINGS(self,    self.OnSettings)

        self.SetBackgroundColour( self._prefsIO.GetValue('M_BG_COLOUR') )
        self.SetSize(wx.Size(180, 300))
        self.SetAutoLayout( True )
        self.Layout()
        self.SetupScrolling()

    # End __init__
    # ----------------------------------------------------------------------


    def _check_prefs(self, prefs):
        """
        Check if preferences are set properly. Set new ones if required.
        Return the new version.
        """
        if prefs is None:
            prefs = Preferences()
        else:
            try:
                bg = prefs.GetValue( 'M_BG_COLOUR' )
                fg = prefs.GetValue( 'M_FG_COLOUR' )
                font = prefs.GetValue( 'M_FONT' )
            except Exception:
                self._prefsIO.SetTheme( BaseTheme() )

        try:
            mult = prefs.GetValue('F_CCB_MULTIPLE')
        except Exception:
            prefs.SetValue( 'F_CCB_MULTIPLE',t='bool',v=True, text='Allow to check/uncheck multiple files in the file manager.')

        try:
            space = prefs.GetValue('F_SPACING')
        except Exception:
            prefs.SetValue( 'F_SPACING', t='int', v=2, text='Space before each item of the file manager.')

        return prefs

    # ----------------------------------------------------------------------


    # ----------------------------------------------------------------------
    # CCB Callbacks
    # ----------------------------------------------------------------------


    def OnCheckBox(self, event):
        """ Action when a check box is clicked. """

        # Grab the CustomCheckBox that generated the event
        control = event.GetEventObject()

        # Get the filename
        filename = None
        for i in range(self._xfiles.GetSize()):
            if self._xfiles.GetObject(i) == control:
                filename = self._xfiles.GetFilename(i)

        # Get the checked/unchecked value
        value = event.IsChecked()

        # Here, we use CustomCheckBox as a RadioBox...
        if value is True and self._ccbmultiple is False:
            # Uncheck the other ccb
            for i in range(self._xfiles.GetSize()):
                ccb = self._xfiles.GetObject(i)
                if ccb != control:
                    ccb.SetValue( False )

        # Send the information to the frame
        evt = FileWanderEvent( filename=filename, status=value )
        evt.SetEventObject(self)
        wx.PostEvent( self.GetTopLevelParent(), evt )

    # End OnCheckBox
    # ----------------------------------------------------------------------


    def SetBackgroundColour(self, colour):
        """ Change the background color of all CustomCheckBox objects. """

        # We set the new colour
        wx.lib.scrolledpanel.ScrolledPanel.SetBackgroundColour( self,colour )
        self.Refresh() # required for the bg color to be applied
        self._text.SetBackgroundColour( colour )

        # Apply as background on all CustomCheckBoxes
        for i in range(self._xfiles.GetSize()):
            ccb = self._xfiles.GetObject(i)
            ccb.SetBackgroundColour(colour)

    # End SetBackgroundColour
    # ----------------------------------------------------------------------


    def SetForegroundColour(self, colour):
        """ Change the foreground color of all CustomCheckBox objects. """

        # We set the new colour
        self._text.SetForegroundColour( colour )

        # Apply as foreground on all CustomCheckBoxes
        for i in range(self._xfiles.GetSize()):
            ccb = self._xfiles.GetObject(i)
            ccb.SetForegroundColour(colour)

    # End SetForegroundColour
    # ----------------------------------------------------------------------


    def SetFont(self, font):
        """ Change font of all text. """

        # Change to the text label
        self._text.SetFont( font )

        # Change to the list of file names
        if self._xfiles.GetSize() == 0:
            return
        for i in range(self._xfiles.GetSize()):
            ccb = self._xfiles.GetObject(i)
            ccb.SetFont(font)
            ccb.GetContainingSizer().Layout()

    # End ChangeFont
    # ----------------------------------------------------------------------


    # ----------------------------------------------------------------------
    # Callbacks to the custom events
    # ----------------------------------------------------------------------


    def OnWander(self, event):
        """
        We received an event to Append/Remove a file.

        """
        f = event.filename
        s = event.status

        if s is True:
            self.AddFile( f )
        else:
            if f is None:
                self.RemoveChecked(checked=False)
            else:
                self.RemoveFile(f)

    # End OnWander
    # ----------------------------------------------------------------------


    def OnCheck(self, event):
        """
        Check/Uncheck a filename.
        If no filename is given, just check/uncheck all files.
        """

        f = event.filename
        s = event.status

        # Add the file if not existing
        if f is not None and not self._xfiles.Exists(f):
            self.AddFile(f)

        # Check/Uncheck
        for i in reversed(range(self._xfiles.GetSize())):
            ccb = self._xfiles.GetObject(i)

            if f is not None and f == self._xfiles.GetFilename(i):
                ccb.SetValue( s )

            if f is None and self._ccbmultiple is True: # select all
                ccb.SetValue( s )

    # End OnCheck
    # ----------------------------------------------------------------------


    def OnSettings(self, event):
        """
        Set new preferences, then apply them.
        """

        self._prefsIO = event.prefsIO

        # Apply the changes on self
        self.SetFont( self._prefsIO.GetValue( 'M_FONT' ))
        self.SetBackgroundColour( self._prefsIO.GetValue( 'M_BG_COLOUR' ))
        self.SetForegroundColour( self._prefsIO.GetValue( 'M_FG_COLOUR' ))

        self.Layout()
        self.Refresh()

    # End OnSettings
    # ------------------------------------------------------------------------


    # ------------------------------------------------------------------------
    # File management
    # ------------------------------------------------------------------------

    def AddFile(self, f):
        """
        Add a new file in the list.

        @return a boolean (the file was added or not).

        """

        # Do not add an existing file
        if self._xfiles.Exists(f):
            return False

        try:
            # create a CustomCheckBox.
            ccb = CCB.CustomCheckBox(self, -1, os.path.basename(f), CCB_MULTIPLE=self._prefsIO.GetValue( 'F_CCB_MULTIPLE' ))
            ccb.SetFont( self._prefsIO.GetValue( 'M_FONT'))
            ccb.SetBackgroundColour( self._prefsIO.GetValue( 'M_BG_COLOUR' ))
            ccb.SetForegroundColour( self._prefsIO.GetValue( 'M_FG_COLOUR' ))
            ccb.SetSpacing( self._prefsIO.GetValue( 'F_SPACING' ))
            ccb.SetToolTipString(f)
            # put the ccb in a sizer (required to enable ccbsizer.Remove())
            s = wx.BoxSizer( wx.HORIZONTAL )
            s.Add(ccb, 1, wx.EXPAND)
            self._ccbsizer.Add(s, proportion=0, flag=wx.TOP, border=10 )
            # add in the list of files
            self._xfiles.Append(f,ccb)
        except Exception as e:
            logging.debug('FileManager. Error uploading: '+f+' '+str(e))
            return False

        self.Layout()
        self.Bind(wx.EVT_CHECKBOX, self.OnCheckBox, ccb)
        return True

    # End AddFile
    # ----------------------------------------------------------------------


    def RemoveFile(self, f):
        """ Remove the given file. """

        if self._xfiles.Exists(f) is True:
            i = self._xfiles.GetIndex(f)
            self._xfiles.GetObject(i).Destroy()
            self._ccbsizer.Remove(i)
            self._xfiles.Remove(i)
            self.Layout()

        # Send the information to the parent: a file was removed successfully
        evt = FileWanderEvent(filename=f, status=False)
        evt.SetEventObject(self)
        wx.PostEvent(self.GetTopLevelParent(), evt)

    # End RemoveFile
    # ----------------------------------------------------------------------


    def RemoveChecked(self, checked=False):
        """
        Remove all checked or all unchecked files.

        @param checked (Boolean)

        """

        for i in reversed(range(self._xfiles.GetSize())):

            ccb = self._xfiles.GetObject(i)
            if (ccb.GetValue() is True and checked is True) or (ccb.GetValue() is False and checked is False):
                self._xfiles.GetObject(i).Destroy()
                self._ccbsizer.Remove(i)
                self._xfiles.Remove(i)

        self.Layout()

    # End RemoveChecked
    # ----------------------------------------------------------------------


    def RemoveAll(self):
        """ Remove all files. """

        self._xfiles.RemoveAll()
        self._ccbsizer.DeleteWindows()
        self.Layout()

    # End RemoveAll
    # ----------------------------------------------------------------------

# --------------------------------------------------------------------------