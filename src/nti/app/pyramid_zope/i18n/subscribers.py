#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
I18N related subscribers.

.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component
from zope import interface

from zope.i18n.interfaces import IUserPreferredLanguages

from pyramid.interfaces import IContextFound
from pyramid.i18n import default_locale_negotiator

from nti.app.authentication import get_remote_user

from .interfaces import IPreferredLanguagesRequest

@component.adapter(IContextFound)
def _adjust_request_interface_for_preferred_languages(event):
	"""
	Checks the conditions outlined in this package's documentation
	and adds a marker interface to the request if they hold true.
	"""
	request = event.request

	# Does pyramid's default negotiator, which uses explicit settings
	# like a request param or cookie have an answer? If so, we need
	# our custom policy...these override the Accept-Language header

	if default_locale_negotiator(request):
		interface.alsoProvides(request, IPreferredLanguagesRequest)
		return

	# What about the zope/plone cookie?
	if request.cookies.get('I18N_LANGUAGE'):
		# For benefit of the default localization machinery
		# in case it's used, copy
		request._LOCALE_ = request.cookies.get('I18N_LANGUAGE')
		interface.alsoProvides(request, IPreferredLanguagesRequest)
		return

	# Ok, is there an authenticated user with preferred languages?
	# (We leave detecting defaults up to the actual policy)
	try:
		remote_user = get_remote_user(request)
	except LookupError:
		# If we're not in a site, we would get an
		# InappropriateSiteError here.
		# We've only actually seen this using pyramid_debugtoolbar
		# when handling an earlier exception of some type.
		# See also root_resource_factory...note that that place
		# specifically checks for the debug toolbar URL, with
		# request.path.startswith( '/_debug_toolbar/' ),
		# but I don't really feel like that's a necessary safety check
		# here
		remote_user = None

	remote_user_langs = remote_user is not None and IUserPreferredLanguages(remote_user)
	if remote_user_langs and remote_user_langs.getPreferredLanguages():
		interface.alsoProvides(request, IPreferredLanguagesRequest)
		return
