# Copyright (c) 2021 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
Provides a lookup that merge results from several lookups.
"""

from __future__ import annotations

# System imports
from itertools import chain
from typing import TYPE_CHECKING, TypeVar
from weakref import WeakValueDictionary  # , WeakSet

# Third-party imports
from typing_extensions import override

# Local imports
from .lookup import Item, Lookup, Result
from .weak_observable import WeakCallable

T = TypeVar('T')
if TYPE_CHECKING:
    from collections.abc import MutableSequence, Sequence, Set
    from typing import Any, Callable


class ProxyLookup(Lookup):
    """
    Implementation of a lookup that concile results from multiple lookups at the same time.
    """

    def __init__(self, *lookups: Lookup) -> None:
        """
        Creates a new ProxyLookup from an optional list of lookups to use as sources.

        :param lookups: Initial lookup sources.
        """
        super().__init__()

        self._lookups = list(lookups)
        self._results: WeakValueDictionary[type[Any], PLResult[Any]] = WeakValueDictionary()

    def add_lookup(self, lookup: Lookup) -> None:
        """
        Adds a lookup to the list of sources for the proxy.
        Will update all results accordingly
        """
        self._lookups.append(lookup)
        for result in self._results.values():
            result._lookup_added(lookup)

    def remove_lookup(self, lookup: Lookup) -> None:
        """
        Removes a lookup from the list of sources for the proxy.
        Will update all results accordingly
        """
        self._lookups.remove(lookup)
        for result in self._results.values():
            result._lookup_removed(lookup)

    @override
    def lookup(self, cls: type[T]) -> T | None:
        for lookup in self._lookups:
            obj = lookup(cls)
            if obj is not None:
                return obj

        return None

    @override
    def lookup_item(self, cls: type[T]) -> Item[T] | None:
        for lookup in self._lookups:
            item = lookup.lookup_item(cls)
            if item is not None:
                return item

        return None

    @override
    def lookup_result(self, cls: type[T]) -> Result[T]:
        result = self._results.get(cls, None)
        if result is not None:
            return result

        result = PLResult(self, cls)
        self._results[cls] = result

        return result


class PLResult(Result[T]):
    """
    Implementation of a composite result that supports having multiple lookup sources.
    When _lookup_added() or _lookup_removed() are invoked (from ProxyLookup.add/remove_lookup()),
    listeners will be notified if instances appears or dissapears from the composite result.
    """

    def __init__(self, lookup: ProxyLookup, cls: type[T]) -> None:
        super().__init__()

        self._lookup = lookup
        self._cls = cls
        self._listeners: MutableSequence[WeakCallable[[Result[T]], Any]] = []

        self._results = {lookup: lookup.lookup_result(cls) for lookup in self._lookup._lookups}

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

    @override
    def add_lookup_listener(self, listener: Callable[[Result[T]], Any]) -> None:
        if not self._listeners:
            for result in self._results.values():
                result.add_lookup_listener(self._proxy_listener)

        self._listeners.append(WeakCallable(listener, self.remove_lookup_listener))

    @override
    def remove_lookup_listener(self, listener: Callable[[Result[T]], Any]) -> None:
        self._listeners.remove(listener)  # pyright: ignore[reportArgumentType]  # WeakCallable.__eq__ handles it transparently

        if not self._listeners:
            for result in self._results.values():
                result.remove_lookup_listener(self._proxy_listener)

    def _proxy_listener(self, result: Result[T]) -> None:
        for listener in self._listeners:
            listener(self)

    @override
    def all_classes(self) -> Set[type[T]]:
        return frozenset(chain(*(result.all_classes() for result in self._results.values())))

    @override
    def all_instances(self) -> Sequence[T]:
        return tuple(chain(*(result.all_instances() for result in self._results.values())))

    @override
    def all_items(self) -> Sequence[Item[T]]:
        return tuple(chain(*(result.all_items() for result in self._results.values())))
