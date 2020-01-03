#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Support for application-level (request, context and user based) internationalization.

Negotiation
===========

The process of finding a locale to use is somewhat complex. It is all
driven around the interface
:class:`zope.i18n.interfaces.IUserPreferredLanguages` and its mutable
subclass
:class:`zope.i18n.interfaces.IModifiableUserPreferredLanguages`. These
are combined with a :class:`zope.i18n.interfaces.INegotiator`, given a
context and a list of available languages, to determine the best
matching locale to use by taking the intersection of the preferred
languages of the context with the available languages (individual
translation utilities handle fallback and default languages).

Zope provides an implementation of preferred languages for (Zope)
requests in
:class:`zope.publisher.browser.ModifiableBrowserLanguages`. This uses
the HTTP ``Accept-Language`` header to determine a language. We let
Pyramid requests also have this implementation through our
compatibility shims in :mod:`nti.pyramid_zope.i18n`.

However, there are cases where we may not want to rely on the browser
to have the right setting, either for testing, or to support broken
browsers, or to explicitly enable user preferences. Supporting user
preferences is easy: provide a ``IUserPreferredLanguages`` adapter for your
``IPrincipal`` implementation. For temporary testing or for the
use of unauthenticated users, we can also look at the HTTP cookies
``_LOCALE_`` (Pyramid's default) and ``I18N_LANGUAGE`` (Zope/Plone
default), or the _LOCALE_ request parameter (or request attribute);
we can even use the `++lang++` namespace to set a language during traversal.

The complexity comes in combining all of these policies. Almost all
uses of the translation functions pass the current request as the
context, and by default that's just going to use the
``Accept-Language`` based picker. Our solution is to define a new
interface :class:`nti.app.pyramid_zope.i18n.interfaces.IPreferredLanguagesRequest`,
deriving from :class:`pyramid.interfaces.IRequest` and register a
policy for that interface. When the
:class:`pyramid.interfaces.IContextFound` event is fired, if the
cookies are present or an authenticated user is present, we make the
request object provide that interface. In this way, our policy is used
to override anything else.

Pyramid/Zope Integration
========================

The Zope I18N system is more powerful and flexible than the Pyramid system.
The Pyramid system is based simply on providing one locale name and a list
of directories containing translations. We implement Pyramid's
:class:`pyramid.interfaces.ILocaleNegotiator` and :class:`pyramid.interfaces.ITranslationDirectories`
based on the information we gather from Zope. In this way, the Pyramid
Chameleon support, for example, uses the same information as other places.

.. important::

   Make sure and include ``<include package="nti.app.pyramid_zope.i18n" file="pyramid.zcml" />``
   from your root ``pyramid.zcml`` to register the negotiator.

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
