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
# File: htkscripts.py
# ---------------------------------------------------------------------------

import os
import os.path
import logging

# ---------------------------------------------------------------------------

class HtkScripts(object):
    """
    @authors: Brigitte Bigi
    @contact: brigitte.bigi@gmail.com
    @license: GPL, v3
    @summary: HTK-ASCII scripts reader/writer.

    This class is able to write all scripts of the VoxForge tutorial.
    They are used to train acoustic models thanks to the HTK toolbox.

    For details, refer to: http://www.voxforge.org/

    """
    def __init__(self):
        """
        Create an HtkScripts instance.

        """
        self.configfile = ""
        self.globalfile = ""
        self.mkphones0file = ""
        self.mkphones1file = ""
        self.mktrifile = ""
        self.maketriphonesfile = ""
        self.silfile = ""

    # -----------------------------------------------------------------------

    def write_all(self, dirname):
        """
        Write all scripts at once, with their default name, in the given
        directory.

        @param dirname (str) a directory name (existing or to be created).

        """
        if os.path.exists( dirname ) is False:
            os.mkdir( dirname )

        self.write_global_ded( os.path.join(dirname, "global.ded") )
        self.write_mkphones0_led( os.path.join(dirname, "mkphones0.led") )
        self.write_mkphones1_led( os.path.join(dirname, "mkphones1.led") )
        self.write_mktri_led( os.path.join(dirname, "mktri.led") )
        self.write_maketriphones_ded( os.path.join(dirname, "maketriphones.ded") )
        self.write_sil_hed( os.path.join(dirname, "sil.hed") )

    # -----------------------------------------------------------------------

    def write_global_ded(self, filename):
        """
        Write an htk script.
        """
        logging.info('Write script file: %s'%filename)
        with open( filename, "w") as fp:
            fp.write("AS sp\n")
            fp.write("RS cmu\n")
            fp.write("MP sil sil sp\n")
            fp.write("\n")
        self.globalfile = filename

    # -----------------------------------------------------------------------

    def write_mkphones0_led(self, filename):
        """
        Write an htk script.
        """
        logging.info('Write script file: %s'%filename)
        with open( filename, "w") as fp:
            fp.write("EX\n")
            fp.write("IS sil sil\n")
            fp.write("DE sp\n")
            fp.write("\n")
        self.mkphones0file = filename

    # -----------------------------------------------------------------------

    def write_mkphones1_led(self, filename):
        """
        Write an htk script.
        """
        logging.info('Write script file: %s'%filename)
        with open( filename, "w") as fp:
            fp.write("EX\n")
            fp.write("IS sil sil\n")
            fp.write("\n")
        self.mkphones1file = filename

    # -----------------------------------------------------------------------

    def write_mktri_led(self, filename):
        """
        Write an htk script.
        Remove the sp state if it already exists in the phonetisation.
        """
        logging.info('Write script file: %s'%filename)
        with open( filename, "w") as fp:
            fp.write("WB sp\n")
            fp.write("WB sil\n")
            fp.write("TC\n")
            fp.write("\n")
        self.mktrifile = filename

    # -----------------------------------------------------------------------

    def write_maketriphones_ded(self, filename):
        """
        Write an htk script.
        """
        logging.info('Write script file: %s'%filename)
        with open( filename, "w") as fp:
            fp.write("AS sp\n")
            fp.write("MP sil sil sp\n")
            fp.write("TC\n")
            fp.write("\n")
        self.maketriphonesfile = filename

    # -----------------------------------------------------------------------

    def write_sil_hed(self, filename):
        """
        Write an htk script.
        """
        logging.info('Write script file: %s'%filename)
        with open( filename, "w") as fp:
            fp.write("AT 2 4 0.2 {sil.transP}\n")
            fp.write("AT 4 2 0.2 {sil.transP}\n")
            fp.write("AT 1 3 0.3 {sp.transP}\n")
            fp.write("TI silst {sil.state[3],sp.state[2]}\n")
            fp.write("\n")
        self.silfile = filename

    # -----------------------------------------------------------------------
