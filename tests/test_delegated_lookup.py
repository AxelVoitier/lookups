# Copyright (c) 2021 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

# System imports
import gc
from collections.abc import (
    Callable,
    Collection,
    Container,
    Hashable,
    Iterable,
    MutableSequence,
    MutableSet,
    Sequence,
    Set,
)
from functools import partial
from typing import Any, cast

# Third-party imports
import pytest
from typing_extensions import override

# Local imports
from lookups import (
    DelegatedLookup,
    EmptyLookup,
    GenericLookup,
    InstanceContent,
    Item,
    Lookup,
    LookupProvider,
    Result,
)
from lookups.delegated_lookup import DelegatedResult

from .tools import TestChildObject, TestOtherObject, TestParentObject


class Provider(LookupProvider):
    def __init__(self, lookup: Lookup) -> None:
        super().__init__()

        self._lookup = lookup
        self.to_notify: DelegatedLookup | None = None

    @override
    def get_lookup(self) -> Lookup:
        return self.lookup

    @property
    def lookup(self) -> Lookup:
        return self._lookup

    @lookup.setter
    def lookup(self, value: Lookup) -> None:
        self._lookup = value
        if self.to_notify:
            self.to_notify.lookup_updated()


def setup_lookups() -> tuple[
    InstanceContent,
    Lookup,
    InstanceContent,
    Lookup,
    Provider,
    DelegatedLookup,
]:
    content1 = InstanceContent()
    lookup1 = GenericLookup(content1)
    content2 = InstanceContent()
    lookup2 = GenericLookup(content2)

    provider = Provider(lookup1)
    delegated_lookup = DelegatedLookup(provider)
    provider.to_notify = delegated_lookup

    return content1, lookup1, content2, lookup2, provider, delegated_lookup


def check_all_instances(expected: MutableSequence[Any], all_instances: Iterable[Any]) -> None:
    assert isinstance(all_instances, Sequence)
    assert not isinstance(all_instances, MutableSequence)
    assert len(all_instances) == len(expected)
    for instance in all_instances:
        assert instance in expected
        expected.remove(instance)


def check_item(expected: object | Sequence[object] | None, item: Item[Any] | None) -> int | None:
    if expected is None:
        assert item is None
        return None

    assert item is not None
    assert isinstance(item, Hashable)

    assert item.get_display_name()
    assert item.get_id()

    if isinstance(expected, Sequence):
        # Otherwise it also understands a Sequence[Unknown]...
        expected = cast('Sequence[object]', expected)

        assert item.get_instance() in expected
        idx = expected.index(item.get_instance())

        assert issubclass(item.get_type(), type(expected[idx]))
        return idx

    else:
        assert item.get_instance() is expected

        assert issubclass(item.get_type(), type(expected))
        return None


def check_result(expected: Collection[Any], result: Result[Any]) -> None:
    expected_classes: set[type[Any]] = {type(instance) for instance in expected}
    expected_copy1 = list(expected)
    expected_copy2 = list(expected)

    assert result

    all_classes = result.all_classes()
    assert isinstance(all_classes, Set)
    assert not isinstance(all_classes, MutableSet)
    assert len(all_classes) == len(expected_classes)
    assert all_classes == expected_classes

    all_instances = result.all_instances()
    check_all_instances(expected_copy1, all_instances)

    all_items = result.all_items()
    assert isinstance(all_items, Sequence)
    assert not isinstance(all_items, MutableSequence)
    assert len(all_items) == len(expected)
    for item, again in zip(all_items, result.all_items()):
        idx = check_item(expected_copy2, item)
        assert idx is not None
        expected_copy2.pop(idx)
        assert item == again


def test_instantiation() -> None:
    assert DelegatedLookup(Provider(EmptyLookup()))


