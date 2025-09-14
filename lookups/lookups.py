# Copyright (c) 2019 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
Static factory methods for creating common lookup implementations.
"""

from __future__ import annotations

# System imports
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, TypeVar

# Third-party imports
from listeners import Listeners
from typing_extensions import override

# Local imports
from . import simple
from . import singleton as singleton_module
from .lookup import Item, Lookup, Result

T = TypeVar('T')
if TYPE_CHECKING:
    from collections.abc import Sequence, Set


def singleton(member: object, id_: str | None = None) -> Lookup:
    return singleton_module.SingletonLookup(member, id_)  # pyright: ignore[reportFunctionMemberAccess]  # Confused pyright...


def fixed(*members: object) -> Lookup:
    if not members:
        return EmptyLookup()

    elif len(members) == 1:
        return singleton(members[0])

    else:
        return simple.SimpleLookup(*members)


class NoResult(Result[T]):
    def __init__(self) -> None:
        super().__init__()

        self.listeners = Listeners[Callable[[Result[T]], Any]]()

    @override
    def all_classes(self) -> Set[type[T]]:
        return frozenset()

    @override
    def all_instances(self) -> Sequence[T]:
        return ()

    @override
    def all_items(self) -> Sequence[Item[T]]:
        return ()


class EmptyLookup(Lookup):
    NO_RESULT: Result[Any] = NoResult()

    @override
    def lookup(self, cls: type[T]) -> None:
        return None

    @override
    def lookup_result(self, cls: type[T]) -> Result[T]:
        return self.NO_RESULT


class LookupItem(Item[T]):
    def __init__(self, instance: T, id_: str | None = None) -> None:
        super().__init__()

        if instance is None:
            msg = 'None cannot be a lookup member'
            raise ValueError(msg)

        self._instance = instance
        self._id = id_

    @override
    def get_display_name(self) -> str:
        return self.get_id()

    @override
    def get_id(self) -> str:
        if (id := self._id) is not None:
            return id
        else:
            return str(self._instance)

    @override
    def get_instance(self) -> T | None:
        return self._instance

    @override
    def get_type(self) -> type[T]:
        return type(self._instance)

    @override
    def __eq__(self, other: object) -> bool:
        if isinstance(other, type(self)):
            return self._instance == other.get_instance()
        else:
            return False

    @override
    def __hash__(self) -> int:
        try:
            return hash(self._instance)
        except TypeError:  # Mutable, cannot be hashed
            return id(self._instance)
