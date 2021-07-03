# -*- coding: utf-8 -*-
# Copyright (c) 2020 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# System imports
import typing as T
from types import MethodType
from weakref import WeakKeyDictionary, WeakMethod, ref, ReferenceType

# Third-party imports
from observable import Observable

# Local imports


class WeakCallable:

    def __init__(self, callable: T.Callable, callback: T.Optional[T.Callable] = None) -> None:
        self._ref: ReferenceType
        if isinstance(callable, MethodType):
            self._ref = WeakMethod(callable, callback)
        else:
            self._ref = ref(callable, callback)

    def __call__(self, *args: T.Any, **kwargs: T.Any) -> T.Any:
        callable = self._ref()
        if callable is not None:
            return callable(*args, **kwargs)

    @property
    def ref(self) -> T.Any:
        return self._ref()

    def __eq__(self, other: T.Any) -> bool:
        if isinstance(other, WeakCallable):
            return self._ref.__eq__(other._ref)
        elif isinstance(other, ref):
            return self._ref.__eq__(other)
        else:
            return self._ref().__eq__(other)

    def __ne__(self, other: T.Any) -> bool:
        if isinstance(other, WeakCallable):
            return self._ref.__ne__(other._ref)
        elif isinstance(other, ref):
            return self._ref.__ne__(other)
        else:
            return self._ref().__ne__(other)

    def __hash__(self) -> int:
        return hash(self._ref)


class WeakObservable(Observable):
    """An Observable with events that are objects instead of str, and we only keep weakrefs on them.
    Handlers will also be saved as proxies."""

    def __init__(self) -> None:
        super().__init__()
        self._events: WeakKeyDictionary[T.Any, T.List[WeakCallable]] = WeakKeyDictionary()

    def on(  # pylint: disable=invalid-name
        self, event: T.Any, *handlers: T.Callable
    ) -> T.Callable:
        """Registers one or more handlers to a specified event.
        This method may as well be used as a decorator for the handler."""

        def _on_wrapper(*handlers: T.Callable) -> T.Callable:
            """wrapper for on decorator"""
            if event not in self._events:
                self._events[event] = []
            for handler in handlers:
                self._events[event].append(WeakCallable(handler, self._events[event].remove))
            return handlers[0]

        if handlers:
            return _on_wrapper(*handlers)
        return _on_wrapper