def test_lookup() -> None:
    content1, lookup1, content2, lookup2, provider, delegated_lookup = setup_lookups()

    parent = TestParentObject()
    content1.add(parent)
    other = TestOtherObject()
    content2.add(other)

    # Test with lookup1

    instance = delegated_lookup.lookup(TestParentObject)
    assert instance
    assert instance is parent

    instance = delegated_lookup.lookup(TestOtherObject)
    assert not instance

    # Swtich to lookup2
    provider.lookup = lookup2

    instance = delegated_lookup.lookup(TestParentObject)
    assert not instance

    instance = delegated_lookup.lookup(TestOtherObject)
    assert instance
    assert instance is other

    # Swtich back to lookup1
    provider.lookup = lookup1

    instance = delegated_lookup.lookup(TestParentObject)
    assert instance
    assert instance is parent

    instance = delegated_lookup.lookup(TestOtherObject)
    assert not instance

    # Stay with lookup1 but trigger an update
    provider.lookup = lookup1

    instance = delegated_lookup.lookup(TestParentObject)
    assert instance
    assert instance is parent

    instance = delegated_lookup.lookup(TestOtherObject)
    assert not instance


def test_lookup_item() -> None:
    content1, lookup1, content2, lookup2, provider, delegated_lookup = setup_lookups()

    parent = TestParentObject()
    content1.add(parent)
    other = TestOtherObject()
    content2.add(other)

    # Test with lookup1

    item = delegated_lookup.lookup_item(TestParentObject)
    check_item(parent, item)

    item = delegated_lookup.lookup_item(TestOtherObject)
    check_item(None, item)

    # Swtich to lookup2
    provider.lookup = lookup2

    item = delegated_lookup.lookup_item(TestParentObject)
    check_item(None, item)

    item = delegated_lookup.lookup_item(TestOtherObject)
    check_item(other, item)

    # Swtich back to lookup1
    provider.lookup = lookup1

    item = delegated_lookup.lookup_item(TestParentObject)
    check_item(parent, item)

    item = delegated_lookup.lookup_item(TestOtherObject)
    check_item(None, item)

    # Stay with lookup1 but trigger an update
    provider.lookup = lookup1

    item = delegated_lookup.lookup_item(TestParentObject)
    check_item(parent, item)

    item = delegated_lookup.lookup_item(TestOtherObject)
    check_item(None, item)


def test_lookup_all() -> None:
    content1, lookup1, content2, lookup2, provider, delegated_lookup = setup_lookups()

    parent = TestParentObject()
    content1.add(parent)
    child = TestChildObject()
    content1.add(child)
    other = TestOtherObject()
    content2.add(other)

    # Test with lookup1

    all_instances = delegated_lookup.lookup_all(TestParentObject)
    check_all_instances([parent, child], all_instances)

    all_instances = delegated_lookup.lookup_all(TestOtherObject)
    check_all_instances([], all_instances)

    # Swtich to lookup2
    provider.lookup = lookup2

    all_instances = delegated_lookup.lookup_all(TestParentObject)
    check_all_instances([], all_instances)

    all_instances = delegated_lookup.lookup_all(TestOtherObject)
    check_all_instances([other], all_instances)

    # Swtich back to lookup1
    provider.lookup = lookup1

    all_instances = delegated_lookup.lookup_all(TestParentObject)
    check_all_instances([parent, child], all_instances)

    all_instances = delegated_lookup.lookup_all(TestOtherObject)
    check_all_instances([], all_instances)

    # Stay with lookup1 but trigger an update
    provider.lookup = lookup1

    all_instances = delegated_lookup.lookup_all(TestParentObject)
    check_all_instances([parent, child], all_instances)

    all_instances = delegated_lookup.lookup_all(TestOtherObject)
    check_all_instances([], all_instances)


