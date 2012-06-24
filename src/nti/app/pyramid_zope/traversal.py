#!/usr/bin/env python

from pyramid import traversal

#resource_path = traversal.resource_path
find_interface = traversal.find_interface
lineage = traversal.lineage

from zope.location import traversing as ztraversing
from zope.location import interfaces as loc_interfaces

import urllib

def resource_path( res ):
	# This function is somewhat more flexible than pyramids, and
	# also more strict. It requires strings (not None, for example)
	# and bottoming out an at IRoot. This helps us get things right.
	# It is probably also a bit slower.
	return urllib.quote( loc_interfaces.ILocationInfo( res ).getPath() )

def normal_resource_path( res ):
	"""
	:return: The result of traversing the containers of `res`,
	but normalized by removing double slashes. This is useful
	when elements in the containment hierarchy do not have
	a name; however, it can hide bugs when all elements are expected
	to have names.
	"""
	# If this starts to get complicated, we can take a dependency
	# on the urlnorm library
	result = resource_path( res )
	result = result.replace( '//', '/' )
	# Our LocalSiteManager is sneaking in here, which we don't want...
	#result = result.replace( '%2B%2Betc%2B%2Bsite/', '' )
	return result
