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
from .lookup import Lookup, Item, Result, LookupListener


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


