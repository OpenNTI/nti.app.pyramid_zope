#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Pyramid template renderer using z3c.pt, for the path syntax
and other niceties that Chameleon itself doesn't support

$Id$
"""
from __future__ import print_function, unicode_literals, absolute_import
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from zope.publisher.interfaces.browser import IBrowserRequest

from z3c.pt.pagetemplate import ViewPageTemplateFile
from chameleon.zpt.template import PageTemplateFile

from pyramid_chameleon.renderer import template_renderer_factory
from pyramid.decorator import reify
from pyramid.renderers import get_renderer
from pyramid.interfaces import ITemplateRenderer

from collections import OrderedDict

def renderer_factory(info):
	"""
	Factory to produce renderers. Intended to be used with asset specs.

	.. note:: At this time, this does not support the pyramid 1.4 macro syntax.
	"""
	return template_renderer_factory(info, ZPTTemplateRenderer)

class _ViewPageTemplateFileWithLoad(ViewPageTemplateFile):
	"""
	Enables the load: expression type for convenience.
	"""
	expression_types = ViewPageTemplateFile.expression_types.copy()
	expression_types['load'] = PageTemplateFile.expression_types['load']

	@property
	def builtins(self):
		d = super(_ViewPageTemplateFileWithLoad,self).builtins
		d['__loader'] = self._loader
		# https://github.com/malthe/chameleon/issues/154
		# We try to get iteration order fixed here:
		result = OrderedDict()
		for k in sorted(d.keys()):
			result[k] = d[k]
		return result


@interface.implementer(ITemplateRenderer)
class ZPTTemplateRenderer(object):
	"""
	Renders using a :class:`z3c.pt.pagetemplate.ViewPageTemplateFile`
	"""

	def __init__(self, path, lookup, macro=None):
		"""
		:keyword macro: New in pyramid 1.4, currently unsupported.
		:raise ValueError: If the ``macro`` argument is supplied.
		"""
		self.path = path
		self.lookup = lookup
		if macro:
			__traceback_info__ = path, lookup, macro
			raise ValueError( macro )

	@reify # avoid looking up reload_templates before manager pushed
	def template(self):
		return _ViewPageTemplateFileWithLoad(self.path,
											 auto_reload=self.lookup.auto_reload,
											 debug=self.lookup.debug,
											 translate=self.lookup.translate)

	def implementation(self): # pragma: no cover
		return self.template

	def __call__(self, value, system):
		"""
		:param value: The object returned from the view. Either a dictionary,
			or a context object. If a context object, will be available at the path
			``options/here`` in the template. If a dictionary, its values are merged with
			those in `system`.
		"""
		__traceback_info__ = value, system
		try:
			system.update(value)
		except (TypeError, ValueError):
			#raise ValueError('renderer was passed non-dictionary as value')
			system['here'] = value
			# See plasTeX/Renderers/__init__.py for comments about how 'self' is a problem

		request = None
		if 'request' in system and system['request'] is not None:
			request = IBrowserRequest( system['request'] )
			system['request'] = request

		view = system['view'] # TODO: We can do better with this
		if view is None and request is not None:
			view = request
			system['view'] = request

		# We used to register macros, but now you should use
		# z3c.macro and the macro: expression type
		#if 'master' not in system:
			# XXX: FIXME: There must be a better way to handle this.
			# How did zope do it? (Acquisition?)
			# (Answer: Yes, basically. Every template was auto-loaded
			# and at a traversable location, usually also in the
			# acquisition path; pages traversed to the macros of the
			# template they wanted. We can do something similar though
			# traversal, we just need to update our templates.)
			# FIXME: Note use of nti.appserver package
		#	master = get_renderer('nti.appserver:templates/master_email.pt').implementation()
		#	system['master'] = master
		result = self.template.bind( view )( **system )
		#print(result)
		return result


from nti.dataserver.utils import _configure
import simplejson
import argparse
import sys
from zope.i18n import translate as ztranslate
import os.path
import sys
import z3c.pt.pagetemplate

def main():
	arg_parser = argparse.ArgumentParser( description="Render a single file with JSON data" )
	arg_parser.add_argument( 'input', help="The input template" )
	arg_parser.add_argument( 'output', help="The output filename, or - for standard out." )
	arg_parser.add_argument( '--json',
							 dest='data',
							 help="The path to a filename to read as JSON data to be used as template options" )
	args = arg_parser.parse_args()

	# Must configure traversing;
	# other stuff might be convenient but slows down startup,
	# so add as use-cases arise
	#_configure( set_up_packages=('nti.appserver', 'nti.app.pyramid_zope') )
	_configure( set_up_packages=( 'z3c.ptcompat', ) )
	# Turn zope.security back off, pointless in this context
	z3c.pt.pagetemplate.sys_modules = sys.modules
	class Lookup(object):
		auto_reload = False
		debug = True
		translate = ztranslate

	class View(object):
		context = None
		request = None

	renderer = ZPTTemplateRenderer( os.path.abspath(args.input), Lookup() )
	system = {}
	system['view'] = View()
	system['request'] = None
	value = {}
	if args.data:
		value = simplejson.load( open( args.data, 'rb') )
	result = renderer( value, system )

	with open(args.output, 'wb') as f:
		f.write( result )

	sys.exit( 0 )

if __name__ == '__main__':
	main()
