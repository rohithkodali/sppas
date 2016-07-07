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
# File: tracks.py
# ----------------------------------------------------------------------------

import os
import logging
import codecs

import annotations.Align.aligners as aligners
from annotations.Align.aligners.alignerio import AlignerIO

from annotationdata.transcription  import Transcription
from annotationdata.tier           import Tier
from annotationdata.ptime.interval import TimeInterval
from annotationdata.ptime.point    import TimePoint
from annotationdata.annotation     import Annotation
from annotationdata.label.label    import Label
from annotationdata.label.text     import Text

import audiodata.autils as autils

from resources.slm.ngramsmodel import START_SENT_SYMBOL, END_SENT_SYMBOL
from resources.rutils import ToStrip

from sp_glob import encoding
from sp_glob import UNKSTAMP

# ----------------------------------------------------------------------

def eval_spkrate( trackstimes, ntokens ):
    """
    Evaluate the speaking rate in number of tokens per seconds.

    """
    return ntokens/sum( [(e-s) for (s,e) in trackstimes] )

# ----------------------------------------------------------------------

def duration2ntokens( duration, spkrate=12. ):
    """
    Try to empirically fix the maximum number of tokens we could expect for a given duration.
    However, the average speaking rate will vary across languages and situations.

    In conversational English, the average rate of speech for men is 125
    words per minute. Women average 150 words per minute. Television
    newscasters frequently hit 175+ words per minute (= 3 words/sec.).
    See: http://sixminutes.dlugan.com/speaking-rate/

    In CID, if we look at all tokens of the IPUs, the speaker rate is:
        - AB: 4.55 tokens/sec.
        - AC: 5.29 tokens/sec.
        - AP: 5.15 tokens/sec.
    See: http://sldr.org/sldr000720/

    To ensure we'll consider enough words, we'll fix a very large value by
    default, i.e. 12 tokens/second.

    @param duration (float - IN) Speech duration in seconds.
    @return a maximum number of tokens we could expect for this duration.

    """
    return int(duration*spkrate)+1

# ----------------------------------------------------------------------

class TrackNamesGenerator():
    def __init__(self):
        pass

    def audiofilename(self, trackdir, tracknumber):
        return os.path.join(trackdir, "track_%.06d.wav" % tracknumber)

    def phonesfilename(self, trackdir, tracknumber):
        return os.path.join(trackdir, "track_%.06d.pron" % tracknumber)

    def tokensfilename(self, trackdir, tracknumber):
        return os.path.join(trackdir, "track_%.06d.term" % tracknumber)

    def alignfilename(self, trackdir, tracknumber, ext=None):
        if ext is None:
            return os.path.join(trackdir, "track_%.06d" % tracknumber)
        return os.path.join(trackdir, "track_%.06d.%s" % (tracknumber,ext))

# ----------------------------------------------------------------------------

