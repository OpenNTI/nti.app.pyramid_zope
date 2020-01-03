#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import unittest

import fudge
from hamcrest import assert_that
from hamcrest import is_
from hamcrest import is_not as does_not

from nti.testing.matchers import is_empty
from nti.testing.matchers import provides

from pyramid.events import ContextFound
from pyramid.interfaces import ITranslationDirectories
from pyramid.request import Request

from zope import component
from zope import interface
from zope.event import notify
from zope.i18n.interfaces import IUserPreferredLanguages

from ..adapters import preferred_language_locale_negotiator
from ..interfaces import IPreferredLanguagesRequest

from ...tests import ConfiguringLayer

def adjust(request):
    notify(ContextFound(request))


class TestApplicationRequestPolicy(unittest.TestCase):
    # pylint:disable=too-many-function-args

    layer = ConfiguringLayer

    request = None

    def setUp(self):
        self.request = Request.blank('/')

    def _langs(self):
        langs = IUserPreferredLanguages(self.request)
        return langs.getPreferredLanguages()

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

    @fudge.patch('nti.app.pyramid_zope.i18n.subscribers.IPrincipal',
                 'nti.app.pyramid_zope.i18n.adapters.IPrincipal')
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

    @fudge.patch('nti.app.pyramid_zope.i18n.subscribers.IPrincipal',
                 'nti.app.pyramid_zope.i18n.adapters.IPrincipal')
    def test_adjust_remote_user_default_en(self, fake_get1, fake_get2):
        #@interface.implementer(IUser)
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

    @fudge.patch('nti.app.pyramid_zope.i18n.subscribers.IPrincipal',
                 'nti.app.pyramid_zope.i18n.adapters.IPrincipal')
    def test_adjust_remote_user_default_ru(self, fake_get1, fake_get2):
        #@interface.implementer(IUser)
        class User(object):
            pass

        fake_get1.is_callable().returns(User())
        fake_get2.is_callable().returns(User())

        self.request.environ['HTTP_ACCEPT_LANGUAGE'] = 'ru'
        adjust(self.request)

        # The accept header rules
        assert_that(self._langs(), is_(['ru']))
        assert_that(self._locale(), is_('ru'))



class TestApplicationTranslationDirs(unittest.TestCase):
    layer = ConfiguringLayer

    @fudge.patch('nti.app.pyramid_zope.i18n.adapters.component.getAllUtilitiesRegisteredFor')
    def test_translation_dirs(self, get_all):
        class Domain(object):
            def __iter__(self):
                return iter([CatInfo()])

        class CatInfo(object):

            def getCatalogsInfo(self):
                return {
                    # These tests only work on POSIX.
                    'en': ['/nti/appserver/locales/en/LC_MESSAGES/z3c.password.mo'],
                    # Entries with more than one are ignored
                    'ru': [
                        'abc',
                        'def',
                    ],
                    # Entries that don't end in .mo are ignored
                    'es': [
                        'foo.pot'
                    ],
                }

        get_all.is_callable().returns(Domain())
        dirs = component.getUtility(ITranslationDirectories)

        self.assertEqual(
            list(dirs),
            ['/nti/appserver/locales'])
