#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DOCUMENT ME.
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

import os
from six import string_types

from zope.browserpage import viewpagetemplatefile

# Make viewlets use our version of page template files
# Unfortunately, the zope.browserpage VPT is slightly
# incompatible in calling convention
from zope.viewlet import viewlet

from zope.pagetemplate.pagetemplatefile import package_home

from z3c.template import template

from nti.app.pyramid_zope.z3c_zpt import ViewPageTemplateFile

logger = __import__('logging').getLogger(__name__)

# Best to use a class not a function to avoid changing
# calling depth

class _VPT(ViewPageTemplateFile):

    def __init__(self, filename, _prefix=None, content_type=None):
        path = _prefix
        if not isinstance(path, string_types) and path is not None:
            # zope likes to pass the globals
            path = package_home(path)
        # TODO: The correct values for reload and debug come from
        # pyramid settings. Can we get to that from here?
        auto_reload = os.getenv('PYRAMID_RELOAD_TEMPLATES')
        debug = os.getenv('PYRAMID_DEBUG_TEMPLATES')
        ViewPageTemplateFile.__init__(self, filename, path=path,
                                      content_type=content_type,
                                      auto_reload=auto_reload,
                                      debug=debug)


if viewlet.ViewPageTemplateFile is viewpagetemplatefile.ViewPageTemplateFile:
    # TODO: Formalize this
    logger.debug("Monkey-patching zope.viewlet to use z3c.pt")
    viewlet.ViewPageTemplateFile = _VPT

if template.ViewPageTemplateFile is viewpagetemplatefile.ViewPageTemplateFile:
    # They claim that including of z3c.ptcompat does this, I'm not
    # convinced
    logger.debug("Monkey-patching z3c.template to use z3c.pt")
    template.ViewPageTemplateFile = _VPT
