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
# File: sppaseditclient.py
# ----------------------------------------------------------------------------

__docformat__ = """epytext"""
__authors__   = """Brigitte Bigi (brigitte.bigi@gmail.com)"""
__copyright__ = """Copyright (C) 2011-2015  Brigitte Bigi"""


# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------

import wx
import wx.media
import logging

from wxgui.sp_icons          import TIER_CHECK
from wxgui.sp_icons          import TIER_INFO
from wxgui.sp_icons          import TIER_SEARCH
from wxgui.sp_icons          import TIER_CHECK_DISABLED
from wxgui.sp_icons          import TIER_INFO_DISABLED
from wxgui.sp_icons          import TIER_SEARCH_DISABLED

from wxgui.sp_icons          import NAV_GO_START_ICON
from wxgui.sp_icons          import NAV_GO_PREVIOUS_ICON
from wxgui.sp_icons          import NAV_GO_NEXT_ICON
from wxgui.sp_icons          import NAV_GO_END_ICON
from wxgui.sp_icons          import NAV_FIT_SELECTION_ICON
from wxgui.sp_icons          import NAV_PERIOD_ZOOM_ICON
from wxgui.sp_icons          import NAV_PERIOD_ZOOM_IN_ICON
from wxgui.sp_icons          import NAV_PERIOD_ZOOM_OUT_ICON
from wxgui.sp_icons          import NAV_VIEW_ZOOM_IN_ICON
from wxgui.sp_icons          import NAV_VIEW_ZOOM_OUT_ICON

from wxgui.sp_consts         import TB_ICONSIZE

from baseclient              import BaseClient
from wxgui.structs.files     import xFiles

from wxgui.ui.CustomEvents   import FileWanderEvent,spEVT_FILE_WANDER
from wxgui.ui.CustomEvents   import spEVT_SETTINGS
from wxgui.ui.CustomEvents   import spEVT_OBJECT_SELECTED

from wxgui.ui.displayctrl    import DisplayCtrl
from wxgui.ui.trsctrl        import TranscriptionCtrl
from wxgui.ui.wavectrl       import WaveCtrl

from wxgui.dialogs.trsinfodialog import TrsInfoDialog
from wxgui.dialogs.sndinfodialog import SndInfoDialog
from wxgui.dialogs.commondialogs import ZoomChooser
from wxgui.views.search          import Search, spEVT_SEARCHED
from wxgui.panels.sndplayer      import SndPlayer
from wxgui.structs.themes        import BaseTheme

from wxgui.cutils.ctrlutils  import CreateButton
from wxgui.cutils.imageutils import spBitmap


# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------

ZOOM_IN_ID  = wx.NewId()
ZOOM_OUT_ID = wx.NewId()

# ----------------------------------------------------------------------------


# ----------------------------------------------------------------------------
# Main class that manage the notebook
# ----------------------------------------------------------------------------

class SppasEditClient( BaseClient ):
    """
    @author:  Brigitte Bigi
    @contact: brigitte.bigi@gmail.com
    @license: GPL, v3
    @summary: This class is used to display the opened files.

    This class manages the pages of a notebook with all opened files.

    Each page (except if empty...) contains an instance of a SppasEdit.

    """

    def __init__( self, parent, prefsIO ):
        BaseClient.__init__( self, parent, prefsIO )
        self._update_members()

    # End __init__
    # ------------------------------------------------------------------------


    def _update_members(self):
        """
        Update members.
        """
        self._multiplefiles = True
        # Quick and dirty solution to communicate with the file manager:
        self._prefsIO.SetValue( 'F_CCB_MULTIPLE', t='bool', v=True, text='')

    # End _update_members
    # ------------------------------------------------------------------------


    def CreateComponent(self, parent, prefsIO ):
        return SppasEdit(parent, prefsIO)

    # ------------------------------------------------------------------------


# ----------------------------------------------------------------------------
# The Component is the content of one page of the notebook.
# ----------------------------------------------------------------------------


