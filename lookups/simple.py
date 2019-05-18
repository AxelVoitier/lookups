# -*- coding: utf-8 -*-
# Copyright (c) 2019 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# System imports
from typing import Sequence, AbstractSet, Type, Optional

# Third-party imports

# Local imports
from . import lookups
from .lookup import Lookup, Result, Item, LookupListener


class SimpleLookup(Lookup):
    '''
    Simple lookup implementation. It can be used to create temporary lookups that do not change over
    time. The result stores references to all objects passed in the constructor. Those objecst are
    the only ones returned as result.
    '''

    def __init__(self, *instances: object) -> None:
        '''
        Creates new SimpleLookup object with supplied instances parameter.

        :param instances: Instances to be used to return from the lookup.
        '''
        self.all_items: Sequence[Item] = tuple(
            lookups.LookupItem(instance) for instance in instances)

    def lookup(self, cls: Type[object]) -> Optional[object]:
        for item in self.all_items:
            if issubclass(item.get_type(), cls):
                return item.get_instance()
        else:
            return None

    def lookup_result(self, cls: Type[object]) -> Result:
        return SimpleResult(self, cls)


class SimpleResult(Result):
    '''
    Result used in SimpleLookup. It holds a reference to the collection passed in constructor.
    As the contents of this lookup result never changes the add_lookup_listener() and
    remove_lookup_listener do not do anything.
    '''

    def __init__(self, simple_lookup: SimpleLookup, cls: Type[object]) -> None:
        self.lookup = simple_lookup
        self.cls = cls
        self._items: Optional[Sequence[Item]] = None

    def add_lookup_listener(self, listener: LookupListener) -> None:
        pass

    def remove_lookup_listener(self, listener: LookupListener) -> None:
        pass

    def all_classes(self) -> AbstractSet[Type[object]]:
        return frozenset(
            item.get_type() for item in self.all_items()
        )

    def all_instances(self) -> Sequence[object]:
        return tuple(filter(
            None,
            (item.get_instance() for item in self.all_items())
        ))

    def all_items(self) -> Sequence[Item]:
        if self._items is None:
            self._items = tuple(
                item for item in self.lookup.all_items
                if issubclass(item.get_type(), self.cls)
            )

        return self._items
