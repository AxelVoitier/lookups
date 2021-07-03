# -*- coding: utf-8 -*-
# Copyright (c) 2021 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
'''
Provides a lookup that merge results from several lookups.
'''

# System imports
from itertools import chain
from typing import Sequence, MutableSequence, AbstractSet, Type, Optional, Callable
from weakref import WeakValueDictionary  # , WeakSet

# Third-party imports

# Local imports
from .lookup import Lookup, Item, Result
from .weak_observable import WeakCallable


class ProxyLookup(Lookup):
    '''
    Implementation of a lookup that concile results from multiple lookups at the same time.
    '''

    def __init__(self, *lookups: Lookup) -> None:
        '''
        Creates a new ProxyLookup from an optional list of lookups to use as sources.

        :param lookups: Initial lookup sources.
        '''
        self._lookups = list(lookups)
        self._results: WeakValueDictionary[Type[object], PLResult] = WeakValueDictionary()

        super().__init__()

    def add_lookup(self, lookup: Lookup) -> None:
        '''
        Adds a lookup to the list of sources for the proxy.
        Will update all results accordingly
        '''
        self._lookups.append(lookup)
        for result in self._results.values():
            result._lookup_added(lookup)

    def remove_lookup(self, lookup: Lookup) -> None:
        '''
        Removes a lookup from the list of sources for the proxy.
        Will update all results accordingly
        '''
        self._lookups.remove(lookup)
        for result in self._results.values():
            result._lookup_removed(lookup)

    def lookup(self, cls: Type[object]) -> Optional[object]:
        for lookup in self._lookups:
            obj = lookup(cls)
            if obj is not None:
                return obj
        else:
            return None

    def lookup_item(self, cls: Type[object]) -> Optional[Item]:
        for lookup in self._lookups:
            item = lookup.lookup_item(cls)
            if item is not None:
                return item
        else:
            return None

    def lookup_result(self, cls: Type[object]) -> Result:
        result = self._results.get(cls, None)
        if result is not None:
            return result

        result = PLResult(self, cls)
        self._results[cls] = result

        return result


class PLResult(Result):
    '''
    Implementation of a composite result that supports having multiple lookup sources.
    When _lookup_added() or _lookup_removed() are invoked (from ProxyLookup.add/remove_lookup()),
    listeners will be notified if instances appears or dissapears from the composite result.
    '''

    def __init__(self, lookup: ProxyLookup, cls: Type[object]) -> None:
        self._lookup = lookup
        self._cls = cls
        self._listeners: MutableSequence[WeakCallable] = []

        self._results = {
            lookup: lookup.lookup_result(cls)
            for lookup in self._lookup._lookups
        }

    def _lookup_added(self, lookup: Lookup) -> None:
        result = lookup.lookup_result(self._cls)
        self._results[lookup] = result

        if self._listeners:
            # If this new result already contains some instances, trigger the listeners.
            # Use all_classes() (that should internally use Item.get_type()) instead of
            # all_instances() to avoid loading instances of converted items.
            if result.all_classes():
                self._proxy_listener(result)

            result.add_lookup_listener(self._proxy_listener)

    def _lookup_removed(self, lookup: Lookup) -> None:
        result = self._results[lookup]

        if self._listeners:
            result.remove_lookup_listener(self._proxy_listener)

            # If this result contained some instances, trigger the listeners.
            # Use all_classes() (that should internally use Item.get_type()) instead of
            # all_instances() to avoid loading instances of converted items.
            if result.all_classes():
                self._proxy_listener(result)

        del self._results[lookup]
        del result

    def add_lookup_listener(self, listener: Callable[[Result], None]) -> None:
        if not self._listeners:
            for result in self._results.values():
                result.add_lookup_listener(self._proxy_listener)

        self._listeners.append(WeakCallable(listener, self._listeners.remove))

    def remove_lookup_listener(self, listener: Callable[[Result], None]) -> None:
        self._listeners.remove(listener)  # type: ignore

        if not self._listeners:
            for result in self._results.values():
                result.remove_lookup_listener(self._proxy_listener)

    def _proxy_listener(self, result: Result) -> None:
        for listener in self._listeners:
            listener(self)

    def all_classes(self) -> AbstractSet[Type[object]]:
        return frozenset(chain(*(
            result.all_classes()
            for result in self._results.values()
        )))

    def all_instances(self) -> Sequence[object]:
        return tuple(chain(*(
            result.all_instances()
            for result in self._results.values()
        )))

    def all_items(self) -> Sequence[Item]:
        return tuple(chain(*(
            result.all_items()
            for result in self._results.values()
        )))
