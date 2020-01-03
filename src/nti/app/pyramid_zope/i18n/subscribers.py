# -*- coding: utf-8 -*-
"""
I18N related subscribers.

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from pyramid.i18n import default_locale_negotiator
from pyramid.interfaces import IContextFound

from zope import component
from zope import interface

from zope.i18n.interfaces import IUserPreferredLanguages
from zope.security.interfaces import IPrincipal
from zope.authentication.interfaces import IUnauthenticatedPrincipal

from .interfaces import IPreferredLanguagesRequest

__docformat__ = "restructuredtext en"

__all__ = [
    'adjust_request_interface_for_preferred_languages',
]




@component.adapter(IContextFound)
def adjust_request_interface_for_preferred_languages(event):
    """
    Checks the conditions outlined in this package's documentation and
    adds a marker interface (:class:`.IPreferredLanguagesRequest`) to
    the request if they hold true.

    This is registered as a subscriber for Pyramid's
    :class:`.IContextFound` event by this package's ``configure.zcml``
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
    remote_user = IPrincipal(request, None)
    if remote_user and not IUnauthenticatedPrincipal.providedBy(remote_user):
        remote_user_langs = IUserPreferredLanguages(remote_user)
        if remote_user_langs and remote_user_langs.getPreferredLanguages(): # pylint:disable=too-many-function-args
            interface.alsoProvides(request, IPreferredLanguagesRequest)
