# Copyright (c) 2021 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# spell-checker:words
# spell-checker:ignore dflt

from __future__ import annotations

# Third-party imports
from collections.abc import Iterator

import pytest
from typing_extensions import override

# Local imports
from lookups import DelegatedLookup, Lookup, LookupProvider, ProxyLookup
from lookups.singleton import SingletonLookup

from .tools import TestChildObject, TestOtherObject, TestParentObject

# System imports


class DefaultLookup(SingletonLookup):
    def __init__(self) -> None:
        super().__init__(TestParentObject())


class DefaultLookupProvider(LookupProvider):
    @override
    def get_lookup(self) -> Lookup:
        return SingletonLookup(TestParentObject())


class DefaultLookupLookupProvider(SingletonLookup, LookupProvider):
    def __init__(self) -> None:
        super().__init__(TestOtherObject())
        self._lookup = SingletonLookup(TestParentObject())

    @override
    def get_lookup(self) -> Lookup:
        return self._lookup


@pytest.fixture
def cleanup() -> Iterator[None]:
    Lookup._DEFAULT_LOOKUP = None
    Lookup._DEFAULT_LOOKUP_PROVIDER = None
    Lookup._DEFAULT_ENTRY_POINT_GROUP = 'lookup.default'

    yield

    Lookup._DEFAULT_LOOKUP = None
    Lookup._DEFAULT_LOOKUP_PROVIDER = None
    Lookup._DEFAULT_ENTRY_POINT_GROUP = 'lookup.default'


def test_default_lookup(cleanup: None) -> None:
    Lookup._DEFAULT_ENTRY_POINT_GROUP = 'lookups.test_default_lookup'
    dflt = Lookup.get_default()
    assert dflt
    assert isinstance(dflt, DefaultLookup)

    all_instances = dflt.lookup_all(object)
    assert len(all_instances) == 1
    assert isinstance(all_instances[0], TestParentObject)

    assert Lookup.get_default() is dflt

    assert Lookup._DEFAULT_LOOKUP is dflt
    assert Lookup._DEFAULT_LOOKUP_PROVIDER is None


def test_default_lookup_lookup_provider(cleanup: None) -> None:
    Lookup._DEFAULT_ENTRY_POINT_GROUP = 'lookups.test_default_lookup_lookup_provider'
    dflt = Lookup.get_default()
    assert dflt
    assert isinstance(dflt, SingletonLookup)

    all_instances = dflt.lookup_all(object)
    assert len(all_instances) == 1
    assert isinstance(all_instances[0], TestParentObject)

    assert Lookup.get_default() is dflt

    assert isinstance(Lookup._DEFAULT_LOOKUP, DefaultLookupLookupProvider)
    assert Lookup._DEFAULT_LOOKUP_PROVIDER is Lookup._DEFAULT_LOOKUP


def test_default_lookup_provider(cleanup: None) -> None:
    Lookup._DEFAULT_ENTRY_POINT_GROUP = 'lookups.test_default_lookup_provider'
    dflt = Lookup.get_default()
    assert dflt
    assert isinstance(dflt, DelegatedLookup)

    all_instances = dflt.lookup_all(object)
    assert len(all_instances) == 1
    assert isinstance(all_instances[0], TestParentObject)

    assert Lookup.get_default() is dflt

    assert Lookup._DEFAULT_LOOKUP is dflt
    assert Lookup._DEFAULT_LOOKUP_PROVIDER is None


def test_default_no_lookup(cleanup: None) -> None:
    Lookup._DEFAULT_ENTRY_POINT_GROUP = 'lookups.test_default_no_lookup'
    dflt = Lookup.get_default()
    assert dflt
    assert isinstance(dflt, ProxyLookup)

    all_instances = dflt.lookup_all(object)
    assert all_instances
    assert (len(all_instances) % 3) == 0  # Because pytest can double up our entry points
    assert {type(instance) for instance in all_instances} == {
        TestParentObject,
        TestChildObject,
        TestOtherObject,
    }

    assert Lookup.get_default() is dflt

    assert Lookup._DEFAULT_LOOKUP is dflt
    assert Lookup._DEFAULT_LOOKUP_PROVIDER is None


def test_default_empty_entry_point_group(cleanup: None) -> None:
    Lookup._DEFAULT_ENTRY_POINT_GROUP = 'lookups.test_default_empty_entry_point_group'
    dflt = Lookup.get_default()
    assert dflt
    assert isinstance(dflt, ProxyLookup)

    all_instances = dflt.lookup_all(object)
    assert not all_instances

    assert Lookup.get_default() is dflt

    assert Lookup._DEFAULT_LOOKUP is dflt
    assert Lookup._DEFAULT_LOOKUP_PROVIDER is None