class SppasEdit( wx.Panel ):
    """
    @author:  Brigitte Bigi
    @contact: brigitte.bigi@gmail.com
    @license: GPL, v3
    @summary: This class is used to display all opened files.

    """

    def __init__(self, parent, prefsIO):
        """
        Constructor.
        """
        wx.Panel.__init__(self, parent, -1, style=wx.NO_BORDER)
        sizer = wx.BoxSizer( wx.VERTICAL )

        # members
        self._prefsIO = self._check_prefs(prefsIO)
        self._xfiles  = xFiles()

        # the display panel
        dp = self._set_display()
        # the navigation bar: a set of panels: self._trans, self._media, self._navig
        sp = self._set_navigation()

        # put the panels in a sizer
        sizer.Add(dp, 1, wx.TOP|wx.EXPAND, border=0)
        sizer.Add(sp, 0, wx.BOTTOM|wx.EXPAND, border=0)

        # events

        self.Bind(wx.EVT_SIZE,      self.OnSize)
        self.GetTopLevelParent().Bind(wx.EVT_CHAR_HOOK, self.OnKeyPress)

        self.Bind(spEVT_FILE_WANDER,     self.OnFileWander)
        self.Bind(spEVT_SETTINGS,        self.OnSettings)
        self.Bind(spEVT_OBJECT_SELECTED, self.OnObjectSelected)

        self.SetBackgroundColour( self._prefsIO.GetValue('M_BG_COLOUR') )

        self.SetSizer(sizer)
        self.SetAutoLayout( True )
        self.Layout()

    # End __init__
    # ------------------------------------------------------------------------


    # ------------------------------------------------------------------------
    # GUI construction
    # ------------------------------------------------------------------------

    def _set_display(self):
        """ Set the display panel. """

        self._displayctrl = DisplayCtrl(self, id=-1, pos=(10,80), size=wx.Size(400,160), prefsIO=self._prefsIO)
        return self._displayctrl


    def _set_navigation(self):
        """ Set all panels: transcription, media and navigate. """

        sp = wx.BoxSizer( wx.HORIZONTAL )

        self._trans = TrsPanel( self, self._prefsIO )
        self._media = MediaPanel( self, self._prefsIO )
        self._navig = NavigatePanel( self, self._prefsIO )

        sp.Add(self._trans, 0, wx.LEFT|wx.TOP|wx.BOTTOM|wx.EXPAND, border=2)
        sp.AddStretchSpacer(1)

        sp.Add(self._media, 0, wx.EXPAND, border=2)
        sp.AddStretchSpacer(1)

        sp.Add(self._navig, 0, wx.RIGHT|wx.TOP|wx.BOTTOM|wx.EXPAND, border=2)

        self._trans.SetDisplay( self._displayctrl )
        self._media.SetDisplay( self._displayctrl )
        self._navig.SetDisplay( self._displayctrl )

        return sp

    # End _set_navigation
    # ------------------------------------------------------------------------


    def _check_prefs(self, prefs):
        """
        Check if preferences are set properly. Set new ones if required.
        Return the new version.
        """
        if prefs is None:
            prefs = Preferences( BaseTheme() )
        else:
            try:
                bg = prefs.GetValue( 'M_BG_COLOUR' )
                fg = prefs.GetValue( 'M_FG_COLOUR' )
                font = prefs.GetValue( 'M_FONT' )
                icons = prefs.GetValue( 'M_ICON_THEME' )
            except Exception:
                self._prefsIO.SetTheme( BaseTheme() )
        return prefs

    #-----------------------------------------------------------------------


    # ------------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------------


    def OnSettings(self, event):
        """
        Set new preferences, then apply them.
        """

        self._prefsIO = event.prefsIO

        # Apply the changes on self
        wx.Window.SetBackgroundColour( self,self._prefsIO.GetValue( 'M_BG_COLOUR' ) )
        wx.Window.SetForegroundColour( self,self._prefsIO.GetValue( 'M_FG_COLOUR' ) )
        wx.Window.SetFont( self,self._prefsIO.GetValue( 'M_FONT' ) )

        # Apply on panels of self
        self._trans.SetBackgroundColour( self._prefsIO.GetValue( 'M_BG_COLOUR' ) )
        self._media.SetBackgroundColour( self._prefsIO.GetValue( 'M_BG_COLOUR' ) )
        self._navig.SetBackgroundColour( self._prefsIO.GetValue( 'M_BG_COLOUR' ) )

        self._displayctrl.SetPreferences( self._prefsIO )

    # End OnSettings
    # ------------------------------------------------------------------------


    #-------------------------------------------------------------------------
    # Callbacks to keyboard events
    #-------------------------------------------------------------------------


    def OnKeyPress(self, event):
        """
        Respond to a keypress event.
        """
        keycode = event.GetKeyCode()
        logging.debug('SppasEdit-Client panel. Key code = %d'%keycode)

        # Zoom In: Ctrl+I
        # Zoom Out: Ctrl+O
        if keycode == ord('I') and event.ControlDown():
            self._navig.onViewZoomIn(event)
        elif keycode == ord('O') and event.ControlDown():
            self._navig.onViewZoomOut(event)

        # OTHER keys require that an object is selected: media or transcription

        selected = self._displayctrl.GetSelectedObject()
        if selected is None:
            event.Skip()
            return

        # Transcription
        # CTRL+F -> Search
        if keycode == ord('F') and event.ControlDown():
            self._trans.onSearch( event )
        elif keycode == ord('G') and event.ControlDown():
            self._trans.onSearch( event )

        # Media player
        # TAB -> PLay
        # Shift+TAB -> Forward
        # Ctrl+TAB -> Rewind
        # F1 -> Pause
        # ESC -> Stop
        elif keycode == wx.WXK_TAB and event.ShiftDown():
            self._media.onNext( event )
        elif keycode == wx.WXK_TAB and event.ControlDown():
            self._media.onRewind( event )
        elif keycode == wx.WXK_TAB:
            self._media.onPlay( event )
        elif keycode == wx.WXK_F1:
            self._media.onPause( event )
        elif keycode == wx.WXK_ESCAPE:
            self._media.onStop( event )

        event.Skip()

    # ------------------------------------------------------------------------


    # ------------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------------


    def OnFileWander(self, event):
        """
        Add/Remove data.
        """
        f = event.filename
        s = event.status

        if s is True:
            try:
                self._displayctrl.SetData( event.filename )
            except Exception as e:
                #import traceback
                #print(traceback.format_exc())
                logging.info(' ** WARNING **: Got exception %s '%(str(e)))
                pass
        else:
            self._displayctrl.UnsetData(f)
            self._media.SetMedia()   # if the file was a sound...
            self._trans.SetTrs()     # if the file was a trs...
            self.Refresh()
            evt = FileWanderEvent(filename=f, status=False)
            evt.SetEventObject(self)
            wx.PostEvent( self.GetParent().GetParent().GetParent(), evt )

    # End OnFileWander
    # ------------------------------------------------------------------------


    def OnObjectSelected(self, event):
        """
        Update panels when the selected object has changed.
        """
        selobj = event.object
        fname  = event.string

        # panels that must be adapted (Set or Unset).
        # (they will get the object with their own displayctrl access)
        self._media.SetMedia()
        self._trans.SetTrs()

        if len(fname)==0:
            self.GetTopLevelParent().StartTimeInStatusBar()
        else:
            self.GetTopLevelParent().StopTimeInStatusBar()
            self.GetTopLevelParent().DisplayTextInStatusbar(fname)

    # End OnObjectSelected
    # ------------------------------------------------------------------------


    def OnSize(self, event):
        """
        Called by the parent when the frame is resized
        and lays out the client window.
        """

        self.Layout()
        self.Refresh()

    # End OnSize
    # ------------------------------------------------------------------------


    # ------------------------------------------------------------------------

    def GetNavigPanel(self):
        return self._navig

    def GetTransPanel(self):
        return self._trans

    def GetMediaPanel(self):
        return self._media

    # ------------------------------------------------------------------------


