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

from hamcrest import is_
from nti.app.testing.application_webtest import ApplicationLayerTest
from hamcrest import assert_that
from nti.testing.matchers import is_empty
from hamcrest import is_not as does_not


from nti.testing.matchers import provides
from zope.event import notify
from ..interfaces import IPreferredLanguagesRequest
from zope.i18n.interfaces import IUserPreferredLanguages

from nti.dataserver.interfaces import IUser
import fudge

from pyramid.request import Request
from pyramid.events import ContextFound
def adjust(request):
	notify(ContextFound(request))



class TestApplicationRequestPolicy(ApplicationLayerTest):

	request = None

	def setUp(self):
		self.request = Request.blank('/')

	def _langs(self):
		return IUserPreferredLanguages(self.request).getPreferredLanguages()

	def test_adjust_interface_blank(self):
		# Initially, nothing
		adjust(self.request)
		assert_that( self.request, does_not(provides(IPreferredLanguagesRequest)) )
		assert_that( self._langs(), is_empty() )

	def test_adjust_zope_cookie(self):
		self.request.cookies['I18N_LANGUAGE'] = 'ru'
		adjust(self.request)
		assert_that( self._langs(), is_(['ru']))

	def test_adjust_pyramid_property(self):
		self.request._LOCALE_ = 'ru'
		adjust(self.request)
		assert_that( self._langs(), is_(['ru']))


	@fudge.patch('nti.app.i18n.subscribers.get_remote_user',
				 'nti.app.i18n.adapters.get_remote_user')
	def test_adjust_remote_user(self, fake_get1, fake_get2):
		@interface.implementer(IUserPreferredLanguages)
		class User(object):
			def getPreferredLanguages(self):
				return ['ru']

		fake_get1.is_callable().returns(User())
		fake_get2.is_callable().returns(User())

		adjust(self.request)
		assert_that( self._langs(), is_(['ru']))


	@fudge.patch('nti.app.i18n.subscribers.get_remote_user',
				 'nti.app.i18n.adapters.get_remote_user')
	def test_adjust_remote_user_default(self, fake_get1, fake_get2):
		@interface.implementer(IUser)
		class User(object):
			pass

		fake_get1.is_callable().returns(User())
		fake_get2.is_callable().returns(User())

		adjust(self.request)
		# The default, because there's no header and nothing
		# specified for this user, is empty (this would trigger
		# the translation domain fallback)
		assert_that( self._langs(), is_([]))


	@fudge.patch('nti.app.i18n.subscribers.get_remote_user',
				 'nti.app.i18n.adapters.get_remote_user')
	def test_adjust_remote_user_default(self, fake_get1, fake_get2):
		@interface.implementer(IUser)
		class User(object):
			pass

		fake_get1.is_callable().returns(User())
		fake_get2.is_callable().returns(User())

		self.request.environ[b'HTTP_ACCEPT_LANGUAGE'] = b'ru'
		adjust(self.request)
		# The accept header rules

		assert_that( self._langs(), is_(['ru']))
