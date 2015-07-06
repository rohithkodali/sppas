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
# ---------------------------------------------------------------------------
# File: annotation.py
# ----------------------------------------------------------------------------

__docformat__ = """epytext"""
__authors__   = """Brigitte Bigi (brigitte.bigi@gmail.com)"""
__copyright__ = """Copyright (C) 2011-2015  Brigitte Bigi"""


# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------

import copy

from label.label         import Label
from ptime.location      import Location

# ----------------------------------------------------------------------------


class Annotation(object):
    """
    @authors: Brigitte Bigi, Tatsuya Watanabe
    @contact: brigitte.bigi@gmail.com
    @license: GPL, v3
    @summary: Represents an annotation.

    An annotation in SPPAS is a container for:
        - a Location()
        - a Label()

    >>> tier = Tier()
    >>> p1 = TimePoint(1.5, radius=0.01)
    >>> p2 = TimePoint(1.6, radius=0.01)
    >>> t = TimeInterval(p1, p2)
    >>> l = Label("foo")
    >>> ann = Annotation(t, l)
    >>> tier.Add(ann)
    True
    >>> ann.GetLocation().GetBeginMidpoint()
    1.5
    >>> ann.GetLocation().GetEndMidpoint()
    1.6
    >>> ann.GetLabel().GetValue()
    foo
    >>> ann.GetLocation().SetBegin( TimePoint( 1.2 ) )

    """

    def __init__(self, place, text=None, tier=None):
        """
        Creates a new Annotation instance.

        @param place (BasePlacement,Localization,Location) the place where the annotation happens
        @param text (Label)
        @param tier (Tier)

        @raise TypeError

        """
        # Assign the label

        if not text:
            text = Label("")

        if isinstance(text, Label) is False:
            raise TypeError("Label argument required, not %r" % text)

        self.__label = text

        # Assign the location
        self.__location = (place
                           if isinstance(place, Location)
                           else Location(place))

    # End __init__
    # -----------------------------------------------------------------------

    def GetTier(self):
        """
        Return the parent Tier.

        """
        return self.__tier

    # End GetTier
    # -----------------------------------------------------------------------


    def GetLabel(self):
        """
        Return the Label instance.

        """
        return self.__label

    # End GetLabel
    # -----------------------------------------------------------------------


    def GetLocation(self):
        """
        Return the Location instance.

        """
        return self.__location

    # End GetLocation
    # -----------------------------------------------------------------------

    # -----------------------------------------------------------------------
    # Methods
    # -----------------------------------------------------------------------

    def Copy(self):
        """
        Return a copy of the annotation.

        """
        return copy.deepcopy(self)

    # End IsPoint
    # -----------------------------------------------------------------------


    # -----------------------------------------------------------------------
    # Overloads
    # -----------------------------------------------------------------------


    def __str__(self):
        return "Annotation: %s / %s" % (self.__location, self.__label)

    def __repr__(self):
        return "%s %s" % (self.__location, self.__label)

    # -----------------------------------------------------------------------

# ---------------------------------------------------------------------------