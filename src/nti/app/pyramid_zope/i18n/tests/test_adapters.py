#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import assert_that
from hamcrest import is_not as does_not

from nti.testing.matchers import is_empty
from nti.testing.matchers import provides

import fudge

from zope import interface

from zope.event import notify

from zope.i18n.interfaces import IUserPreferredLanguages

from pyramid.events import ContextFound

from pyramid.request import Request

from nti.app.i18n.adapters import preferred_language_locale_negotiator

from nti.app.i18n.interfaces import IPreferredLanguagesRequest

from nti.dataserver.interfaces import IUser

from nti.app.testing.application_webtest import ApplicationLayerTest


def adjust(request):
    notify(ContextFound(request))


class TestApplicationRequestPolicy(ApplicationLayerTest):

    request = None

    def setUp(self):
        self.request = Request.blank('/')

    def _langs(self):
        return IUserPreferredLanguages(self.request).getPreferredLanguages()

    def _locale(self):
        return preferred_language_locale_negotiator(self.request)

    def test_adjust_interface_blank(self):
        # Initially, nothing
        adjust(self.request)
        assert_that(self.request, does_not(
            provides(IPreferredLanguagesRequest)))
        assert_that(self._langs(), is_empty())
        assert_that(self._locale(), is_('en'))

    def test_adjust_zope_cookie(self):
        self.request.cookies['I18N_LANGUAGE'] = 'ru'
        adjust(self.request)
        assert_that(self._langs(), is_(['ru']))
        assert_that(self._locale(), is_('ru'))

    def test_adjust_pyramid_property(self):
        self.request._LOCALE_ = 'ru'
        adjust(self.request)
        assert_that(self._langs(), is_(['ru']))
        assert_that(self._locale(), is_('ru'))

    @fudge.patch('nti.app.i18n.subscribers.get_remote_user',
                 'nti.app.i18n.adapters.get_remote_user')
    def test_adjust_remote_user(self, fake_get1, fake_get2):
        @interface.implementer(IUserPreferredLanguages)
        class User(object):
            def getPreferredLanguages(self):
                return ['ru']

        fake_get1.is_callable().returns(User())
        fake_get2.is_callable().returns(User())

        adjust(self.request)
        assert_that(self._langs(), is_(['ru']))
        assert_that(self._locale(), is_('ru'))

    @fudge.patch('nti.app.i18n.subscribers.get_remote_user',
                 'nti.app.i18n.adapters.get_remote_user')
    def test_adjust_remote_user_default_en(self, fake_get1, fake_get2):
        @interface.implementer(IUser)
        class User(object):
            pass

        fake_get1.is_callable().returns(User())
        fake_get2.is_callable().returns(User())

        adjust(self.request)
        # The default, because there's no header and nothing
        # specified for this user, is empty (this would trigger
        # the translation domain fallback)
        assert_that(self._langs(), is_([]))
        assert_that(self._locale(), is_('en'))

    @fudge.patch('nti.app.i18n.subscribers.get_remote_user',
                 'nti.app.i18n.adapters.get_remote_user')
    def test_adjust_remote_user_default_ru(self, fake_get1, fake_get2):
        @interface.implementer(IUser)
        class User(object):
            pass

        fake_get1.is_callable().returns(User())
        fake_get2.is_callable().returns(User())

        self.request.environ['HTTP_ACCEPT_LANGUAGE'] = 'ru'
        adjust(self.request)

        # The accept header rules
        assert_that(self._langs(), is_(['ru']))
        assert_that(self._locale(), is_('ru'))


from hamcrest import has_item

import os

from zope import component

from pyramid.interfaces import ITranslationDirectories


class TestApplicationTranslationDirs(ApplicationLayerTest):

    def test_translation_dirs(self):
        import nti.appserver
        dirs = component.getUtility(ITranslationDirectories)
        assert_that(dirs, has_item(os.path.join(os.path.dirname(nti.appserver.__file__),
                                                'locales')))
