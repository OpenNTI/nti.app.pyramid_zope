# -*- coding: utf-8 -*-
"""
Integrations for :mod:`zope.security` and :mod:`zope.authentication`.

Many of these are adapters registered automatically by this package's
configure.zcml.

In plain Zope3, the :class:`zope.publisher.interfaces.IRequest` *is*
an :class:`zope.security.interfaces.IParticipation` for the request's
principal (or the unauthenticated or fallback unauthenticated
principal). That request is defined to be the first participation in
the interaction by :mod:`zope.app.publication.zopepublication` (right after
authentication and right before traversal).

Pyramid's request is not a participation, and Pyramid doesn't
establish an interaction either. Something else (typically a
tween like **TODO: Copy Tween**) does that. These adapters will
work only after that is done.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from pyramid.threadlocal import get_current_request
from pyramid.interfaces import IRequest

from zope import component
from zope import interface

from zope.authentication.interfaces import IFallbackUnauthenticatedPrincipal
from zope.security import management as default_interaction_mgmt
from zope.security.interfaces import IInteractionManagement
from zope.security.interfaces import IInteraction
from zope.security.interfaces import IPrincipal
from zope.security.interfaces import NoInteraction

@component.adapter(IRequest)
@interface.implementer(IInteraction)
def interaction_from_request(request=None):
    """
    interaction_from_request(request: IRequest) -> IInteraction

    Find the :class:`.IInteraction` for the *request*.

    The request is adapted to :class:`IInteractionManagement` (using
    the default :mod:`zope.security.management` for a thread-local
    interaction if there is no specific adapter registered), and
    the current interaction is returned.

    This is registered as an adapter on the Pyramid ``IRequest`` interface;
    to provide a more specific policy, register an adapter on the concrete
    class.

    :raise zope.security.interfaces.NoInteraction: If there is
       no interaction.

    .. seealso:: :class:`zope.security.interfaces.IInteractionManagement`
    """
    request = get_current_request() if request is None else request
    interaction_mgmt = IInteractionManagement(request, default_interaction_mgmt)
    # If we return None here, we can use a default value for the interaction
    # or raise a TypeError with IInteraction(request, <default>); if we
    # raise NoInteraction it would be propagated unconditionally.
    return interaction_mgmt.getInteraction() # pylint:disable=too-many-function-args


@component.adapter(IInteraction)
@interface.implementer(IPrincipal)
def principal_from_interaction(interaction):
    """
    principal_from_interaction(interaction: IInteraction) -> IPrincipal

    Find the primary :class:`IPrincipal` for the *interaction*. The primary
    principal is the principal of the first participation.
    """
    return next(iter(interaction.participations)).principal


@component.adapter(IRequest)
@interface.implementer(IPrincipal)
def principal_from_request(request=None):
    """
    principal_from_request(request: IRequest) -> IPrincipal

    Find the primary :class:`IPrincipal` for the *request*.

    First adapts the request into an :class:`IInteraction` (probably
    using :func:`interaction_from_request`), and then adapts the
    interaction into an ``IPrincipal`` (probably using :func:`principal_from_interaction`).
    If there is no interaction, the unauthenticated principal is returned.

    This is registered as an adapter on the Pyramid ``IRequest`` interface;
    to provide a more specific policy, register an adapter on the concrete
    class.

    """
    try:
        interaction = IInteraction(
            request if request is not None else get_current_request(),
        )
    except NoInteraction:
        return component.getUtility(IFallbackUnauthenticatedPrincipal)

    return IPrincipal(interaction)
