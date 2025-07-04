# Copyright (c) 2021 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

# System imports
import gc
from collections.abc import Hashable, Iterable, MutableSequence, MutableSet, Sequence, Set
from typing import Any

# Third-party imports
import pytest

# Local imports
from lookups import EntryPointLookup, Item, Result

from .tools import TestChildObject, TestOtherObject, TestParentObject

# WARNING: For some reasons, pytest seems to duplicate the entry points. This is probably because
#          it tries to make the package available as if it was installed. So, if you already have
#          the lookups package installed (like in editable mode for instance) in your environment,
#          the entry points will be doubled.


MEMBER_FIXTURES = [
    (object, (TestParentObject, TestChildObject, TestOtherObject)),
    (TestParentObject, (TestParentObject, TestChildObject)),
    (TestChildObject, TestChildObject),
    (TestOtherObject, TestOtherObject),
]


def check_all_instances(
    expected_classes: type[Any] | tuple[type[Any], ...],
    all_instances: Iterable[Any],
) -> None:
    assert isinstance(all_instances, Sequence)
    assert not isinstance(all_instances, MutableSequence)
    for instance in all_instances:
        assert isinstance(instance, expected_classes)


def check_item(expected_classes: type[Any] | tuple[type[Any], ...], item: Item[Any] | None) -> None:
    assert item is not None
    assert isinstance(item, Hashable)

    assert item.get_display_name()
    assert item.get_id()

    assert isinstance(item.get_instance(), expected_classes)

    assert issubclass(item.get_type(), expected_classes)


def test_instantiation() -> None:
    assert EntryPointLookup('lookups.test_entry_point')


def test_non_existant_group() -> None:
    assert EntryPointLookup('non-existant')


@pytest.mark.parametrize(('search', 'expected_classes'), MEMBER_FIXTURES)
def test_lookup(search: type[Any], expected_classes: type[Any] | tuple[type[Any], ...]) -> None:
    lookup = EntryPointLookup('lookups.test_entry_point')

    assert isinstance(lookup.lookup(search), expected_classes)


@pytest.mark.parametrize(('search', 'expected_classes'), MEMBER_FIXTURES)
def test_lookup_item(
    search: type[Any],
    expected_classes: type[Any] | tuple[type[Any], ...],
) -> None:
    lookup = EntryPointLookup('lookups.test_entry_point')

    item = lookup.lookup_item(search)
    check_item(expected_classes, item)
    assert item == lookup.lookup_item(search)


@pytest.mark.parametrize(('search', 'expected_classes'), MEMBER_FIXTURES)
def test_lookup_all(search: type[Any], expected_classes: type[Any] | tuple[type[Any], ...]) -> None:
    lookup = EntryPointLookup('lookups.test_entry_point')

    all_instances = lookup.lookup_all(search)
    check_all_instances(expected_classes, all_instances)


@pytest.mark.parametrize(('search', 'expected_classes'), MEMBER_FIXTURES)
def test_lookup_result(
    search: type[Any],
    expected_classes: type[Any] | tuple[type[Any], ...],
) -> None:
    lookup = EntryPointLookup('lookups.test_entry_point')
    if not isinstance(expected_classes, Sequence):
        expected_classes = (expected_classes,)

    result = lookup.lookup_result(search)
    assert result

    all_classes = result.all_classes()
    assert isinstance(all_classes, Set)
    assert not isinstance(all_classes, MutableSet)
    assert len(all_classes) == len(expected_classes)
    assert all_classes == set(expected_classes)

    all_instances = result.all_instances()
    check_all_instances(expected_classes, all_instances)

    all_items = result.all_items()
    assert isinstance(all_items, Sequence)
    assert not isinstance(all_items, MutableSequence)
    for item, again in zip(all_items, result.all_items()):
        check_item(expected_classes, item)
        assert item == again


@pytest.mark.parametrize(('search', 'expected_classes'), MEMBER_FIXTURES)
def test_listeners(search: type[Any], expected_classes: type[Any] | tuple[type[Any], ...]) -> None:
    lookup = EntryPointLookup('lookups.test_entry_point')

    result = lookup.lookup_result(search)

    def call_me_back(result: Result[Any]) -> None:
        pass

    result.listeners += call_me_back
    result.listeners -= call_me_back

    result.listeners += call_me_back
    del call_me_back
    gc.collect()
