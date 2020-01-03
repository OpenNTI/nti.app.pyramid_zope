#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division

from nti.testing.layers import ZopeComponentLayer
from nti.testing.layers import ConfiguringLayerMixin

class ConfiguringLayer(ZopeComponentLayer,
                       ConfiguringLayerMixin):
    set_up_packages = ('nti.app.pyramid_zope',)

    @classmethod
    def setUp(cls):
        cls.setUpPackages()

    @classmethod
    def tearDown(cls):
        cls.tearDownPackages()

    @classmethod
    def testSetUp(cls):
        "Does nothing"

    testTearDown = testSetUp
