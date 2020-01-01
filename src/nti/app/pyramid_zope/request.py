#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Partial support for making a Pyramid request/response object pair work more
like a Zope request.

Partially based on ideas from :mod:`pyramid_zope_request`
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"


from zope import component
from zope import interface

from zope.authentication.interfaces import IUnauthenticatedPrincipal

from zope.i18n.locales import locales

from zope.proxy import non_overridable
from zope.proxy import getProxiedObject

from zope.proxy.decorator import SpecificationDecoratorBase


import zope.publisher.interfaces.browser

from zope.security.interfaces import NoInteraction
from zope.security.management import getInteraction

from six import text_type
from pyramid.interfaces import IRequest
from pyramid.i18n import get_locale_name

from nti.property.property import alias

# Implement the request
# and the "skin". In zope, the skin is changeable (IBrowserRequest
# implements ISkinnable), especially
# through the ++skin++ namespace adapter. Here
# we're just declaring it (as it happens, IDefaultBrowserLayer
# is a sub-type of IBrowserRequest)


@component.adapter(IRequest)
@interface.implementer(zope.publisher.interfaces.browser.IBrowserRequest,
                       zope.publisher.interfaces.browser.IDefaultBrowserLayer)
class PyramidZopeRequestProxy(SpecificationDecoratorBase):
    """
    Makes a Pyramid IRequest object look like a Zope request
    for purposes of rendering. The existing interfaces (IRequest) are preserved.

    Changes to a proxy, including annotations, are persistent, and
    will be reflected if the same pyramid request is proxied again
    later (unlike :mod:`pyramid_zope_request`, which takes the approach of
    subclassing :class:`zope.publisher.base.BaseRequest` and overriding
    certain methods to call through to pyramid, but not things
    like annotations.)

    .. note:: Most of this behaviour is added from reverse-engineering what
            existing zope code, most notably :mod:`z3c.table.table` uses.
            Some additional support for :mod:`z3c.form` comes from
            looking at what :mod:`pyramid_zope_request` does.
    """

    def __init__(self, base):
        super(PyramidZopeRequestProxy, self).__init__(base)
        if getattr(base, 'registry', None) is None:
            base.registry = component.getSiteManager()

        base.response.getHeader = lambda k: base.response.headers[k]

        def setHeader(name, value, literal=False):
            __traceback_info__ = name, value, literal
            # Go to bytes for python 2 if incoming was a string
            name = str(name)
            value = str(value) if isinstance(value, text_type) else value
            if name.lower() == 'content-type':
                # work around that webob stores the charset
                # in the header ``Content-type``, zope kills the charset
                # by setting e.g. ``text/html`` without charset
                charset = base.response.charset
                base.response.headers[name] = value
                # restore the old charset
                base.response.charset = charset
            else:
                base.response.headers[name] = value
        base.response.setHeader = setHeader
        base.response.addHeader = setHeader

        base.response.getStatus = lambda: base.response.status_code
        base.response.setStatus = lambda status_code: setattr(base.response,
                                                              'status_code',
                                                              status_code)

    @non_overridable
    def get(self, key, default=None):
        """
        Returns GET and POST params. Multiple values are returned as lists.

        Pyramid's IRequest has a deprecated method that exposes
        the WSGI environ, making the request dict-like for the environ.
        Hence the need to mark this method non_overridable.
        """
        # Zope does this by actually processing the inputs
        # into a "form" object

        def _d_o_l(o):
            # DummyRequest GET/POST are different
            return o.dict_of_lists() if hasattr(o, 'dict_of_lists') else o.copy()
        dict_of_lists = _d_o_l(self.GET)
        dict_of_lists.update(_d_o_l(self.POST))
        val = dict_of_lists.get(key)
        if val:
            if len(val) == 1:
                val = val[0]  # de-list things that only appeared once
        else:
            # Ok, in the environment?
            val = self.environ.get(key, default)
        return val

    def items(self):
        result = {}
        result.update(self.environ)
        result.update(self.GET)
        result.update(self.POST)
        return result.items()

    def keys(self):
        return [k for k, _ in self.items()]

    def values(self):
        return [v for _, v in self.items()]

    def __iter__(self):
        return iter(self.keys())

    def __len__(self):
        return len(self.items())

    def __contains__(self, key):
        return key in self.keys()

    def __getitem__(self, key):
        result = self.get(key, self)
        if result is self:
            raise KeyError(key)
        return result

    def getHeader(self, name, default=None):
        return self.headers.get(name, default)

    def getURL(self):
        return self.path_url

    @property
    def locale(self):
        try:
            # Country is optional
            lang_country = get_locale_name(self).split('-')
        except AttributeError:  # Testing, registry has no settings
            lang_country = ('en', 'US')
        return locales.getLocale(*lang_country)

    @property
    def annotations(self):
        return getProxiedObject(self).__dict__.setdefault('annotations', {})

    def _get__annotations__(self):
        return getProxiedObject(self).__dict__.get('__annotations__')

    def _set__annotations__(self, val):
        getProxiedObject(self).__dict__['__annotations__'] = val
    __annotations__ = property( # pylint:disable=bad-option-value,property-on-old-class
        # On python 2, pylint thinks this is an old-style
        # class, for some reason, and complains here. But not about
        # the call to super() in the constructor.
        # Python 3, of course has no old-style classes so it doesn't have that
        # warning
        _get__annotations__,
        _set__annotations__
    )


    environment = alias('environ')

    @property
    def bodyStream(self):
        return self.body_file_seekable

    def _unimplemented(self, *args, **kwargs):
        raise NotImplementedError()

    @property
    def _unimplemented_prop(self):
        return NotImplemented

    setPathSuffix = _unimplemented
    getTraversalStack = _unimplemented
    setTraversalStack = _unimplemented
    processInputs = _unimplemented
    publication = _unimplemented_prop
    setPublication = _unimplemented
    getPositionalArguments = _unimplemented
    retry = _unimplemented
    hold = _unimplemented
    setupLocale = _unimplemented
    traverse = _unimplemented
    close = _unimplemented
    debug = False

    def supportsRetry(self):
        return False

    # This is supposed to be an IParticipation;
    # we could almost do that
    setPrincipal = _unimplemented

    @property
    def principal(self):
        try:
            return getInteraction().participations[0].principal
        except (NoInteraction, IndexError, AttributeError):
            return component.queryUtility(IUnauthenticatedPrincipal)

    @property
    def interaction(self):
        try:
            return getInteraction()
        except NoInteraction:
            return None
