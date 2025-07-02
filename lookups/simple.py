# Copyright (c) 2019 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

# System imports
from typing import TYPE_CHECKING, TypeVar

# Third-party imports
from typing_extensions import override

# Local imports
from . import lookups
from .lookup import Item, Lookup, Result

T = TypeVar('T')
if TYPE_CHECKING:
    from collections.abc import Sequence, Set
    from typing import Any, Callable


class SimpleLookup(Lookup):
    """
    Simple lookup implementation. It can be used to create temporary lookups that do not change over
    time. The result stores references to all objects passed in the constructor. Those objecst are
    the only ones returned as result.
    """

    def __init__(self, *instances: object) -> None:
        """
        Creates new SimpleLookup object with supplied instances parameter.

        :param instances: Instances to be used to return from the lookup.
        """
        super().__init__()

        self.all_items: Sequence[Item[Any]] = tuple(
            lookups.LookupItem(instance) for instance in instances
        )

    @override
    def lookup(self, cls: type[T]) -> T | None:
        for item in self.all_items:
            if issubclass(item.get_type(), cls):
                return item.get_instance()

        return None

    @override
    def lookup_result(self, cls: type[T]) -> Result[T]:
        return SimpleResult[T](self, cls)


class SimpleResult(Result[T]):
    """
    Result used in SimpleLookup. It holds a reference to the collection passed in constructor.
    As the contents of this lookup result never changes the add_lookup_listener() and
    remove_lookup_listener do not do anything.
    """

    def __init__(self, simple_lookup: SimpleLookup, cls: type[T]) -> None:
        super().__init__()

        self.lookup = simple_lookup
        self.cls = cls
        self._items: Sequence[Item[T]] | None = None

    @override
    def add_lookup_listener(self, listener: Callable[[Result[T]], Any]) -> None:
        pass

    @override
    def remove_lookup_listener(self, listener: Callable[[Result[T]], Any]) -> None:
        pass

    @override
    def all_classes(self) -> Set[type[T]]:
        return frozenset(item.get_type() for item in self.all_items())

    @override
    def all_instances(self) -> Sequence[T]:
        return tuple(filter(None, (item.get_instance() for item in self.all_items())))

    @override
    def all_items(self) -> Sequence[Item[T]]:
        if (items := self._items) is None:
            self._items = items = tuple(
                item for item in self.lookup.all_items if issubclass(item.get_type(), self.cls)
            )

        return items
