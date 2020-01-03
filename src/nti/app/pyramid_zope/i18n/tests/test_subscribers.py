#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import unittest

import fudge
from hamcrest import assert_that
from hamcrest import has_property
from hamcrest import is_not as does_not

from nti.testing.matchers import provides
from pyramid.events import ContextFound
from pyramid.request import Request
from zope import interface
from zope.i18n.interfaces import IUserPreferredLanguages

from ..interfaces import IPreferredLanguagesRequest
from ..subscribers import adjust_request_interface_for_preferred_languages as _adjust

def adjust(request):
    _adjust(ContextFound(request))


class TestSubscribers(unittest.TestCase):

    request = None

    def setUp(self):
        self.request = Request.blank('/')

    def test_adjust_interface_blank(self):
        # Initially, nothing
        adjust(self.request)
        assert_that(self.request,
                    does_not(provides(IPreferredLanguagesRequest)))

    def test_adjust_zope_cookie(self):
        self.request.cookies['I18N_LANGUAGE'] = 'ru'
        adjust(self.request)
        assert_that(self.request, provides(IPreferredLanguagesRequest))
        # It got copied to the request attribute too for benefit
        # of the default pyramid localizer
        assert_that(self.request, has_property('_LOCALE_', 'ru'))

    def test_adjust_pyramid_property(self):
        self.request._LOCALE_ = 'ru'
        adjust(self.request)
        assert_that(self.request, provides(IPreferredLanguagesRequest))

    @fudge.patch('nti.app.pyramid_zope.i18n.subscribers.IPrincipal')
    def test_adjust_remote_user(self, fake_get):

        @interface.implementer(IUserPreferredLanguages)
        class User(object):
            def getPreferredLanguages(self):
                return ['ru']

        fake_get.is_callable().returns(User())

        adjust(self.request)
        assert_that(self.request, provides(IPreferredLanguagesRequest))
