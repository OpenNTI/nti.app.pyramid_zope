#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Partial support for making a Pyramid request object work more
like a Zope request.

$Id$
"""

from __future__ import print_function, unicode_literals, absolute_import
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface
from zope import component
from zope.i18n.locales import locales

from pyramid.i18n import get_locale_name
import pyramid.interfaces


from zope.proxy import non_overridable, getProxiedObject
from zope.proxy.decorator import SpecificationDecoratorBase
import zope.publisher.interfaces.browser
import zope.publisher.browser
#import zope.publisher.interfaces.http # For IHTTPResponse, should we need it
import operator

@interface.implementer(zope.publisher.interfaces.browser.IBrowserRequest)
@component.adapter(pyramid.interfaces.IRequest)
class PyramidZopeRequestProxy(SpecificationDecoratorBase):
	"""
	Makes a Pyramid IRequest object look like a Zope request
	for purposes of rendering. The existing interfaces (IRequest) are preserved.

	.. note:: Most of this behaviour is added from reverse-engineering what
		existing zope code, most notably :mod:`z3c.table.table` uses.
	"""

	def __init__( self, base ):
		SpecificationDecoratorBase.__init__( self, base )
		base.response.getHeader = lambda k: base.response.headers[k]
		base.response.setHeader = lambda k, v, literal=False: operator.setitem( base.response.headers, str(k), str(v) if isinstance(v,unicode) else v )

	@non_overridable
	def get( self, key, default=None ):
		"""
		Returns GET and POST params. Multiple values are returned as lists.

		Pyramid's IRequest has a deprecated method that exposes
		the WSGI environ, making the request dict-like for the environ.
		Hence the need to mark this method non_overridable.
		"""
		def _d_o_l( o ):
			return o.dict_of_lists() if hasattr( o, 'dict_of_lists' ) else o.copy() # DummyRequest GET/POST are different
		dict_of_lists = _d_o_l( self.GET )
		dict_of_lists.update( _d_o_l( self.POST ) )
		val = dict_of_lists.get( key )
		if val:
			if len(val) == 1:
				val = val[0] # de-list things that only appeared once
		else:
			# Ok, in the environment?
			val = self.environ.get( key, default )
		return val

	def getHeader(self, name, default=None):
		return self.headers.get( name, default )


	@property
	def locale(self):
		return locales.getLocale( *get_locale_name( self ).split( '-' ) )

	@property
	def annotations(self):
		return getProxiedObject(self).__dict__.setdefault( 'annotations', {} )

	def _get__annotations__(self):
		return getProxiedObject(self).__dict__.get( '__annotations__' )
	def _set__annotations__(self, val):
		getProxiedObject(self).__dict__['__annotations__'] = val
	__annotations__ = property(_get__annotations__, _set__annotations__)
