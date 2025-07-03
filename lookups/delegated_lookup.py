# Copyright (c) 2021 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
Provides a lookup that redirects to another (dynamic) lookup, through a LookupProvider.
"""
# In original Java lookups, it corresponds to SimpleProxyLookup,
# itself accessible through Lookups.proxy().

from __future__ import annotations

# System imports
from typing import TYPE_CHECKING, Any, Callable, TypeVar
from weakref import WeakValueDictionary

# Third-party imports
from listeners import Listener, ListenerKind, Observable
from typing_extensions import override

# Local imports
from .lookup import Item, Lookup, LookupProvider, Result

T = TypeVar('T')
L = TypeVar('L', bound=Callable[..., Any])
if TYPE_CHECKING:
    from collections.abc import Sequence, Set


class DelegatedLookup(Lookup):
    """
    Implementation of a lookup that forward all requests to another lookup. The point being that
    the other lookup can change completely (ie. be a different object instance). This lookup remains
    the same object (obviously) and take care of handing over all the outstanding results and
    listener subscriptions to the new lookup.

    The delegate lookup is given by a LookupProvider. Just remember to call lookup_updated()
    whenever the delegate lookup changes.
    """

    def __init__(self, provider: LookupProvider) -> None:
        """
        Creates a new DelegatedLookup that gets its delegate from the supplied LookupProvider.
        The provider is immediately asked for a Lookup.

        :param provider: Lookup provider that will be asked when lookup_updated() is invoked.
        """
        super().__init__()

        self._provider = provider
        self._delegate = provider.get_lookup()
        self._results: WeakValueDictionary[type[object], DelegatedResult[Any]] = (
            WeakValueDictionary()
        )

    def lookup_updated(self) -> None:
        """
        Check for change in delegate lookup. This method purposedly does not take any lookup in
        parameter. Because only the provider given at creation time can supply a new lookup. The
        lookup provider is a priviledged API.
        """
        lookup = self._provider.get_lookup()
        if self._delegate != lookup:
            self._delegate = lookup

            for result in self._results.values():
                result.lookup_updated()

    @property
    def delegate(self) -> Lookup:
        """Returns the lookup we currently delegate to."""
        return self._delegate

    @override
    def lookup(self, cls: type[T]) -> T | None:
        return self._delegate.lookup(cls)

    @override
    def lookup_result(self, cls: type[T]) -> Result[T]:
        if (result := self._results.get(cls, None)) is not None:
            return result

        result = DelegatedResult[T](self, cls)
        self._results[cls] = result

        return result


class _DelegatedResultListeners(Observable[Callable[[Result[T]], Any]]):
    def __init__(self, result: DelegatedResult[T]) -> None:
        super().__init__()

        self.__result = result

    @override
    def _add_listener(self, listener: Listener[L], listener_kind: ListenerKind) -> None:
        # On the first listener, we setup our own listener on the delegate
        if not self:
            self.__result._delegate.listeners += self._proxy_listener

        super()._add_listener(listener, listener_kind)

    @override
    def _remove_listener(self, listener: Listener[L]) -> None:
        super()._remove_listener(listener)

        # On the last listener, we remove our own listener from the delegate
        if not self:
            self.__result._delegate.listeners -= self._proxy_listener

    def _proxy_listener(self, result: Result[T]) -> None:
        self(self.__result)


class DelegatedResult(Result[T]):
    """
    Implementation of a result that supports changing lookup source.
    When lookup_updated() is invoked (from DelegatedLookup.lookup_updated()), the actual result is
    switched over from the old lookup delegate to the new. Listeners are also notified if the
    switch over happens to modify the content of this result.
    """

    def __init__(self, lookup: DelegatedLookup, cls: type[T]) -> None:
        """
        Creates a new DelegatedResult for the given class.

        A result is immediately asked to the delegate lookup.
        """
        super().__init__()

        self._lookup = lookup
        self._cls = cls
        self._delegate = self._lookup.delegate.lookup_result(self._cls)
        self.listeners: _DelegatedResultListeners[T] = _DelegatedResultListeners(self)

    def lookup_updated(self) -> None:
        result = self._lookup.delegate.lookup_result(self._cls)
        if result != self._delegate:
            old_result, self._delegate = self._delegate, result

            if self.listeners:
                old_result.listeners -= self.listeners._proxy_listener

                # If these results contains some instances, trigger the listeners.
                # Use all_classes() (that should internally use Item.get_type()) instead of
                # all_instances() to avoid loading instances of converted items.
                if old_result.all_classes() or result.all_classes():
                    self.listeners._proxy_listener(result)

                result.listeners += self.listeners._proxy_listener

            del old_result  # Explicit

    @override
    def all_classes(self) -> Set[type[T]]:
        return self._delegate.all_classes()

    @override
    def all_instances(self) -> Sequence[T]:
        return self._delegate.all_instances()

    @override
    def all_items(self) -> Sequence[Item[T]]:
        return self._delegate.all_items()
