# Copyright (c) 2019 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

# System imports
import gc
import threading
from collections.abc import (
    Collection,
    Hashable,
    Iterable,
    MutableSequence,
    MutableSet,
    Sequence,
    Set,
)
from concurrent.futures import ThreadPoolExecutor
from typing import Any

# Third-party imports
import pytest
from _pytest.mark.structures import ParameterSet
from typing_extensions import override

# Local imports
from lookups import Convertor, GenericLookup, InstanceContent, Item, Result
from lookups.generic_lookup import GLResult
from lookups.instance_content import ConvertingItem
from lookups.set_storage import SetStorage

from .tools import TestChildObject, TestOtherObject, TestParentObject

THREAD_WAITING_TIME = 0.025


obj = object()
obj2 = object()
parent = TestParentObject()
parent2 = TestParentObject()
child = TestChildObject()
child2 = TestChildObject()
other = TestOtherObject()


MEMBER_FIXTURES: list[
    tuple[Collection[object], type[Any], Sequence[object] | None] | ParameterSet
] = [
    # 0 member
    ([], object, None),
    # 1 member
    pytest.param([None], object, None, marks=pytest.mark.xfail),
    # object
    ([obj], object, [obj]),
    ([obj], TestOtherObject, None),
    # TestParentObject
    ([parent], object, [parent]),
    ([parent], TestParentObject, [parent]),
    ([parent], TestChildObject, None),
    ([parent], TestOtherObject, None),
    # TestChildObject
    ([child], object, [child]),
    ([child], TestParentObject, [child]),
    ([child], TestChildObject, [child]),
    ([child], TestOtherObject, None),
    # 2 members
    # None
    pytest.param([None, None], object, None, marks=pytest.mark.xfail),
    pytest.param([obj, None], object, [obj], marks=pytest.mark.xfail),
    # object
    ([obj, parent, child, other], object, [obj, parent, child, other]),
    ([obj, obj, child, other], object, [obj, child, other]),
    ([obj, obj2, child, other], object, [obj, obj2, child, other]),
    ([other, other, other, other], object, [other]),
    # TestParentObject
    ([obj, parent, child, other], TestParentObject, [parent, child]),
    ([parent, parent, child, other], TestParentObject, [parent, child]),
    ([parent, parent2, child, other], TestParentObject, [parent, parent2, child]),
    ([other, other, other, other], TestParentObject, None),
    # TestChildObject
    ([obj, parent, child, other], TestChildObject, [child]),
    ([child, parent, child, other], TestChildObject, [child]),
    ([child, parent, child2, other], TestChildObject, [child, child2]),
    ([other, other, other, other], TestChildObject, None),
]


# Helpers


def setup_lookup(
    members: Collection[Any],
    convertor: Convertor[Any, Any] | None = None,
) -> tuple[InstanceContent, GenericLookup]:
    content = InstanceContent()
    lookup = GenericLookup(content)
    content.set(members, convertor=convertor)

    return content, lookup


def check_all_instances(expected: MutableSequence[Any], all_instances: Iterable[Any]) -> None:
    assert isinstance(all_instances, Sequence)
    assert not isinstance(all_instances, MutableSequence)
    assert len(all_instances) == len(expected)
    for instance in all_instances:
        assert instance in expected
        expected.remove(instance)


def check_item(expected: Sequence[object] | None, item: Item[Any] | None) -> int | None:
    if expected is None:
        assert item is None
        return None

    assert item is not None
    assert isinstance(item, Hashable)

    assert item.get_display_name()
    assert item.get_id()

    assert item.get_instance() in expected
    idx = expected.index(item.get_instance())

    assert issubclass(item.get_type(), type(expected[idx]))
    return idx


# Objects life-cycle


def test_instantiation() -> None:
    assert InstanceContent()
    assert GenericLookup(InstanceContent())


def test_cannot_reuse_content() -> None:
    content, _ = setup_lookup([])

    with pytest.raises(RuntimeError):
        GenericLookup(content)


# InstanceContent.add()


