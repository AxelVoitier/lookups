# Copyright (c) 2019 Contributors as noted in the AUTHORS file
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
from _pytest.mark.structures import ParameterSet

# Local imports
from lookups import Item, Result, fixed

from .tools import TestChildObject, TestOtherObject, TestParentObject

obj = object()
obj2 = object()
parent = TestParentObject()
parent2 = TestParentObject()
child = TestChildObject()
child2 = TestChildObject()
other = TestOtherObject()

MEMBER_FIXTURES: list[tuple[Iterable[Any], type[Any], Sequence[object]] | ParameterSet] = [
    # 0 member
    ([], object, []),
    # 1 member
    # None
    pytest.param([None], object, [], marks=pytest.mark.xfail),
    # object
    ([obj], object, [obj]),
    ([obj], TestOtherObject, []),
    # TestParentObject
    ([parent], object, [parent]),
    ([parent], TestParentObject, [parent]),
    ([parent], TestChildObject, []),
    ([parent], TestOtherObject, []),
    # TestChildObject
    ([child], object, [child]),
    ([child], TestParentObject, [child]),
    ([child], TestChildObject, [child]),
    ([child], TestOtherObject, []),
    # 2 members
    # None
    pytest.param([None, None], object, [], marks=pytest.mark.xfail),
    pytest.param([obj, None], object, [obj], marks=pytest.mark.xfail),
    # object
    ([obj, parent, child, other], object, [obj, parent, child, other]),
    ([obj, obj, child, other], object, [obj, obj, child, other]),
    ([obj, obj2, child, other], object, [obj, obj2, child, other]),
    ([other, other, other, other], object, [other, other, other, other]),
    # TestParentObject
    ([obj, parent, child, other], TestParentObject, [parent, child]),
    ([parent, parent, child, other], TestParentObject, [parent, parent, child]),
    ([parent, parent2, child, other], TestParentObject, [parent, parent2, child]),
    ([other, other, other, other], TestParentObject, []),
    # TestChildObject
    ([obj, parent, child, other], TestChildObject, [child]),
    ([child, parent, child, other], TestChildObject, [child, child]),
    ([child, parent, child2, other], TestChildObject, [child, child2]),
    ([other, other, other, other], TestChildObject, []),
]


def check_all_instances(expected: tuple[object, ...], all_instances: Sequence[Any]) -> None:
    assert isinstance(all_instances, Sequence)
    assert not isinstance(all_instances, MutableSequence)
    assert len(all_instances) == len(expected)
    assert all_instances == expected


def check_item(expected: object | None, item: Item[Any] | None) -> None:
    if expected is None:
        assert item is None
        return

    assert item is not None
    assert isinstance(item, Hashable)

    assert item.get_display_name()
    assert item.get_id()

    assert item.get_instance() is expected

    assert issubclass(item.get_type(), type(expected))


def test_instantiation() -> None:
    assert fixed()


@pytest.mark.parametrize(('members', 'search', 'expected'), MEMBER_FIXTURES)
def test_lookup(
    members: Iterable[object],
    search: type[Any],
    expected: Sequence[object],
) -> None:
    expected_first = expected[0] if expected else None
    lookup = fixed(*members)

    assert lookup.lookup(search) == expected_first


@pytest.mark.parametrize(('members', 'search', 'expected'), MEMBER_FIXTURES)
def test_lookup_item(
    members: Iterable[object],
    search: type[Any],
    expected: Sequence[object],
) -> None:
    expected_first = expected[0] if expected else None
    lookup = fixed(*members)

    item = lookup.lookup_item(search)
    check_item(expected_first, item)
    assert item == lookup.lookup_item(search)


@pytest.mark.parametrize(('members', 'search', 'expected'), MEMBER_FIXTURES)
def test_lookup_all(
    members: Iterable[object],
    search: type[Any],
    expected: Sequence[object],
) -> None:
    expected = tuple(expected)
    lookup = fixed(*members)

    all_instances = lookup.lookup_all(search)
    check_all_instances(expected, all_instances)


@pytest.mark.parametrize(('members', 'search', 'expected'), MEMBER_FIXTURES)
def test_lookup_result(
    members: Iterable[object],
    search: type[Any],
    expected: Sequence[object],
) -> None:
    expected = tuple(expected)
    expected_classes = {type(instance) for instance in expected}
    lookup = fixed(*members)

    result = lookup.lookup_result(search)
    assert result

    all_classes = result.all_classes()
    assert isinstance(all_classes, Set)
    assert not isinstance(all_classes, MutableSet)
    assert len(all_classes) == len(expected_classes)
    assert all_classes == expected_classes

    all_instances = result.all_instances()
    check_all_instances(expected, all_instances)

    all_items = result.all_items()
    assert isinstance(all_items, Sequence)
    assert not isinstance(all_items, MutableSequence)
    assert len(all_items) == len(expected)
    for item, instance, again in zip(all_items, expected, result.all_items()):
        check_item(instance, item)
        assert item == again


@pytest.mark.parametrize(('members', 'search', 'expected'), MEMBER_FIXTURES)
def test_listeners(
    members: Iterable[object],
    search: type[Any],
    expected: Sequence[object],
) -> None:
    lookup = fixed(*members)

    result = lookup.lookup_result(search)

    def call_me_back(result: Result[Any]) -> None:
        pass

    result.listeners += call_me_back
    result.listeners -= call_me_back

    result.listeners += call_me_back
    del call_me_back
    gc.collect()
