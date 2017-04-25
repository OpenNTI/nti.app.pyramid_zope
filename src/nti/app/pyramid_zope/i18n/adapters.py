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

from zope.cachedescriptors.property import Lazy

from zope.i18n.interfaces import IUserPreferredLanguages
from zope.i18n.interfaces import IModifiableUserPreferredLanguages

from zope.publisher.interfaces.browser import IBrowserRequest

from pyramid.i18n import default_locale_negotiator

from nti.app.authentication import get_remote_user

from nti.dataserver.interfaces import IUser

from .interfaces import IPreferredLanguagesRequest

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

from zope.i18n.locales import locales
from zope.i18n.locales import LoadLocaleError

from pyramid.interfaces import ILocaleNegotiator

@interface.provider(ILocaleNegotiator)
def preferred_language_locale_negotiator(request):
	"""
	A pyramid locale negotiator that piggybacks off
	the preferred language support. We return a valid locale
	name consisting of at most language-territory, but at least language.
	A valid locale is one for which we have available locale data,
	not necessarily one for which any translation data is available.
	"""

	# This code is similar to that in zope.publisher.http.HTTPRequest.
	# it's point is to find the most specific available locale possible.
	# We differ in that, instead of returning a generic default, we
	# specifically return the english default. We also differ in that we
	# return a locale name instead of a locale object.

	result = _UserPreferredLanguages.PREFERRED_LANGUAGES[0]

	pref_langs = IUserPreferredLanguages(request, None)
	pref_langs = pref_langs.getPreferredLanguages() if pref_langs is not None else ()

	for lang in pref_langs:
		parts = (lang.split('-') + [None, None])[:3]
		try:
			locales.getLocale(*parts)
			result = lang
			break
		except LoadLocaleError:
			continue

	return result

import os

from zope.i18n.interfaces import ITranslationDomain

from pyramid.interfaces import ITranslationDirectories

@interface.implementer(ITranslationDirectories)
class ZopeTranslationDirectories(object):
	"""
	Implements the readable contract of Pyramid's translation directory
	list by querying for the zope translation domain objects. This way
	we don't have to repeat the configuration.

	.. note:: This queries just once, the first time it is used.

	.. note:: We lose the order or registrations, if that mattered.
	"""

	def __iter__(self):
		return iter(self._dirs)

	def __repr__(self):
		return repr(list(self))

	@Lazy
	def _dirs(self):
		dirs = []
		domains = component.getAllUtilitiesRegisteredFor(ITranslationDomain)
		for domain in domains:
			for paths in domain.getCatalogsInfo().values():
				# The catalog info is a dictionary of language to [file]
				if len(paths) == 1 and paths[0].endswith('.mo'):
					path = paths[0]
					# strip off the file, go to the directory containing the
					# language directories
					path = os.path.sep.join(path.split(os.path.sep)[:-3])
					if path not in dirs:
						dirs.append(path)
		return dirs