def test_add_before_attach() -> None:
    members = [object, parent, child, other, parent]
    content = InstanceContent()

    for member in members:
        content.add(member)

    lookup = GenericLookup(content)

    storage = lookup._storage
    assert storage
    assert isinstance(storage, SetStorage)
    assert storage._content

    def check_in_storage(obj: object) -> bool:
        return any(pair.get_instance() == obj for pair in storage._content)

    for member in members:
        assert check_in_storage(member)


def test_add_after_attach() -> None:
    members = [object, parent, child, other, parent]
    content = InstanceContent()
    lookup = GenericLookup(content)

    for member in members:
        content.add(member)

    storage = lookup._storage
    assert storage
    assert isinstance(storage, SetStorage)
    assert storage._content

    def check_in_storage(obj: object) -> bool:
        return any(pair.get_instance() == obj for pair in storage._content)

    for member in members:
        assert check_in_storage(member)


# InstanceContent.set()


def test_set_before_attach() -> None:
    members = [object, parent, child, other, parent]
    content = InstanceContent()

    content.set(members)

    lookup = GenericLookup(content)

    storage = lookup._storage
    assert storage
    assert isinstance(storage, SetStorage)
    assert storage._content

    def check_in_storage(obj: object) -> bool:
        return any(pair.get_instance() == obj for pair in storage._content)

    for member in members:
        assert check_in_storage(member)


def test_set_after_attach() -> None:
    members = [object, parent, child, other, parent]
    content = InstanceContent()
    lookup = GenericLookup(content)

    content.set(members)

    storage = lookup._storage
    assert storage
    assert isinstance(storage, SetStorage)
    assert storage._content

    def check_in_storage(obj: object) -> bool:
        return any(pair.get_instance() == obj for pair in storage._content)

    for member in members:
        assert check_in_storage(member)


# InstanceContent.remove()


def test_remove_before_attach() -> None:
    members = [object, parent, child, other, parent]
    content = InstanceContent()
    content.set(members)

    for member in members:
        content.remove(member)

    lookup = GenericLookup(content)

    assert not lookup._storage
    # Can't test much more if no storage here...


def test_remove_after_attach() -> None:
    members = [object, parent, child, other, parent]
    content = InstanceContent()
    lookup = GenericLookup(content)
    content.set(members)

    for member in members:
        try:
            content.remove(member)
        except KeyError:  # noqa: PERF203
            print('Could not remove', member)

    storage = lookup._storage
    assert storage
    assert isinstance(storage, SetStorage)
    assert storage._content == set()

    def check_in_storage(obj: object) -> bool:
        return any(pair.get_instance() == obj for pair in storage._content)

    for member in members:
        assert not check_in_storage(member)


# Basic lookup methods


@pytest.mark.parametrize(('members', 'search', 'expected'), MEMBER_FIXTURES)
def test_lookup(
    members: Collection[Any],
    search: type[Any],
    expected: Sequence[Any] | None,
) -> None:
    _, lookup = setup_lookup(members)

    if expected:
        assert lookup.lookup(search) in expected
    else:
        assert lookup.lookup(search) is expected


@pytest.mark.parametrize(('members', 'search', 'expected'), MEMBER_FIXTURES)
def test_lookup_item(
    members: Collection[Any],
    search: type[Any],
    expected: Sequence[Any] | None,
) -> None:
    _, lookup = setup_lookup(members)

    item = lookup.lookup_item(search)
    check_item(expected, item)
    assert item == lookup.lookup_item(search)


@pytest.mark.parametrize(('members', 'search', 'expected'), MEMBER_FIXTURES)
def test_lookup_all(
    members: Collection[Any],
    search: type[Any],
    expected: Sequence[Any] | None,
) -> None:
    expected = list(expected) if expected is not None else []
    _, lookup = setup_lookup(members)

    all_instances = lookup.lookup_all(search)
    check_all_instances(expected, all_instances)


# Lookup.lookup_result()