class TrackSplitter( Transcription ):
    """
    @author:       Brigitte Bigi
    @organization: Laboratoire Parole et Langage, Aix-en-Provence, France
    @contact:      brigitte.bigi@gmail.com
    @license:      GPL, v3
    @copyright:    Copyright (C) 2011-2016  Brigitte Bigi
    @summary:      Write tokenized-phonetized segments from Tiers.

    """
    def __init__(self, name="NoName", mintime=0., maxtime=0.):
        """
        Creates a new SegmentsOut instance.

        """
        Transcription.__init__(self, name, mintime, maxtime)
        self._radius = 0.005
        self._tracknames = TrackNamesGenerator()
        self._aligntrack = None

    # ------------------------------------------------------------------------

    def set_tracksnames( self, tracknames ):
        self._tracknames = tracknames

    # ------------------------------------------------------------------------

    def set_trackalign( self, ta ):
        self._aligntrack = ta

    # ------------------------------------------------------------------------

    def split(self, inputaudio, phontier, toktier, diralign):
        """
        Split all the data into tracks.

        @param phontier (Tier - IN) the tier with phonetization to split
        @param toktier  (Tier - IN) the tier with tokenization to split
        @param diralign (str - IN) the directory to put units.

        @return List of units with (start-time end-time)

        """
        if phontier.IsTimeInterval() is False:
            if self._aligntrack is None or self._aligntrack.get_aligner() != "julius":
                raise IOError("The phonetization tier is not of type TimeInterval and the aligner can't perform this segmentation.")
            else:
                self._create_tracks(inputaudio, phontier, toktier, diralign)

        units = self._write_text_tracks(phontier, toktier, diralign)
        self._write_audio_tracks(inputaudio, units, diralign)
        return units

    # ------------------------------------------------------------------------

    def _create_tracks(self, inputaudio, phontier, toktier, diralign):
        """
        """
        # only julius can do that (for now)
        aligner = aligners.instantiate(self._aligntrack.get_model(),"julius")
        aligner.set_infersp(False)
        aligner.set_outext("walign")
        alignerio = AlignerIO()

        logging.debug( "Find automatically chunks for audio file: %s"%inputaudio)
        anchortier = AnchorTier()

        # Extract the data we'll work on
        channel = autils.extract_audio_channel( inputaudio,0 )
        channel = autils.format_channel( channel,16000,2 )
        pronlist = self._tier2raw( phontier ).split()
        toklist  = self._tier2raw( toktier ).split()
        if len(pronlist) != len(toklist):
            raise IOError("Inconsistency between the number of items in phonetization %d and tokenization %d."%(len(pronlist),len(toklist)))

        # Search silences and use them as anchors.
        logging.debug(" ... Search silences:")
        trackstimes = autils.search_channel_speech( channel )
        self._append_silences(trackstimes, anchortier)
        for i,a in enumerate(anchortier):
            logging.debug(" ... ... %i: %s"%(i,a))

        # Estimates the speaking rate (amount of tokens/sec. in average)
        spkrate = eval_spkrate( trackstimes, len(toklist) )
        logging.debug(' ... Real speaking rate is: %.3f tokens/sec.'%spkrate)
        spkrate = int(spkrate*1.8)
        logging.debug(' ... ... we will approx. to %d tokens/sec.'%spkrate)

        # Windowing on the audio
        logging.debug(" ... Windowing the audio file:")
        fromtime = 0.
        totime   = 0.
        fromtoken = 0
        totoken   = 0
        maxtime  = trackstimes[-1][1]
        while fromtime < maxtime:

            (fromtime,totime) = anchortier.fix_window(fromtime)
            nbtokens = duration2ntokens( totime-fromtime, spkrate )
            totoken = min( (fromtoken + nbtokens), len(toklist))
            if fromtime >= totime:
                print "That's the end: fromtime=",fromtime," totime=",totime
                break
            logging.debug(" ... ... window: ")
            logging.debug("... ... ... - time  from %.4f to %.4f."%(fromtime,totime))
            logging.debug("... ... ... - token from %d to %d."%(fromtoken,totoken))
            logging.debug("%s"%(" ".join(  toklist[fromtoken:totoken] )))

            # create audio file
            fnw = self._tracknames.alignfilename(diralign,0)
            fna = self._tracknames.audiofilename(diralign,0)
            trackchannel = autils.extract_channel_fragment( channel, fromtime, totime, 0.2)
            autils.write_channel( fna, trackchannel )

            # call the ASR engine to recognize tokens of this track
            aligner.set_phones( " ".join( pronlist[fromtoken:totoken] ) )
            aligner.set_tokens( " ".join(  toklist[fromtoken:totoken] ) )
            aligner.run_alignment(fna, fnw)

            # get the tokens time-aligned by the ASR engine
            wordalign = alignerio.read_aligned(fnw)[1]  # (starttime,endtime,label,score)
            print "ASR direct output:"
            for (b,e,w,s) in wordalign:
                print " -> ",b,e,w,s

            wordalign = self._adjust_asr_result(wordalign, fromtime, 0.2)
            print "ASR ADJUSTED:"
            for (b,e,w,s) in wordalign:
                print " -> ",b,e,w,s

            # match automatic and manual sequences of tokens
            (lastasrtoken,lastmantoken) = self._append_chunks( wordalign, toklist[fromtoken:totoken], anchortier )

            print "Last token = ",fromtoken+lastmantoken,toklist[fromtoken+lastmantoken]
            print "Last time  = ",lastasrtoken,wordalign[lastasrtoken][1]
            fromtoken = fromtoken + lastmantoken + 1
            fromtime  = wordalign[lastasrtoken][1]

            print "Next trip with fromtoken=",toklist[fromtoken],"fromtime=",fromtime
            # delete files

        raise NotImplementedError("the aligner can't perform the units segmentation.")

    # ------------------------------------------------------------------------

    def _adjust_asr_result(self, wordsalign, fromtime, silence):
        """
        Adapt wordsalign: remove <s> and </s> then adjust time values.

        """
        # shift all time values of "silence" delta
        for i in range(len(wordsalign)):
            wordsalign[i][0] = wordsalign[i][0] - silence
            wordsalign[i][1] = wordsalign[i][1] - silence

        # remove the first <s> and the last </s>
        wordsalign.pop(0)
        wordsalign.pop()

        if len(wordsalign) == 0:
            raise IOError('The ASR failed to find tokens.')

        # the first token was recognized during the silence we prepended!!!!
        if wordsalign[0][1] < 0:
            wordsalign.pop(0)

        # fix the (new) first token to the beginning of the audio, i.e. 0.
        wordsalign[0][0] = 0.

        # shift to the real time values in the audioinput
        for i in range(len(wordsalign)):
            wordsalign[i][0] = wordsalign[i][0] + fromtime
            wordsalign[i][1] = wordsalign[i][1] + fromtime

        return wordsalign

    # ------------------------------------------------------------------------

    def _append_chunks(self, tokensalign, tokenslist, anchortier ):
        """
        Try to find chunks and append in anchortier.
        Chunk search is based on the n-grams matching between the words the
        ASR found and the tokens manually transcribed.

        @param tokensalign (list of tuples - IN) The list of tokens the ASR found in an extract
        @param tokenslist (list of str - IN) The sequence of manually transcribed tokens matching the extract and after
        @param anchortier (Tier - INOUT) The tier to add chunks

        """
        # list of tokens the ASR automatically time-aligned
        tasr = [unicode(token) for (start,end,token,score) in tokensalign]
        tman = [unicode(token) for token in tokenslist]
        ngram = 4 # to start with 3-grams...

        # find matching patterns from left to right
        lrmatching = []
        while ngram > 1:
            ngram = ngram-1

            # create n-gram sequences of manually transcribed tokens
            nman = zip(*[tman[i:] for i in range(ngram)])

            # create n-gram sequences of ASR transcribed tokens
            # if ngram=1, keep only tokens with a high confidence score
            if ngram>1:
                nasr = zip(*[tasr[i:] for i in range(ngram)])
            else:
                nasr = []
                for (start,end,token,score) in tokensalign:
                    if score > 0.9:
                        nasr.append( unicode(token) )
                    else:
                        nasr.append( unicode("<unk>") )

            # find matching patterns
            lastidx = min(len(nasr),len(nman))
            idxa = 0
            idxm = 0
            while idxa<lastidx and idxm<lastidx:
                found = False

                if nasr[idxa] == nman[idxm]:
                    print "Matching exact with n=",ngram, range(idxa,idxa+ngram)
                    for i in range(ngram):
                        lrmatching.append( (idxa+i,idxm+i) )
                    found = True

                if not found and idxm < lastidx:
                    if nasr[idxa] == nman[idxm+1]:
                        idxm = idxm + 1
                        print "Matching shift+1 with n=",ngram, range(idxa,idxa+ngram)
                        for i in range(ngram):
                            lrmatching.append( (idxa+i,idxm+i) )
                        found = True

                if not found and idxm > 0:
                    if nasr[idxa] == nman[idxm-1]:
                        idxm = idxm - 1
                        print "Matching shift-1 with n=",ngram, range(idxa,idxa+ngram)
                        for i in range(ngram):
                            lrmatching.append( (idxa+i,idxm+i) )

                idxa = idxa + 1
                idxm = idxm + 1

        matching = sorted(list(set(lrmatching)))

        if len(matching) == 0:
            raise Exception('No matching found between ASR result and manual transcription.')

        # OK, insert the chunks we found in anchortier
        print "Matching set of tokens:"
        for (a,m) in matching:
            print " ... ...",a,"-",m," ->",tasr[a],nman[m]

        # Return the indexes of the last token of the last anchor
        return matching[-1]

    # ------------------------------------------------------------------------

    def _tier2raw( self,tier ):
        """
        Return all interval contents into a single string.
        """
        raw = ""
        for ann in tier:
            if ann.GetLabel().IsSilence() is False:
                besttext = ann.GetLabel().GetValue()
                if UNKSTAMP in besttext:
                    besttext = "sil"
                raw = raw + " " + besttext

        return ToStrip(raw)

    # ------------------------------------------------------------------------

    def _write_text_tracks(self, phontier, toktier, diralign):
        """
        Write tokenization and phonetization of tiers into separated track files.

        """
        tokens = True
        if toktier is None:
            toktier = phontier.Copy()
            tokens = False
        if phontier.GetSize() != toktier.GetSize():
            raise IOError('Inconsistency between the number of intervals of tokenization (%d) and phonetization (%d) tiers.'%(phontier.GetSize(),toktier.GetSize()))

        units = []
        for annp,annt in zip(phontier,toktier):

            b = annp.GetLocation().GetBegin().GetMidpoint()
            e = annp.GetLocation().GetEnd().GetMidpoint()
            units.append( (b,e) )

            # Here we write only the text-label with the best score,
            # we dont care about alternative text-labels
            fnp = self._tracknames.phonesfilename(diralign, len(units))
            textp = annp.GetLabel().GetValue()
            self._write_text_track( fnp, textp )

            fnt = self._tracknames.tokensfilename(diralign, len(units))
            label = annt.GetLabel()
            if tokens is False and label.IsSpeech() is True:
                textt = " ".join( ["w_"+str(i+1) for i in range(len(textp.split()))] )
            else:
                textt = label.GetValue()
            self._write_text_track( fnt, textt )

        return units

    def _write_text_track(self, trackname, trackcontent):
        with codecs.open(trackname,"w", encoding) as fp:
            fp.write(trackcontent)

    # ------------------------------------------------------------------------

    def _write_audio_tracks(self, inputaudio, units, diralign, silence=0.):
        """
        Write the first channel of an audio file into separated track files.
        Re-sample to 16000 Hz, 16 bits.

        """
        channel = autils.extract_audio_channel( inputaudio,0 )
        channel = autils.format_channel( channel,16000,2 )

        for track,u in enumerate(units):
            (s,e) = u
            trackchannel = autils.extract_channel_fragment( channel, s, e, silence)
            trackname    = self._tracknames.audiofilename(diralign, track+1)
            autils.write_channel(trackname, trackchannel)

    # ------------------------------------------------------------------------

    def _append_silences(self, trackstimes, tier):
        """
        Add silences in tier from a list of speech segments.

        @param trackstimes (list - IN) List of tuples (fromtime,totime)
        @param tier (Tier - INOUT) The tier to append silence intervals

        """
        radius = 0.005
        toprec = 0.
        for (fromtime,totime) in trackstimes:
            # From the previous track to the current track: silence
            if toprec < fromtime:
                begin = toprec
                end   = fromtime
                a     = Annotation(TimeInterval(TimePoint(begin,radius), TimePoint(end,radius)), Label("#"))
                tier.Append(a)
            toprec = totime
        if tier.GetSize()>0:
            tier[-1].GetLocation().SetEndRadius(0.)
            tier[0].GetLocation().SetBeginRadius(0.)

