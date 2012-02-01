#!/usr/bin/env python

from pyramid import traversal

resource_path = traversal.resource_path
find_interface = traversal.find_interface
lineage = traversal.lineage

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
	result = traversal.resource_path( res )
	result = result.replace( '//', '/' )
	return result