@pytest.mark.parametrize(('members', 'search', 'expected'), MEMBER_FIXTURES)
def test_lookup_result(
    members: Collection[Any],
    search: type[Any],
    expected: Sequence[Any] | None,
) -> None:
    print(members, search, expected)
    expected = list(expected) if expected is not None else []
    print(members, search, expected)
    expected_classes: set[type[Any]] = {type(instance) for instance in expected}
    _, lookup = setup_lookup(members)

    result = lookup.lookup_result(search)
    assert result

    all_classes = result.all_classes()
    assert isinstance(all_classes, Set)
    assert not isinstance(all_classes, MutableSet)
    assert len(all_classes) == len(expected_classes)
    assert all_classes == expected_classes

    all_instances = result.all_instances()
    check_all_instances(list(expected), all_instances)

    all_items = result.all_items()
    assert isinstance(all_items, Sequence)
    assert not isinstance(all_items, MutableSequence)
    assert len(all_items) == len(expected)
    for item, again in zip(all_items, result.all_items()):
        idx = check_item(expected, item)
        assert idx is not None
        expected.pop(idx)
        assert item == again


def test_lookup_result_already_exist() -> None:
    _, lookup = setup_lookup([])

    result1 = lookup.lookup_result(object)
    result2 = lookup.lookup_result(object)

    assert result1 is result2


# Result listeners


@pytest.mark.parametrize(('members', 'search', 'expected'), MEMBER_FIXTURES)
def test_listener(
    members: Collection[Any],
    search: type[Any],
    expected: Sequence[Any] | None,
) -> None:
    print(members, search, expected)
    expected = list(expected) if expected is not None else []
    content, lookup = setup_lookup([])

    result = lookup.lookup_result(search)
    assert not result.all_items()

    def call_me_back(result: Result[Any]) -> None:
        nonlocal called_with
        called_with = result
        print('Got called', result)

    called_with = None
    result.listeners += call_me_back

    # Adding members

    for member in members:
        print('Adding', member)
        added = content.add(member)
        if member in expected:
            if added:
                assert called_with
                assert member in result.all_instances()
                assert member in called_with.all_instances()
                called_with = None
            else:
                assert called_with is None
                assert member in result.all_instances()
        else:
            assert called_with is None

    # Removing members

    for member in members:
        print('Removing', member)
        try:
            content.remove(member)
        except KeyError:
            continue
        else:
            if member in expected:
                assert called_with
                assert member not in result.all_instances()
                assert member not in called_with.all_instances()
                called_with = None
            else:
                assert called_with is None

    # Removing listener and adding/removing members

    result.listeners -= call_me_back

    for member in members:
        print('Adding', member)
        content.add(member)
        assert called_with is None

        print('Removing', member)
        try:
            content.remove(member)
        except KeyError:
            continue
        else:
            assert called_with is None

    # Test again, this time deleting the listener

    result.listeners += call_me_back
    del call_me_back

    for member in members:
        print('Adding', member)
        content.add(member)
        assert called_with is None

        print('Removing', member)
        try:
            content.remove(member)
        except KeyError:
            continue
        else:
            assert called_with is None


@pytest.mark.parametrize(('members', 'search', 'expected'), MEMBER_FIXTURES)
def test_bound_method_listener(
    members: Collection[Any],
    search: type[Any],
    expected: Sequence[Any] | None,
) -> None:
    print(members, search, expected)
    expected = list(expected) if expected is not None else []
    content, lookup = setup_lookup([])

    result = lookup.lookup_result(search)
    assert not result.all_items()

    class ToCall:
        def call_me_back(self, result: Result[Any]) -> None:
            nonlocal called_with
            called_with = result
            print('Got called', result)

    to_call = ToCall()
    called_with = None
    result.listeners += to_call.call_me_back

    # Adding members

    for member in members:
        print('Adding', member)
        added = content.add(member)
        if member in expected:
            if added:
                assert called_with
                assert member in result.all_instances()
                assert member in called_with.all_instances()
                called_with = None
            else:
                assert called_with is None
                assert member in result.all_instances()
        else:
            assert called_with is None

    # Removing members

    for member in members:
        print('Removing', member)
        try:
            content.remove(member)
        except KeyError:
            continue
        else:
            if member in expected:
                assert called_with
                assert member not in result.all_instances()
                assert member not in called_with.all_instances()
                called_with = None
            else:
                assert called_with is None

    # Removing listener and adding/removing members

    result.listeners -= to_call.call_me_back

    for member in members:
        print('Adding', member)
        content.add(member)
        assert called_with is None

        print('Removing', member)
        try:
            content.remove(member)
        except KeyError:
            continue
        else:
            assert called_with is None

    # Test again, this time deleting the listener object
    result.listeners += to_call.call_me_back
    del to_call

    for member in members:
        print('Adding', member)
        content.add(member)
        assert called_with is None

        print('Removing', member)
        try:
            content.remove(member)
        except KeyError:
            continue
        else:
            assert called_with is None


