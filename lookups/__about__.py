# Copyright (c) 2019 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# System imports
from importlib import metadata

# Third-party imports

# Local imports


__all__ = [
    '__author__',
    '__copyright__',
    '__email__',
    '__license__',
    '__summary__',
    '__title__',
    '__uri__',
    '__version__',
]

mtdt = metadata.metadata('lookups')

__title__ = mtdt['Name']
__summary__ = mtdt['Summary']
__uri__ = mtdt['Home-page']

__version__ = mtdt['Version']

__author__ = mtdt['Author']
__email__ = mtdt['Author-email']

__license__ = mtdt['License']
__copyright__ = 'Copyright 2019 Lookups contributors (see AUTHORS.md)'
