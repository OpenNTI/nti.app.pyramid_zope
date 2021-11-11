#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import assert_that
from hamcrest import calling
from hamcrest import has_entry
from hamcrest import has_key
from hamcrest import has_length
from hamcrest import instance_of
from hamcrest import is_
from hamcrest import less_than
from hamcrest import raises

from zope import component
from zope import interface

from zope.interface import providedBy

from zope.publisher.interfaces.http import IResult

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

        # IBrowserRequest should appear in our flattened interfaces
        # before IRequest
        flattened = list(providedBy(zrequest).flattened())

        assert_that(flattened.index(IBrowserRequest),
                    less_than(flattened.index(IRequest)))

    def test_form_parsing(self):
        environ = {
            'PATH_INFO': '/',
            'QUERY_STRING':
                'lastName=Doe;country:list=Japan;country:list=Hungary;continent:list=asia',
        }
        request = Request(environ)
        zrequest = IBrowserRequest(request)
        assert_that(zrequest.form,
                    {'country': ['Japan', 'Hungary'],
                     'lastName': 'Doe',
                     'continent': 'asia'})

    def test_has_key(self):
        environ = {
            'PATH_INFO': '/',
            'QUERY_STRING':
                'lastName=Doe;country:list=Japan;country:list=Hungary',
        }
        request = Request(environ)
        zrequest = IBrowserRequest(request)

        assert_that(zrequest.has_key('lastName'), is_(True))

    def test_request_dict_like(self):
        environ = {
            'wsgi.url_scheme': 'http',
            'PATH_INFO': '/',
            'QUERY_STRING':
                'lastName=Doe;country:list=Japan;country:list=Hungary',
        }
        request = Request(environ)
        zrequest = IBrowserRequest(request)

        assert_that(zrequest, has_length(5)) #GET, POST, & environ
        assert_that(zrequest, has_key('lastName'))
        assert_that(zrequest['lastName'], is_('Doe'))
        assert_that(calling(zrequest.__getitem__).with_args('notexist'), raises(KeyError))

        items = zrequest.items()
        assert_that(items, has_length(6))
        assert_that(zrequest.values(), is_([v for _, v in items]))

        assert_that([x for x in zrequest], is_(zrequest.keys()))
        

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

        assert_that(zrequest.getURL(0, True), is_('/folder/item'))

    def test_positional_args(self):
        request = Request.blank('/dataserver2/foo/bar.html')
        zrequest = IBrowserRequest(request)

        assert_that(zrequest.getPositionalArguments(), is_(()))

    def test_get_header(self):
        request = Request.blank('/')
        zrequest = IBrowserRequest(request)

        assert_that(zrequest.getHeader('host'), is_('localhost:80'))
        assert_that(zrequest.getHeader('doesntexit', 'default'), is_('default'))

    def test_virtual_root(self):
        request = Request.blank('/')
        zrequest = IBrowserRequest(request)

        assert_that(zrequest.getVirtualHostRoot(), is_(None))

    def test_supports_retry(self):
        request = Request.blank('/')
        zrequest = IBrowserRequest(request)

        assert_that(zrequest.supportsRetry(), is_(False))


@interface.implementer(IResult)
class HTTPResult(object):

    def __init__(self, msg, req=None):
        self.msg = getattr(msg, 'msg', msg)

    def __iter__(self):
        return iter([self.msg])

class AdaptableResult(object):

    def __init__(self, msg):
        self.msg = msg

class TestResponse(SharedConfiguringTestBase):

    set_up_packages = (__name__,)

    def setUp(self):
        self.request = Request.blank('/')
        self.zrequest = IBrowserRequest(self.request)
        self.response = self.zrequest.response

    def test_redirect(self):
        self.response.redirect('/newpath')

        assert_that(self.response.status_code, is_(302))
        assert_that(self.response.headers, has_entry('Location', 'http://localhost/newpath'))

        self.response.redirect('/anotherpath', 301)
        assert_that(self.response.status_code, is_(301))
        assert_that(self.response.headers, has_entry('Location', 'http://localhost/anotherpath'))

    def test_set_header_keeps_charset(self):
        charset = self.response.charset
        assert_that(charset, is_('UTF-8'))

        self.response.setHeader('content-type', 'text/html')
        assert_that(charset, is_('UTF-8'))
        assert_that(self.response.headers['Content-Type'], is_('text/html; charset=UTF-8'))

    def test_set_header(self):
        self.response.setHeader(u'x-test', u'value') # Note we provided unicode strings
        key, value = next((x, y) for x,y in self.response.headers.iteritems() if x == 'x-test')

        assert_that(key, is_('x-test'))
        assert_that(value, is_('value'))
        
        # unicode headers are converted to native strings
        assert_that(key, instance_of(str))
        assert_that(value, instance_of(str))

    def test_set_result_unicode(self):
        self.response.setResult(u'this is a unicode mdash —')
        assert_that(self.response.body, is_(b'this is a unicode mdash \xe2\x80\x94'))

    def test_set_result_str(self):
        self.response.setResult('this is a unicode mdash')
        assert_that(self.response.body, is_(b'this is a unicode mdash'))

    def test_set_result_iresult(self):
        result = HTTPResult(b'this is a unicode mdash \xe2\x80\x94')
        self.response.setResult(result)
        assert_that(self.response.body, is_(b'this is a unicode mdash \xe2\x80\x94'))

    def test_set_result_adapts_iresult(self):
        sm = component.getGlobalSiteManager()
        sm.registerAdapter(HTTPResult,
                           provided=IResult,
                           required=(AdaptableResult, IBrowserRequest,))

        try:
        
            result = AdaptableResult(b'this is a unicode mdash \xe2\x80\x94')
            self.response.setResult(result)
            assert_that(self.response.body, is_(b'this is a unicode mdash \xe2\x80\x94'))
        finally:
            sm.unregisterAdapter(HTTPResult,
                                 provided=IResult,
                                 required=(AdaptableResult, IBrowserRequest,))

    def test_set_result_none(self):
        self.response.setResult(None)
        assert_that(self.response.body, is_(b''))

    def test_set_result_raises_on_bad_input(self):
        result = AdaptableResult(b'this is a unicode mdash \xe2\x80\x94')
        assert_that(calling(self.response.setResult).with_args(result),
                    raises(TypeError))
        