def test_multiple_listeners() -> None:
    content, lookup = setup_lookup([])

    result = lookup.lookup_result(TestParentObject)

    def call_me_back1(result: Result[Any]) -> None:
        called_with[1] = result
        print('1 Got called', result)

    def call_me_back2(result: Result[Any]) -> None:
        called_with[2] = result
        print('2 Got called', result)

    called_with = {}
    result.listeners += call_me_back1
    result.listeners += call_me_back2

    members = [obj, obj, obj2, parent, child]

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

    def check_not_called() -> None:
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

    # Removing listener and adding/removing members

    result.listeners -= call_me_back1
    result.listeners -= call_me_back2

    check_not_called()

    # Test again, this time deleting the listener object

    result.listeners += call_me_back1
    result.listeners += call_me_back2
    del call_me_back1
    del call_me_back2

    check_not_called()


def test_multiple_results() -> None:
    content, lookup = setup_lookup([])

    result_object = lookup.lookup_result(object)
    result_parent = lookup.lookup_result(TestParentObject)
    result_child = lookup.lookup_result(TestChildObject)
    result_other = lookup.lookup_result(TestOtherObject)

    def call_me_back(result: Result[Any]) -> None:
        assert isinstance(result, GLResult)
        called_with[result._cls] = result
        print('Got called', result)

    called_with = {}
    result_object.listeners += call_me_back
    result_parent.listeners += call_me_back
    result_child.listeners += call_me_back
    result_other.listeners += call_me_back

    members = [obj, obj, obj2, parent]

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

    def check_not_called() -> None:
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

    # Removing listener and adding/removing members

    result_object.listeners -= call_me_back
    result_parent.listeners -= call_me_back
    result_child.listeners -= call_me_back
    result_other.listeners -= call_me_back

    check_not_called()

    # Test again, this time deleting the listener object

    result_object.listeners += call_me_back
    result_parent.listeners += call_me_back
    result_child.listeners += call_me_back
    result_other.listeners += call_me_back
    del call_me_back

    check_not_called()


@pytest.mark.xfail
def test_modify_lookup_from_listener() -> None:
    content, lookup = setup_lookup([])

    result_object = lookup.lookup_result(object)

    def call_me_back(result: Result[Any]) -> None:
        content.add(obj2)

    result_object.listeners += call_me_back

    content.add(obj)


def test_del_result_clear_listener() -> None:
    content, lookup = setup_lookup([])
    result_object = lookup.lookup_result(object)

    def call_me_back(result: Result[Any]) -> None:
        nonlocal called_with
        called_with = result
        print('Got called', result)

    called_with = None
    result_object.listeners += call_me_back

    content.add(obj)
    assert called_with is result_object
    called_with = None

    del result_object
    gc.collect()

    content.add(obj2)
    assert not called_with


# Result listeners with Executor