def test_lookup_result() -> None:
    content1, lookup1, content2, lookup2, provider, delegated_lookup = setup_lookups()

    parent = TestParentObject()
    content1.add(parent)
    child = TestChildObject()
    content1.add(child)
    other = TestOtherObject()
    content2.add(other)

    # Test with lookup1

    result = delegated_lookup.lookup_result(TestParentObject)
    check_result([parent, child], result)

    result = delegated_lookup.lookup_result(TestOtherObject)
    check_result([], result)

    # Swtich to lookup2
    provider.lookup = lookup2

    result = delegated_lookup.lookup_result(TestParentObject)
    check_result([], result)

    result = delegated_lookup.lookup_result(TestOtherObject)
    check_result([other], result)

    # Swtich back to lookup1
    provider.lookup = lookup1

    result = delegated_lookup.lookup_result(TestParentObject)
    check_result([parent, child], result)

    result = delegated_lookup.lookup_result(TestOtherObject)
    check_result([], result)

    # Stay with lookup1 but trigger an update
    provider.lookup = lookup1

    result = delegated_lookup.lookup_result(TestParentObject)
    check_result([parent, child], result)

    result = delegated_lookup.lookup_result(TestOtherObject)
    check_result([], result)


def test_lookup_result_already_exist() -> None:
    _, lookup1, _, lookup2, provider, delegated_lookup = setup_lookups()

    # Test with lookup1

    result1 = delegated_lookup.lookup_result(object)

    assert result1 is delegated_lookup.lookup_result(object)

    # Swtich to lookup2
    provider.lookup = lookup2

    assert result1 is delegated_lookup.lookup_result(object)

    # Swtich back to lookup1
    provider.lookup = lookup1

    assert result1 is delegated_lookup.lookup_result(object)

    # Stay with lookup1 but trigger an update
    provider.lookup = lookup1

    assert result1 is delegated_lookup.lookup_result(object)


called_with: Result[Any] | None = None


def check_listener(
    content1: InstanceContent,
    lookup1: Lookup,
    content2: InstanceContent,
    lookup2: Lookup,
    provider: Provider,
    delegated_lookup: DelegatedLookup,
    result: Result[Any],
) -> Callable[[], None]:
    global called_with
    called_with = None

    parent = TestParentObject()
    child = TestChildObject()
    other = TestOtherObject()

    def check_add_remove(
        members1: Iterable[object],
        members2: Iterable[object],
        expected: Container[object],
    ) -> None:
        def check_add(members: Iterable[object], content: InstanceContent) -> None:
            global called_with

            for member in members:
                print('Adding', member, 'in content', content)
                content.add(member)
                if member in expected:
                    assert called_with is not None
                    assert called_with is result
                    assert member in called_with.all_instances()
                    called_with = None
                else:
                    assert called_with is None

        def check_remove(members: Iterable[object], content: InstanceContent) -> None:
            global called_with

            for member in members:
                print('Removing', member, 'from content', content)
                content.remove(member)
                if member in expected:
                    assert called_with is not None
                    assert called_with is result
                    assert member not in called_with.all_instances()
                    called_with = None
                else:
                    assert called_with is None

        check_add(members1, content1)
        check_add(members2, content2)
        check_remove(members1, content1)
        check_remove(members2, content2)

    def check_presence(present: Iterable[object], not_present: Iterable[object]) -> None:
        for member in present:
            assert called_with is not None
            assert member in called_with.all_instances()

        for member in not_present:
            assert called_with is not None
            assert member not in called_with.all_instances()

    check_add_remove([parent], [child, other], [parent])

    # Setup for checking invokation on switch
    content1.set([parent])
    assert called_with is result
    called_with = None
    content2.set([child, other])
    assert called_with is None

    # Swtich to lookup2
    provider.lookup = lookup2

    assert called_with is result
    check_presence([child], [parent, other])
    called_with = None

    # Clear out contents for next tests
    content1.set([])
    assert called_with is None
    content2.set([])
    assert called_with is result
    called_with = None

    check_add_remove([parent], [child, other], [child])

    # Swtich back to lookup1 (should not be invoked as lookups are empty)
    provider.lookup = lookup1
    assert called_with is None

    check_add_remove([parent], [child, other], [parent])

    # Setup for checking invokation on switch
    content1.set([parent])
    assert called_with is result
    called_with = None
    content2.set([child, other])
    assert called_with is None

    # Stay with lookup1 but trigger an update
    provider.lookup = lookup1

    assert called_with is None
    called_with = result  # Just to make check_presence work
    check_presence([parent], [child, other])
    called_with = None

    return partial(check_add_remove, [parent], [child, other], [])


