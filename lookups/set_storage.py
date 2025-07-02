# Copyright (c) 2019 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

# System imports
from typing import TYPE_CHECKING, TypeVar
from weakref import WeakValueDictionary

# Third-party imports
from typing_extensions import override

# Local imports
from .generic_lookup import Storage, Transaction

T = TypeVar('T')
if TYPE_CHECKING:
    from collections.abc import Collection, Iterable
    from typing import Any

    from .generic_lookup import GLResult, Pair


class SetStorage(Storage):
    """Storing Pairs in a set datastructure, for GenericLookup."""

    def __init__(self) -> None:
        super().__init__()

        self._content: Collection[Pair[Any]] = set()

        # Do not serialize
        self._results: WeakValueDictionary[type[object], GLResult[Any]] = WeakValueDictionary()

    @override
    def begin_transaction(self, ensure: int) -> Transaction:
        return SetTransaction(ensure, self._content)

    @override
    def end_transaction(self, transaction: Transaction) -> Iterable[GLResult[Any]]:
        self._content, change_set = transaction.new_content(self._content)

        results_to_notify: set[GLResult[Any]] = set()
        for pair in change_set:
            cls = pair.get_type()
            for result_type, result in self._results.items():
                if issubclass(cls, result_type):
                    results_to_notify.add(result)
                    result.clear_cache()

        return results_to_notify

    @override
    def lookup(self, cls: type[T]) -> Iterable[Pair[T]]:
        for pair in self._content:  # TODO: improve
            if issubclass(pair.get_type(), cls):
                yield pair

    @override
    def register_result(self, result: GLResult[T]) -> None:
        self._results[result._cls] = result

    @override
    def find_result(self, cls: type[T]) -> GLResult[T] | None:
        return self._results.get(cls, None)

    @override
    def __contains__(self, item: object) -> bool:
        return item in self._content


class SetTransaction(Transaction):
    def __init__(self, ensure: int, current_content: Collection[Pair[Any]]) -> None:
        super().__init__()

        self._new_list = set(current_content)
        self._changed: set[Pair[Any]] = set()

    @override
    def new_content(
        self,
        prev: Collection[Pair[Any]],
    ) -> tuple[Collection[Pair[Any]], set[Pair[Any]]]:
        return self._new_list, self._changed

    @override
    def add(self, pair: Pair[Any]) -> bool:
        not_present = pair not in self._new_list
        if not_present:
            self._changed.add(pair)
        self._new_list.add(pair)
        return not_present

    @override
    def remove(self, pair: Pair[Any]) -> None:
        self._changed.add(pair)
        self._new_list.remove(pair)

    @override
    def set_all(self, pairs: Collection[Pair[Any]]) -> None:
        pairs = set(pairs)
        self._changed.update(pairs.symmetric_difference(self._new_list))
        self._new_list = pairs