@pytest.mark.parametrize(('members', 'search', 'expected'), MEMBER_FIXTURES)
def test_listener_with_executor(
    members: Collection[Any],
    search: type[Any],
    expected: Sequence[Any] | None,
    request: pytest.FixtureRequest,
) -> None:
    print(members, search, expected)
    expected = list(expected) if expected is not None else []
    executor = ThreadPoolExecutor()
    request.addfinalizer(executor.shutdown)
    content = InstanceContent(notify_in=executor)
    lookup = GenericLookup(content)
    test_thread = threading.current_thread()
    called_event = threading.Event()

    result = lookup.lookup_result(search)
    assert not result.all_items()

    def call_me_back(result: Result[Any]) -> None:
        nonlocal called_with, called_in_thread
        called_with = result
        called_in_thread = threading.current_thread()
        print('Got called', result)
        called_event.set()

    called_with = None
    called_in_thread = None
    result.listeners += call_me_back

    # Adding members

    for member in members:
        print('Adding', member)
        added = content.add(member)
        if member in expected:
            if added:
                assert called_event.wait(THREAD_WAITING_TIME), (
                    'Timeout waiting for callback to be called'
                )
                called_event.clear()
                assert called_with
                assert member in result.all_instances()
                assert member in called_with.all_instances()
                assert called_in_thread
                assert called_in_thread != test_thread
                called_with = None
                called_in_thread = None
            else:
                assert not called_event.wait(THREAD_WAITING_TIME), (
                    'Callback got called when it should not'
                )
                assert called_with is None
                assert called_in_thread is None
                assert member in result.all_instances()
        else:
            assert not called_event.wait(THREAD_WAITING_TIME), (
                'Callback got called when it should not'
            )
            assert called_with is None
            assert called_in_thread is None

    # Removing members

    for member in members:
        print('Removing', member)
        try:
            content.remove(member)
        except KeyError:
            continue
        else:
            if member in expected:
                assert called_event.wait(THREAD_WAITING_TIME), (
                    'Timeout waiting for callback to be called'
                )
                called_event.clear()
                assert called_with
                assert member not in result.all_instances()
                assert member not in called_with.all_instances()
                assert called_in_thread
                assert called_in_thread != test_thread
                called_with = None
                called_in_thread = None
            else:
                assert not called_event.wait(THREAD_WAITING_TIME), (
                    'Callback got called when it should not'
                )
                assert called_with is None
                assert called_in_thread is None

    # Removing listener and adding/removing members

    result.listeners -= call_me_back

    for member in members:
        print('Adding', member)
        content.add(member)
        assert called_with is None

        print('Removing', member)
        try:
            content.remove(member)
        except KeyError:
            continue
        else:
            assert not called_event.wait(THREAD_WAITING_TIME), (
                'Callback got called when it should not'
            )
            assert called_with is None
            assert called_in_thread is None


def test_multiple_results_with_executor(request: pytest.FixtureRequest) -> None:
    executor = ThreadPoolExecutor()
    request.addfinalizer(executor.shutdown)
    content = InstanceContent(notify_in=executor)
    lookup = GenericLookup(content)
    test_thread = threading.current_thread()

    result_object = lookup.lookup_result(object)
    result_parent = lookup.lookup_result(TestParentObject)
    result_child = lookup.lookup_result(TestChildObject)
    result_other = lookup.lookup_result(TestOtherObject)
    called_events = {
        object: threading.Event(),
        TestParentObject: threading.Event(),
        TestChildObject: threading.Event(),
        TestOtherObject: threading.Event(),
    }

    def call_me_back(result: Result[Any]) -> None:
        assert isinstance(result, GLResult)
        called_with[result._cls] = result
        called_in_thread[result._cls] = threading.current_thread()
        print('Got called', result)
        called_events[result._cls].set()

    called_with = {}
    called_in_thread = {}
    result_object.listeners += call_me_back
    result_parent.listeners += call_me_back
    result_child.listeners += call_me_back
    result_other.listeners += call_me_back

    members = [obj, obj, obj2, parent]

    def check_for_a_class(member: object, added: bool, cls: type[Any], result_cls: object) -> None:  # noqa: FBT001
        if isinstance(member, cls):
            if added:
                assert called_events[cls].wait(THREAD_WAITING_TIME), (
                    'Timeout waiting for callback to be called'
                )
                called_events[cls].clear()
                assert cls in called_with
                assert called_with[cls] == result_cls
                assert called_in_thread[cls]
                assert called_in_thread[cls] != test_thread
                del called_with[cls]
                del called_in_thread[cls]
            else:
                assert not called_events[cls].wait(THREAD_WAITING_TIME), (
                    'Callback got called when it should not'
                )
                assert cls not in called_with
                assert cls not in called_in_thread
        else:
            assert not called_events[cls].wait(THREAD_WAITING_TIME), (
                'Callback got called when it should not'
            )
            assert cls not in called_with
            assert cls not in called_in_thread

    # Adding members

    for member in members:
        print('Adding', member)
        added = content.add(member)
        check_for_a_class(member, added, object, result_object)
        check_for_a_class(member, added, TestParentObject, result_parent)
        check_for_a_class(member, added, TestChildObject, result_child)
        check_for_a_class(member, added, TestOtherObject, result_other)
        assert not called_with
        assert not called_in_thread

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
            assert not called_in_thread

    # Removing listener and adding/removing members

    result_object.listeners -= call_me_back
    result_parent.listeners -= call_me_back
    result_child.listeners -= call_me_back
    result_other.listeners -= call_me_back

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
            assert not called_events[type(member)].wait(THREAD_WAITING_TIME), (
                'Callback got called when it should not'
            )
            assert not called_with
            assert not called_in_thread


