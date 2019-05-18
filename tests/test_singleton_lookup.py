# -*- coding: utf-8 -*-
# Copyright (c) 2019 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# System imports
from collections.abc import Hashable, Sequence, MutableSequence, Set, MutableSet

# Third-party imports
import pytest

# Local imports
from lookups import singleton
from .tools import TestParentObject, TestChildObject, TestOtherObject


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


def check_all_instances(member, all_instances):
    assert isinstance(all_instances, Sequence)
    assert not isinstance(all_instances, MutableSequence)
    assert len(all_instances) == 1
    assert all_instances == (member, )


def check_item(member, id_, item):
    assert item is not None
    assert isinstance(item, Hashable)

    assert item.get_display_name()
    if id_ is not None:
        assert item.get_id() == id_
    else:
        assert item.get_id()

    assert item.get_instance() is member

    assert item.get_type() is type(member)


def test_instantiation():
    assert singleton(object(), None)


@pytest.mark.parametrize('member, id_, search', MEMBER_FIXTURES)
def test_lookup(member, id_, search):
    lookup = singleton(member, id_)
    assert lookup.lookup(search) is member


@pytest.mark.parametrize('member, id_, search', MEMBER_FIXTURES)
def test_lookup_item(member, id_, search):
    lookup = singleton(member, id_)

    item = lookup.lookup_item(search)
    check_item(member, id_, item)
    assert item == lookup.lookup_item(search)


@pytest.mark.parametrize('member, id_, search', MEMBER_FIXTURES)
def test_lookup_all(member, id_, search):
    lookup = singleton(member, id_)

    all_instances = lookup.lookup_all(search)
    check_all_instances(member, all_instances)


@pytest.mark.parametrize('member, id_, search', MEMBER_FIXTURES)
def test_lookup_result(member, id_, search):
    lookup = singleton(member, id_)

    result = lookup.lookup_result(search)
    assert result

    # TODO: Test listener

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
