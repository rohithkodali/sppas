# -*- coding: UTF-8 -*-
"""
    ..
        ---------------------------------------------------------------------
         ___   __    __    __    ___
        /     |  \  |  \  |  \  /              the automatic
        \__   |__/  |__/  |___| \__             annotation and
           \  |     |     |   |    \             analysis
        ___/  |     |     |   | ___/              of speech

        http://www.sppas.org/

        Use of this software is governed by the GNU Public License, version 3.

        SPPAS is free software: you can redistribute it and/or modify
        it under the terms of the GNU General Public License as published by
        the Free Software Foundation, either version 3 of the License, or
        (at your option) any later version.

        SPPAS is distributed in the hope that it will be useful,
        but WITHOUT ANY WARRANTY; without even the implied warranty of
        MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
        GNU General Public License for more details.

        You should have received a copy of the GNU General Public License
        along with SPPAS. If not, see <http://www.gnu.org/licenses/>.

        This banner notice must not be removed.

        ---------------------------------------------------------------------

    src.annotations.__init__.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :author:       Brigitte Bigi
    :organization: Laboratoire Parole et Langage, Aix-en-Provence, France
    :contact:      brigitte.bigi@gmail.com
    :license:      GPL, v3
    :copyright:    Copyright (C) 2011-2017  Brigitte Bigi
    :summary:      SPPAS Automatic annotations global variables.

"""
from sppas.src.utils.maketext import translate
t = translate("annotations")

# ---------------------------------------------------------------------------
# Default output extension:

DEFAULT_OUTPUT_EXTENSION = ".xra"

# ---------------------------------------------------------------------------
# Annotation status, mainly used for log:

ERROR_ID = -1
INFO_ID = 3
IGNORE_ID = 2
WARNING_ID = 1
OK_ID = 0

# ---------------------------------------------------------------------------
# Symbols used by SPPAS annotations to represent an event:

SYMBOLS = {
    '#': "silence",
    '+': "pause",
    '*': "noise",
    '@': "laugh",
    '@@': "laugh",
    'dummy': 'dummy'
}