# ------------------------------------------------------------------
# ------------------------------------------------------------------

class AnchorTier( Tier ):
    """
    @author:       Brigitte Bigi
    @organization: Laboratoire Parole et Langage, Aix-en-Provence, France
    @contact:      brigitte.bigi@gmail.com
    @license:      GPL, v3
    @copyright:    Copyright (C) 2011-2016  Brigitte Bigi
    @summary:      Read time-aligned segments, convert into Tier.

    """
    def __init__(self, name="Anchors"):
        """
        Creates a new SegmentsIn instance.

        """
        Tier.__init__(self, name)
        self._windowdelay = 4.0
        self._margindelay = 2.0


    def fix_window(self, fromtime):
        """
        Return the "totime" corresponding to a flexible-sized window.

        if fromtime inside an anchor:
            fromtime = end-anchor-time

        totime is either:

            - fromtime + begin-of-the-next-anchor
              if there is an anchor in interval [fromtime,fromtime+delay]

            - fromtime + begin-of-the-next-anchor
              if there is an anchor in interval [fromtime,fromtime+delay+margin]
                (this is to ensure that the next window won't be too small)

            - fromtime + delay

        """
        # The totime corresponding to a full window
        totime = fromtime+self._windowdelay

        # Do we have already anchors between fromtime and totime?
        anns = self.Find( fromtime, totime, overlaps=True )
        if len(anns)>0:
            totime = anns[0].GetLocation().GetBegin().GetMidpoint()
            # fromtime is perhaps INSIDE an anchor!
            # or at the beginning of an anchor.
            # So... try again by shifting fromtime to the end of such anchor
            if fromtime >= totime:
                (fromtime,totime) = self.fix_window( anns[0].GetLocation().GetEnd().GetMidpoint() )

        else:
            # test with the margin to ensure the next window won't be too small
            anns = self.Find( totime, totime+self._margindelay, overlaps=True )
            if len(anns)>0:
                # totime is the begin of the first anchor we got in the margin
                totime = anns[0].GetLocation().GetBegin().GetMidpoint()

        return (fromtime,totime)

