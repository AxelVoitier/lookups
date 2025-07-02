# Copyright (c) 2020 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

# System imports
from types import MethodType
from typing import TYPE_CHECKING, Generic, TypeVar
from weakref import WeakKeyDictionary, WeakMethod, ref

# Third-party imports
from observable import Observable  # pyright: ignore[reportMissingTypeStubs]  # Can't do much...
from typing_extensions import ParamSpec, override

# Local imports

P = ParamSpec('P')
R = TypeVar('R')
if TYPE_CHECKING:
    from typing import Any, Callable
    # from weakref import ReferenceType


class WeakCallable(Generic[P, R]):
    def __init__(
        self,
        callable: Callable[P, R],
        callback: Callable[[Callable[P, R]], Any] | None = None,
        # Not true (the true form is bellow), but we ensure compatiblity,
        # so we simplify the signature for our callers
        # callback: Callable[[ReferenceType[Callable[P, R]]], Any] | None = None,
    ) -> None:
        super().__init__()

        if isinstance(callable, MethodType):
            self._ref = WeakMethod(callable, callback)  # pyright: ignore[reportArgumentType]  # Due to our signature simplification
        else:
            self._ref = ref(callable, callback)  # pyright: ignore[reportArgumentType]  # Due to our signature simplification

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R | None:
        callable = self._ref()
        if callable is not None:
            return callable(*args, **kwargs)

        return None

    @property
    def ref(self) -> Callable[P, R] | None:
        return self._ref()

    @override
    def __eq__(self, other: object) -> bool:
        if isinstance(other, WeakCallable):
            return self._ref.__eq__(other._ref)
        elif isinstance(other, ref):
            return self._ref.__eq__(other)  # pyright: ignore[reportUnknownArgumentType]  # It thinks it is a ReferenceType[Unknown]...
        else:
            return self._ref().__eq__(other)

    @override
    def __ne__(self, other: object) -> bool:
        if isinstance(other, WeakCallable):
            return self._ref.__ne__(other._ref)
        elif isinstance(other, ref):
            return self._ref.__ne__(other)  # pyright: ignore[reportUnknownArgumentType]  # It thinks it is a ReferenceType[Unknown]...
        else:
            return self._ref().__ne__(other)

    @override
    def __hash__(self) -> int:
        return hash(self._ref)


class WeakObservable(Observable):
    """An Observable with events that are objects instead of str, and we only keep weakrefs on them.
    Handlers will also be saved as proxies."""

    def __init__(self) -> None:
        super().__init__()

        self._events: WeakKeyDictionary[Any, list[WeakCallable[Any, Any]]] = WeakKeyDictionary()  # pyright: ignore[reportIncompatibleVariableOverride]  # Bad/No typing of observable

    @override
    def on(
        self,
        event: Any,
        *handlers: Callable[P, R],
    ) -> Callable[[Callable[P, R]], Callable[P, R]]:
        """Registers one or more handlers to a specified event.
        This method may as well be used as a decorator for the handler."""

        def _on_wrapper(*handlers: Callable[P, R]) -> Callable[P, R]:
            """wrapper for on decorator"""
            if event not in self._events:
                self._events[event] = []
            for handler in handlers:
                self._events[event].append(WeakCallable(handler, self._events[event].remove))  # pyright: ignore[reportArgumentType]  # Will work anyway
            return handlers[0]

        if handlers:
            return _on_wrapper(*handlers)  # pyright: ignore[reportReturnType]  # Bad/No typing of observable
        return _on_wrapper
