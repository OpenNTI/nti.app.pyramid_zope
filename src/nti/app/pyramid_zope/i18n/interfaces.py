#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
I18N related interfaces.

.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from pyramid.interfaces import IRequest


class IPreferredLanguagesRequest(IRequest):
    """
    An extension to a standard request used as a marker.
    """
