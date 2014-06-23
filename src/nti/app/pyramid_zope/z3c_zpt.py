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

from z3c.pt.pagetemplate import BaseTemplate
from z3c.pt.pagetemplate import ViewPageTemplateFile
from chameleon.zpt.template import PageTemplateFile

from pyramid_chameleon.renderer import template_renderer_factory
from pyramid.decorator import reify

# ITemplateRenderer is deprecated as of pyramid 1.5a3,
# but there is no corresponding pyramid_chameleon
# release yet, so we still need to implement it, not
# its parent IRenderer. Avoid the deprecation warning
# this way
import pyramid.interfaces
try:
	ITemplateRenderer = pyramid.interfaces.__dict__['ITemplateRenderer']
except KeyError:
	raise ImportError()


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
	# NOTE: We cannot do the rational thing and copy this
	# and modify our local value. This is because
	# certain packages, notably z3c.macro,
	# modify the superclass's value; depending on the order
	# of import, we may or may not get that change.
	# So we do the bad thing too and modify the superclass also

	@property
	def builtins(self):
		d = super(_ViewPageTemplateFileWithLoad,self).builtins
		d['__loader'] = self._loader
		# https://github.com/malthe/chameleon/issues/154
		# That's been fixed, so we should no longer
		# need to do this:
		## We try to get iteration order fixed here:
		#result = OrderedDict()
		#for k in sorted(d.keys()):
		#	result[k] = d[k]
		#return result
		return d

BaseTemplate.expression_types['load'] = PageTemplateFile.expression_types['load']

# Re-export our version
ViewPageTemplateFile = _ViewPageTemplateFileWithLoad

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
import yaml
import csv
import argparse
import sys
from zope.i18n import translate as ztranslate
import os.path
import z3c.pt.pagetemplate
import codecs
from zope.traversing import api as tapi
from chameleon.tal import RepeatDict

def main():
	arg_parser = argparse.ArgumentParser( description="Render a single file with JSON data" )
	arg_parser.add_argument( 'input', help="The input template" )
	arg_parser.add_argument( 'output', help="The output filename, or - for standard out." )
	arg_parser.add_argument( '--data',
							 dest='data',
							 help="The path to a filename to read to get the data for template options.\n"
							 "JSON, YAML or CSV can be used. If JSON or YAML, the options will be whatever was"
							 " specified in the file, typically a dictionary or array."
							 "If CSV, the first row should be a header row naming the fields, and the options"
							 " will be a list of dictionaries with those keys" )
	arg_parser.add_argument( '--repeat-on',
							 dest='repeat_on',
							 help="If given, a traversal path that specifies something that can be "
							 "iterated; the template will be applied repeatedly to the elements.")
	arg_parser.add_argument( '--repeat-on-sequence-name',
							 dest='repeat_on_sequence_name',
							 help="If given along with --repeat-on, this name will be bound in"
							 "the options dictionary as the sequence that --repeat-on is iterating"
							 )
	arg_parser.add_argument( '--repeat-on-name',
							 dest='repeat_on_name',
							 help="The name of the element being iterated. REQUIRED if --repeat-on is given")
	arg_parser.add_argument( '--repeat-as-iterable',
							 dest='repeat_iter',
							 action='store_true',
							 default=False,
							 help="If given, wrap each item from --repeat-on as a one-element list. This makes "
							 "it easy to convert templates to create multiple files and share the basic iteration code.")
	arg_parser.add_argument( '--repeat-filename-specific-path',
							 dest='repeat_filename',
							 help="If given, a TAL path evaluated for each item being repeated. If found and true, "
							 "used as a part of the filename, subject to mangling.")
	arg_parser.add_argument( '--json', dest='data' )
	arg_parser.add_argument( '--encoding',
							 dest='encoding',
							 help="The encoding of the output file." )

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
	options = {}
	if args.data:
		# Mac Excel likes to save CSV files with Mac line endings (\r)
		# which is weird and breaks the parser unless universal newlines
		# is in effect.
		openers = {'.csv':  ('rU', lambda x: list(csv.DictReader(x))),
				   '.yaml': ('rb', yaml.load),
				   '.json': ('rb', simplejson.load)}
		mode, func = openers[os.path.splitext(args.data)[1]]
		with open(args.data, mode) as data:
			options = func(data)

	encoding = args.encoding or 'utf-8'
	def _write(result, output):
		# The result of PT rendering is a unicode string.
		# If it contained actual non-ascii characters,
		# we need to pick an encoding on the way out.
		# Because we are in HTML/XML the safest thing to
		# do for an encoding that doesn't handle a given value
		# is to use an entity escape (however our default of utf8
		# should handle everything)
		with codecs.open(output, 'wb', encoding=encoding, errors='xmlcharrefreplace') as f:
			f.write( result )

	if args.repeat_on:
		output_base, output_ext = os.path.splitext( args.output )

		repeat_on = tapi.traverse( options, args.repeat_on )
		if args.repeat_on_sequence_name:
			repeat_on = list(repeat_on) # so multiple iterations work
			options[args.repeat_on_sequence_name] = repeat_on

		# Establish a repeat dict for the pages. This will be visible
		# as options/repeat, leaving the builtin repeat as specified.
		# (If our template class overrode _pt_get_context, we could
		# promote this to the top-level (builtin) scope (chameleon will
		# accept that, z3c.pt is the one that prevents it by wrapping
		# ALL keyword args in the options dict)).
		# When you specify the repeat_on_name, the RepeatItem will then be
		# available at 'options/repeat/$repeat_on_name', giving you access
		# to such things as 'index'.
		# NOTE: For that to work, we have to iterate across the returned
		# iterator, because the RepeatItem that's in the dict must stay in
		# sync, and it does this by peeking into the iterator itself.
		global_repeat = options['repeat'] = RepeatDict({})

		# register the repeat item...
		global_repeat(args.repeat_on_name, repeat_on)
		# ...get it...
		global_repeat_item  = global_repeat[args.repeat_on_name]
		# ...now iterate on it
		global_repitition_iterator = iter(global_repeat_item)

		for repitition_value in global_repitition_iterator:
			i = global_repeat_item.index # auto-advanced
			raw_val = repitition_value

			if args.repeat_iter: # wrap if required
				repitition_value = [repitition_value]

			options_for_this_repitition = options.copy()
			options_for_this_repitition[args.repeat_on_name] = repitition_value
			result = renderer( options_for_this_repitition, system )

			output_specific = None
			if args.repeat_filename:
				try:
					output_specific = tapi.traverse(raw_val, args.repeat_filename)
					output_specific = output_specific.strip()
					output_specific = output_specific.lower().replace(' ', '_')
					output_specific = output_specific.replace(os.path.sep, '_')
					if not output_specific:
						raise ValueError()
				except (KeyError,TypeError,ValueError):
					output_specific = None
			if output_specific is None:
				output_specific = str(i)

			output = output_base + os.path.extsep + output_specific + output_ext
			_write( result, output )
	else:
		result = renderer( options, system )
		_write( result, args.output )


	sys.exit( 0 )

if __name__ == '__main__':
	main()
