#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import assert_that
from hamcrest import calling
from hamcrest import is_
from hamcrest import raises

from nti.testing.matchers import verifiably_provides

from zope.publisher.interfaces.browser import IBrowserRequest

from pyramid.request import Request
from pyramid.interfaces import IRequest

from nti.testing.base import SharedConfiguringTestBase


class TestRequest(SharedConfiguringTestBase):

    set_up_packages = (__name__,)

    def test_adapts(self):
        request = Request.blank('/')
        zrequest = IBrowserRequest(request)
        assert_that(zrequest, verifiably_provides(IBrowserRequest))
        # and it's still a valid pyramid request
        assert_that(zrequest, verifiably_provides(IRequest))

    def test_form_parsing(self):
        environ = {
            'PATH_INFO': '/',
            'QUERY_STRING':
                'lastName=Doe;country:list=Japan;country:list=Hungary',
        }
        request = Request(environ)
        zrequest = IBrowserRequest(request)
        assert_that(zrequest.form,
                    {'country': ['Japan', 'Hungary'], 'lastName': 'Doe'})

    def test_has_key(self):
        environ = {
            'PATH_INFO': '/',
            'QUERY_STRING':
                'lastName=Doe;country:list=Japan;country:list=Hungary',
        }
        request = Request(environ)
        zrequest = IBrowserRequest(request)

        assert_that(zrequest.has_key('lastName'), is_(True))

    def test_url_traversal(self):
        request = Request.blank('http://foobar.com/folder/item')
        zrequest = IBrowserRequest(request)

        assert_that(str(zrequest.URL), is_('http://foobar.com/folder/item'))

        assert_that(zrequest.URL['-1'], is_('http://foobar.com/folder'))
        assert_that(zrequest.URL['-2'], is_('http://foobar.com'))
        assert_that(calling(zrequest.URL.__getitem__).with_args('-3'), raises(KeyError))

        assert_that(zrequest.URL['0'], is_('http://foobar.com'))
        assert_that(zrequest.URL['1'], is_('http://foobar.com/folder'))
        assert_that(zrequest.URL['2'], is_('http://foobar.com/folder/item'))
        assert_that(calling(zrequest.URL.__getitem__).with_args('3'), raises(KeyError))

        assert_that(zrequest.URL.get('0'), is_('http://foobar.com'))
        assert_that(zrequest.URL.get('1'), is_('http://foobar.com/folder'))
        assert_that(zrequest.URL.get('2'), is_('http://foobar.com/folder/item'))
        assert_that(zrequest.URL.get('3', 'none'), is_('none'))

    def test_positional_args(self):
        request = Request.blank('/dataserver2/foo/bar.html')
        zrequest = IBrowserRequest(request)

        assert_that(zrequest.getPositionalArguments(), is_(()))
