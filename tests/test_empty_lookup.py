# -*- coding: utf-8 -*-
# Copyright (c) 2019 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# System imports
from collections.abc import Sequence, MutableSequence, Set, MutableSet

# Third-party imports

# Local imports
from lookups.lookups import EmptyLookup


def check_all_instances(all_instances):
    assert isinstance(all_instances, Sequence)
    assert not isinstance(all_instances, MutableSequence)
    assert len(all_instances) == 0


def test_instantiation():
    assert EmptyLookup()


def test_lookup():
    lookup = EmptyLookup()
    assert lookup.lookup(object) is None


def test_lookup_item():
    lookup = EmptyLookup()

    item = lookup.lookup_item(object)
    assert item is None


def test_lookup_all():
    lookup = EmptyLookup()

    all_instances = lookup.lookup_all(object)
    check_all_instances(all_instances)


def test_lookup_result():
    lookup = EmptyLookup()

    result = lookup.lookup_result(object)
    assert result

    # TODO: Test listener

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
