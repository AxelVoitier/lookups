# Copyright (c) 2019 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

# System imports
import gc
from collections.abc import MutableSequence, MutableSet, Sequence, Set
from typing import Any

# Third-party imports
# Local imports
from lookups import EmptyLookup, Result


def check_all_instances(all_instances: Sequence[Any]) -> None:
    assert isinstance(all_instances, Sequence)
    assert not isinstance(all_instances, MutableSequence)
    assert len(all_instances) == 0


def test_instantiation() -> None:
    assert EmptyLookup()


def test_lookup() -> None:
    lookup = EmptyLookup()
    assert lookup.lookup(object) is None


def test_lookup_item() -> None:
    lookup = EmptyLookup()

    item = lookup.lookup_item(object)
    assert item is None


def test_lookup_all() -> None:
    lookup = EmptyLookup()

    all_instances = lookup.lookup_all(object)
    check_all_instances(all_instances)


def test_lookup_result() -> None:
    lookup = EmptyLookup()

    result = lookup.lookup_result(object)
    assert result

    all_classes = result.all_classes()
    assert isinstance(all_classes, Set)
    assert not isinstance(all_classes, MutableSet)
    assert len(all_classes) == 0

    all_instances = result.all_instances()
    check_all_instances(all_instances)

    all_items = result.all_items()
    assert isinstance(all_items, Sequence)
    assert not isinstance(all_items, MutableSequence)
    assert len(all_items) == 0


def test_listeners() -> None:
    lookup = EmptyLookup()

    result = lookup.lookup_result(object)

    def call_me_back(result: Result[Any]) -> None:
        pass

    result.listeners += call_me_back
    result.listeners -= call_me_back

    result.listeners += call_me_back
    del call_me_back
    gc.collect()
