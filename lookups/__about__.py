# -*- coding: utf-8 -*-
# Copyright (c) 2019 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# System imports
try:
    from importlib import metadata
except ImportError:
    import importlib_metadata as metadata  # type: ignore

# Third-party imports

# Local imports


__all__ = [
    '__title__', '__summary__', '__uri__', '__version__',
    '__author__', '__email__', '__license__', '__copyright__',
]

mtdt = metadata.metadata('lookups')  # type: ignore

__title__ = mtdt['Name']
__summary__ = mtdt['Summary']
__uri__ = mtdt['Home-page']

__version__ = mtdt['Version']

__author__ = mtdt['Author']
__email__ = mtdt['Author-email']

__license__ = mtdt['License']
__copyright__ = 'Copyright 2019 Lookups contributors (see AUTHORS.md)'