def test_listener() -> None:
    content1, lookup1, content2, lookup2, provider, delegated_lookup = setup_lookups()

    result = delegated_lookup.lookup_result(TestParentObject)
    assert not result.all_items()

    def call_me_back(result: Result[Any]) -> None:
        global called_with
        called_with = result
        print('Got called', result)

    result.listeners += call_me_back

    call_after_remove_del = check_listener(
        content1,
        lookup1,
        content2,
        lookup2,
        provider,
        delegated_lookup,
        result,
    )

    # Removing listener and adding/removing members
    result.listeners -= call_me_back
    call_after_remove_del()

    # Test again, this time deleting the listener
    result.listeners += call_me_back
    del call_me_back
    gc.collect()
    call_after_remove_del()


def test_bound_method_listener() -> None:
    content1, lookup1, content2, lookup2, provider, delegated_lookup = setup_lookups()

    result = delegated_lookup.lookup_result(TestParentObject)
    assert not result.all_items()

    class ToCall:
        def call_me_back(self, result: Result[Any]) -> None:
            global called_with
            called_with = result
            print('Got called', result)

    to_call = ToCall()
    result.listeners += to_call.call_me_back

    call_after_remove_del = check_listener(
        content1,
        lookup1,
        content2,
        lookup2,
        provider,
        delegated_lookup,
        result,
    )

    # Removing listener and adding/removing members
    result.listeners -= to_call.call_me_back
    call_after_remove_del()

    # Test again, this time deleting the listener
    result.listeners += to_call.call_me_back
    del to_call
    gc.collect()
    call_after_remove_del()


def test_multiple_listeners() -> None:
    content1, _, content2, lookup2, provider, delegated_lookup = setup_lookups()

    result = delegated_lookup.lookup_result(TestParentObject)

    def call_me_back1(result: Result[Any]) -> None:
        called_with[1] = result
        print('1 Got called', result)

    def call_me_back2(result: Result[Any]) -> None:
        called_with[2] = result
        print('2 Got called', result)

    called_with: dict[int, Result[Any]] = {}
    result.listeners += call_me_back1
    result.listeners += call_me_back2

    members = [object(), TestParentObject(), TestChildObject(), TestOtherObject()]

    def check_for_a_class(member: object, added: bool, cls: type[Any], result_cls: object) -> None:  # noqa: FBT001
        if isinstance(member, cls):
            if added:
                assert 1 in called_with
                assert called_with[1] is result_cls
                del called_with[1]
                assert 2 in called_with
                assert called_with[2] is result_cls
                del called_with[2]
            else:
                assert not called_with
        else:
            assert not called_with

    def check_add_remove(content: InstanceContent) -> None:
        # Adding members

        for member in members:
            print('Adding', member)
            added = content.add(member)
            check_for_a_class(member, added, TestParentObject, result)
            assert not called_with

        # Removing members

        for member in members:
            print('Removing', member)
            try:
                content.remove(member)
            except KeyError:
                continue
            else:
                check_for_a_class(member, True, TestParentObject, result)  # noqa: FBT003
                assert not called_with

    def check_not_called(content: InstanceContent) -> None:
        for member in members:
            print('Adding', member)
            content.add(member)
            assert not called_with

            print('Removing', member)
            try:
                content.remove(member)
            except KeyError:
                continue
            else:
                assert not called_with

    check_add_remove(content1)
    check_not_called(content2)
    provider.lookup = lookup2
    called_with = {}
    check_not_called(content1)
    check_add_remove(content2)

    # Removing listener and adding/removing members

    result.listeners -= call_me_back1
    result.listeners -= call_me_back2

    check_not_called(content2)

    # Test again, this time deleting the listener object

    result.listeners += call_me_back1
    result.listeners += call_me_back2
    del call_me_back1
    del call_me_back2

    check_not_called(content2)


