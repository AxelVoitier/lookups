# Copyright (c) 2019 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

# System imports
import gc
from collections.abc import Hashable, MutableSequence, MutableSet, Sequence, Set
from typing import Any

# Third-party imports
import pytest

# Local imports
from lookups import Item, Result, singleton

from .tools import TestChildObject, TestOtherObject, TestParentObject

MEMBER_FIXTURES = [
    # None
    pytest.param(None, None, object, marks=pytest.mark.xfail),
    # object
    (object(), None, object),
    (object(), 'obj', object),
    pytest.param(object(), None, TestOtherObject, marks=pytest.mark.xfail),
    # TestParentObject
    (TestParentObject(), None, object),
    (TestParentObject(), 'parent', object),
    (TestParentObject(), None, TestParentObject),
    (TestParentObject(), 'parent', TestParentObject),
    pytest.param(TestParentObject(), None, TestChildObject, marks=pytest.mark.xfail),
    pytest.param(TestParentObject(), 'parent', TestChildObject, marks=pytest.mark.xfail),
    pytest.param(TestParentObject(), None, TestOtherObject, marks=pytest.mark.xfail),
    pytest.param(TestParentObject(), 'parent', TestOtherObject, marks=pytest.mark.xfail),
    # TestChildObject
    (TestChildObject(), None, object),
    (TestChildObject(), 'child', object),
    (TestChildObject(), None, TestParentObject),
    (TestChildObject(), 'child', TestParentObject),
    (TestChildObject(), None, TestChildObject),
    (TestChildObject(), 'child', TestChildObject),
    pytest.param(TestChildObject(), None, TestOtherObject, marks=pytest.mark.xfail),
    pytest.param(TestChildObject(), 'child', TestOtherObject, marks=pytest.mark.xfail),
]


def check_all_instances(member: object, all_instances: Sequence[Any]) -> None:
    assert isinstance(all_instances, Sequence)
    assert not isinstance(all_instances, MutableSequence)
    assert len(all_instances) == 1
    assert all_instances == (member,)


def check_item(member: object, id_: str | None, item: Item[Any] | None) -> None:
    assert item is not None
    assert isinstance(item, Hashable)

    assert item.get_display_name()
    if id_ is not None:
        assert item.get_id() == id_
    else:
        assert item.get_id()

    assert item.get_instance() is member

    assert issubclass(item.get_type(), type(member))


def test_instantiation() -> None:
    assert singleton(object(), None)


@pytest.mark.parametrize(('member', 'id_', 'search'), MEMBER_FIXTURES)
def test_lookup(member: object, id_: str | None, search: type[Any]) -> None:
    lookup = singleton(member, id_)
    assert lookup.lookup(search) is member


@pytest.mark.parametrize(('member', 'id_', 'search'), MEMBER_FIXTURES)
def test_lookup_item(member: object, id_: str | None, search: type[Any]) -> None:
    lookup = singleton(member, id_)

    item = lookup.lookup_item(search)
    check_item(member, id_, item)
    assert item == lookup.lookup_item(search)


@pytest.mark.parametrize(('member', 'id_', 'search'), MEMBER_FIXTURES)
def test_lookup_all(member: object, id_: str | None, search: type[Any]) -> None:
    lookup = singleton(member, id_)

    all_instances = lookup.lookup_all(search)
    check_all_instances(member, all_instances)


@pytest.mark.parametrize(('member', 'id_', 'search'), MEMBER_FIXTURES)
def test_lookup_result(member: object, id_: str | None, search: type[Any]) -> None:
    lookup = singleton(member, id_)

    result = lookup.lookup_result(search)
    assert result

    all_classes = result.all_classes()
    assert isinstance(all_classes, Set)
    assert not isinstance(all_classes, MutableSet)
    assert len(all_classes) == 1
    assert next(iter(all_classes)) is type(member)

    all_instances = result.all_instances()
    check_all_instances(member, all_instances)

    all_items = result.all_items()
    assert isinstance(all_items, Sequence)
    assert not isinstance(all_items, MutableSequence)
    assert len(all_items) == 1
    check_item(member, id_, all_items[0])
    assert all_items[0] == lookup.lookup_item(search)


@pytest.mark.parametrize(('member', 'id_', 'search'), MEMBER_FIXTURES)
def test_listeners(member: object, id_: str | None, search: type[Any]) -> None:
    lookup = singleton(member, id_)

    result = lookup.lookup_result(search)

    def call_me_back(result: Result[Any]) -> None:
        pass

    result.listeners += call_me_back
    result.listeners -= call_me_back

    result.listeners += call_me_back
    del call_me_back
    gc.collect()