# InstanceContent Convertor


class KeyObject:
    def __init__(self, member: object) -> None:
        super().__init__()

        self.member = member

    @override
    def __repr__(self) -> str:
        return f'Key({super().__repr__()}) of {self.member!r}'


class MyConvertor(Convertor[KeyObject, Any]):
    def __init__(self, map_: dict[KeyObject, object]) -> None:
        super().__init__()

        self.map = map_
        self.convert_called: KeyObject | None = None
        self.type_called: KeyObject | None = None

    def reset(self) -> None:
        print('reset')
        self.convert_called = None
        self.type_called = None

    @override
    def convert(self, obj: KeyObject) -> Any:
        print('convert called', obj)
        self.convert_called = obj
        return self.map[obj]

    @override
    def type(self, obj: KeyObject) -> type[Any]:
        print('type called', obj)
        self.type_called = obj
        return type(self.map[obj])

    @override
    def id(self, obj: KeyObject) -> str:
        return str(id(obj))

    @override
    def display_name(self, obj: KeyObject) -> str:
        return str(obj)


class WrapObject:
    def __init__(self, o: object) -> None:
        super().__init__()

        self.o = o

    @override
    def __hash__(self) -> int:
        return hash(self.o)

    @override
    def __eq__(self, other: object) -> bool:
        return self.o == other

    @override
    def __repr__(self) -> str:
        return f'Wrap({super().__repr__()}) for {self.o!r}'


def make_convertor_maps(
    members: Iterable[Any],
) -> tuple[
    dict[KeyObject, object],
    dict[Any, list[KeyObject]],
]:
    keys_to_members: dict[KeyObject, object] = {}
    members_to_keys: dict[Any, list[KeyObject]] = {}
    added_members: set[object] = set()
    for member in members:
        if type(member) is object:
            member = WrapObject(member)  # noqa: PLW2901
        if member in added_members:
            continue

        key = KeyObject(member)
        keys_to_members[key] = member
        if member not in members_to_keys:
            members_to_keys[member] = []
        members_to_keys[member].append(key)
        added_members.add(member)

    return keys_to_members, members_to_keys


def test_convertor_none_key() -> None:
    with pytest.raises(ValueError, match='None cannot be a lookup member'):
        setup_lookup([None], MyConvertor({}))


def test_convertor_add() -> None:
    members = [object, parent, child, other, parent]
    content = InstanceContent()
    lookup = GenericLookup(content)

    keys_to_members, _ = make_convertor_maps(members)
    convertor = MyConvertor(keys_to_members)

    for key in keys_to_members:
        content.add(key, convertor=convertor)

    storage = lookup._storage
    assert storage
    assert isinstance(storage, SetStorage)
    assert storage._content

    def check_in_storage(obj: object) -> bool:
        return any(pair.get_instance() == obj for pair in storage._content)

    for member in members:
        assert check_in_storage(member)


def test_convertor_set() -> None:
    members = [object, parent, child, other, parent]
    content = InstanceContent()
    lookup = GenericLookup(content)

    keys_to_members, _ = make_convertor_maps(members)
    convertor = MyConvertor(keys_to_members)

    content.set(keys_to_members.keys(), convertor=convertor)

    storage = lookup._storage
    assert storage
    assert isinstance(storage, SetStorage)
    assert storage._content

    def check_in_storage(obj: object) -> bool:
        return any(pair.get_instance() == obj for pair in storage._content)

    for member in members:
        assert check_in_storage(member)


