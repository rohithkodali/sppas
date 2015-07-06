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
# File: process.py
# ----------------------------------------------------------------------------

__docformat__ = """epytext"""
__authors__   = """Brigitte Bigi (brigitte.bigi@gmail.com)"""
__copyright__ = """Copyright (C) 2011-2015  Brigitte Bigi"""


# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------

import sys
import os
import shlex
import subprocess
import datetime

from sp_glob import program, version, copyright

import utils.fileutils

from annotations.log import sppasLog

from annotationdata.tier import Tier
from annotationdata.transcription import Transcription
from annotationdata.annotation import Annotation
from annotationdata.label.label import Label
from annotationdata.ptime.point import TimePoint
from annotationdata.ptime.interval import TimeInterval
import annotationdata.io

from annotations.Momel.momel     import sppasMomel
from annotations.Wav.wavseg      import sppasSeg
from annotations.Token.tok       import sppasTok
from annotations.Phon.phon       import sppasPhon
from annotations.Align.align     import sppasAlign
from annotations.Syll.syll       import sppasSyll
from annotations.Repetitions.repetition  import sppasRepetition

from threading import Thread
# ----------------------------------------------------------------------------

class sppasProcess( Thread ):
#class sppasProcess():
    """
    Parent class for running annotation processes.
    Process a directory full of files or a single file, and report on a
    progress.

    """

    def __init__(self, parameters):
        """
        Create a new sppasProcess instance.
        Initialize a Thread.

        @param parameters (sppasParam) SPPAS parameters, i.e. config of annotations

        """
        Thread.__init__(self)

        # fix input variables
        self.parameters = parameters
        self._progress = None
        self._logfile  = None

        self.start()

    # End __init__
    # ------------------------------------------------------------------------


    def set_filelist(self, extension, not_ext=[], not_start=[]):
        """
        Create a list of file names from the parameter inputs.

        @param extension: expected file extension
        @param not_ext: list of extension of files that must not be treated
        @param not_start: list of start of filenames that must not be treated

        @return a list of strings

        """
        filelist = []
        try:
            for sinput in self.parameters.get_sppasinput():

                # Input is a file (and not a directory)
                if extension.lower() in ['.wav','.wave'] and os.path.isfile(sinput) is True:
                    filelist.append( sinput )

                elif sinput.lower().endswith('.wav') is True or sinput.lower().endswith('.wave') is True:
                    sinput = os.path.splitext( sinput )[0] + extension
                    if os.path.isfile(sinput) is True:
                        filelist.append( sinput )
                    else:
                        if self._logfile is not None:
                            self._logfile.print_message("Can't find file %s\n"%sinput, indent=1,status=1)

                # Input is a directory:
                else:
                    # Get the list of files with 'extension' from the input directory
                    files = utils.fileutils.get_files( sinput, extension )
                    filelist.extend( files )
        except:
            pass

        # Removing files with not_ext as extension or containing not_start
        # TODO: DEBUG!!!
        fl2 = []
        for x in filelist:
            is_valid = True
            for ne in not_ext:
                if x.lower().endswith(ne.lower()) == True:
                    #filelist.remove(x)
#                    print "remove %s"%x
                    is_valid = False
#                else:
#                    print "end with %s:%s? added %s"%(ne,x,x)
            for ns in not_start:
                basex = os.path.basename(x.lower())
                if basex.startswith(ns.lower()) == True:
                    #filelist.remove(x)
#                    print "remove %s"%x
                    is_valid = False