# ------------------------------------------------------------------
# ------------------------------------------------------------------

class TracksReader( Transcription ):
    """
    @author:       Brigitte Bigi
    @organization: Laboratoire Parole et Langage, Aix-en-Provence, France
    @contact:      brigitte.bigi@gmail.com
    @license:      GPL, v3
    @copyright:    Copyright (C) 2011-2016  Brigitte Bigi
    @summary:      Read time-aligned segments, convert into Tier.

    """
    def __init__(self, name="NoName", mintime=0., maxtime=0.):
        """
        Creates a new SegmentsIn instance.

        """
        Transcription.__init__(self, name, mintime, maxtime)
        self.alignerio = AlignerIO()
        self._radius = 0.005
        self._tracknames = TrackNamesGenerator()

    # ------------------------------------------------------------------------

    def set_tracksnames( self, tracknames ):
        self._tracknames = tracknames

    # ------------------------------------------------------------------------

    def read(self, dirname, units):
        """
        Read a set of alignment files and set as tiers.

        @param dirname (str - IN) the input directory containing a set of unit
        @param units (list - IN) List of units with start/end times

        """
        # Verify if the directory exists
        if os.path.exists( dirname ) is False:
            raise IOError("Missing directory: " + dirname+".\n")

        # Create new tiers
        itemp = self.NewTier("PhonAlign")
        itemw = self.NewTier("TokensAlign")

        # Explore each unit to get alignments
        for track in range(len(units)):

            # Get real start and end time values of this unit.
            unitstart,unitend = units[track]

            basename = self._tracknames.alignfilename(dirname, track+1)
            (_phonannots,_wordannots) = self.alignerio.read_aligned(basename)

            # Append alignments in tiers
            self._append_tuples(itemp, _phonannots, unitstart, unitend)
            self._append_tuples(itemw, _wordannots, unitstart, unitend)

        # Adjust Radius
        if itemp.GetSize()>1:
            itemp[-1].GetLocation().SetEndRadius(0.)
        if itemw.GetSize()>1:
            itemw[-1].GetLocation().SetEndRadius(0.)
            try:
                self._hierarchy.addLink('TimeAlignment', itemp, itemw)
            except Exception as e:
                logging.info('Error while assigning hierarchy between phonemes and tokens: %s'%(str(e)))
                pass

    # ------------------------------------------------------------------------

    def _append_tuples(self, tier, tdata, delta, unitend):
        """
        Append a list of (start,end,text,score) into the tier.
        Shift start/end of a delta value and set the last end value.

        """
        try:

            for i,t in enumerate(tdata):
                (loc_s,loc_e,lab,scr) = t
                loc_s += delta
                loc_e += delta
                if i==(len(tdata)-1):
                    loc_e = unitend

                # prepare the code in case we'll find a solution with
                # alternatives phonetizations/tokenization....
                #lab = [lab]
                #scr = [scr]
                #label = Label()
                #for l,s in zip(lab,scr):
                #    label.AddValue(Text(l,s))
                label = Label( Text(lab,scr) )
                annotationw = Annotation(TimeInterval(TimePoint(loc_s,self._radius), TimePoint(loc_e,self._radius)), label)
                tier.Append(annotationw)

        except Exception:
            import traceback
            print(traceback.format_exc())
            logging.info('No alignment appended in tier from %f to %f.'%(delta,unitend))
            pass

