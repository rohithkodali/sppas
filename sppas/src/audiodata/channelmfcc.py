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
# File: channelmfcc.py
# ---------------------------------------------------------------------------

import subprocess

from utils.type        import test_command
from audiodata.channel import Channel

# ---------------------------------------------------------------------------

class ChannelMFCC( object ):
    """
    @author:       Brigitte Bigi
    @organization: Laboratoire Parole et Langage, Aix-en-Provence, France
    @contact:      brigitte.bigi@gmail.com
    @license:      GPL, v3
    @copyright:    Copyright (C) 2011-2016  Brigitte Bigi
    @summary:      A channel MFCC extractor class.

    Mel-frequency cepstrum (MFC) is a representation of the short-term power
    spectrum of a sound, based on a linear cosine transform of a log power
    spectrum on a nonlinear mel scale of frequency.

    MFCCs are commonly derived as follows:

        1. Take the Fourier transform of (a windowed excerpt of) a signal.
        2. Map the powers of the spectrum obtained above onto the mel scale, using triangular overlapping windows.
        3. Take the logs of the powers at each of the mel frequencies.
        4. Take the discrete cosine transform of the list of mel log powers, as if it were a signal.
        5. The MFCCs are the amplitudes of the resulting spectrum.

    """
    def __init__(self, channel=None):
        """
        Constructor.

        @param channel (Channel) The channel to work on. Currently not used...!!!

        """
        self.channel = channel

    # ----------------------------------------------------------------------

    def hcopy(self, wavconfigfile, scpfile):
        """
        Create MFCC files from features described in the config file.
        Requires HCopy to be installed.

        @param wavconfigfile (str)
        @param scpfile (str)

        """
        if test_command("HCopy") is False: return False

        try:
            subprocess.check_call(["HCopy", "-T", "0",
                                  "-C", wavconfigfile,
                                  "-S", scpfile])
        except subprocess.CalledProcessError:
            return False

        return True

    # ----------------------------------------------------------------------

    def evaluate(self, features):
        """
        Evaluate MFCC of the given channel.

        """
        raise NotImplementedError

    # ----------------------------------------------------------------------