#                else:
#                    print "start with %s:%s? added %s"%(ns,x,x)
            if is_valid == True:
                fl2.append(x)

        return fl2

    # End set_filelist
    # ------------------------------------------------------------------------


    def _get_filename(self, filename, extensions):
        """
        Return a filename corresponding to one of extensions.

        @param filename input file name
        @param extensions is the list of expected extension
        @return a file name of the first existing file with an expected extension or None

        """

        for ext in extensions:

            extfilename = os.path.splitext( filename )[0] + ext
            newfilename = utils.fileutils.exists(extfilename)
            if newfilename is not None and os.path.isfile(newfilename):
                return newfilename

        return None

    # ------------------------------------------------------------------------


    def run_momel(self, stepidx):
        """
        Execute the SPPAS implementation of momel.

        @param stepidx index of this annotations in the parameters
        @return number of files processed successfully

        """
        # Initializations
        step = self.parameters.get_step(stepidx)
        stepname = self.parameters.get_step_name(stepidx)
        files_processed_success = 0
        self._progress.set_header(stepname)
        self._progress.update(0,"")

        # Get the list of input file names, with the ".wav" (or ".wave") extension
        filelist = self.set_filelist(".wav",not_start=["track_"])
        if len(filelist) == 0:
            return 0
        total = len(filelist)

        # Create annotation instance
        try:
            m = sppasMomel( self._logfile )
        except Exception as e:
            if self._logfile is not None:
                self._logfile.print_message( "%s\n"%str(e), indent=1,status=1 )
            return 0

        # Execute annotation for each file in the list
        for i,f in enumerate(filelist):

            # fix the default values
            m.fix_options( step.get_options() )

            # Indicate the file to be processed
            self._progress.set_text( os.path.basename(f)+" ("+str(i+1)+"/"+str(total)+")" )
            if self._logfile is not None:
                self._logfile.print_message(stepname+" of file " + f, indent=1 )

            # Get the input file
            inname = self._get_filename(f, [".hz", ".PitchTier"])
            if inname is not None:

                # Fix output file names
                outname = os.path.splitext(f)[0]+"-momel.PitchTier"
                textgridoutname = os.path.splitext(f)[0] + "-momel.TextGrid"

                # Execute annotation
                try:
                    m.run(inname, trsoutput=textgridoutname, outputfile=outname)
                    files_processed_success += 1
                    if self._logfile is not None:
                        self._logfile.print_message(textgridoutname,indent=2,status=0)
                except Exception as e:
                    if self._logfile is not None:
                        self._logfile.print_message(textgridoutname+": %s"%str(e),indent=2,status=-1)
            else:
                if self._logfile is not None:
                    self._logfile.print_message("Failed to find a file with pitch values. Read the documentation for details.",indent=2,status=2)

            # Indicate progress
            self._progress.set_fraction(float((i+1))/float(total))
            if self._logfile is not None:
                self._logfile.print_newline()

        # Indicate completed!
        self._progress.update(1,"Completed (%d files successfully over %d files).\n"%(files_processed_success,total))
        self._progress.set_header("")

        return files_processed_success

    # End run_momel
    # ------------------------------------------------------------------------


    def run_ipusegmentation(self, stepidx):
        """
        Execute the SPPAS-IPUSegmentation program.

        @return number of files processed successfully

        """
        # Initializations
        step = self.parameters.get_step(stepidx)
        stepname = self.parameters.get_step_name(stepidx)
        files_processed_success = 0
        self._progress.set_header(stepname)
        self._progress.update(0,"")

        # Get the list of input file names, with the ".wav" extension
        filelist = self.set_filelist(".wav")
        if len(filelist) == 0:
            return 0
        total = len(filelist)

        # Create annotation instance, and fix options
        try:
            seg = sppasSeg(self._logfile)
        except Exception as e:
            if self._logfile is not None:
                self._logfile.print_message( "%s\n"%str(e), indent=1,status=1 )
            return 0

        # Execute the annotation for each file in the list
        for i,f in enumerate(filelist):

            # fix the default values
            seg.fix_options( step.get_options() )

            # Indicate the file to be processed
            if self._logfile is not None:
                self._logfile.print_message(stepname+" of file "+f, indent=1 )
            self._progress.set_text( os.path.basename(f)+" ("+str(i+1)+"/"+str(total)+")" )

            # Fix input/output file name
            outname = os.path.splitext(f)[0] + self.parameters.get_output_format()

            # Is there already an existing IPU-seg (in any format)!
            existoutname = self._get_filename(f, ['.xra', '.TextGrid', '.eaf', '.csv', '.mrk' ])

            # it's existing... but not in the expected format: convert!
            if existoutname is not None and existoutname != outname:
                # just copy the file!
                if self._logfile is not None:
                    self._logfile.print_message('Export '+existoutname, indent=2)
                    self._logfile.print_message('into '+outname, indent=2)
                try:
                    t = annotationdata.io.read(existoutname)
                    annotationdata.io.write(outname,t)
                    # OK, now outname is as expected! (or not...)
                except Exception:
                    pass

            # Execute annotation
            tgfname = utils.fileutils.exists(outname)
            if tgfname is None:
                # No already existing IPU seg., but perhaps a txt.
                txtfile = self._get_filename(f, [".txt"])
                if self._logfile is not None:
                    if txtfile:
                        self._logfile.print_message("A transcription was found, perform Silence/Speech segmentation time-aligned with a transcription %s"%txtfile, indent=2,status=3)
                    else:
                        self._logfile.print_message("No transcription was found, perform Silence/Speech segmentation only.", indent=2,status=3)
                try:
                    seg.run(f, trsinputfile=txtfile, ntracks=None, diroutput=None, tracksext=None, listoutput=None, textgridoutput=outname)
                    files_processed_success += 1
                    if self._logfile is not None:
                        self._logfile.print_message(outname, indent=2,status=0)
                except Exception as e:
                    if self._logfile is not None:
                        self._logfile.print_message( "%s for file %s\n"%(str(e),outname), indent=2,status=-1 )
            else:
                if seg.get_dirtracks() is True:
                    self._logfile.print_message("A time-aligned transcription was found, split into multiple files", indent=2,status=3)
                    try:
                        seg.run(f, trsinputfile=tgfname, ntracks=None, diroutput=None, tracksext=None, listoutput=None, textgridoutput=None)
                        files_processed_success += 1
                        if self._logfile is not None:
                            self._logfile.print_message(tgfname, indent=2,status=0 )
                    except Exception as e:
                        if self._logfile is not None:
                            self._logfile.print_message( "%s for file %s\n"%(str(e),tgfname), indent=2,status=-1 )
                else:
                    if self._logfile is not None:
                        self._logfile.print_message( "because a previous segmentation is existing.", indent=2,status=2 )

            # Indicate progress
            self._progress.set_fraction(float((i+1))/float(total))
            if self._logfile is not None:
                self._logfile.print_newline()

        # Indicate completed!
        self._progress.update(1,"Completed (%d files successfully over %d files).\n"%(files_processed_success,total))
        self._progress.set_header("")

        return files_processed_success

    # End run_ipusegmentation
    # ------------------------------------------------------------------------


    def run_tokenization(self, stepidx):
        """
        Execute the SPPAS-Tokenization program.

        @return number of files processed successfully

        """
        # Initializations
        step = self.parameters.get_step(stepidx)
        stepname = self.parameters.get_step_name(stepidx)
        files_processed_success = 0
        self._progress.set_header(stepname)
        self._progress.update(0,"")

        # Get the list of input file names, with the ".wav" (or ".wave") extension
        filelist = self.set_filelist(".wav",not_start=["track_"])
        if len(filelist) == 0:
            return 0
        total = len(filelist)

        # Create annotation instance
        try:
            self._progress.set_text("Loading resources...")
            t = sppasTok( step.get_langresource(), logfile=self._logfile, lang=step.get_lang() )
        except Exception as e:
            if self._logfile is not None:
                self._logfile.print_message( "%s\n"%str(e), indent=1,status=1 )
            return 0

        # Execute the annotation for each file in the list
        for i,f in enumerate(filelist):

            # fix the default values
            t.fix_options( step.get_options() )

            # Indicate the file to be processed
            self._progress.set_text( os.path.basename(f)+" ("+str(i+1)+"/"+str(total)+")" )
            if self._logfile is not None:
                self._logfile.print_message(stepname+" of file " + f, indent=1 )

            # Get the input file
            inname = self._get_filename(f, [self.parameters.get_output_format(), '.xra', '.TextGrid', '.eaf', '.trs', '.csv', '.mrk'])
            if inname is not None:

                # Fix output file name
                outname = os.path.splitext(f)[0] + '-token' + self.parameters.get_output_format()

                # Execute annotation
                try:
                    t.run( inname, outputfile=outname )
                except Exception as e:
                    if self._logfile is not None:
                        self._logfile.print_message( "%s for file %s\n"%(str(e),outname), indent=2,status=-1 )
                else:
                    files_processed_success += 1
                    if self._logfile is not None:
                        self._logfile.print_message(outname, indent=2,status=0 )

            else:
                if self._logfile is not None:
                    self._logfile.print_message("Failed to find a file with transcription. Read the documentation for details.",indent=2,status=2)

            # Indicate progress
            self._progress.set_fraction(float((i+1))/float(total))
            if self._logfile is not None:
                self._logfile.print_newline()

        # Indicate completed!
        self._progress.update(1,"Completed (%d files successfully over %d files).\n"%(files_processed_success,total))
        self._progress.set_header("")

        return files_processed_success

    # End run_tokenization
    # ------------------------------------------------------------------------


    def run_phonetization(self, stepidx):
        """
        Execute the SPPAS-Phonetization program.

        @return number of files processed successfully

        """
        # Initializations
        step = self.parameters.get_step(stepidx)
        stepname = self.parameters.get_step_name(stepidx)
        files_processed_success = 0
        self._progress.set_header(stepname)
        self._progress.update(0,"")

        # Get the list of input file names, with the ".wav" (or ".wave") extension
        filelist = self.set_filelist(".wav",not_start=["track_"])
        if len(filelist) == 0:
            return 0
        total = len(filelist)

        # Create annotation instance
        try:
            self._progress.set_text("Loading resources...")
            p = sppasPhon( step.get_langresource(), logfile=self._logfile )
        except Exception as e:
            if self._logfile is not None:
                stre = unicode(e.message).encode("utf-8")
                self._logfile.print_message( "%s\n"%stre, indent=1,status=1 )
            return 0

        # Execute the annotation for each file in the list
        for i,f in enumerate(filelist):

            # fix the default values
            p.fix_options( step.get_options() )

            # Indicate the file to be processed
            self._progress.set_text( os.path.basename(f)+" ("+str(i+1)+"/"+str(total)+")" )
            if self._logfile is not None:
                self._logfile.print_message(stepname+" of file " + f, indent=1)

            # Get the input file
            inname = self._get_filename(f, ['-token'+self.parameters.get_output_format(), '-token.xra', '-token.TextGrid', '-token.eaf', '-token.csv', '-token.mrk'])
            if inname is not None:

                # Fix output file name
                outname = os.path.splitext(f)[0] + '-phon' + self.parameters.get_output_format()

                # Execute annotation
                try:
                    p.run( inname, outputfile=outname )
                except Exception as e:
                    if self._logfile is not None:
                        self._logfile.print_message( "%s for file %s\n"%(str(e),outname), indent=2,status=-1 )
                else:
                    files_processed_success += 1
                    if self._logfile is not None:
                        self._logfile.print_message(outname, indent=2,status=0 )

            else:
                if self._logfile is not None:
                    self._logfile.print_message("Failed to find a file with toketization. Read the documentation for details.",indent=2,status=2)

            # Indicate progress
            self._progress.set_fraction(float((i+1))/float(total))
            if self._logfile is not None:
                self._logfile.print_newline()

        # Indicate completed!
        self._progress.update(1,"Completed (%d files successfully over %d files).\n"%(files_processed_success,total))
        self._progress.set_header("")

        return files_processed_success

    # End run_phonetization
    # ------------------------------------------------------------------------


    def run_alignment(self, stepidx):
        """
        Execute the SPPAS-Alignment program.

        """
        # Initializations
        step = self.parameters.get_step(stepidx)
        stepname = self.parameters.get_step_name(stepidx)
        files_processed_success = 0
        self._progress.set_header(stepname)
        self._progress.update(0,"")

        # Get the list of input file names, with the ".wav" (or ".wave") extension
        filelist = self.set_filelist(".wav",not_start=["track_"])
        if len(filelist) == 0:
            return 0
        total = len(filelist)

        # Create annotation instance
        try:
            a = sppasAlign( step.get_langresource(), logfile=self._logfile )
        except Exception as e:
            if self._logfile is not None:
                self._logfile.print_message( "%s\n"%str(e), indent=1,status=1 )
            return 0

        # Execute the annotation for each file in the list
        for i,f in enumerate(filelist):

            # fix the default values
            a.fix_options( step.get_options() )

            # Indicate the file to be processed
            self._progress.set_text( os.path.basename(f)+" ("+str(i+1)+"/"+str(total)+")" )
            if self._logfile is not None:
                self._logfile.print_message(stepname+" of file " + f, indent=1 )

            # Get the input file
            inname = self._get_filename(f, ['-phon'+self.parameters.get_output_format(), '-phon.xra', '-phon.TextGrid', '-phon.eaf', '-phon.csv', '-phon.mrk'])
            intok = self._get_filename(f, ['-token'+self.parameters.get_output_format(), '-token.xra', '-token.TextGrid', '-token.eaf', '-token.csv', '-token.mrk'])
            if inname is not None:

                # Fix output file name
                outname = os.path.splitext(f)[0] + '-palign' + self.parameters.get_output_format()

                # Execute annotation
                try:
                    a.run( inname, intok, f, outputfilename=outname )
                except Exception as e:
                    if self._logfile is not None:
                        stre = unicode(e.message).encode("utf-8")
                        self._logfile.print_message( "%s for file %s\n"%(stre,outname), indent=2,status=-1 )
                else:
                    files_processed_success += 1
                    if self._logfile is not None:
                        self._logfile.print_message(outname, indent=2,status=0 )

            else:
                if self._logfile is not None:
                    self._logfile.print_message("Failed to find a file with phonetization. Read the documentation for details.",indent=2,status=2)

            # Indicate progress
            self._progress.set_fraction(float((i+1))/float(total))
            if self._logfile is not None:
                self._logfile.print_newline()

        # Indicate completed!
        self._progress.update(1,"Completed (%d files successfully over %d files).\n"%(files_processed_success,total))
        self._progress.set_header("")

        return files_processed_success

    # End run_alignment
    # ------------------------------------------------------------------------


    def run_syllabification(self, stepidx):
        """
        Execute the SPPAS syllabification.

        """
        # Initializations
        step = self.parameters.get_step(stepidx)
        stepname = self.parameters.get_step_name(stepidx)
        files_processed_success = 0
        self._progress.set_header(stepname)
        self._progress.update(0,"")

        # Get the list of input file names, with the ".wav" (or ".wave") extension
        filelist = self.set_filelist(".wav",not_start=["track_"])
        if len(filelist) == 0:
            return 0
        total = len(filelist)

        # Create annotation instance
        try:
            s = sppasSyll( step.get_langresource(), self._logfile )
        except Exception as e:
            if self._logfile is not None:
                self._logfile.print_message( "%s\n"%str(e), indent=1,status=1 )
            return 0

        for i,f in enumerate(filelist):

            # fix the default values
            s.fix_options( step.get_options() )

            # Indicate the file to be processed
            self._progress.set_text( os.path.basename(f)+" ("+str(i+1)+"/"+str(total)+")" )
            if self._logfile is not None:
                self._logfile.print_message(stepname+" of file " + f, indent=1 )

            # Get the input file
            inname = self._get_filename(f, ['-palign'+self.parameters.get_output_format(), '-palign.xra', '-palign.TextGrid', '-palign.eaf', '-palign.csv', '-palign.mrk'])
            if inname is not None:

                # Fix output file name
                outname = os.path.splitext(f)[0] + '-salign' + self.parameters.get_output_format()

                # Execute annotation
                try:
                    s.run( inname, outputfilename=outname )
                except Exception as e:
                    if self._logfile is not None:
                        self._logfile.print_message( "%s for file %s\n"%(str(e),outname), indent=2,status=-1 )
                else:
                    files_processed_success += 1
                    if self._logfile is not None:
                        self._logfile.print_message(outname, indent=2,status=0 )
            else:
                if self._logfile is not None:
                    self._logfile.print_message("Failed to find a file with time-aligned phonemes. Read the documentation for details.",indent=2,status=2)

            # Indicate progress
            self._progress.set_fraction(float((i+1))/float(total))
            if self._logfile is not None:
                self._logfile.print_newline()

        # Indicate completed!
        self._progress.update(1,"Completed (%d files successfully over %d files).\n"%(files_processed_success,total))
        self._progress.set_header("")

        return files_processed_success

    # End run_syllabification
    # ------------------------------------------------------------------------


    def run_repetition(self, stepidx):
        """
        Execute the automatic repetitions detection.

        """
        # Initializations
        step = self.parameters.get_step(stepidx)
        stepname = self.parameters.get_step_name(stepidx)
        files_processed_success = 0
        self._progress.set_header(stepname)
        self._progress.update(0,"")

        # Get the list of input file names, with the ".wav" (or ".wave") extension
        filelist = self.set_filelist(".wav",not_start=["track_"])
        if len(filelist) == 0:
            return 0
        total = len(filelist)

        # Create annotation instance
        try:
            self._progress.set_text("Loading resources...")
            r = sppasRepetition( step.get_langresource(), self._logfile )
        except Exception as e:
            if self._logfile is not None:
                self._logfile.print_message( "%s\n"%str(e), indent=1,status=1 )
            return 0

        for i,f in enumerate(filelist):

            # fix the default values
            r.fix_options( step.get_options() )

            # Indicate the file to be processed
            self._progress.set_text( os.path.basename(f)+" ("+str(i+1)+"/"+str(total)+")" )
            if self._logfile is not None:
                self._logfile.print_message(stepname+" of file " + f, indent=1 )

            # Get the input file
            inname = self._get_filename(f, ['-palign'+self.parameters.get_output_format(), '-palign.xra', '-palign.TextGrid', '-palign.eaf', '-palign.csv', '-palign.mrk'])
            if inname is not None:

                # Fix output file name
                outname = os.path.splitext(f)[0] + '-ralign' + self.parameters.get_output_format()

                # Execute annotation
                try:
                    r.run( inname, outputfilename=outname )
                except Exception as e:
                    if self._logfile is not None:
                        self._logfile.print_message( "%s for file %s\n"%(str(e),outname), indent=2,status=-1 )
                else:
                    files_processed_success += 1
                    if self._logfile is not None:
                        self._logfile.print_message(outname, indent=2,status=0 )
            else:
                if self._logfile is not None:
                    self._logfile.print_message("Failed to find a file with time-aligned tokens. Read the documentation for details.",indent=2,status=2)

            # Indicate progress
            self._progress.set_fraction(float((i+1))/float(total))
            if self._logfile is not None:
                self._logfile.print_newline()

        # Indicate completed!
        self._progress.update(1,"Completed (%d files successfully over %d files).\n"%(files_processed_success,total))
        self._progress.set_header("")

        return files_processed_success

    # End run_repetition
    # ------------------------------------------------------------------------


    def __add_trs(self, trs, trsinputfile):
        trsinput = annotationdata.io.read( trsinputfile )
        try:
            for tier in trsinput:
                alreadin = False
                if trs.IsEmpty() is False:
                    tiername = tier.GetName()
                    for t in trs:
                        if t.GetName() == tiername:
                            alreadin = True
                if alreadin is False:
                    trs.Add(tier)
        except Exception as e:
            raise Exception(str(e))

    # ------------------------------------------------------------------------


    def merge(self):
        """
        Merge all annotated files.
        Create a TextGrid.

        """

        self._progress.set_header("Create a merged TextGrid file...")
        self._progress.update(0,"")

        # Get the list of files with the ".wav" extension
        filelist = self.set_filelist(".wav", ["track_"])
        total = len(filelist)

        output_format = self.parameters.get_output_format()
        for i,f in enumerate(filelist):

            nbfiles = 0

            # Change f, to allow "replace" to work properly
            basef = os.path.splitext(f)[0]

            if self._logfile is not None:
                self._logfile.print_message("Merge outputs " + f, indent=1 )
            self._progress.set_text( os.path.basename(f)+" ("+str(i+1)+"/"+str(total)+")" )

            trs = Transcription()
            try:
                self.__add_trs(trs, basef + output_format) # Transcription
                nbfiles = nbfiles + 1
            except Exception:
                pass
            try:
                self.__add_trs(trs, basef + "-token" + output_format) # Tokenization
                nbfiles = nbfiles + 1
            except Exception:
                pass
            try:
                self.__add_trs(trs, basef + "-phon" + output_format) # Phonetization
                nbfiles = nbfiles + 1
            except Exception:
                pass
            try:
                self.__add_trs(trs, basef + "-palign" + output_format) # PhonAlign, TokensAlign
                nbfiles = nbfiles + 1
            except Exception:
                pass
            try:
                self.__add_trs(trs, basef + "-salign" + output_format) # Syllables
                nbfiles = nbfiles + 1
            except Exception:
                pass
            try:
                self.__add_trs(trs, basef + "-ralign" + output_format) # Repetitions
                nbfiles = nbfiles + 1
            except Exception:
                pass
            try:
                self.__add_trs(trs, basef + "-momel.TextGrid") # Momel, INTSINT
                nbfiles = nbfiles + 1
            except Exception:
                pass

            try:
                if nbfiles > 1:
                    tier = Tier("Information")
                    _e = trs.GetEnd()
                    label = "This annotation was produced by " + program + " " + version + " on " + str(datetime.date.today())
                    tier.Append(Annotation(TimeInterval(TimePoint(trs.GetBegin()), TimePoint(float(_e)/2.0)), Label(label)))
                    tier.Append(Annotation(TimeInterval(TimePoint((float(_e)/2.0)), TimePoint(_e)), Label(copyright)))
                    trs.Add(tier)
                    annotationdata.io.write( basef + "-merge.TextGrid", trs)
                    if self._logfile is not None:
                        self._logfile.print_message( basef + "-merge.TextGrid", indent=2,status=0)
                elif self._logfile is not None:
                    self._logfile.print_message( "", indent=2,status=2 )
            except Exception as e:
                if self._logfile is not None:
                    self._logfile.print_message( str(e), indent=2,status=-1)

            self._progress.set_fraction(float((i+1))/float(total))
            if self._logfile is not None:
                self._logfile.print_newline()

        self._progress.update(1,"Completed.")
        self._progress.set_header("")

    # End merge
    # ------------------------------------------------------------------------


    def run_annotations(self, progress):
        """
        Execute activated SPPAS steps.
        Get execution information from the 'parameters' object.

        """
        self._progress = progress

        # ##################################################################### #
        # Steps validation
        # ##################################################################### #
        for step in range(self.parameters.get_step_numbers()):
            if self.parameters.get_langresourcetype(step)=="directory":
                if self.parameters.get_langresource(step)=="None" or not os.path.exists(self.parameters.get_langresource(step)):
                    self.parameters.disable_step(step)
            elif self.parameters.get_langresourcetype(step)=="file":
                if self.parameters.get_langresource(step)=="None" or not os.path.isfile(self.parameters.get_langresource(step)):
                    self.parameters.disable_step(step)

        # ##################################################################### #
        # Print header message in the log file
        # ##################################################################### #
        try:
            self._logfile = sppasLog( self.parameters )
            self._logfile.open_new( self.parameters.get_logfilename() )
            self._logfile.print_header()
        except Exception:
            self._logfile=None
            pass

        # ##################################################################### #
        # Run!
        # ##################################################################### #
        nbruns = []
        steps = False

        for i in range( self.parameters.get_step_numbers() ):

            nbruns.append(-1)
            if self.parameters.get_step_status(i) is True:

                if self._logfile is not None:
                    self._logfile.print_step(i)

                if steps is False:
                    steps=True
                else:
                    self._progress.set_new()

                if self.parameters.get_step_key(i) == "momel":
                    nbruns[i] = self.run_momel(i)
                elif self.parameters.get_step_key(i) == "ipus":
                    nbruns[i] = self.run_ipusegmentation(i)
                elif self.parameters.get_step_key(i) == "tok":
                    nbruns[i] = self.run_tokenization(i)
                elif self.parameters.get_step_key(i) == "phon":
                    nbruns[i] = self.run_phonetization(i)
                elif self.parameters.get_step_key(i) == "align":
                    nbruns[i] = self.run_alignment(i)
                elif self.parameters.get_step_key(i) == "syll":
                    nbruns[i] = self.run_syllabification(i)
                elif self.parameters.get_step_key(i) == "repetition":
                    nbruns[i] = self.run_repetition(i)
                elif self._logfile is not None:
                    self._logfile.print_message('Unrecognized annotation step:%s'%self.parameters.get_step_name(i))

        if self._logfile is not None:
            self._logfile.print_separator()
            self._logfile.print_newline()
            self._logfile.print_separator()

        self.merge()

        # ##################################################################### #
        # Log file: Final information
        # ##################################################################### #
        if self._logfile is not None:
            self._logfile.print_separator()
            self._logfile.print_message('Result statistics:')
            self._logfile.print_separator()
            for i in range( self.parameters.get_step_numbers() ):
                self._logfile.print_stat( i,nbruns[i] )
            self._logfile.print_separator()
            self._logfile.close()


    # End run
    # ------------------------------------------------------------------------