# ----------------------------------------------------------------------------




class NavigatePanel( wx.Panel ):
    """
    @author:  Brigitte Bigi
    @contact: brigitte.bigi@gmail.com
    @license: GPL
    @summary: This class is used to display a time-navigation panel.

    It is used to change the displayed time period.

    """

    def __init__(self, parent, prefsIO):
        """
        Constructor.
        """
        wx.Panel.__init__(self, parent, style=wx.NO_BORDER)
        gbs = wx.GridBagSizer(hgap=5, vgap=5)

        # members
        self._prefsIO = prefsIO
        self._buttons = {}
        self._display = None
        self._scrollcoef = 75.0 # Time scroll (percentage)
        self._zoomcoef   = 50.0 # Time zoom (percentage)

        # create the buttons
        theme = self._prefsIO.GetValue('M_ICON_THEME')
        bgcolour = self._prefsIO.GetValue('M_BG_COLOUR')

        self._buttons['gostart'] = CreateButton( self, spBitmap(NAV_GO_START_ICON,TB_ICONSIZE,theme),    self.onGoStart, gbs, colour=bgcolour)
        self._buttons['goback']  = CreateButton( self, spBitmap(NAV_GO_PREVIOUS_ICON,TB_ICONSIZE,theme), self.onGoBack,  gbs, colour=bgcolour)
        self._buttons['gonext']  = CreateButton( self, spBitmap(NAV_GO_NEXT_ICON,TB_ICONSIZE,theme),     self.onGoNext,  gbs, colour=bgcolour)
        self._buttons['goend']   = CreateButton( self, spBitmap(NAV_GO_END_ICON,TB_ICONSIZE,theme),      self.onGoEnd,   gbs, colour=bgcolour)
        self._buttons['fitsel']  = CreateButton( self, spBitmap(NAV_FIT_SELECTION_ICON,TB_ICONSIZE,theme), self.onFitSelection, gbs, colour=bgcolour)

        self._buttons['hzoom']    = CreateButton( self, spBitmap(NAV_PERIOD_ZOOM_ICON,TB_ICONSIZE,theme),    self.onPeriodZoom, gbs, colour=bgcolour)
        self._buttons['hzoomin']  = CreateButton( self, spBitmap(NAV_PERIOD_ZOOM_IN_ICON,TB_ICONSIZE,theme), self.onPeriodZoomIn, gbs, colour=bgcolour)
        self._buttons['hzoomout'] = CreateButton( self, spBitmap(NAV_PERIOD_ZOOM_OUT_ICON,TB_ICONSIZE,theme),self.onPeriodZoomOut,gbs, colour=bgcolour)
        self._buttons['vzoomin']  = CreateButton( self, spBitmap(NAV_VIEW_ZOOM_IN_ICON,TB_ICONSIZE,theme),   self.onViewZoomIn,   gbs, colour=bgcolour)
        self._buttons['vzoomout'] = CreateButton( self, spBitmap(NAV_VIEW_ZOOM_OUT_ICON,TB_ICONSIZE,theme),  self.onViewZoomOut,  gbs, colour=bgcolour)

        # button placement in the sizer
        gbs.Add(self._buttons['gostart'],(0,0), flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border=1)
        gbs.Add(self._buttons['goback'], (0,1), flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border=1)
        gbs.Add(self._buttons['gonext'], (0,2), flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border=1)
        gbs.Add(self._buttons['goend'],  (0,3), flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border=1)
        gbs.Add(self._buttons['fitsel'], (0,4), flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border=1)

        gbs.Add(self._buttons['hzoom'],   (0,5), flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border=1)
        gbs.Add(self._buttons['hzoomin'], (0,6), flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border=1)
        gbs.Add(self._buttons['hzoomout'],(0,7), flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border=1)

        gbs.Add(self._buttons['vzoomin'], (0,8), flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border=1)
        gbs.Add(self._buttons['vzoomout'],(0,9), flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border=1)

        self.SetBackgroundColour( self.GetParent().GetBackgroundColour() )

        self.SetSizer( gbs )
        self.SetAutoLayout( True )
        self.Layout()

    # End __init__
    #-------------------------------------------------------------------------



    #-------------------------------------------------------------------------
    # Callbacks for Scrolling...
    #-------------------------------------------------------------------------


    def onGoStart(self, event):
        """
        Go at the beginning (change time period).
        """
        self.SetNewPeriod( 1.0, "start" )

    # End onGoStart
    #-------------------------------------------------------------------------


    def onGoBack(self, event):
        """
        Go backward (change time period).
        """
        self.SetNewPeriod( 1.0 - self._scrollcoef/100.0, "scroll" )

    # End onGoBack
    #-------------------------------------------------------------------------


    def onGoNext(self, event):
        """
        Go forward (change time period).
        """
        self.SetNewPeriod( 1.0 + self._scrollcoef/100.0, "scroll" )

    # End onGoNext
    #-------------------------------------------------------------------------


    def onGoEnd(self, event):
        """
        Go at the end of the drawing (change time period).
        """
        self.SetNewPeriod( 1.0, "end" )

    # End onGoEnd
    #-------------------------------------------------------------------------


    #-------------------------------------------------------------------------
    # Callbacks for Zooming...
    #-------------------------------------------------------------------------


    def onPeriodZoom(self, event):
        """
        Open a display dialog to get zoom values.
        """
        if self._display is None: return

        dlg = ZoomChooser( self, self._display.GetPeriod().GetStart(), self._display.GetPeriod().GetEnd() )
        if dlg.ShowModal() == wx.ID_OK:
            (s,e) = dlg.GetValues()
            try:
                s = float(s)
                e = float(e)
            except Exception:
                logging.info('Zoom cancelled (can not be applied: from %f to %f).'%(s,e))
                return
            (s,e) = self._display.GetPeriod().Check(float(s), float(e))
            self._changedrawingperiod( s,e )

        dlg.Destroy()

    # End onPeriodZoom
    #-------------------------------------------------------------------------


    def onPeriodZoomIn(self, event):
        """
        Reduce the displayed time period of the drawing.
        """
        self.SetNewPeriod( 1.0 - self._zoomcoef/100.0, "zoom" )

    # End onPeriodZoomIn
    #-------------------------------------------------------------------------


    def onPeriodZoomOut(self, event):
        """
        Enlarge the displayed time period of the drawing.
        """
        self.SetNewPeriod( 1.0 + self._zoomcoef/100.0, "zoom" )

    # End onPeriodZoomOut
    #-------------------------------------------------------------------------


    def onViewZoomIn(self, event):
        """
        Reduce the height of the drawing.
        """
        if self._display is None: return
        self._display.ZoomUp()

    # End onViewZoomIn
    #-------------------------------------------------------------------------


    def onViewZoomOut(self, event):
        """
        Enlarge the height of the drawing.
        """
        if self._display is None: return
        self._display.ZoomDown()

    # End onViewZoomOut
    #-------------------------------------------------------------------------


    def onFitSelection(self, event):
        """
        Fit the period on the selection (selection is indicated by the ruler).
        """
        if self._display is None: return

        ruler = self._display.GetRuler()
        start,end = ruler.GetSelectionIndicatorValues()

        # don't do anything if the period did not changed!
        period = self._display.GetPeriod()
        if start == period.GetStart() and end == period.GetEnd():
            return

        # Check period before changing, then change!
        checkstart,checkend = period.Check(start,end)

        self._changedrawingperiod(checkstart, checkend)
        ruler.SetSelectionIndicatorValues(start, end)

        self._display.Refresh()

    # End onFitSelection
    #-------------------------------------------------------------------------


    def OnCenterSelection(self, event):
        """
        Fit the period to place the selection at the middle of the screen
        (selection is indicated by the ruler).
        The delta value of the period is not changed.
        """
        if self._display is None:
            return

        ruler  = self._display.GetRuler()
        period = self._display.GetPeriod()

        selstart,selend = ruler.GetSelectionIndicatorValues()
        start,end = period.GetStart(),period.GetEnd()
        delta = period.Delta()

        middle    = round(start + (end-start)/2.,           2)
        selmiddle = round(selstart + (selend-selstart)/2.,  2)
        if middle != selmiddle:
            start = selmiddle - delta/2.
            end   = selmiddle + delta/2.
            start,end = period.Check(start,end)
            self._changedrawingperiod(start, end)
            self._display.Refresh()

    # End onCenterSelection
    #-------------------------------------------------------------------------


    # ------------------------------------------------------------------------
    # GUI...
    # ------------------------------------------------------------------------


    def SetBackgroundColour(self, colour):
        """
        Set the background color of this panel.
        """

        wx.Window.SetBackgroundColour( self,colour )
        for b in self._buttons:
            self._buttons[b].SetBackgroundColour( colour )
        self.Refresh()

    # End SetBackgroundColour
    # ------------------------------------------------------------------------


    #-------------------------------------------------------------------------
    # Getters and Setters
    #-------------------------------------------------------------------------


    def SetNewPeriod(self, coeff, mode):
        """ Update the drawing period. """

        if self._display is None: return

        period = self._display.GetPeriod()
        if mode == "zoom":
            start,end = period.Zoom( coeff )
        elif mode == "scroll":
            start,end = period.Scroll( coeff )
        elif mode == "start":
            start,end = period.ScrollToStart( )
        elif mode == "end":
            start,end = period.ScrollToEnd( )

        self._changedrawingperiod(start,end)

    # End SetNewPeriod
    #-------------------------------------------------------------------------


    def SetDisplay(self, drawing):
        """
        Set a new drawing.
        """
        self._display = drawing

    # End SetDisplay
    #------------------------------------------------------------------------


    #-------------------------------------------------------------------------
    # Private
    #-------------------------------------------------------------------------


    def _changedrawingperiod(self, start, end):
        period = self._display.GetPeriod()
        if start != period.GetStart() or end != period.GetEnd():
            period.Update(start,end)
            self._display.SetPeriod( period )

    # End _changedrawingperiod
    #-------------------------------------------------------------------------



