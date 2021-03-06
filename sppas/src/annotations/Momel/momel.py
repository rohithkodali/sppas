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
# File: momel.py
# ----------------------------------------------------------------------------

import math

from st_cib import Targets
import momelutil

# ----------------------------------------------------------------------------

class Momel:
    """
    @author:       Brigitte Bigi
    @organization: Laboratoire Parole et Langage, Aix-en-Provence, France
    @contact:      brigitte.bigi@gmail.com
    @license:      GPL, v3
    @copyright:    Copyright (C) 2011-2016  Brigitte Bigi
    @summary:      A class to filter f0 and to modelize the melodie.

    """
    def __init__(self):
        """
        Create a new Momel instance.

        """
        # Constants
        self.SEUILV = 50.
        self.FSIGMA = 1.
        self.HALO_BORNE_TRAME = 4
        self.RAPP_GLITCH = 0.05
        self.ELIM_GLITCH = True

        # Create data structures with default values
        self.initialize()

        # Default Option values

        # cible window length (lfen1 est en pointes echantillon, pas milliseconds)
        self.lfen1 = 30
        # f0 threshold
        self.hzinf = 50
        # f0 ceiling (Hirst, Di Cristo et Espesser : hzsup est calcule automatiquement)
        self.hzsup = 600
        # maximum error (Maxec est 1+Delta en Hirst, Di Cristo et Espesser)
        self.maxec = 1.04
        # reduc window length (lfen2 est en pointes echantillon, pas milliseconds)
        self.lfen2 = 20
        # minimal distance (seuildiff_x est en pointes echantillon, pas milliseconds)
        self.seuildiff_x = 5
        # minimal frequency ratio
        self.seuilrapp_y = 0.05

    # -------------------------------------------------------------------

    def initialize(self):
        """ Set some variables to their default values.
            Parameters: None
            Return:     None
        """
        # Array of pitch values
        self.hzptr = []
        self.nval  = 0
        self.delta = 0.01

        # Output of cible:
        self.cib = []
        # Output of reduc:
        self.cibred = []
        # Output of reduc2:
        self.cibred2 = []

    # -------------------------------------------------------------------

    def set_pitch_array(self,arrayvals):
        self.hzptr = arrayvals
        self.nval = len(self.hzptr)

    def set_option_elim_glitch(self,activate=True):
        self.ELIM_GLITCH=activate

    def set_option_win1(self,val):
        self.lfen1 = val
        assert(self.lfen1 > 0)

    def set_option_lo(self,val):
        self.hzinf = val

    def set_option_hi(self,val):
        self.hzsup = val

    def set_option_maxerr(self,val):
        self.maxec = val

    def set_option_win2(self,val):
        self.lfen2 = val

    def set_option_mind(self,val):
        self.seuildiff_x = val

    def set_option_minr(self,val):
        self.seuilrapp_y = val

    # ------------------------------------------------------------------

    def elim_glitch(self):
        """ Eliminate Glitch of the pitch values array.
            Set a current pith value to 0 if left and right values
            are greater than 5% more than the current value.
            Parameters: None
            Return:     None
        """
        _delta = 1.0 + self.RAPP_GLITCH
        for i in range(1,self.nval-1):
            cur  = self.hzptr[i]
            gprec = self.hzptr[i-1] * _delta
            gnext = self.hzptr[i+1] * _delta
            if (cur > gprec and cur > gnext):
                self.hzptr[i] = 0.

    # ------------------------------------------------------------------

    def calcrgp(self,pond,dpx,fpx):
        """
        From inputs, estimates: a0, a1, a2.

        """
        pn = 0.
        sx = sx2 = sx3 = sx4 = sy = sxy = sx2y = 0.
        for ix in range(dpx,fpx+1):
            p = pond[ix]
            if (p != 0.):
                val_ix = float(ix)
                y   = self.hzptr[ix]
                x2  = val_ix * val_ix
                x3  = x2 * val_ix
                x4  = x2 * x2
                xy  = val_ix * y
                x2y = x2 * y

                pn   = pn  + p
                sx   = sx  + (p * val_ix)
                sx2  = sx2 + (p * x2)
                sx3  = sx3 + (p * x3)
                sx4  = sx4 + (p * x4)
                sy   = sy  + (p * y)
                sxy  = sxy + (p * xy)
                sx2y = sx2y + (p * x2y)

        if (pn < 3.):
            raise ValueError('pn < 3')

        spdxy  = sxy  - (sx * sy) / pn
        spdx2  = sx2  - (sx * sx) / pn
        spdx3  = sx3  - (sx * sx2) / pn
        spdx4  = sx4  - (sx2 * sx2) / pn
        spdx2y = sx2y - (sx2 * sy) / pn

        muet = (spdx2 * spdx4) - (spdx3 * spdx3)
        if (spdx2 == 0. or muet == 0.):
            raise ValueError('spdx2 == 0. or muet == 0.')

        self.a2 = (spdx2y * spdx2 - spdxy * spdx3) / muet
        self.a1 = (spdxy - self.a2 * spdx3) / spdx2
        self.a0 = (sy - self.a1 * sx - self.a2 * sx2) / pn

    # ------------------------------------------------------------------

    def cible(self):
        """
        Find momel target points.

        """
        if len(self.hzptr)==0:
            raise IOError('Momel::momel.py. IOError: empty pitch array')
        if (self.hzsup < self.hzinf):
            raise ValueError('Momel::momel.py. Options error: F0 ceiling > F0 threshold')

        pond = []
        pondloc = [] # local copy of pond
        hzes = []
        for ix in range(self.nval):
            hzes.append(0.)
            if (self.hzptr[ix] > self.SEUILV):
                pond.append(1.0)
                pondloc.append(1.0)
            else:
                pond.append(0.0)
                pondloc.append(0.0)

        # Examinate each pitch value
        for ix in range(self.nval):
            # Current interval to analyze: from dpx to fpx
            dpx = ix - int(self.lfen1 / 2)
            fpx = dpx + self.lfen1 + 1


            # BB: do not go out of the range!
            if dpx < 0:
                dpx = 0
            if fpx > self.nval:
                fpx = self.nval

            # copy original pond values for the current interval
            for i in range(dpx,fpx):
                pondloc[i] = pond[i]

            nsup  = 0
            nsupr = -1
            xc = yc = 0.0
            ret_rgp = True
            while nsup > nsupr:
                nsupr = nsup
                nsup  = 0
                try:
                    # Estimate values of: a0, a1, a2
                    self.calcrgp(pondloc, dpx, fpx-1)
                except Exception:
                    # if calcrgp failed.
                    #print "calcrgp failed: ",e
                    ret_rgp=False
                    break
                else:
                    # Estimate hzes
                    for ix2 in range(dpx,fpx):
                        hzes[ix2] = self.a0 + (self.a1 + self.a2 * float(ix2)) * float(ix2)
                    for x in range(dpx,fpx):
                        if (self.hzptr[x] == 0. or (hzes[x] / self.hzptr[x]) > self.maxec):
                            nsup = nsup + 1
                            pondloc[x] = 0.0

            # Now estimate xc and yc for the new 'cible'
            if (ret_rgp==True and self.a2 != 0.0):
                vxc = (0.0 - self.a1) / (self.a2 + self.a2)
                if ((vxc > ix - self.lfen1) and (vxc < ix + self.lfen1)):
                    vyc = self.a0 + (self.a1 + self.a2 * vxc) * vxc
                    if (vyc > self.hzinf and vyc < self.hzsup):
                        xc = vxc
                        yc = vyc

            c = Targets()
            c.set(xc,yc)
            self.cib.append(c)

    # ------------------------------------------------------------------

    def reduc(self):
        """
        First target reduction of too close points.

        """
        # initialisations
        # ---------------
        xdist = []
        ydist = []
        dist  = []
        for i in range(self.nval):
            xdist.append(-1.)
            ydist.append(-1.)
            dist.append(-1.)

        lf  = int(self.lfen2 / 2)
        xds = yds = 0.
        np  = 0

        # xdist and ydist estimations
        for i in range(self.nval-1):
            # j1 and j2 estimations (interval min and max values)
            j1 = 0
            if (i > lf):
                j1 = i - lf
            j2 = self.nval - 1
            if (i+lf < self.nval-1):
                j2 = i + lf

            # left (g means left)
            sxg = syg = 0.
            ng = 0
            for j in range(j1,i+1):
                if (self.cib[j].get_y() > self.SEUILV):
                    sxg = sxg + self.cib[j].get_x()
                    syg = syg + self.cib[j].get_y()
                    ng = ng + 1

            # right (d means right)
            sxd = syd = 0.
            nd = 0
            for j in range(i+1,j2):
                if (self.cib[j].get_y() > self.SEUILV):
                    sxd = sxd + self.cib[j].get_x()
                    syd = syd + self.cib[j].get_y()
                    nd = nd + 1

            # xdist[i] and ydist[i] evaluations
            if (nd * ng > 0):
                xdist[i] = math.fabs (sxg / ng - sxd / nd)
                ydist[i] = math.fabs (syg / ng - syd / nd)
                xds = xds + xdist[i]
                yds = yds + ydist[i]
                np = np + 1
        # end for

        if np==0 or xds==0. or yds==0.:
            raise ValueError('Not enough targets with a value more than '+str(self.SEUILV)+' hz \n')


        # dist estimation (on pondere par la distance moyenne)
        # ----------------------------------------------------
        px = float(np) / xds
        py = float(np) / yds
        for i in range(self.nval):
            if (xdist[i] > 0.):
                dist[i] = (xdist[i] * px + ydist[i] * py) / (px + py)

        # Cherche les maxs des pics de dist > seuil
        # -----------------------------------------
        # Seuil = moy des dist ponderees
        seuil = 2. / (px + py)

        susseuil = False
        # Add the start value (=0)
        xd = []
        xd.append(0)
        xmax = 0

        for i in range(self.nval):
            if (len(xd) > int(self.nval/2)):
                raise Exception('Too many partitions (',len(xd),')\n')
            if (susseuil == False):
                if (dist[i] > seuil):
                    susseuil = True
                    xmax = i
            else:
                if (dist[i] > dist[xmax]):
                    xmax = i
                if (dist[i] < seuil and xmax > 0):
                    xd.append(xmax)
                    susseuil = False
        # end for
        # do not forget the last analyzed value!
        if (susseuil == True):
            xd.append(xmax)
        # Add the final value (=nval)
        xd.append(self.nval)

        # Partition sur les x
        # -------------------
        for ip in range(len(xd)-1):
            # bornes partition courante
            parinf = xd[ip]
            parsup = xd[ip + 1]

            sx = sx2 = sy = sy2 = 0.
            n = 0

            # moyenne sigma
            for j in range(parinf,parsup):
                # sur la pop d'une partition
                if (self.cib[j].get_y() > 0.):
                    sx  = sx  + self.cib[j].get_x()
                    sx2 = sx2 + self.cib[j].get_x() * self.cib[j].get_x()
                    sy  = sy  + self.cib[j].get_y()
                    sy2 = sy2 + self.cib[j].get_y() * self.cib[j].get_y()
                    n = n + 1

            # pour la variance
            if (n > 1):
                xm = float(sx) / float(n)
                ym = float(sy) / float(n)
                varx = float(sx2) / float(n) - xm * xm
                vary = float(sy2) / float(n) - ym * ym

                if (varx <= 0.):
                # cas ou variance devrait etre == +epsilon
                    varx = 0.1
                if (vary <= 0.):
                    vary = 0.1

                et2x = self.FSIGMA * math.sqrt (varx)
                et2y = self.FSIGMA * math.sqrt (vary)
                seuilbx = xm - et2x
                seuilhx = xm + et2x
                seuilby = ym - et2y
                seuilhy = ym + et2y

                #  Elimination (set cib to 0)
                for j in range(parinf,parsup):
                    if (self.cib[j].get_y() > 0. and (self.cib[j].get_x() < seuilbx or self.cib[j].get_x() > seuilhx or self.cib[j].get_y() < seuilby or self.cib[j].get_y() > seuilhy)):
                        self.cib[j].set_x(0.)
                        self.cib[j].set_y(0.)

            # Recalcule moyennes
            # ------------------
            sx = sy = 0.
            n = 0
            for j in range(parinf,parsup):
                if (self.cib[j].get_y() > 0.):
                    sx = sx + self.cib[j].get_x()
                    sy = sy + self.cib[j].get_y()
                    n = n + 1

            # Reduit la liste des cibles
            if (n > 0):
                cibred_cour = Targets()
                cibred_cour.set(sx/n, sy/n, n)
                ncibr = len(self.cibred) - 1

                if (ncibr < 0 ):
                    ncibr = 0
                    self.cibred.append(cibred_cour)
                else:
                    # si les cibred[].x ne sont pas strictement croissants
                    # on ecrase  la cible ayant le poids le moins fort
                    if (cibred_cour.get_x() > self.cibred[ncibr].get_x()):
                        # 1 cibred en +  car t croissant
                        ncibr = ncibr + 1
                        self.cibred.append(cibred_cour)
                    else:
                        # t <= precedent
                        if (cibred_cour.get_p() > self.cibred[ncibr].get_p()):
                            # si p courant >, ecrase la precedente
                            self.cibred[ncibr].set(cibred_cour.get_x(),cibred_cour.get_y(),cibred_cour.get_p())
        # end For ip

    # ------------------------------------------------------------------

    def reduc2(self):
        """ reduc2.
            2eme filtrage des cibles trop proches en t [et Hz]
        """
        # classe ordre temporel croissant les cibred
        c = momelutil.quicksortcib(self.cibred)
        self.cibred = c

        self.cibred2.append(self.cibred[0])
        pnred2 = 0
        assert(self.seuilrapp_y > 0.)
        ncibr_brut = len(self.cibred)
        for i in range(1,ncibr_brut):
            delta_x = self.cibred[i].get_x() - self.cibred2[pnred2].get_x()
            if(float(delta_x) < float(self.seuildiff_x)):
                if ( math.fabs( float((self.cibred[i].get_y() - self.cibred2[pnred2].get_y()) ) / self.cibred2[pnred2].get_y())  < self.seuilrapp_y ):
                    self.cibred2[pnred2].set_x( (self.cibred2[pnred2].get_x() + self.cibred[i].get_x())/2. )
                    self.cibred2[pnred2].set_y( (self.cibred2[pnred2].get_y() + self.cibred[i].get_y())/2. )
                    self.cibred2[pnred2].set_p( (self.cibred2[pnred2].get_p() + self.cibred[i].get_p()) )
                else:
                    if (self.cibred2[pnred2].get_p() < self.cibred[i].get_p()):
                        self.cibred2[pnred2].set(self.cibred[i].get_x(),self.cibred[i].get_y(),self.cibred[i].get_p())
            else:
                pnred2 = pnred2 + 1
                self.cibred2.append( self.cibred[i] )

    # ------------------------------------------------------------------

    def borne(self):
        """ borne.
            Principes:
            calcul borne G (D)  si 1ere (derniere) cible est
            ( > (debut_voisement+halo) )
            ( < (fin_voisement -halo)  )
            ce pt de debut(fin) voisement  == frontiere
            cible extremite == ancre
            regression quadratique sur Hz de  [frontiere ancre]
        """
        halo = self.HALO_BORNE_TRAME
        ancre = Targets()
        borne = Targets()

        # Borne gauche
        # ------------

        # Recherche 1er voise
        premier_voise=0
        while(premier_voise < self.nval and self.hzptr[premier_voise] < self.SEUILV):
            premier_voise = premier_voise + 1

        if( int(self.cibred2[0].get_x()) > (premier_voise + halo) ):
            # origine des t : ancre.x, et des y : ancre.y
            ancre = self.cibred2[0]

            sx2y = 0.
            sx4  = 0.

            j = 0
            for i in range( int(ancre.get_x()),0):
                if (self.hzptr[i] > self.SEUILV):
                    x2 = float(j)*float(j)
                    sx2y = sx2y + (x2* (self.hzptr[i] - ancre.get_y()))
                    sx4 = sx4 + (x2*x2)
                j = j + 1

            frontiere = float(premier_voise)
            a = 0.
            if sx4 > 0.:
                a = sx2y / sx4

            borne.set_x( frontiere - (ancre.get_x() - frontiere ) )
            borne.set_y( ancre.get_y() + (2 * a * (ancre.get_x() - frontiere)*(ancre.get_x() - frontiere)) )

        # recherche dernier voisement
        dernier_voise = self.nval - 1
        while ( dernier_voise >=0 and self.hzptr[dernier_voise] < self.SEUILV):
            dernier_voise = dernier_voise - 1


        # ################################################################## #

        #nred2 = len(self.cibred2)
        #if( int(self.cibred2[nred2-1].get_x()) < (dernier_voise - halo)):
            # origine des t : ancre.x, et des y : ancre.y
            #ancre = self.cibred2[nred2-1]

            #sx2y = 0.
            #sx4 = 0.
            #j = 0
            #for i in range( int(ancre.get_x()),self.nval):
                #if (self.hzptr[i] > self.SEUILV):
                    #x2 = float(j) * float(j)
                    #sx2y = sx2y + (x2 * (self.hzptr[i] - ancre.get_y()))
                    #sx4 = sx4 + (x2*x2)
                #j = j + 1
            #frontiere = float(dernier_voise)
            #a = 0.
            #if (sx4 > 0.):
                #a = sx2y / sx4

            #borne.set_x( frontiere + (frontiere - ancre.get_x()) )
            #borne.set_y( ancre.get_y() + (2. * a * (ancre.get_x() - frontiere)*(ancre.get_x() - frontiere)) )

    # ------------------------------------------------------------------

    def annotate(self, pitchvalues):
        """
        Apply momel from a vector of pitch values, one each 0.01 sec.

        Return a list.

        """
        # Get pitch values
        self.initialize()
        self.set_pitch_array( pitchvalues )

        if self.ELIM_GLITCH is True:
            self.elim_glitch()

        self.cible()
        self.reduc()
        if len(self.cibred) == 0:
            raise Exception("No left point after the first pass of point reduction.\n")

        self.reduc2()
        if len(self.cibred2) == 0:
            raise Exception("No left point after the second pass of point reduction.\n")

        self.borne()

        return self.cibred2

    # ------------------------------------------------------------------
