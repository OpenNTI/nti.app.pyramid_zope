#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""


.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

#disable: accessing protected members, too many methods
#pylint: disable=W0212,R0904

from zope import interface

import unittest
from hamcrest import assert_that

from hamcrest import is_not as does_not
from hamcrest import has_property

from nti.testing.matchers import provides

from ..interfaces import IPreferredLanguagesRequest
from zope.i18n.interfaces import IUserPreferredLanguages
from ..subscribers import _adjust_request_interface_for_preferred_languages as _adjust

import fudge

from pyramid.request import Request
from pyramid.events import ContextFound
def adjust(request):
	_adjust(ContextFound(request))

class TestSubscribers(unittest.TestCase):

	request = None

	def setUp(self):
		self.request = Request.blank('/')

	def test_adjust_interface_blank(self):
		# Initially, nothing
		adjust(self.request)
		assert_that( self.request, does_not(provides(IPreferredLanguagesRequest)) )

	def test_adjust_zope_cookie(self):
		self.request.cookies['I18N_LANGUAGE'] = 'ru'
		adjust(self.request)
		assert_that(self.request, provides(IPreferredLanguagesRequest))
		# It got copied to the request attribute too for benefit
		# of the default pyramid localizer
		assert_that(self.request, has_property('_LOCALE_', 'ru'))

	def test_adjust_pyramid_property(self):
		self.request._LOCALE_ = 'ru'
		adjust(self.request)
		assert_that(self.request, provides(IPreferredLanguagesRequest))

	@fudge.patch('nti.app.i18n.subscribers.get_remote_user')
	def test_adjust_remote_user(self, fake_get):
		@interface.implementer(IUserPreferredLanguages)
		class User(object):
			def getPreferredLanguages(self):
				return ['ru']

		fake_get.is_callable().returns(User())

		adjust(self.request)
		assert_that(self.request, provides(IPreferredLanguagesRequest))

	@fudge.patch('nti.app.i18n.subscribers.get_remote_user')
	def test_adjust_remote_user_raises(self, fake_get):
		from nti.dataserver.interfaces import InappropriateSiteError

		fake_get.is_callable().raises(InappropriateSiteError("Outside site"))

		adjust(self.request)
		assert_that(self.request, does_not(provides(IPreferredLanguagesRequest)))