def test_multiple_results() -> None:
    content1, _, content2, lookup2, provider, delegated_lookup = setup_lookups()

    result_object = delegated_lookup.lookup_result(object)
    result_parent = delegated_lookup.lookup_result(TestParentObject)
    result_child = delegated_lookup.lookup_result(TestChildObject)
    result_other = delegated_lookup.lookup_result(TestOtherObject)

    def call_me_back(result: Result[Any]) -> None:
        assert isinstance(result, DelegatedResult)
        called_with[result._cls] = result
        print('Got called', result)

    called_with: dict[type[Any], Result[Any]] = {}
    result_object.listeners += call_me_back
    result_parent.listeners += call_me_back
    result_child.listeners += call_me_back
    result_other.listeners += call_me_back

    members = [object(), TestParentObject(), TestChildObject(), TestOtherObject()]

    def check_for_a_class(member: object, added: bool, cls: type[Any], result_cls: object) -> None:  # noqa: FBT001
        if isinstance(member, cls):
            if added:
                assert cls in called_with
                assert called_with[cls] is result_cls
                del called_with[cls]
            else:
                assert cls not in called_with
        else:
            assert cls not in called_with

    def check_add_remove(content: InstanceContent) -> None:
        # Adding members

        for member in members:
            print('Adding', member)
            added = content.add(member)
            check_for_a_class(member, added, object, result_object)
            check_for_a_class(member, added, TestParentObject, result_parent)
            check_for_a_class(member, added, TestChildObject, result_child)
            check_for_a_class(member, added, TestOtherObject, result_other)
            assert not called_with

        # Removing members

        for member in members:
            print('Removing', member)
            try:
                content.remove(member)
            except KeyError:
                continue
            else:
                check_for_a_class(member, True, object, result_object)  # noqa: FBT003
                check_for_a_class(member, True, TestParentObject, result_parent)  # noqa: FBT003
                check_for_a_class(member, True, TestChildObject, result_child)  # noqa: FBT003
                check_for_a_class(member, True, TestOtherObject, result_other)  # noqa: FBT003
                assert not called_with

    def check_not_called(content: InstanceContent) -> None:
        for member in members:
            print('Adding', member)
            content.add(member)
            assert not called_with

            print('Removing', member)
            try:
                content.remove(member)
            except KeyError:
                continue
            else:
                assert not called_with

    check_add_remove(content1)
    check_not_called(content2)
    provider.lookup = lookup2
    called_with = {}
    check_not_called(content1)
    check_add_remove(content2)

    # Removing listener and adding/removing members

    result_object.listeners -= call_me_back
    result_parent.listeners -= call_me_back
    result_child.listeners -= call_me_back
    result_other.listeners -= call_me_back

    check_not_called(content2)

    # Test again, this time deleting the listener object

    result_object.listeners += call_me_back
    result_parent.listeners += call_me_back
    result_child.listeners += call_me_back
    result_other.listeners += call_me_back
    del call_me_back

    check_not_called(content2)


@pytest.mark.xfail
def test_modify_lookup_from_listener() -> None:
    content1, *_, delegated_lookup = setup_lookups()

    result = delegated_lookup.lookup_result(object)

    obj1 = TestParentObject()
    obj2 = TestParentObject()

    def call_me_back(result: Result[Any]) -> None:
        content1.add(obj2)

    result.listeners += call_me_back

    content1.add(obj1)


def test_del_result_clear_listener() -> None:
    content1, _, content2, lookup2, provider, delegated_lookup = setup_lookups()

    result = delegated_lookup.lookup_result(object)

    obj1 = TestParentObject()
    obj2 = TestParentObject()

    def call_me_back(result: Result[Any]) -> None:
        nonlocal called_with
        called_with = result
        print('Got called', result)

    called_with = None
    result.listeners += call_me_back

    content1.add(obj1)
    called_with = cast('Result[Any] | None', called_with)
    assert called_with is not None
    assert obj1 in called_with.all_instances()
    called_with = None

    del result
    gc.collect()

    content1.add(obj2)
    assert called_with is None

    result = delegated_lookup.lookup_result(object)

    provider.lookup = lookup2
    called_with = None

    del result
    gc.collect()

    content2.add(obj2)
    assert called_with is None
