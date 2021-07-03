# -*- coding: utf-8 -*-
# Copyright (c) 2019 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# System imports

# Third-party imports

# Local imports
from .lookup import (
    Lookup, Result, Item,
    LookupProvider,
)
from .lookups import singleton, fixed, EmptyLookup
from .simple import SimpleLookup
from .generic_lookup import GenericLookup, AbstractLookup
from .instance_content import InstanceContent, Convertor
from .delegated_lookup import DelegatedLookup
from .proxy_lookup import ProxyLookup
from .entry_point import EntryPointLookup
from .__about__ import (
    __title__, __summary__, __uri__, __version__,
    __author__, __email__, __license__, __copyright__,
)

__all__ = [
    'Lookup', 'Result', 'Item',
    'LookupProvider',
    'GenericLookup', 'AbstractLookup', 'InstanceContent', 'Convertor',
    'SimpleLookup',
    'DelegatedLookup', 'ProxyLookup', 'EntryPointLookup',
    'singleton', 'fixed', 'EmptyLookup',

    '__title__', '__summary__', '__uri__', '__version__',
    '__author__', '__email__', '__license__', '__copyright__',
]
