#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import assert_that
from hamcrest import is_

from zope import interface

from nti.testing.matchers import verifiably_provides

from zope.security.interfaces import IParticipation
from zope.security.interfaces import IPrincipal

from zope.security.management import endInteraction
from zope.security.management import newInteraction
from zope.security.management import queryInteraction

from nti.testing.base import SharedConfiguringTestBase

@interface.implementer(IPrincipal)
class _Principal(object):

    __slots__ = ('username')

    def __init__(self, username):
        self.username = username

@interface.implementer(IParticipation)
class _Participation(object):

    __slots__ = ('interaction', 'principal')

    def __init__(self, principal):
        self.interaction = None
        self.principal = principal

class TestSecurity(SharedConfiguringTestBase):

    set_up_packages = (__name__,)

    def test_handles_participations_list(self):
        principal = _Principal('bob')
        participation = _Participation(principal)

        newInteraction(participation)

        try:
            interaction = queryInteraction()
            p_from_i = IPrincipal(interaction)
            assert_that(p_from_i.username, is_(principal.username))
        finally:
            endInteraction()
