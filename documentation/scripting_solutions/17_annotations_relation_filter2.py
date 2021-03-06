#!/usr/bin python
"""

@author:       Brigitte Bigi
@date:         2016-May-07
@contact:      brigitte.bigi@gmail.com
@license:      GPL, v3
@copyright:    Copyright (C) 2016  Brigitte Bigi

@summary:      Open an annotated file and filter to answer the following request:
               get tokens either preceded by OR followed by a silence.
"""

import sys
import os
from os.path import *
sys.path.append( join("..","..", "sppas", "src") )

import annotationdata.aio
from annotationdata import Transcription
from annotationdata import Sel, Rel, Filter, SingleFilter, RelationFilter

# ----------------------------------------------------------------------------
# Variables
# ----------------------------------------------------------------------------

filename='F_F_B003-P9-merge.TextGrid'

# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------

# Read an annotated file.
trs = annotationdata.aio.read(filename)

# Get the expected tier
tier = trs.Find("TokensAlign", case_sensitive=False)
if tier is None:
    print "No tier", tiername, " in file ", filename
    sys.exit(1)

# Fix a radius, just to be sure that relations will be efficient!
tier.SetRadius(0.005)

# Create filters

# all tokens, except silences
# Caution: it also includes short pauses, laught, etc.
# Create filters
ft = Filter(tier)
fX = SingleFilter(~Sel(exact='#'),ft)
fY = SingleFilter(Sel(exact="#"),ft)

# Create relations (preceded by => meets) OR (followed by => metby)
relation = Rel('meets') | Rel('metby')

# Create the filter
frel = RelationFilter(relation,fX,fY)

# Create a tier with relations meets OR met by.
# Replace the label of the token by the name of the relation
# If both relations are true, relation' names are concatenated.
filteredtier = frel.Filter( annotformat="{rel}" )

# Print filtered annotations
for ann in filteredtier:
    print ann

# ----------------------------------------------------------------------------
