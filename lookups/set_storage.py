# -*- coding: utf-8 -*-
# Copyright (c) 2019 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# System imports
from typing import Iterable, Collection, Set, Type, Optional, Tuple
from weakref import WeakValueDictionary

# Third-party imports

# Local imports
from . import generic_lookup as GL


class SetStorage(GL.Storage):
    '''Storing Pairs in a set datastructure, for GenericLookup.'''

    def __init__(self) -> None:
        self._content: Collection[GL.Pair] = set()

        # Do not serialize
        self._results: WeakValueDictionary[Type[object], GL.GLResult] = WeakValueDictionary()

    def begin_transaction(self, ensure: int) -> GL.Transaction:
        return SetTransaction(ensure, self._content)

    def end_transaction(self, transaction: GL.Transaction) -> Iterable[GL.GLResult]:
        self._content, change_set = transaction.new_content(self._content)

        results_to_notify = set()
        for pair in change_set:
            cls = pair.get_type()
            for result_type, result in self._results.items():
                if issubclass(cls, result_type):
                    results_to_notify.add(result)
                    result.clear_cache()

        return results_to_notify

    def lookup(self, cls: Type[object]) -> Iterable[GL.Pair]:
        for pair in self._content:  # TODO: improve
            if issubclass(pair.get_type(), cls):
                yield pair

    def register_result(self, result: GL.GLResult) -> None:
        self._results[result._cls] = result

    def find_result(self, cls: Type[object]) -> Optional[GL.GLResult]:
        return self._results.get(cls, None)


class SetTransaction(GL.Transaction):

    def __init__(self, ensure: int, current_content: Collection[GL.Pair]) -> None:
        self._new_list = set(current_content)
        self._changed: Set[GL.Pair] = set()

    def new_content(self, prev: Collection[GL.Pair]) -> Tuple[Collection[GL.Pair], Set[GL.Pair]]:
        return self._new_list, self._changed

    def add(self, pair: GL.Pair) -> bool:
        not_present = pair not in self._new_list
        if not_present:
            self._changed.add(pair)
        self._new_list.add(pair)
        return not_present

    def remove(self, pair: GL.Pair) -> None:
        self._changed.add(pair)
        self._new_list.remove(pair)

    def set_all(self, pairs: Collection[GL.Pair]) -> None:
        pairs = set(pairs)
        self._changed.update(pairs.symmetric_difference(self._new_list))
        self._new_list = pairs
