# -*- coding: utf-8 -*-
"""
I18N related adapters.


"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os

import pyramid.interfaces

from pyramid.i18n import default_locale_negotiator
from pyramid.interfaces import ILocaleNegotiator
from pyramid.interfaces import ITranslationDirectories

from zope import component
from zope import interface

from zope.cachedescriptors.property import Lazy

from zope.i18n.interfaces import IModifiableUserPreferredLanguages
from zope.i18n.interfaces import ITranslationDomain
from zope.i18n.interfaces import IUserPreferredCharsets
from zope.i18n.interfaces import IUserPreferredLanguages
from zope.i18n.locales import LoadLocaleError
from zope.i18n.locales import locales

from zope.publisher.http import HTTPCharsets
from zope.publisher.interfaces.browser import IBrowserRequest

from zope.security.interfaces import IPrincipal

from .interfaces import IPreferredLanguagesRequest
from ..request import PyramidZopeRequestProxy

__all__ = [
    'EnglishUserPreferredLanguages',
    'PreferredLanguagesPolicy',
    'PyramidBrowserPreferredCharsets',
    'PyramidBrowserPreferredLanguages',
    'preferred_language_locale_negotiator',
    'ZopeTranslationDirectories',
]


@component.adapter(None)
@interface.implementer(IUserPreferredLanguages)
def EnglishUserPreferredLanguages(unused_user):
    """
    An implementation of :class:`.IUserPreferredLanguages` that always returns
    English.

    This is registered as the least-specific
    adapter for generic objects.
    """
    return EnglishUserPreferredLanguagesImpl


@interface.provider(IUserPreferredLanguages)
class EnglishUserPreferredLanguagesImpl(object):
    PREFERRED_LANGUAGES = ('en',)

    @classmethod
    def getPreferredLanguages(cls):
        return cls.PREFERRED_LANGUAGES


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
        remote_user = IPrincipal(self.request, None)
        remote_user_langs = IUserPreferredLanguages(remote_user)
        if remote_user_langs is not EnglishUserPreferredLanguagesImpl:
            return remote_user_langs.getPreferredLanguages() # pylint:disable=too-many-function-args

        # Ok, see what the HTTP request can come up with. Note that we're
        # going to the Zope interface so that we don't get into an infinite
        # loop
        browser_request = IBrowserRequest(self.request)
        browser_langs = IModifiableUserPreferredLanguages(browser_request)
        return browser_langs.getPreferredLanguages() # pylint:disable=too-many-function-args


@interface.implementer(IUserPreferredLanguages)
@component.adapter(pyramid.interfaces.IRequest)
def PyramidBrowserPreferredLanguages(request):
    # we implement IUserPreferredLanguages on the Pyramid object, but
    # return an IModifiableUserPreferredLanguages on the Zope object.
    # This prevents an infinite loop
    return IModifiableUserPreferredLanguages(PyramidZopeRequestProxy(request))


@interface.implementer(IUserPreferredCharsets)
@component.adapter(pyramid.interfaces.IRequest)
def PyramidBrowserPreferredCharsets(request):
    # Unfortunately, the trick we use for UserPreferredLanguages
    # (through an interface) does not work here and so we have to tightly
    # couple to an implementation.
    return HTTPCharsets(PyramidZopeRequestProxy(request))


@interface.provider(ILocaleNegotiator)
def preferred_language_locale_negotiator(request):
    """
    A pyramid locale negotiator that piggybacks off
    the preferred language support. We return a valid locale
    name consisting of at most language-territory, but at least language.
    A valid locale is one for which we have available locale data,
    not necessarily one for which any translation data is available.
    """
    # pylint:disable=too-many-function-args, assignment-from-no-return

    # This code is similar to that in zope.publisher.http.HTTPRequest.
    # it's point is to find the most specific available locale possible.
    # We differ in that, instead of returning a generic default, we
    # specifically return the english default. We also differ in that we
    # return a locale name instead of a locale object.

    result = EnglishUserPreferredLanguagesImpl.PREFERRED_LANGUAGES[0]

    pref_langs = IUserPreferredLanguages(request, ())
    if pref_langs:
        pref_langs = pref_langs.getPreferredLanguages()

    for lang in pref_langs:
        parts = (lang.split('-') + [None, None])[:3]
        try:
            locales.getLocale(*parts)
            result = lang
            break
        except LoadLocaleError: # pragma: no cover
            continue

    return result


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

    def __repr__(self): # pragma: no cover
        # TODO: Why is this repr this way? It makes broken test
        # output very confusing. There are no specific tests for it.
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

    @classmethod
    def testing_cleanup(cls): # pragma: no cover
        for d in component.getAllUtilitiesRegisteredFor(ITranslationDirectories):
            if isinstance(d, ZopeTranslationDirectories):
                d.__dict__.pop('_dirs', None)

try:
    from zope.testing import cleanup
except ImportError: # pragma: no cover
    pass
else:
    cleanup.addCleanUp(ZopeTranslationDirectories.testing_cleanup)
