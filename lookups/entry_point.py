# -*- coding: utf-8 -*-
# Copyright (c) 2021 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
'''
Provides a lookup that get its instances from package entry points.
'''

# System imports
try:
    from importlib import metadata
except ImportError:
    import importlib_metadata as metadata  # type: ignore

# Third-party imports

# Local imports
from . import SimpleLookup


class EntryPointLookup(SimpleLookup):
    '''
    Implementation of a lookup that loads its instances from a specified entry-point group.
    Current implementation is simple and static. It might change in the future.
    '''

    def __init__(self, group: str) -> None:
        '''
        Creates new EntryPointLookup object from supplied entry-point group name.
        Entry-points are instantiated using a no-arg constructor call.
        All entry-points are loaded and instantiated at creation.

        Future implementations could potentially do lazy loading, as well as "listen" for dynamic
        changes in the entry-point list (to support case of plugin loading/unloading).

        If the group does not exists or is empty, it will just create an empty lookup instead of
        raising an exception. This is to be in-line with future implementation that might support
        dynamic entry-points, and so could potentially start with an empty group at first.

        :param group: Entry-point group to load instances from.
        '''
        eps = metadata.entry_points()  # type: ignore
        try:
            group_eps = eps[group]
        except KeyError:
            instances = []
        else:
            instances = [ep.load()() for ep in group_eps]

        super().__init__(*instances)
