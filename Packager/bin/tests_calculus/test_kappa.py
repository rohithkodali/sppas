#!/usr/bin/env python
# -*- coding:utf-8 -*-

import unittest
import os
import sys
import operator
from os.path import *

SPPAS = dirname(dirname(dirname(dirname(abspath(__file__)))))
sys.path.append(os.path.join(SPPAS, 'sppas', 'src'))

from annotationdata.annotation  import Annotation
from annotationdata.label.label import Label
from annotationdata.label.text  import Text
from annotationdata.ptime.interval import TimeInterval
from annotationdata.ptime.point import TimePoint
from annotationdata.tier        import Tier

from calculus.kappa import Kappa

class TestVectorKappa(unittest.TestCase):

    def setUp(self):
        self.p = [ (1.0,0.0) , (0.0,1.0) , (0.0,1.0) , (1.0,0.0) , (1.0,0.0) ]
        self.q = [ (1.0,0.0) , (0.0,1.0) , (1.0,0.0) , (1.0,0.0) , (1.0,0.0) ]

    def testkappa(self):
        kappa = Kappa(self.p,self.q)
        self.assertTrue(kappa.check_vector(self.p))
        self.assertTrue(kappa.check_vector(self.q))
        self.assertTrue(kappa.check()) # check both p and q
        self.assertFalse(kappa.check_vector([ (0.,1.) , (0.,1.,0.) ]))
        self.assertFalse(kappa.check_vector([ (0.0,0.1) ]))
        v = kappa.evaluate()
        self.assertEqual(0.54545, round(v,5))

class TestTierKappa(unittest.TestCase):

    def setUp(self):
        self.x = Annotation(TimeInterval(TimePoint(1,0.),   TimePoint(2,0.01)),    Label('toto'))
        self.y = Annotation(TimeInterval(TimePoint(3,0.01), TimePoint(4, 0.01 )),  Label('titi'))
        self.a = Annotation(TimeInterval(TimePoint(5,0.01), TimePoint(6.5,0.005)), Label('toto'))
        self.b = Annotation(TimeInterval(TimePoint(6.5,0.005), TimePoint(9.5,0.)), Label('toto'))
        self.tier = Tier()
        self.tier.Append(self.x)
        self.tier.Append(self.y)
        self.tier.Append(self.a)
        self.tier.Append(self.b)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestVectorKappa)
    unittest.TextTestRunner(verbosity=2).run(suite)