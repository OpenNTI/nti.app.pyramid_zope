#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
$Id$
"""
from __future__ import print_function, unicode_literals

#pylint: disable=R0904


from zope import interface
from zope.traversing import interfaces as trv_interfaces


#from pyramid.testing import DummyRequest
from nti.app.testing.request_response import ByteHeadersDummyRequest as DummyRequest

from .. import traversal

from nti.app.testing.layers import AppLayerTest

class TestTraversal(AppLayerTest):

	def test_unicode_traversal(self):

		@interface.implementer(trv_interfaces.ITraversable)
		class BrokenTraversable(object):
			raised = False
			def traverse( self, name, furtherPath ):
				BrokenTraversable.raised = True
				getattr( self, u'\u2019', None ) # Raise unicode error

		@interface.implementer(trv_interfaces.ITraversable)
		class DirectTraversable(object):
			def traverse( self, name, furtherPath ):
				return BrokenTraversable()

		req = DummyRequest(path='/a/b/c')
		req.matchdict = {'traverse': ('a','b','c')}
		traversal.ZopeResourceTreeTraverser( DirectTraversable() )( req )
		assert BrokenTraversable.raised
