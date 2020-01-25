# -*- coding: utf-8 -*-
# Copyright (c) 2020 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# System imports
import typing as T
from weakref import WeakKeyDictionary, CallableProxyType, proxy as weakproxy

# Third-party imports
from observable import Observable

# Local imports


class WeakObservable(Observable):
    """An Observable with events that are objects instead of str, and we only keep weakrefs on them.
    Handlers will also be saved as proxies."""

    def __init__(self) -> None:
        super().__init__()
        self._events: WeakKeyDictionary[T.Any, T.List[CallableProxyType]] = WeakKeyDictionary()

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
                self._events[event].append(weakproxy(handler))
            return handlers[0]

        if handlers:
            return _on_wrapper(*handlers)
        return _on_wrapper
