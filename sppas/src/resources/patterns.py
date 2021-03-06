# -*- coding: UTF-8 -*-
# ---------------------------------------------------------------------------
#            ___   __    __    __    ___
#           /     |  \  |  \  |  \  /              the automatic
#           \__   |__/  |__/  |___| \__             annotation and
#              \  |     |     |   |    \             analysis
#           ___/  |     |     |   | ___/              of speech
#
#
#                           http://www.sppas.org/
#
# ---------------------------------------------------------------------------
#            Laboratoire Parole et Langage, Aix-en-Provence, France
#                   Copyright (C) 2011-2017  Brigitte Bigi
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
# File: src.resources.patterns.py
# ----------------------------------------------------------------------------

import math

# ----------------------------------------------------------------------------


class Patterns(object):
    """
    @author:       Brigitte Bigi
    @organization: Laboratoire Parole et Langage, Aix-en-Provence, France
    @contact:      brigitte.bigi@gmail.com
    @license:      GPL, v3
    @copyright:    Copyright (C) 2011-2017  Brigitte Bigi
    @summary:      Pattern matching.

    Pattern matching aims at checking a given sequence of tokens for the
    presence of the constituents of some pattern. In contrast to pattern
    recognition, the match usually has to be exact.

    Several pattern matching algorithms are implemented in this class.
    They allow to find an hypothesis pattern in a reference.

    """
    MAX_GAP = 4
    MAX_NGRAM = 8

    # ------------------------------------------------------------------------

    def __init__(self):
        """ Create a new Pattern instance with default members value. """

        self._ngram = 3
        self._score = 1.
        self._gap = 2
        self._interstice = self._gap * 2

    # ------------------------------------------------------------------------
    # Getters
    # ------------------------------------------------------------------------

    def get_score(self):
        """ Return the score value (float). """

        return self._score

    def get_ngram(self):
        """ Return the n value for n-grams (int). """

        return self._ngram

    def get_gap(self):
        """ Return the gap value (int). """

        return self._gap

    # ------------------------------------------------------------------------
    # Setters
    # ------------------------------------------------------------------------

    def set_ngram(self, n):
        """
        Fix the value of n of the n-grams.

        :param n: (int) Value of n (1<n<MAX_NGRAM)

        """
        n = int(n)
        if 0 < n < Patterns.MAX_NGRAM:
            self._ngram = n
        else:
            raise ValueError("n value of n-grams pattern matching must range [1;%d]. Got %d." % (Patterns.MAX_NGRAM, n))

    # ------------------------------------------------------------------------

    def set_gap(self, g):
        """
        Fix the value of the gap.

        :param g: (int) Value of the gap (0<g<MAX_GAP)

        """
        g = int(g)
        if 0 <= g < Patterns.MAX_GAP:
            self._gap = g
            self._interstice = 2*g
        else:
            raise ValueError("gap value of pattern matching must range [0;%d]. Got %d." % (Patterns.MAX_GAP, g))

    # ------------------------------------------------------------------------

    def set_score(self, s):
        """
        Fix the value of the score.

        :param s: (float) Value of the score (0<s<1)

        """
        s = float(s)
        if 0 <= s <= 1.:
            self._score = s
        else:
            raise ValueError("score value of unigrams pattern matching must range [0;1]. Got %f." % s)

    # ------------------------------------------------------------------------
    # Matching search methods
    # ------------------------------------------------------------------------

    def ngram_matches(self, ref, hyp):
        """
        n-gram matches between ref and hyp.
        Search for common n-gram sequences of hyp in ref.

        :param ref: (list of tokens - IN) List of references
        :param hyp: (list of tuples - IN) List of hypothesis with their scores
        The scores are supposed to range in [0;1] values.

        :returns: List of matching indexes as tuples (i_ref, i_hyp)

        """
        matchings = []
        (nman, nasr) = self._create_ngrams(ref, hyp)

        previdxm = 0

        for idxa in range(len(nasr)):

            matchidxa = []
            for idxm in range(previdxm, len(nman)):
                if nasr[idxa] == nman[idxm]:
                    matchidxa.append(idxm)

            # if we found more than one match, then ignore!
            # (it can be caused by self-repetitions for example,
            # or ORs if there are more than one speaker in the audiofile)
            if len(matchidxa) == 1:
                idxm = matchidxa[0]
                previdxm = idxm+1
                for i in range(self._ngram):
                    matchings.append((idxm+i,idxa+i))

        return sorted(list(set(matchings)))

    # ------------------------------------------------------------------------

    def ngram_alignments(self, ref, hyp):
        """
        n-gram alignment of ref and hyp.

        The algorithm is based on the finding of matching n-grams, in the
        range of a given gap. If 1-gram, keep only hypothesis items with a
        high confidence score. A gap of search has to be fixed.
        An interstice value ensure the gap between an item in the ref and
        in the hyp won't be too far.

        :param ref: (list of tokens - IN) List of references
        :param hyp: (list of tuples - IN) List of hypothesis with their scores
        The scores are supposed to range in [0;1] values.
        :returns: List of alignments indexes as tuples (i_ref,i_hyp),

        Example:

        ref:  w0  w1  w2  w3  w4  w5  w6  w7  w8  w9  w10  w11  w12
               |   |   |   |       |   |          |
               |   |   |    \      |   |         /
               |   |   |      \    |   |        /
        hyp:  w0  w1  w2  wX  w3  w5  w6  wX  w9

        returned matchings:
         - if n=3: [ (0,0), (1,1), (2,2) ]
         - if n=2: [(0, 0), (1, 1), (2, 2), (5, 5), (6, 6)]
         - if n=1, it depends on the scores in hyp and the value of the gap.

        """
        alignment = []

        (nman, nasr) = self._create_ngrams(ref, hyp)

        lastidxa = len(nasr)
        lastidxm = len(nman)
        lastidx = min(lastidxa, lastidxm)

        idxa = 0
        idxm = 0

        while idxa < lastidxa and idxm < (lastidx+self._gap-1):

            found = False

            # matching
            if idxm < lastidxm and nasr[idxa] == nman[idxm]:
                for i in range(self._ngram):
                    alignment.append((idxm+i,idxa+i))
                found = True

            # matching, supposing deletions in hyp
            if idxm < lastidxm:
                for gap in range(self._gap):
                    if not found and idxm < (lastidxm-gap-1):
                        if nasr[idxa] == nman[idxm+gap+1]:
                            idxm = idxm + gap + 1
                            for i in range(self._ngram):
                                alignment.append((idxm+i, idxa+i))
                            found = True

            # matching, supposing insertions in hyp
            if idxm > 0:
                for gap in range(self._gap):
                    if not found and idxm > (gap+1):
                        if nasr[idxa] == nman[idxm-gap-1]:
                            idxm = idxm - gap - 1
                            for i in range(self._ngram):
                                alignment.append((idxm+i,idxa+i))
                            found = True

            idxa = idxa + 1
            idxm = idxm + 1

            # in case that idx in ref and idx in hyp are too far away...
            interstice = math.fabs(idxm - idxa)
            if interstice > self._interstice:
                vmax = max(idxa, idxm)
                idxa = vmax
                idxm = vmax

        return sorted(list(set(alignment)))

    # ------------------------------------------------------------------------

    def dp_matching(self, ref, hyp):
        """
        Dynamic Programming alignment of ref and hyp.

        The DP alignment algorithm performs a global minimization of a
        Levenshtein distance function which weights the cost of correct words,
        insertions, deletions and substitutions as 0, 3, 3 and 4 respectively.

         See:
         TIME WARPS, STRING EDITS, AND MACROMOLECULES:
         THE THEORY AND PRACTICE OF SEQUENCE COMPARISON,
         by Sankoff and Kruskal, ISBN 0-201-07809-0

        """
        raise NotImplementedError

    # ------------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------------

    def _create_ngrams(self, ref, hyp):
        """ Create ngrams of the reference and the hypothesis. """

        # create n-gram sequences of the reference
        nman = zip(*[ref[i:] for i in range(self._ngram)])

        # create n-gram sequences of the hypothesis
        # if ngram=1, keep only items with a high confidence score
        if self._ngram > 1:
            tab = [token for (token,score) in hyp]
            nasr = zip(*[tab[i:] for i in range(self._ngram)])
        else:
            nasr = []
            for (token, score) in hyp:
                if score >= self._score:
                    nasr.append((token,))
                else:
                    nasr.append(("<>",))

        return nman, nasr

    # ------------------------------------------------------------------------
