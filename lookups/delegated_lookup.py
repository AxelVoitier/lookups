# -*- coding: utf-8 -*-
# Copyright (c) 2021 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
'''
Provides a lookup that redirects to another (dynamic) lookup, through a LookupProvider.
'''
# In original Java lookups, it corresponds to SimpleProxyLookup,
# itself accessible through Lookups.proxy().

# System imports
from typing import Sequence, MutableSequence, AbstractSet, Type, Optional, Callable
from weakref import WeakValueDictionary

# Third-party imports

# Local imports
from .lookup import Lookup, Item, Result, LookupProvider
from .weak_observable import WeakCallable


class DelegatedLookup(Lookup):
    '''
    Implementation of a lookup that forward all requests to another lookup. The point being that
    the other lookup can change completely (ie. be a different object instance). This lookup remains
    the same object (obviously) and take care of handing over all the outstanding results and
    listener subscriptions to the new lookup.

    The delegate lookup is given by a LookupProvider. Just remember to call lookup_updated()
    whenever the delegate lookup changes.
    '''

    def __init__(self, provider: LookupProvider) -> None:
        '''
        Creates a new DelegatedLookup that gets its delegate from the supplied LookupProvider.
        The provider is immediately asked for a Lookup.

        :param provider: Lookup provider that will be asked when lookup_updated() is invoked.
        '''
        self._provider = provider
        self._delegate = provider.get_lookup()
        self._results: WeakValueDictionary[Type[object], DelegatedResult] = WeakValueDictionary()

    def lookup_updated(self) -> None:
        '''
        Check for change in delegate lookup. This method purposedly does not take any lookup in
        parameter. Because only the provider given at creation time can supply a new lookup. The
        lookup provider is a priviledged API.
        '''
        lookup = self._provider.get_lookup()
        if self._delegate != lookup:
            self._delegate = lookup

            for result in self._results.values():
                result.lookup_updated()

    @property
    def delegate(self) -> Lookup:
        '''Returns the lookup we currently delegate to.'''
        return self._delegate

    def lookup(self, cls: Type[object]) -> Optional[object]:
        return self._delegate.lookup(cls)

    def lookup_result(self, cls: Type[object]) -> Result:
        result = self._results.get(cls, None)
        if result is not None:
            return result

        result = DelegatedResult(self, cls)
        self._results[cls] = result

        return result


class DelegatedResult(Result):
    '''
    Implementation of a result that supports changing lookup source.
    When lookup_updated() is invoked (from DelegatedLookup.lookup_updated()), the actual result is
    switched over from the old lookup delegate to the new. Listeners are also notified if the
    switch over happens to modify the content of this result.
    '''

    def __init__(self, lookup: DelegatedLookup, cls: Type[object]) -> None:
        '''
        Creates a new DelegatedResult for the given class.

        A result is immediately asked to the delegate lookup.
        '''
        self._lookup = lookup
        self._cls = cls
        self._delegate = self._lookup.delegate.lookup_result(self._cls)
        self._listeners: MutableSequence[WeakCallable] = []

    def lookup_updated(self) -> None:
        result = self._lookup.delegate.lookup_result(self._cls)
        if result != self._delegate:
            old_result, self._delegate = self._delegate, result

            if self._listeners:
                old_result.remove_lookup_listener(self._proxy_listener)

                # If these results contains some instances, trigger the listeners.
                # Use all_classes() (that should internally use Item.get_type()) instead of
                # all_instances() to avoid loading instances of converted items.
                if old_result.all_classes() or result.all_classes():
                    self._proxy_listener(result)

                result.add_lookup_listener(self._proxy_listener)

            del old_result  # Explicit

    def add_lookup_listener(self, listener: Callable[[Result], None]) -> None:
        if not self._listeners:
            self._delegate.add_lookup_listener(self._proxy_listener)

        self._listeners.append(WeakCallable(listener, self._listeners.remove))

    def remove_lookup_listener(self, listener: Callable[[Result], None]) -> None:
        self._listeners.remove(listener)  # type: ignore

        if not self._listeners:
            self._delegate.remove_lookup_listener(self._proxy_listener)

    def _proxy_listener(self, result: Result) -> None:
        for listener in self._listeners:
            listener(self)

    def all_classes(self) -> AbstractSet[Type[object]]:
        return self._delegate.all_classes()

    def all_instances(self) -> Sequence[object]:
        return self._delegate.all_instances()

    def all_items(self) -> Sequence[Item]:
        return self._delegate.all_items()
