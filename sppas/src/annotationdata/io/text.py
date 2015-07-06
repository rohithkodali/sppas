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
#       Copyright (C) 2015  Brigitte Bigi
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

import re
import codecs
import csv
import cStringIO
from annotationdata.transcription import Transcription
from annotationdata.label.label import Label
import annotationdata.ptime.point
from annotationdata.ptime.interval import TimeInterval
from annotationdata.ptime.framepoint import FramePoint
from annotationdata.annotation import Annotation
from re import split


TEXT_RADIUS = 0.0005


def TimePoint(time):
    return annotationdata.ptime.point.TimePoint(time, TEXT_RADIUS)


class RawText(Transcription):

    @staticmethod
    def detect(filename):
        with codecs.open(filename, 'r', 'utf-8'):
            pass
        return True

    # End detect
    # -----------------------------------------------------------------

    def __init__(self, name="NoName", coeff=1, mintime=None, maxtime=None):
        """
        Creates a new Transcription instance.

        """
        Transcription.__init__(self, name, coeff, mintime, maxtime)

    # End __init__
    # -----------------------------------------------------------------

    @staticmethod
    def __read_annotation(phrase, number):
        return Annotation(FramePoint(number), Label(phrase))

    # End __read_annotation
    # -----------------------------------------------------------------

    def read(self, filename):
        """
        Read a raw text.
        Each CR/LF is a unit separator (not added in the Transcription()).
        Each # is also a unit separator (added in the Transcription()).
        """
        # Remark: here we use FramePoint() as a "rank" function
        with codecs.open(filename, 'r', 'utf-8') as fp:

            tier = self.NewTier('RawTrs')

            n = 1
            for line in fp:
                line = line.strip()
                # we ought not to have to remove the BOM
                # line.lstrip(unicode(codecs.BOM_UTF8, "utf8"))

                if line.find("#") > -1:

                    phrases = map(lambda s: s.strip(), split('(#)', line))

                    for phrase in phrases:  # keep '#' in the tab
                        if len(phrase) > 0:
                            tier.Append(RawText.__read_annotation(phrase, n))
                            n += 1

                elif len(line) > 0:
                    tier.Append(RawText.__read_annotation(line, n))
                    n += 1

    # End read
    # -----------------------------------------------------------------

    def write(self, filename):
        """
        Write an ascii file, as txt file.

        @param filename: (String) is the output file name, ending with ".txt"

        """
        with codecs.open(filename, 'w', 'utf-8', buffering=8096) as fp:
            if self.GetSize() != 1:
                raise Exception(
                    "Cannot write a multi tier annotation to a txt.")

            for annotation in self[0]:
                fp.write(annotation.GetLabel().GetValue() + '\n')

    # End write
    # -----------------------------------------------------------------


class CSV(Transcription):
    @staticmethod
    def detect(filename):
        csvLine = re.compile(
            '^(("([^"]|"")*"|[^",]*),)+("([^"]|"")*"|[^",]*)$')

        with codecs.open(filename, 'r', 'utf-8') as fp:
            detected = True
            for i in range(1, 10):
                if not csvLine.match(fp.next()):
                    detected = False

        return detected

    # End detect
    # -----------------------------------------------------------------

    class UnicodeReader:
        """
        A CSV reader which will iterate over lines in the CSV file "f",
        which is encoded in the given encoding.
        """
        @staticmethod
        def utf_8_encoder(unicode_csv_data):
            for line in unicode_csv_data:
                yield line.encode('utf-8')

        # End utf_8_encoder
        # -----------------------------------------------------------------

        def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):

            self.reader = csv.reader(CSV.UnicodeReader.utf_8_encoder(f),
                                     dialect=dialect, **kwds)

        # End __init__
        # -----------------------------------------------------------------

        def next(self):
            row = self.reader.next()
            return [unicode(s, "utf-8") for s in row]

        # End next
        # -----------------------------------------------------------------

        def __iter__(self):
            return self

        # End __iter__
        # -----------------------------------------------------------------

    class UnicodeWriter:
        """
        A CSV writer which will write rows to CSV file "f",
        which is encoded in the given encoding.
        """

        def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
            # Redirect output to a queue
            self.queue = cStringIO.StringIO()
            self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
            self.stream = f

        # End __init__
        # -----------------------------------------------------------------

        def writerow(self, row):
            self.writer.writerow([s.encode("utf-8") for s in row])
            # Fetch UTF-8 output from the queue ...
            data = self.queue.getvalue()
            data = data.decode("utf-8")
            # write to the target stream
            self.stream.write(data)
            # empty queue
            self.queue.truncate(0)

        # End writerow
        # -----------------------------------------------------------------

        def writerows(self, rows):
            for row in rows:
                self.writerow(row)

        # End writerows
        # -----------------------------------------------------------------

    def __init__(self, name="NoName", coeff=1, mintime=None, maxtime=None):
        """
        Creates a new CSV Transcription instance.

        """
        super(CSV, self).__init__(name, coeff, mintime, maxtime)

    # End __init__
    # -----------------------------------------------------------------

    def read(self, filename):
        """
        Read a CSV file.

        Support tiers of types: TimeInterval or TimePoint
        (3rd or 4th column with an empty field).

        @param filename: is the input file name
        @param fill_gaps: (Boolean) if it is set to True,
                          the input is supposed to be time-continued and gaps
                          will be filled with a non-labelled annotation

        """

        with codecs.open(filename, "r", 'utf-8-sig') as fp:

            reader = CSV.UnicodeReader(fp)
            tier = None

            for row in reader:
                if len(row) != 4:
                    raise Exception('Invalid row in CSV file: %r' % row)

                name, begin, end, label = row

                if tier is None or name != tier.GetName():
                    tier = self.NewTier(name)

                hasBegin = len(begin.strip()) > 0
                hasEnd = len(end.strip()) > 0

                if hasBegin and hasEnd:
                    time = TimeInterval(TimePoint(float(begin)),
                                        TimePoint(float(end)))
                elif hasBegin:
                    time = TimePoint(float(begin))

                elif hasEnd:
                    time = TimePoint(float(end))

                else:
                    raise Exception('No valid timepoint in CSV file row: %r'
                                    % row)

                tier.Add(Annotation(time, Label(label)))

        self.SetMinTime(0.)
        self.SetMaxTime(self.GetEnd())

    # End read
    # -----------------------------------------------------------------

    def write(self, filename):
        """
        Write a csv file.

        @param filename: is the output file name, ending with ".csv"

        """
        with codecs.open(filename, 'w', 'utf-8-sig', buffering=8096) as fp:

            writer = CSV.UnicodeWriter(fp)

            for tier in self:
                if tier.IsEmpty():
                    continue

                for annotation in tier:

                    name = tier.GetName()

                    if annotation.GetLocation().IsInterval():
                        begin = str(
                            annotation.GetLocation().GetBeginMidpoint())
                        end = str(
                            annotation.GetLocation().GetEndMidpoint())
                    else:
                        begin = str(
                            annotation.GetLocation().GetPointMidpoint())
                        end = ''

                    label = annotation.GetLabel().GetValue()

                    row = [name, begin, end, label]
                    writer.writerow(row)

    # End write
    # -----------------------------------------------------------------