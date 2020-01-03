#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
I18N related interfaces.

.. $Id$
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from pyramid.interfaces import IRequest

__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)



class IPreferredLanguagesRequest(IRequest):
    """
    An extension to a standard request used as a marker.
    """
