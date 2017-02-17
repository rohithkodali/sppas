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

    src.anndata.annlabel.label.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
from ..anndataexc import AnnDataTypeError

from .text import sppasText

# ----------------------------------------------------------------------------


class sppasLabel(object):
    """
    :author:       Brigitte Bigi
    :organization: Laboratoire Parole et Langage, Aix-en-Provence, France
    :contact:      brigitte.bigi@gmail.com
    :license:      GPL, v3
    :copyright:    Copyright (C) 2011-2017  Brigitte Bigi
    :summary:      Represents the label of an Annotation.

    A label is a list of possible sppasText(), represented as a UNICODE string.
    A data type can be associated, as sppasText() can be 'int', 'float' or 'bool'.

    """
    def __init__(self, text=None, score=None):
        """ Creates a new Label instance.

        :param text: (sppasText)
        :param score: (float)

        """
        self.__texts = list()
        self.__fct = max

        if text is not None:
            self.append(text, score)

    # -----------------------------------------------------------------------

    def get_function_score(self):
        """ Return the function used to compare scores. """

        return self.__fct

    # -----------------------------------------------------------------------

    def set_function_score(self, fct_name):
        """ Set a new function to compare scores.

        :param fct_name: one of min or max.

        """
        if fct_name not in (min, max):
            raise AnnDataTypeError(fct_name, "min, max")

        self.__fct = fct_name

    # -----------------------------------------------------------------------

    def append_content(self, content, data_type="str", score=None):
        """ Add a text into the list.

        :param content: (str)
        :param data_type: (str): The type of this text content (str, int, float, bool)
        :param score: (float)

        """
        text = sppasText(content, data_type)
        self.append(text, score)

    # -----------------------------------------------------------------------

    def append(self, text, score=None):
        """ Add a sppasText into the list.

        :param text: (Text)
        :param score: (float)

        """
        if not isinstance(text, sppasText):
            raise AnnDataTypeError(text, "sppasText")

        self.__texts.append((text, score))

    # -----------------------------------------------------------------------

    def remove(self, text):
        """ Remove a text of the list.

        :param text: (Text)

        """
        if not isinstance(text, sppasText):
            raise AnnDataTypeError(text, "sppasText")

        for (t, s) in self.__texts:
            if t == text:
                self.__texts.remove((t, s))

    # -----------------------------------------------------------------------

    def set_score(self, text, score):
        """ Set a score to a given text.

        :param text: (sppasText)
        :param score: (float)

        """
        if not isinstance(text, sppasText):
            raise AnnDataTypeError(text, "sppasText")

        for (t, s) in self.__texts:
            if t == text:
                s = score

    # -----------------------------------------------------------------------

    def get_best(self):
        """ Return the best sppasText, i.e. the one with the better score.

        :returns: (sppasText or None)

        """
        if len(self.__texts) == 0:
            return None

        if len(self.__texts) == 1:
            return self.__texts[0][0]

        _maxt = self.__texts[0][0]
        _maxscore = self.__texts[0][1]
        for (t, s) in reversed(self.__texts):
            if s is not None and s > _maxscore:
                _maxscore = s
                _maxt = t

        return _maxt

    # -----------------------------------------------------------------------

    def get(self):
        """ Return the list of sppasText and their scores. """

        return self.__texts

    # -----------------------------------------------------------------------
    # Overloads
    # -----------------------------------------------------------------------

    def __repr__(self):
        st = ""
        for t, s in self.__texts:
            st += "sppasText({:s}, score={:f}), ".format(t, s)
        return st

    # -----------------------------------------------------------------------

    def __str__(self):
        return "{:s}".format("; ".join([t for t in self.__texts]))

    # -----------------------------------------------------------------------

    def __iter__(self):
        for a in self.__texts:
            yield a

    # -----------------------------------------------------------------------

    def __getitem__(self, i):
        return self.__texts[i]

    # -----------------------------------------------------------------------

    def __len__(self):
        return len(self.__texts)