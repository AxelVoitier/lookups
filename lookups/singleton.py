# Copyright (c) 2019 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

# System imports
from typing import TYPE_CHECKING, Any, Callable, TypeVar

# Third-party imports
from listeners import Observable
from typing_extensions import override

# Local imports
from . import lookups
from .lookup import Item, Lookup, Result

T = TypeVar('T')
if TYPE_CHECKING:
    from collections.abc import Sequence, Set


class SingletonLookup(Lookup):
    """
    Unmodifiable lookup that contains just one fixed object.
    """

    def __init__(self, member: object, id_: str | None = None) -> None:
        """
        :param member: The only fixed instance in this lookup.
        :param id_: Persistent identifier for member.
        """
        super().__init__()

        if member is None:
            msg = 'None cannot be a lookup member'
            raise ValueError(msg)

        self._member = member
        self._id = id_

    @override
    def lookup(self, cls: type[T]) -> T | None:
        if isinstance(self._member, cls):
            return self._member
        else:
            return None

    @override
    def lookup_result(self, cls: type[T]) -> Result[T]:
        item = self.lookup_item(cls)
        if item is not None:
            return SingletonResult(item)
        else:
            return lookups.EmptyLookup().lookup_result(cls)

    @override
    def lookup_item(self, cls: type[T]) -> Item[T] | None:
        if isinstance(self._member, cls):
            return lookups.LookupItem(self._member, self._id)
        else:
            return None

    @override
    def lookup_all(self, cls: type[T]) -> Sequence[T]:
        if isinstance(self._member, cls):
            return (self._member,)
        else:
            return ()

    @override
    def __str__(self) -> str:
        return f'SingletonLookup[{self._member!s}]'


class SingletonResult(Result[T]):
    def __init__(self, item: Item[T]) -> None:
        super().__init__()

        self._item = item

        self.listeners = Observable[Callable[[Result[T]], Any]]()

    @override
    def all_classes(self) -> Set[type[T]]:
        return frozenset((self._item.get_type(),))

    @override
    def all_instances(self) -> Sequence[T]:
        if (instance := self._item.get_instance()) is not None:
            return (instance,)
        else:
            return ()

    @override
    def all_items(self) -> Sequence[Item[T]]:
        return (self._item,)