#-----------------------------------------------------------------------------



class TrsPanel( wx.Panel ):
    """
    @author:  Brigitte Bigi
    @contact: brigitte.bigi@gmail.com
    @license: GPL, v3
    @summary: This class is used to display a transcription panel.

    This panel is used to manage transcription files.

    """

    def __init__(self, parent, prefsIO):
        """ Create a new instance. """

        wx.Panel.__init__(self, parent, style=wx.NO_BORDER)
        sizer = wx.BoxSizer( wx.HORIZONTAL )

        # members
        self._prefsIO  = prefsIO
        self._display  = None
        self._trsctrl  = None
        self._buttons  = {}
        self._search    = None

        # create the buttons bar
        theme = self._prefsIO.GetValue('M_ICON_THEME')
        bgcolour = self._prefsIO.GetValue('M_BG_COLOUR')
        self._buttons['tiercheck'] = CreateButton( self, spBitmap(TIER_CHECK_DISABLED,TB_ICONSIZE,theme),  self.onTierCheck,sizer, colour=bgcolour)
        self._buttons['tierinfo']  = CreateButton( self, spBitmap(TIER_INFO_DISABLED,TB_ICONSIZE,theme),   self.onTierInfo, sizer, colour=bgcolour)
        self._buttons['search']    = CreateButton( self, spBitmap(TIER_SEARCH_DISABLED,TB_ICONSIZE,theme), self.onSearch,   sizer, colour=bgcolour)

        # sizer
        sizer.Add(self._buttons['tiercheck'], 1, flag=wx.ALL, border=2)
        sizer.Add(self._buttons['tierinfo'],  1, flag=wx.ALL, border=2)
        sizer.Add(self._buttons['search'],    1, flag=wx.ALL, border=2)

        self.Bind(spEVT_SEARCHED, self.onSearched)
        self.SetBackgroundColour( self.GetParent().GetBackgroundColour() )

        self.SetSizer( sizer )
        self.SetAutoLayout( True )
        self.Layout()

    # End __init__
    #-------------------------------------------------------------------------


    #-------------------------------------------------------------------------
    # Callbacks
    #-------------------------------------------------------------------------


    def onTierCheck(self, event):
        """ Fix the list of tiers to Show/Hide. """

        if self._trsctrl is None: return

        # Get the list of tiers' names
        lst = self._trsctrl.GetTierNames()
        if len(lst) == 0: return # hum... just to be sure

        dlg = wx.MultiChoiceDialog( self,
                                   "Check the tiers to show:",
                                   "Tiers to show/hide", lst)
        dlg.SetSelections( self._trsctrl.GetTierIdxChecked() )

        if dlg.ShowModal() == wx.ID_OK:
            # get the list of tiers' names that are checked
            selections = dlg.GetSelections()
            checked = [lst[x] for x in selections]

            if len(checked) == 0:
                wx.MessageBox("At least one tier must be checked!", "ERROR", wx.ICON_ERROR | wx.OK)
            else:
                # send the list to the trsctrl instance, then redraw
                self._trsctrl.SetTierChecked( checked )

        dlg.Destroy()

    # End onTierCheck
    #-------------------------------------------------------------------------


    def onTierInfo(self, event):
        """ Show details about the selected transcription file. """

        if self._trsctrl is None: return

        fname = self._display.GetSelectionFilename()
        dlg = TrsInfoDialog( self, self._prefsIO, fname,  self._trsctrl.GetTranscription() )

    # End onTierInfo
    #-------------------------------------------------------------------------


    def onSearch(self, event):
        """ Open a frame to search patterns into a tier. """

        if self._trsctrl is None: return

        try:
            self._search.SetFocus()
        except Exception:
            self._search = None

        focus = True
        if self._search is not None:
            # If CTRL+G then find next occurrence
            # else just set the focus to the _search frame.
            obj = event.GetEventObject()
            try:
                keycode = event.GetKeyCode()
                if keycode==71 and event.ControlDown():
                    self._search.OnFind(event)
                    focus = False
            except Exception:
                pass
        else:
            self._search = Search(self, self._prefsIO, self._trsctrl.GetTranscription())

        if focus is True:
            self._search.SetFocus()
            self._search.Raise()

    # End onSearch
    #-------------------------------------------------------------------------


    def onSearched(self, event):
        """
        Something was found by the Search frame.
        """
        s = event.start
        e = event.end
        logging.debug('onSearched. Found from %f to %f'%(s,e))

        self._display.GetRuler().SetSelectionIndicatorValues(s,e)
        self.GetParent().GetNavigPanel().OnCenterSelection(None)

    #-------------------------------------------------------------------------


    # ------------------------------------------------------------------------
    # Functions...
    # ------------------------------------------------------------------------


    def SetBackgroundColour(self, colour):
        """ Change the background of the panel. """

        wx.Window.SetBackgroundColour( self, colour )
        for b in self._buttons:
            self._buttons[b].SetBackgroundColour( colour )
        self.Refresh()

    # End SetBackgroundColour
    # ------------------------------------------------------------------------


    #-------------------------------------------------------------------------
    # Data management
    #-------------------------------------------------------------------------


    def SetDisplay(self, drawing):
        """
        Set a new displayctrl, then a new trsctrl (if any).
        """

        self._display = drawing
        if self._display is None:
            self.ActivateButtons(False)
            self.EnableButtons(True)
            self._trsctrl = None
        else:
            self.SetTrs()

    #-------------------------------------------------------------------------


    def SetTrs(self):
        """ Set a new transcription. """

        self._trsctrl = None
        if self._display is None: return

        self.ActivateButtons(False)
        dcobj = self._display.GetSelectedObject()
        if dcobj is None:
            return
        if not isinstance(dcobj,TranscriptionCtrl):
            return

        self._trsctrl = dcobj
        self.ActivateButtons(True)
        if self._search is not None:
            try:
                self._search.SetTranscription(self._trsctrl.GetTranscription())
            except Exception:
                pass

        self.Refresh()

    # End SetTrs
    #-------------------------------------------------------------------------


    def UnsetData(self):
        """ Unset the current drawing. """

        if self._display is None:
            return

        self._display = None
        self._trsctrl = None

        self.ActivateButtons(False)
        self.EnableButtons(True)

        for k in self._buttons:
            self._buttons[k].Enable( False )

        self.Refresh()

    # End UnsetData
    #-------------------------------------------------------------------------


    #-------------------------------------------------------------------------
    # Private...
    #-------------------------------------------------------------------------


    def ActivateButtons(self, value=True):
        self.EnableButtons(False)
        if value is True:
            self._buttons['tiercheck'].SetBitmapLabel( spBitmap( TIER_CHECK ) )
            self._buttons['tierinfo'].SetBitmapLabel( spBitmap( TIER_INFO ) )
            self._buttons['search'].SetBitmapLabel( spBitmap( TIER_SEARCH ) )
        else:
            self._buttons['tiercheck'].SetBitmapLabel(  spBitmap( TIER_CHECK_DISABLED ) )
            self._buttons['tierinfo'].SetBitmapLabel(  spBitmap( TIER_INFO_DISABLED ) )
            self._buttons['search'].SetBitmapLabel(  spBitmap( TIER_SEARCH_DISABLED ) )

    #-------------------------------------------------------------------------


    def EnableButtons(self, value=True):
        for b in self._buttons:
            self._buttons[b].Enable( not value )

    #-------------------------------------------------------------------------



