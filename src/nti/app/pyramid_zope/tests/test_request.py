#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import assert_that

from zope.publisher.interfaces.browser import IBrowserRequest

from pyramid.request import Request
from pyramid.interfaces import IRequest

from nti.testing.base import SharedConfiguringTestBase

from nti.testing.matchers import verifiably_provides

class TestRequest(SharedConfiguringTestBase):
	set_up_packages = (__name__,)
	def test_adapts(self):
		request = Request.blank('/')
		zrequest = IBrowserRequest( request )
		from zope import interface

		assert_that( zrequest, verifiably_provides(IBrowserRequest) )
		# and it's still a valid pyramid request
		assert_that( zrequest, verifiably_provides(IRequest) )
