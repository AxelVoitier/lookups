# -*- coding: utf-8 -*-
# Copyright (c) 2019 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
'''
Static factory methods for creating common lookup implementations.
'''

# System imports
from typing import Sequence, AbstractSet, Type, Optional

# Third-party imports

# Local imports
from . import singleton as singleton_module, simple
from .lookup import Lookup, Item, Result, LookupListener


def singleton(member: object, id_: str = None) -> Lookup:
    return singleton_module.SingletonLookup(member, id_)


def fixed(*members: object) -> Lookup:
    if not members:
        return EmptyLookup()

    elif len(members) == 1:
        return singleton(members[0])

    else:
        return simple.SimpleLookup(*members)


class NoResult(Result):

    def add_lookup_listener(self, listener: LookupListener) -> None:
        pass

    def remove_lookup_listener(self, listener: LookupListener) -> None:
        pass

    def all_classes(self) -> AbstractSet[Type[object]]:
        return frozenset()

    def all_instances(self) -> Sequence[object]:
        return tuple()

    def all_items(self) -> Sequence[Item]:
        return tuple()


class EmptyLookup(Lookup):

    NO_RESULT = NoResult()

    def lookup(self, cls: Type[object]) -> Optional[object]:
        return None

    def lookup_result(self, cls: Type[object]) -> Result:
        return self.NO_RESULT


class LookupItem(Item):

    def __init__(self, instance: object, id_: str = None) -> None:
        if instance is None:
            raise ValueError('None cannot be a lookup member')

        self._instance = instance
        self._id = id_

    def get_display_name(self) -> str:
        return self.get_id()

    def get_id(self) -> str:
        if self._id is not None:
            return self._id
        else:
            return str(self._instance)

    def get_instance(self) -> Optional[object]:
        return self._instance

    def get_type(self) -> Type[object]:
        return self._instance.__class__

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Item):
            return self._instance == other.get_instance()
        else:
            return False

    def __hash__(self) -> int:
        return hash(self._instance)