#-----------------------------------------------------------------------------



class MediaPanel( SndPlayer ):
    """
    @author:  Brigitte Bigi
    @contact: brigitte.bigi@gmail.com
    @license: GPL, v3
    @summary: This class is used to display an audio player panel.

    Display an audio player panel, used to play media files.

    """

    def __init__(self, parent, prefsIO):
        """
        Constructor.
        """
        self._prefsIO = prefsIO

        SndPlayer.__init__(self, parent, orient=wx.HORIZONTAL, refreshtimer=5, prefsIO=self._prefsIO)
        self.ActivateButtons(False)

        # members
        self._display = None
        self.SetBackgroundColour( self.GetParent().GetBackgroundColour() )

    # End __init__
    #-------------------------------------------------------------------------


    #-------------------------------------------------------------------------
    # Callbacks
    #-------------------------------------------------------------------------


    def onNext(self, event):
        """ Go forward in the music. """

        SndPlayer.onNext(self,event)
        self.UpdateRuler()

    # End onNext
    #-------------------------------------------------------------------------


    def onRewind(self, event):
        """ Go backward in the music. """

        SndPlayer.onRewind(self,event)
        self.UpdateRuler()

    # End onRewind
    #-------------------------------------------------------------------------


    def onPause(self, event):
        """ Pauses the music. """

        SndPlayer.onPause(self,event)
        self.UpdateRuler()

    # End onPause
    #-------------------------------------------------------------------------


    def onPlay(self, event):
        """ Plays the music. """

        if self._mediaplayer is None and self._display is None:
            return
        if self._mediaplayer is None and self._display is not None:
            self.SetMedia() # now, a selection?
        if self._dcobj != self._display.GetSelectedObject():
            self.SetMedia() # selection has changed since last play...
        if self._mediaplayer is None:
            logging.debug('onPlay error. unable to play: finally ... no media. ')
            return

        if self._mediaplayer.GetState() == wx.media.MEDIASTATE_PLAYING:
            return

        # the period on screen
        start,end = self._display.GetPeriodValues()
        self.SetOffsetPeriod( int(start*1000.), int(end*1000.) )

        # Use the indicator as a slider, then get the value to seek
        v = self._display.GetRuler().GetPlayerIndicatorValue()
        if v is not None:
            offset = int(v*1000.0)
            # was required in previous wx versions (wnds bug)
            #if offset == 0: offset = 1
        else:
            offset = int(start*1000.)
        if offset == -1:
            offset = int(start*1000.)

        self._mediaplayer.Seek( offset, mode=wx.FromStart )

        #
        SndPlayer.onPlay(self,event)

    # End onPlay
    #-------------------------------------------------------------------------


    def onStop(self, event):
        """ Stops the music and resets the play button. """

        if self._mediaplayer is None:  return

        if self._display:
            self._offsets = self._display.GetPeriodValues()
        else:
            self._offsets = (0,0)

        SndPlayer.onStop(self,event)
        self.UpdateRuler()

    # End onStop
    #-------------------------------------------------------------------------


    def onTimer(self, event):
        """ Keeps the player updated. OVERRIDE. """

        if self._mediaplayer is None:
            return

        # Get current position
        offset = self._mediaplayer.Tell()
        # Allowed position
        try:
            (s,e) = self._display.GetPeriodValues()
            delta = (e-s)*100
            maxoffset = int(e*1000)
            # Quick and dirty:
            if offset >= ( maxoffset - delta ) and self._mediaplayer.GetState() != wx.media.MEDIASTATE_STOPPED:
                m = (e-s)/2
                self._display.SetPeriodValues( s+m, e+m )
        except Exception:
            self.onStop(event)

        # Maximum media offset
        if self._mediaplayer.GetState() == wx.media.MEDIASTATE_PLAYING and offset == 0:
            self.onStop(event)

        if self._mediaplayer.GetState() != wx.media.MEDIASTATE_STOPPED:
            self.UpdateRuler()

    # End onTimer
    #-------------------------------------------------------------------------


    def UpdateRuler(self):
        offset = self._mediaplayer.Tell()
        if self._display:
            self._display.GetRuler().SetPlayerIndicatorValue( float(offset)/1000.0 )
            self._display.GetRuler().Refresh()

    #-------------------------------------------------------------------------



    #-------------------------------------------------------------------------
    # Data management
    #-------------------------------------------------------------------------


    def SetDisplay(self, d):

        self._display = d
        if self._display is None:
            self.ActivateButtons(False)
            self.EnableButtons(True)
            self._mediaplayer = None
        else:
            self.SetMedia()

    # End SetDisplay
    #-------------------------------------------------------------------------


    def SetMedia(self):
        """ Set a new mediaplayer. """

        self.onStop(None)
        self._mediaplayer = None
        if self._display is None: return

        self._dcobj = self._display.GetSelectedObject()

        if self._dcobj is None:
            self.FileDeSelected()

        logging.debug("SET-MEDIA to: %s"%self._dcobj)
        if not isinstance(self._dcobj,WaveCtrl):
            self.FileDeSelected()
            return

        filename = self._display.GetSelectionFilename()
        logging.debug('  Media file name=%s'%filename)
        SndPlayer.FileSelected( self,filename )

        self.Refresh()

    # End SetMedia
    #-------------------------------------------------------------------------


    def FileDeSelected(self):
        """ Unset the current mediaplayer. """

        if self._display is None: return
        #self._display = None
        SndPlayer.FileDeSelected(self)

    # End FileDeSelected
    #-------------------------------------------------------------------------


# ----------------------------------------------------------------------------