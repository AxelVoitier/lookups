# -*- coding: utf-8 -*-
# Copyright (c) 2019 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# System imports
from typing import Sequence, AbstractSet, Type, Optional

# Third-party imports

# Local imports
from . import lookups
from .lookup import Lookup, Result, Item, LookupListener


class SingletonLookup(Lookup):
    '''
    Unmodifiable lookup that contains just one fixed object.
    '''

    def __init__(self, member: object, id_: str = None) -> None:
        '''
        :param member: The only fixed instance in this lookup.
        :param id_: Persistent identifier for member.
        '''
        if member is None:
            raise ValueError('None cannot be a lookup member')

        self._member = member
        self._id = id_

    def lookup(self, cls: Type[object]) -> Optional[object]:
        if isinstance(self._member, cls):
            return self._member
        else:
            return None

    def lookup_result(self, cls: Type[object]) -> Result:
        item = self.lookup_item(cls)
        if item is not None:
            return SingletonResult(item)
        else:
            return lookups.EmptyLookup().lookup_result(cls)

    def lookup_item(self, cls: Type[object]) -> Optional[Item]:
        if isinstance(self._member, cls):
            return lookups.LookupItem(self._member, self._id)
        else:
            return None

    def lookup_all(self, cls: Type[object]) -> Sequence[object]:
        if isinstance(self._member, cls):
            return (self._member, )
        else:
            return tuple()

    def __str__(self) -> str:
        return 'SingletonLookup[%s]' % str(self._member)


class SingletonResult(Result):

    def __init__(self, item: Item) -> None:
        self._item = item

    def add_lookup_listener(self, listener: LookupListener) -> None:
        pass

    def remove_lookup_listener(self, listener: LookupListener) -> None:
        pass

    def all_classes(self) -> AbstractSet[Type[object]]:
        return frozenset((self._item.get_type(), ))

    def all_instances(self) -> Sequence[object]:
        instance = self._item.get_instance()
        if instance is not None:
            return self._item.get_instance(),
        else:
            return tuple()

    def all_items(self) -> Sequence[Item]:
        return self._item,