def test_convertor_remove() -> None:
    members = [object, parent, child, other, parent]
    content = InstanceContent()
    lookup = GenericLookup(content)

    keys_to_members, _ = make_convertor_maps(members)
    convertor = MyConvertor(keys_to_members)
    content.set(keys_to_members.keys(), convertor=convertor)

    for key in keys_to_members:
        try:
            content.remove(key, convertor=convertor)
        except KeyError:  # noqa: PERF203
            print('Could not remove', key)

    storage = lookup._storage
    assert storage
    assert isinstance(storage, SetStorage)
    assert storage._content == set()

    def check_in_storage(obj: object) -> bool:
        return any(pair.get_instance() == obj for pair in storage._content)

    for member in members:
        assert not check_in_storage(member)


@pytest.mark.parametrize(('members', 'search', 'expected'), MEMBER_FIXTURES)
def test_instance_convertor_lookup(
    members: Collection[Any],
    search: type[Any],
    expected: Sequence[Any] | None,
) -> None:
    keys_to_members, members_to_keys = make_convertor_maps(members)
    convertor = MyConvertor(keys_to_members)
    _, lookup = setup_lookup(keys_to_members.keys(), convertor)

    got = lookup.lookup(search)
    if expected:
        assert got in expected
        assert convertor.convert_called in members_to_keys[got]
        assert convertor.type_called in members_to_keys[got]
    else:
        assert got is None
        assert convertor.convert_called is None
        if members:
            assert isinstance(convertor.type_called, KeyObject)
        else:
            assert convertor.type_called is None


@pytest.mark.parametrize(('members', 'search', 'expected'), MEMBER_FIXTURES)
def test_instance_convertor_lookup_item(
    members: Collection[Any],
    search: type[Any],
    expected: Sequence[Any] | None,
) -> None:
    def clear_cache() -> None:
        assert isinstance(lookup._storage, SetStorage)
        for item in lookup._storage._content:
            assert isinstance(item, ConvertingItem)
            item._ref = None
        for result in lookup._storage._results.values():
            result.clear_cache()

    keys_to_members, members_to_keys = make_convertor_maps(members)
    convertor = MyConvertor(keys_to_members)
    _, lookup = setup_lookup(keys_to_members.keys(), convertor)

    item = lookup.lookup_item(search)
    check_item(expected, item)
    # Clear, as we want to check just what lookup_item() does
    convertor.reset()
    clear_cache()
    assert item == lookup.lookup_item(search)
    assert convertor.convert_called is None, 'lookup_item() should not convert the instance'
    if expected:
        assert item is not None
        assert convertor.type_called in members_to_keys[item.get_instance()]
    else:
        assert convertor.convert_called is None
        if members:
            assert isinstance(convertor.type_called, KeyObject)
        else:
            assert convertor.type_called is None


@pytest.mark.parametrize(('members', 'search', 'expected'), MEMBER_FIXTURES)
def test_instance_convertor_lookup_all(
    members: Collection[Any],
    search: type[Any],
    expected: Sequence[Any] | None,
) -> None:
    def clear_cache() -> None:
        assert isinstance(lookup._storage, SetStorage)
        for item in lookup._storage._content:
            assert isinstance(item, ConvertingItem)
            item._ref = None
        for result in lookup._storage._results.values():
            result.clear_cache()

    keys_to_members, _ = make_convertor_maps(members)
    convertor = MyConvertor(keys_to_members)
    _, lookup = setup_lookup(keys_to_members.keys(), convertor)

    expected = list(expected) if expected is not None else []
    all_instances = lookup.lookup_all(search)
    check_all_instances(list(expected), all_instances)
    # Clear, as we want to check just what lookup_all() does
    convertor.reset()
    clear_cache()
    assert all_instances == lookup.lookup_all(search)
    if expected:
        # Can't test much here
        assert isinstance(convertor.convert_called, KeyObject)
        assert isinstance(convertor.type_called, KeyObject)
    else:
        assert convertor.convert_called is None
        if members:
            assert isinstance(convertor.type_called, KeyObject)
        else:
            assert convertor.type_called is None


