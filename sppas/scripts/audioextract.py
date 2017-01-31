#!/usr/bin/env python2
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

    scripts.audioextract.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    ... a script to extract a channel from an audio file.

"""
from argparse import ArgumentParser
import os
import sys

PROGRAM = os.path.abspath(__file__)
SPPAS = os.path.dirname(os.path.dirname(os.path.dirname(PROGRAM)))
sys.path.append(SPPAS)

import sppas.src.audiodata
from sppas.src.audiodata.audio import AudioPCM

# ----------------------------------------------------------------------------

parser = ArgumentParser(usage="%s -w input file -o output file -c channel" % os.path.basename(PROGRAM),
                        description="... a script to extract a channel from an audio file.")

parser.add_argument("-w", metavar="file", required=True,  help='Audio Input file name')
parser.add_argument("-o", metavar="file", required=True,  help='Audio Output file name')
parser.add_argument("-c", metavar="value", default=1, type=int, required=False,
                    help='Number of the channel to extract (default: 1=first=left)')

if len(sys.argv) <= 1:
    sys.argv.append('-h')

args = parser.parse_args()

# ----------------------------------------------------------------------------

audio = sppas.src.audiodata.open(args.w)

if args.c == 0 or args.c > audio.get_nchannels():
    print "Wrong channel value (must be > 0 and < number of channels)"
    sys.exit(1)

idx = audio.extract_channel(args.c-1)

# Save the converted channel
audio_out = AudioPCM()
audio_out.append_channel(audio.get_channel(idx))
sppas.src.audiodata.save(args.o, audio_out)