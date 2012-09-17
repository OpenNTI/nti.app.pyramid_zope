#!/usr/bin/env python

from pyramid import traversal

#resource_path = traversal.resource_path
find_interface = traversal.find_interface
lineage = traversal.lineage

from zope.location.interfaces import LocationError

from zope.location import interfaces as loc_interfaces

import urllib


from zope import interface
from zope.event import notify
from zope.traversing import api as ztraversing
from zope.traversing.interfaces import BeforeTraverseEvent, ITraversable

from zope.deferredimport import deprecatedFrom
deprecatedFrom( "Prefer nti.dataserver.traversal",
				"nti.dataserver.traversal",
				"resource_path", "normal_resource_path" )

import pyramid.interfaces
from pyramid.interfaces import VH_ROOT_KEY
from pyramid.compat import is_nonstr_iter, decode_path_info
from pyramid.exceptions import URLDecodeError

split_path_info = traversal.split_path_info
empty = traversal.empty

@interface.implementer(pyramid.interfaces.ITraverser)
class ZopeResourceTreeTraverser(traversal.ResourceTreeTraverser):
	"""
	A :class:`ITraverser` based on pyramid's default traverser, but modified to
	use the zope.traversing machinery instead of (only) dictionary lookups.
	This provides is with the flexibility of the :class:`zope.traversing.interfaces.ITraversable`
	adapter pattern, plus the support of namespace lookups (:func:`zope.traversing.namespace.nsParse`
	and :func:`zope.traversing.namespace.namespaceLookup`)
	"""

	def __init__(self, root):
		traversal.ResourceTreeTraverser.__init__( self, root )

	def __call__(self, request):
		# JAM: Unfortunately, the superclass implementation is entirely monolithic
		# and we so we cannot reuse any part of it. Instead,
		# we copy-and-paste it. Unless otherwise noted, comments below are
		# original.
		# JAM: Note the abundance of no covers. These are for features we are
		# not currently using and the code is lifted directly from pyramid.
		environ = request.environ

		if request.matchdict is not None:
			matchdict = request.matchdict

			path = matchdict.get('traverse', '/') or '/'
			if is_nonstr_iter(path):
				# this is a *traverse stararg (not a {traverse})
				# routing has already decoded these elements, so we just
				# need to join them
				path = '/'.join(path) or '/'

			subpath = matchdict.get('subpath', ())
			if not is_nonstr_iter(subpath):  # pragma: no cover
				# this is not a *subpath stararg (just a {subpath})
				# routing has already decoded this string, so we just need
				# to split it
				subpath = split_path_info(subpath)

		else:  # pragma: no cover
			# this request did not match a route
			subpath = ()
			try:
				# empty if mounted under a path in mod_wsgi, for example
				path = decode_path_info(environ['PATH_INFO'] or '/')
			except KeyError:
				path = '/'
			except UnicodeDecodeError as e:
				raise URLDecodeError(e.encoding, e.object, e.start, e.end,
									 e.reason)

		if VH_ROOT_KEY in environ: # pragma: no cover
			# HTTP_X_VHM_ROOT
			vroot_path = decode_path_info(environ[VH_ROOT_KEY])
			vroot_tuple = split_path_info(vroot_path)
			vpath = vroot_path + path # both will (must) be unicode or asciistr
			vroot_idx = len(vroot_tuple) - 1
		else:
			vroot_tuple = ()
			vpath = path
			vroot_idx = -1

		root = self.root
		ob = vroot = root

		if vpath == '/': # invariant: vpath must not be empty
			# prevent a call to traversal_path if we know it's going
			# to return the empty tuple
			vpath_tuple = ()
		else:
			# we do dead reckoning here via tuple slicing instead of
			# pushing and popping temporary lists for speed purposes
			# and this hurts readability; apologies
			i = 0
			view_selector = self.VIEW_SELECTOR
			vpath_tuple = split_path_info(vpath)
			for segment in vpath_tuple:
				# JAM: Fire traversal events, mainly so sites get installed. See
				# zope.publisher.base.
				notify( BeforeTraverseEvent( ob, request ) )
				# JAM: Notice that checking for '@@' is special cased, and
				# doesn't go through the normal namespace lookup as it would in
				# plain zope traversal.
				if segment.startswith( view_selector ): # pragma: no cover
					return {'context': ob,
							'view_name': segment[2:],
							'subpath': vpath_tuple[i + 1:],
							'traversed': vpath_tuple[:vroot_idx + i + 1],
							'virtual_root': vroot,
							'virtual_root_path': vroot_tuple,
							'root': root}

				try:
					# JAM: This is where we differ. instead of using __getitem__,
					# we use the traversing machinery.
					# TODO: The zope app would use IPublishTraverser, which
					# would install security proxies along the way. We probably don't need to
					# do that?
					# NOTE: By passing the request here, we require all traversers
					# (including the namespace traversers) to be registered as multi-adapters.
					# None of the default namespaces are. See our configure.zcml for what is.

					# Note: We're not allowing modification of further_path. This wil raise an error.
					# It can be important to have that information during traversal, though, so that's why we pass
					# it. That's the primary difference between traverseName and traversePathElement

					# JAM: Damn stupid implementation of traversePathElement ignores
					# the request argument to find a traversable /except/ when a namespace is found.
					# therefore, we explicitly query for the multi adapter ourself in the non-namespace case
					# (In the namespace case, we let traversing handle it, because it needs a named adapter
					# after parsing)
					traversable = None
					if segment and segment[0] not in '+@' and not ITraversable.providedBy( ob ):
						try:
							traversable = request.registry.queryMultiAdapter( (ob, request), ITraversable )
						except TypeError:
							# Some things are registered for "*" (DefaultTraversable) which means they get called
							# here. If they can't take two arguments, then we bail. Sucks.
							pass
					next_ob = ztraversing.traversePathElement( ob, segment, vpath_tuple[i+1:],
															   traversable=traversable,
															   request=request )
				except LocationError:
					# LocationError is a type of KeyError. The DefaultTraversable turns
					# plain KeyError and TypeErrors into LocationError.
					return {'context': ob,
							'view_name': segment,
							'subpath': vpath_tuple[ i + 1:],
							'traversed': vpath_tuple[:vroot_idx + i + 1],
							'virtual_root': vroot,
							'virtual_root_path': vroot_tuple,
							'root': root}
				if i == vroot_idx: # pragma: no cover
					vroot = next_ob
				ob = next_ob
				i += 1

		# JAM: Also fire before traversal for the actual context item, since we
		# won't actually traverse into it. Be sure not to fire multiple times for this (E.g., the root)
		# This logic is complicated by the multi-returns above.
		notify( BeforeTraverseEvent( ob, request ) )

		return {'context': ob,
				'view_name': empty,
				'subpath': subpath,
				'traversed': vpath_tuple,
				'virtual_root': vroot,
				'virtual_root_path': vroot_tuple,
				'root': root}
