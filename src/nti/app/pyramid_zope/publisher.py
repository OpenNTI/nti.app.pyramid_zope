#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides code for bridging pyramid views to zope views. Useful for
running things like the Zope Management Interface (ZMI) in the context
of a pyramid application.

TODO This is currently a WIP and care should be taken before using this
in a production environment.
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import functools

from pyramid.httpexceptions import HTTPForbidden
from pyramid.httpexceptions import HTTPNotFound

from pyramid.interfaces import IViewMapper
from pyramid.interfaces import IViewMapperFactory

from zope import component
from zope import interface

from zope.publisher.interfaces import IPublishTraverse
from zope.publisher.interfaces import NotFound

from zope.publisher.interfaces.browser import IBrowserView
from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from zope.publisher.interfaces.browser import IBrowserRequest
from zope.publisher.interfaces.browser import IBrowserPublisher

from zope.publisher.publish import mapply

from zope.publisher.skinnable import setDefaultSkin

from zope.security.adapter import LocatingTrustedAdapterFactory
from zope.security.adapter import LocatingUntrustedAdapterFactory

from zope.security.interfaces import Unauthorized
from zope.security.interfaces import Forbidden

from zope.security.checker import ProxyFactory

from zope.security.checker import canAccess

from zope.traversing.publicationtraverse import PublicationTraverser

from nti.base._compat import text_

logger = __import__('logging').getLogger(__name__)

def configure_zope_publisher(pyramid_config):
    """
    Find zope.publisher "views" and bridge them into pyramid views
    that can be traversed and called via our traditional pyramid
    stack. The zope views we care about right now are primarily those
    used by ZMI, but it's hard to target those specifically. As this
    looks for registered adapters we should be invoked after any
    configuration that sets up zmi is processed.

    TODO We capture things a bit more broadly then I think we would
    like right now.
    """

    # Rip through the component registry looking for zope "views".
    # These are multiadapters from (Interface, IDefaultBrowserLayer) to things
    # that we can ultimately invoke via ``zope.publisher.publish.mapply``.
    # TODO right now we look for any adapters for things that isOrExtend Interface
    # and IDefaultBrowerLayer.

    sm = component.getGlobalSiteManager()

    def _factory_predicate(factory):
        """
        Checking the type of the factory like that should limit this
        to views that require a permission that isn't public. That may
        be what we want here.
        """
        # TODO that doesn't actually seem to work. We find nothing to register based on this condition.
        #return type(factory) in (LocatingTrustedAdapterFactory, LocatingUntrustedAdapterFactory)
        return True

    toregister = [
        v for v in sm.registeredAdapters()
        if len(v.required) == 2
        and _factory_predicate(v.factory)
        and all(
            x.isOrExtends(y)
            for x, y
            in zip(v.required, [interface.Interface, IDefaultBrowserLayer])
        )
    ]

    # Now we have a set of zope "views". We need to register them as pyramid views
    logger.info('Will bridge %i zope views to pyramid', len(toregister))
    for view in toregister:
        logger.debug('Registering view %s for %s name = %s', view.factory, view.required[0], view.name)

        # Of course calling what are zope views from pyramid isn't exactly straight forward.
        # The stacks are entirely different and there is bridging work that must happen.
        # We use a custom IViewMapper to control how we invoke these particular views (and
        # a corresponding IViewMapperFactory). This allows us to do things like bridge
        # our pyramid request to an zope IBrowserRequest, do any further traversing,
        # security checks, etc.

        # TODO note the lack of permission here. Zope views rely heavily on zope.security.checker
        # and friend to implement per attribute/method security checks. Our IViewMapper callable
        # handles some of that via the existing zope functions and has place holders for others.
        # We might be able to build a pyramid acl based on the zope.security permission on the __call__
        # method of the zope "view" if one exists, but, as we found out these "views" aren't always
        # views and they rely on further traversing to get so something with an actual
        # security check. More to come and investigate here...
        pyramid_config.add_view(view.factory,
                                name=view.name,
                                # The first thing we adapt from is our pyramid context
                                for_=view.required[0],
                                # TODO Given our custom mapper I'm not sure route is required here?
                                route_name='objects.generic.traversal',
                                mapper=_vmfactory)

def map_to_pyramid_exceptions(function):
    """
    A decorator that reraises zope.security.interfaces.Forbidden
    and zope.security.interfaces.Unauthorized as a pyramid
    HTTPForbidden exception
    """
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except (Forbidden, Unauthorized) as e:
            raise HTTPForbidden(e)
        except (NotFound) as e:
            raise HTTPNotFound(e)
    return wrapper

class ZopeViewCaller(object):
    """
    A callable object whose instances can be used as the return value
    of an IViewMapper. This encapsulates the bulk of the logic involved
    with correctly invoking a zope view via pyramid.
    """
    
    def __init__(self, zview):
        self.view = zview

    @map_to_pyramid_exceptions
    def __call__(self, context, request):
        """
        TODO much of this was reversed engineered through trial and error
        over the course of several hours before I found and understood how
        all the zope pieces fit together with https://github.com/zopefoundation/zope.publisher/blob/9fa4a2cda8999c61f249995a7b421b4710135050/src/zope/publisher/publish.py#L129

        Some pieces from that have been added, but there are likely still things we aren't doing
        and some places where we could leverage existing zope code.
        """

        # The first thing we need to do is turn our pyramid request into an
        # IBrowserRequest that zope knows how to deal with. We have an incomplete
        # implementation. I believe most of the remaining bugs have to do with
        # missing/incomplete or poorly implemented features of the request.
        #from IPython.core.debugger import Tracer; Tracer()()
        request = IBrowserRequest(request)

        # Now set our default skin on the request.
        setDefaultSkin(request)

        # TODO we're traversing again, but this time through the zope
        # side to both ensure security proxies are in place, and to
        # traverse the entire way. We traversed at least partway via
        # pyramid, and we throw that away, but this is a much cleaner
        # implementation

        path = request.path
        assert path[0] == '/'
        path = path[1:]
        
        ztraverser = PublicationTraverser()

        # TODO Pyramid root is our /dataserver2 folder, we need it's parent. the db root(?).
        # Need a better way to get this generally or a level of indirection. In zope
        # that level of indirection comes from the publication object's getApplication method
        app_root = request.root.__parent__
        res = ztraverser.traverseRelativeURL(request, app_root, path)

        # # Things aren't as simple as simply calling res. There is black magic in zope.publisher.publish
        # # that invokes the callable based on it's signature potentially supply kwargs from the request
        # # params. That utlimately boils down to mapply.
        # # TODO the second tuple is typically IBrowserRequest.getPositionalArguments which we don't
        # # implement and most implementations return an empty tuple anyway. Need to probably implement
        # # that on our bridged request.
        result = mapply(res, tuple(), request)

        # Calling res may return something that can be used as a response body, or it may
        # have just manipulated request.response directly.
        response = request.response
        if result is not response:
            response.setResult(result)
        return response

@interface.implementer(IViewMapper)
def _vm(view):
    return ZopeViewCaller(view)

@interface.implementer(IViewMapperFactory)
def _vmfactory(**kwargs):
    return _vm
