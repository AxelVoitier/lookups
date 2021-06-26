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
from observable import Observable, EventNotFound, HandlerNotFound

# Local imports


class WeakObservable(Observable):
    """An Observable with events that are objects instead of str, and we only keep weakrefs on them.
    Handlers will also be saved as proxies."""

    def __init__(self) -> None:
        super().__init__()
        self._events: WeakKeyDictionary[T.Any, T.List[ReferenceType]] = WeakKeyDictionary()

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
                if isinstance(handler, MethodType):
                    self._events[event].append(WeakMethod(handler))
                else:
                    self._events[event].append(ref(handler))
            return handlers[0]

        if handlers:
            return _on_wrapper(*handlers)
        return _on_wrapper

    def off(  # pylint: disable=keyword-arg-before-vararg
            self, event: T.Any = None, *handlers: T.Callable
    ) -> None:
        """Unregisters a whole event (if no handlers are given) or one
        or more handlers from an event.
        Raises EventNotFound when the given event isn't registered.
        Raises HandlerNotFound when a given handler isn't registered."""

        if not event:
            self._events.clear()
            return

        if event not in self._events:
            raise EventNotFound(event)

        if not handlers:
            self._events.pop(event)
            return

        for callback in handlers:
            callback_ref: ReferenceType
            if isinstance(callback, MethodType):
                callback_ref = WeakMethod(callback)
            else:
                callback_ref = ref(callback)

            if callback_ref not in self._events[event]:
                raise HandlerNotFound(event, callback)

            while callback_ref in self._events[event]:
                self._events[event].remove(callback_ref)
        return

    def trigger(self, event: T.Any, *args: T.Any, **kw: T.Any) -> bool:
        """Triggers all handlers which are subscribed to an event.
        Returns True when there were callbacks to execute, False otherwise."""

        callbacks = list(self._events.get(event, []))
        if not callbacks:
            return False

        for callback_ref in callbacks:
            callback = callback_ref()
            if callback is not None:
                callback(*args, **kw)
            else:
                callbacks.remove(callback_ref)
        return True
