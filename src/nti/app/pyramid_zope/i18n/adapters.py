#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
I18N related adapters.

.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface
from zope import component

from zope.i18n.interfaces import IUserPreferredLanguages
from zope.i18n.interfaces import IModifiableUserPreferredLanguages
from zope.publisher.interfaces.browser import IBrowserRequest
from nti.dataserver.interfaces import IUser

from .interfaces import IPreferredLanguagesRequest

from pyramid.i18n import default_locale_negotiator

from nti.app.authentication import get_remote_user

# The user-based stuff will probably move around when we make it
# a mutable preference?

@interface.implementer(IUserPreferredLanguages)
@component.adapter(IUser)
class _UserPreferredLanguages(object):
	"""
	The preferred languages to use when externalizing for a particular
	user.

	.. todo:: Right now, this is hardcoded to english. We need to store this/derive from request.
	"""
	def __init__( self, context ):
		pass

	PREFERRED_LANGUAGES = ('en',)

	def getPreferredLanguages(self):
		return self.PREFERRED_LANGUAGES

# because this is hardcoded, we can be static for now
_user_preferred_languages = _UserPreferredLanguages(None)
@interface.implementer(IUserPreferredLanguages)
@component.adapter(IUser)
def UserPreferredLanguages(user):
	return _user_preferred_languages


@interface.implementer(IUserPreferredLanguages)
@component.adapter(IPreferredLanguagesRequest)
class PreferredLanguagesPolicy(object):
	"""
	Implements the preferred languages policy as documented for this
	package: an explicit request parameter or cookie will be used
	first, followed by something set during traversal, followed by a
	non-default persistent user preference, followed by the value set
	from the HTTP headers.
	"""

	def __init__(self, request):
		self.request = request

	def getPreferredLanguages(self):
		# If the default locale negotiater can get a value,
		# that means we had a parameter or one of the cookies
		# (because of the subscriber that gets us here).

		negotiated = default_locale_negotiator(self.request)
		if negotiated:
			return [negotiated]

		# Here is where we would check for something during traversal,
		# but we don't actually support that at this time because it
		# relies on implementation details

		# Is there a non-default user preference? Right now we know
		# what a default is due to implementation details above. We also
		# know for sure that we *have* a remote use, otherwise we wouldn't
		# be here
		remote_user = get_remote_user(self.request)
		remote_user_langs = IUserPreferredLanguages(remote_user).getPreferredLanguages()
		if remote_user_langs is not _UserPreferredLanguages.PREFERRED_LANGUAGES:
			return remote_user_langs

		# Ok, see what the HTTP request can come up with. Note that we're
		# going to the Zope interface so that we don't get into an infinite loop
		browser_request = IBrowserRequest(self.request)
		browser_langs = IModifiableUserPreferredLanguages(browser_request)
		return browser_langs.getPreferredLanguages()
