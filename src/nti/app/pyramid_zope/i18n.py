#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Support for language and charset negotiation for
pyramid requests.

.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component
from zope import interface

# What the hell. Since we now can make a pyramid request look like a
# Zope request, we might as well be able to make a Pyramid request
# directly handle language negotiation in the good zope way
from zope.i18n.interfaces import IUserPreferredCharsets
from zope.i18n.interfaces import IUserPreferredLanguages
from zope.i18n.interfaces import IModifiableUserPreferredLanguages

import pyramid.interfaces

from .request import PyramidZopeRequestProxy

@interface.implementer(IUserPreferredLanguages)
@component.adapter(pyramid.interfaces.IRequest)
def PyramidBrowserPreferredLanguages(request):
	# we implement IUserPreferredLanguages on the Pyramid object, but
	# return an IModifiableUserPreferredLanguages on the Zope object.
	# This prevents an infinite loop
	# from zope.publisher.browser import ModifiableBrowserLanguages
	return IModifiableUserPreferredLanguages( PyramidZopeRequestProxy( request ) )

@interface.implementer(IUserPreferredCharsets)
@component.adapter(pyramid.interfaces.IRequest)
def PyramidBrowserPreferredCharsets(request):
	# Unfortunately, the trick we use for UserPreferredLanguages does
	# not work here
	from zope.publisher.http import HTTPCharsets
	return HTTPCharsets( PyramidZopeRequestProxy( request ) )