@pytest.mark.parametrize(('members', 'search', 'expected'), MEMBER_FIXTURES)
def test_instance_convertor_lookup_result(
    members: Collection[Any],
    search: type[Any],
    expected: Sequence[Any] | None,
) -> None:
    def clear_cache() -> None:
        assert isinstance(lookup._storage, SetStorage)
        for item in lookup._storage._content:
            assert isinstance(item, ConvertingItem)
            item._ref = None
        for result in lookup._storage._results.values():
            result.clear_cache()

    def swap_object_cls(cls: type[Any]) -> type[Any]:
        if cls is object:
            return WrapObject
        else:
            return cls

    expected = list(expected) if expected is not None else []
    expected_classes = {swap_object_cls(type(instance)) for instance in expected}  # pyright: ignore[reportUnknownArgumentType]
    keys_to_members, _ = make_convertor_maps(members)
    convertor = MyConvertor(keys_to_members)
    _, lookup = setup_lookup(keys_to_members.keys(), convertor)

    # lookup_result

    result = lookup.lookup_result(search)
    assert result
    assert convertor.convert_called is None, 'lookup_result() should not convert the instances'
    if expected:
        assert isinstance(convertor.type_called, KeyObject)
    else:
        assert convertor.convert_called is None
        if members:
            assert isinstance(convertor.type_called, KeyObject)
        else:
            assert convertor.type_called is None
    convertor.reset()
    clear_cache()

    # all_classes

    all_classes = result.all_classes()
    assert isinstance(all_classes, Set)
    assert not isinstance(all_classes, MutableSet)
    assert len(all_classes) == len(expected_classes)
    assert all_classes == expected_classes
    assert convertor.convert_called is None, 'all_classes() should not convert the instances'
    if expected:
        assert isinstance(convertor.type_called, KeyObject)
    else:
        assert convertor.convert_called is None
        if members:
            assert isinstance(convertor.type_called, KeyObject)
        else:
            assert convertor.type_called is None
    convertor.reset()
    clear_cache()

    # all_instances

    all_instances = result.all_instances()
    check_all_instances(list(expected), all_instances)
    if expected:
        # Can't test much here
        assert isinstance(convertor.convert_called, KeyObject)
        assert isinstance(convertor.type_called, KeyObject)
    else:
        assert convertor.convert_called is None
        if members:
            assert isinstance(convertor.type_called, KeyObject)
        else:
            assert convertor.type_called is None
    convertor.reset()
    clear_cache()

    # all_items

    all_items = result.all_items()
    assert isinstance(all_items, Sequence)
    assert not isinstance(all_items, MutableSequence)
    assert len(all_items) == len(expected)
    for item, again in zip(all_items, result.all_items()):
        idx = check_item(expected, item)
        assert idx is not None
        expected.pop(idx)
        assert item == again
    # Clear, as we want to check just what lookup_all() does
    convertor.reset()
    clear_cache()
    assert all_items == result.all_items()
    assert convertor.convert_called is None, 'all_items() should not convert the instances'
    if members:
        assert isinstance(convertor.type_called, KeyObject)
    else:
        assert convertor.type_called is None


# GenericLookup subclass API


class MyLookup(GenericLookup):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._initialise_called = None
        self._before_lookup_called = None

    @override
    def _initialise(self) -> None:
        self._initialise_called = True

    @override
    def _before_lookup(self, cls: type[object]) -> None:
        self._before_lookup_called = cls


def test_subclass_api() -> None:
    content = InstanceContent()
    lookup = MyLookup(content)

    assert not lookup._initialise_called
    assert not lookup._before_lookup_called

    content.add(object())

    assert lookup._initialise_called
    assert not lookup._before_lookup_called

    lookup.lookup(object)

    assert lookup._before_lookup_called is object


# Miscelleanous features


def test_str() -> None:
    """Checks that __str__ don\'t raise exceptions"""
    content, lookup = setup_lookup([])
    assert str(content)
    assert str(lookup)
    assert lookup._storage
    assert str(lookup._storage)
    assert str(lookup.lookup_result(object))


# TODO:
# Test GLResult caches
