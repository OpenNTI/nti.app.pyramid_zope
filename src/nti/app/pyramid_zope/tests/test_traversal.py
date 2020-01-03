#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tests for traversal.py.
"""
from __future__ import print_function, unicode_literals

import unittest

from zope import interface
from zope.traversing import interfaces as trv_interfaces

from pyramid.testing import DummyRequest

from hamcrest import assert_that
from hamcrest import has_entries
from hamcrest import is_

from . import ConfiguringLayer
from .. import traversal

class TestTraversal(unittest.TestCase):

    def test_unicode_traversal(self):
        # UnicodeEncodeError is specially handled
        # by the traversing machinery and doesn't raise
        # an error. (This is in zope.traversing.)

        # On Python 2, this was triggered in the real world by
        # attempting to access a non-ASCII attribute on an object
        # (which isn't allowed); this happened in the real world:
        #     getattr(self, u'\u2019', None) # Raise unicode error
        # On Python 3, though, that's fine and is
        # allowed. The UnicodEncodeError constructor takes lots of
        # parameters, so rather than instantiate directly, we
        # trigger it indirectly by encoding --- as Python2 would do.

        @interface.implementer(trv_interfaces.ITraversable)
        class BrokenTraversable(object):
            raised = False
            def traverse(self, name, furtherPath): # pylint:disable=unused-argument
                BrokenTraversable.raised = True
                return u'\u2019'.encode('ascii')

        @interface.implementer(trv_interfaces.ITraversable)
        class Root(object):
            def traverse(self, name, furtherPath):  # pylint:disable=unused-argument
                return BrokenTraversable()

        req = DummyRequest(path='/a/b/c')
        req.matchdict = {'traverse': ('a', 'b', 'c')}
        result = traversal.ZopeResourceTreeTraverser(Root())(req)

        self.assertTrue(BrokenTraversable.raised)

        assert_that(result, has_entries(
            context=is_(BrokenTraversable),
            root=is_(Root),
        ))

class TestConfiguration(unittest.TestCase):

    layer = ConfiguringLayer

    def test_configures(self):
        """
        Setting up the layer either works or fails.
        """
        # TODO: More specific tests
