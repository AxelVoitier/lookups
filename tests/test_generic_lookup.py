# -*- coding: utf-8 -*-
# Copyright (c) 2019 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# System imports
import gc
import threading
from collections.abc import Hashable, Sequence, MutableSequence, Set, MutableSet
from concurrent.futures import ThreadPoolExecutor

# Third-party imports
import pytest

# Local imports
from lookups import GenericLookup, InstanceContent, Convertor
from .tools import TestParentObject, TestChildObject, TestOtherObject


THREAD_WAITING_TIME = 0.025


obj = object()
obj2 = object()
parent = TestParentObject()
parent2 = TestParentObject()
child = TestChildObject()
child2 = TestChildObject()
other = TestOtherObject()


MEMBER_FIXTURES = [
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


def setup_lookup(members, convertor=None):
    content = InstanceContent()
    lookup = GenericLookup(content)
    content.set(members, convertor=convertor)

    return content, lookup


def check_all_instances(expected, all_instances):
    assert isinstance(all_instances, Sequence)
    assert not isinstance(all_instances, MutableSequence)
    assert len(all_instances) == len(expected)
    for instance in all_instances:
        assert instance in expected
        expected.remove(instance)


def check_item(expected, item):
    if expected is None:
        assert item is None
        return

    assert item is not None
    assert isinstance(item, Hashable)

    assert item.get_display_name()
    assert item.get_id()

    assert item.get_instance() in expected
    idx = expected.index(item.get_instance())

    assert issubclass(item.get_type(), type(expected[idx]))
    return idx


# Objects life-cycle


def test_instantiation():
    assert InstanceContent()
    assert GenericLookup(InstanceContent())


def test_cannot_reuse_content():
    content, lookup = setup_lookup([])

    with pytest.raises(RuntimeError):
        GenericLookup(content)


# InstanceContent.add()


def test_add_before_attach():
    members = [object, parent, child, other, parent]
    content = InstanceContent()

    for member in members:
        content.add(member)

    lookup = GenericLookup(content)

    assert lookup._storage
    assert lookup._storage._content

    def check_in_storage(obj):
        for pair in lookup._storage._content:
            if pair.get_instance() == obj:
                return True
        else:
            return False

    for member in members:
        assert check_in_storage(member)


def test_add_after_attach():
    members = [object, parent, child, other, parent]
    content = InstanceContent()
    lookup = GenericLookup(content)

    for member in members:
        content.add(member)

    assert lookup._storage
    assert lookup._storage._content

    def check_in_storage(obj):
        for pair in lookup._storage._content:
            if pair.get_instance() == obj:
                return True
        else:
            return False

    for member in members:
        assert check_in_storage(member)


# InstanceContent.set()


def test_set_before_attach():
    members = [object, parent, child, other, parent]
    content = InstanceContent()

    content.set(members)

    lookup = GenericLookup(content)

    assert lookup._storage
    assert lookup._storage._content

    def check_in_storage(obj):
        for pair in lookup._storage._content:
            if pair.get_instance() == obj:
                return True
        else:
            return False

    for member in members:
        assert check_in_storage(member)


def test_set_after_attach():
    members = [object, parent, child, other, parent]
    content = InstanceContent()
    lookup = GenericLookup(content)

    content.set(members)

    assert lookup._storage
    assert lookup._storage._content

    def check_in_storage(obj):
        for pair in lookup._storage._content:
            if pair.get_instance() == obj:
                return True
        else:
            return False

    for member in members:
        assert check_in_storage(member)


# InstanceContent.remove()


def test_remove_before_attach():
    members = [object, parent, child, other, parent]
    content = InstanceContent()
    content.set(members)

    for member in members:
        content.remove(member)

    lookup = GenericLookup(content)

    assert not lookup._storage
    # Can't test much more if no storage here...


def test_remove_after_attach():
    members = [object, parent, child, other, parent]
    content = InstanceContent()
    lookup = GenericLookup(content)
    content.set(members)

    for member in members:
        try:
            content.remove(member)
        except KeyError:
            print('Could not remove', member)

    assert lookup._storage
    assert lookup._storage._content == set()

    def check_in_storage(obj):
        for pair in lookup._storage._content:
            if pair.get_instance() == obj:
                return True
        else:
            return False

    for member in members:
        assert not check_in_storage(member)


# Basic lookup methods


@pytest.mark.parametrize('members, search, expected', MEMBER_FIXTURES)
def test_lookup(members, search, expected):
    content, lookup = setup_lookup(members)

    if expected:
        assert lookup.lookup(search) in expected
    else:
        assert lookup.lookup(search) is expected


@pytest.mark.parametrize('members, search, expected', MEMBER_FIXTURES)
def test_lookup_item(members, search, expected):
    content, lookup = setup_lookup(members)

    item = lookup.lookup_item(search)
    check_item(expected, item)
    assert item == lookup.lookup_item(search)


@pytest.mark.parametrize('members, search, expected', MEMBER_FIXTURES)
def test_lookup_all(members, search, expected):
    expected = list(expected) if expected is not None else []
    content, lookup = setup_lookup(members)

    all_instances = lookup.lookup_all(search)
    check_all_instances(expected, all_instances)


# Lookup.lookup_result()


@pytest.mark.parametrize('members, search, expected', MEMBER_FIXTURES)
def test_lookup_result(members, search, expected):
    print(members, search, expected)
    expected = list(expected) if expected is not None else []
    print(members, search, expected)
    expected_classes = {type(instance) for instance in expected}
    content, lookup = setup_lookup(members)

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
        expected.pop(idx)
        assert item == again


def test_lookup_result_already_exist():
    content, lookup = setup_lookup([])

    result1 = lookup.lookup_result(object)
    result2 = lookup.lookup_result(object)

    assert result1 is result2


# Result listeners


@pytest.mark.parametrize('members, search, expected', MEMBER_FIXTURES)
def test_listener(members, search, expected):
    print(members, search, expected)
    expected = list(expected) if expected is not None else []
    content, lookup = setup_lookup([])

    result = lookup.lookup_result(search)
    assert not result.all_items()

    def call_me_back(result):
        nonlocal called_with
        called_with = result
        print('Got called', result)

    called_with = None
    result.add_lookup_listener(call_me_back)

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

    result.remove_lookup_listener(call_me_back)

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


def test_multiple_listeners():
    content, lookup = setup_lookup([])

    result_object = lookup.lookup_result(object)
    result_parent = lookup.lookup_result(TestParentObject)
    result_child = lookup.lookup_result(TestChildObject)
    result_other = lookup.lookup_result(TestOtherObject)

    def call_me_back(result):
        called_with[result._cls] = result
        print('Got called', result)

    called_with = {}
    result_object.add_lookup_listener(call_me_back)
    result_parent.add_lookup_listener(call_me_back)
    result_child.add_lookup_listener(call_me_back)
    result_other.add_lookup_listener(call_me_back)

    members = [obj, obj, obj2, parent]

    def check_for_a_class(member, added, cls, result_cls):
        if isinstance(member, cls):
            if added:
                assert cls in called_with
                assert called_with[cls] == result_cls
                del called_with[cls]
            else:
                assert cls not in called_with
        else:
            assert cls not in called_with

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
            check_for_a_class(member, True, object, result_object)
            check_for_a_class(member, True, TestParentObject, result_parent)
            check_for_a_class(member, True, TestChildObject, result_child)
            check_for_a_class(member, True, TestOtherObject, result_other)
            assert not called_with

    # Removing listener and adding/removing members

    result_object.remove_lookup_listener(call_me_back)
    result_parent.remove_lookup_listener(call_me_back)
    result_child.remove_lookup_listener(call_me_back)
    result_other.remove_lookup_listener(call_me_back)

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


@pytest.mark.xfail
def test_modify_lookup_from_listener():
    content, lookup = setup_lookup([])

    result_object = lookup.lookup_result(object)

    def call_me_back(result):
        content.add(obj2)

    result_object.add_lookup_listener(call_me_back)

    content.add(obj)


def test_del_result_clear_listener():
    content, lookup = setup_lookup([])
    result_object = lookup.lookup_result(object)

    def call_me_back(result):
        nonlocal called_with
        called_with = result
        print('Got called', result)

    called_with = None
    result_object.add_lookup_listener(call_me_back)

    content.add(obj)
    assert called_with is result_object
    called_with = None

    del result_object
    gc.collect()

    content.add(obj2)
    assert not called_with


# Result listeners with Executor


@pytest.mark.parametrize('members, search, expected', MEMBER_FIXTURES)
def test_listener_with_executor(members, search, expected, request):
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

    def call_me_back(result):
        nonlocal called_with, called_in_thread
        called_with = result
        called_in_thread = threading.current_thread()
        print('Got called', result)
        called_event.set()

    called_with = None
    called_in_thread = None
    result.add_lookup_listener(call_me_back)

    # Adding members

    for member in members:
        print('Adding', member)
        added = content.add(member)
        if member in expected:
            if added:
                assert called_event.wait(
                    THREAD_WAITING_TIME), 'Timeout waiting for callback to be called'
                called_event.clear()
                assert called_with
                assert member in result.all_instances()
                assert member in called_with.all_instances()
                assert called_in_thread
                assert called_in_thread != test_thread
                called_with = None
                called_in_thread = None
            else:
                assert not called_event.wait(
                    THREAD_WAITING_TIME), 'Callback got called when it should not'
                assert called_with is None
                assert called_in_thread is None
                assert member in result.all_instances()
        else:
            assert not called_event.wait(
                THREAD_WAITING_TIME), 'Callback got called when it should not'
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
                assert called_event.wait(
                    THREAD_WAITING_TIME), 'Timeout waiting for callback to be called'
                called_event.clear()
                assert called_with
                assert member not in result.all_instances()
                assert member not in called_with.all_instances()
                assert called_in_thread
                assert called_in_thread != test_thread
                called_with = None
                called_in_thread = None
            else:
                assert not called_event.wait(
                    THREAD_WAITING_TIME), 'Callback got called when it should not'
                assert called_with is None
                assert called_in_thread is None

    # Removing listener and adding/removing members

    result.remove_lookup_listener(call_me_back)

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
            assert not called_event.wait(
                THREAD_WAITING_TIME), 'Callback got called when it should not'
            assert called_with is None
            assert called_in_thread is None


def test_multiple_listeners_with_executor(request):
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

    def call_me_back(result):
        called_with[result._cls] = result
        called_in_thread[result._cls] = threading.current_thread()
        print('Got called', result)
        called_events[result._cls].set()

    called_with = {}
    called_in_thread = {}
    result_object.add_lookup_listener(call_me_back)
    result_parent.add_lookup_listener(call_me_back)
    result_child.add_lookup_listener(call_me_back)
    result_other.add_lookup_listener(call_me_back)

    members = [obj, obj, obj2, parent]

    def check_for_a_class(member, added, cls, result_cls):
        if isinstance(member, cls):
            if added:
                assert called_events[cls].wait(
                    THREAD_WAITING_TIME), 'Timeout waiting for callback to be called'
                called_events[cls].clear()
                assert cls in called_with
                assert called_with[cls] == result_cls
                assert called_in_thread[cls]
                assert called_in_thread[cls] != test_thread
                del called_with[cls]
                del called_in_thread[cls]
            else:
                assert not called_events[cls].wait(
                    THREAD_WAITING_TIME), 'Callback got called when it should not'
                assert cls not in called_with
                assert cls not in called_in_thread
        else:
            assert not called_events[cls].wait(
                THREAD_WAITING_TIME), 'Callback got called when it should not'
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
            check_for_a_class(member, True, object, result_object)
            check_for_a_class(member, True, TestParentObject, result_parent)
            check_for_a_class(member, True, TestChildObject, result_child)
            check_for_a_class(member, True, TestOtherObject, result_other)
            assert not called_with
            assert not called_in_thread

    # Removing listener and adding/removing members

    result_object.remove_lookup_listener(call_me_back)
    result_parent.remove_lookup_listener(call_me_back)
    result_child.remove_lookup_listener(call_me_back)
    result_other.remove_lookup_listener(call_me_back)

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
            assert not called_events[type(member)].wait(
                THREAD_WAITING_TIME), 'Callback got called when it should not'
            assert not called_with
            assert not called_in_thread


# InstanceContent Convertor


class MyConvertor(Convertor):

    def __init__(self, map_):
        self.map = map_
        self.convert_called = None
        self.type_called = None

    def reset(self):
        print('reset')
        self.convert_called = None
        self.type_called = None

    def convert(self, obj):
        print('convert called', obj)
        self.convert_called = obj
        return self.map[obj]

    def type(self, obj):
        print('type called', obj)
        self.type_called = obj
        return type(self.map[obj])

    def id(self, obj):
        return str(id(obj))

    def display_name(self, obj):
        return str(obj)


class KeyObject:

    def __repr__(self):
        return f'Key({super().__repr__()}) of {self.member!r}'


class WrapObject:

    def __init__(self, o):
        self.o = o

    def __hash__(self):
        return hash(self.o)

    def __eq__(self, other):
        return self.o == other

    def __repr__(self):
        return f'Wrap({super().__repr__()}) for {self.o!r}'


def make_convertor_maps(members):
    keys_to_members = {}
    members_to_keys = {}
    added_members = set()
    for member in members:
        if type(member) is object:
            member = WrapObject(member)
        if member in added_members:
            continue

        key = KeyObject()
        key.member = member
        keys_to_members[key] = member
        if member not in members_to_keys:
            members_to_keys[member] = []
        members_to_keys[member].append(key)
        added_members.add(member)

    return keys_to_members, members_to_keys


def test_convertor_none_key():
    with pytest.raises(ValueError):
        content, lookup = setup_lookup([None], MyConvertor({}))


def test_convertor_add():
    members = [object, parent, child, other, parent]
    content = InstanceContent()
    lookup = GenericLookup(content)

    keys_to_members, members_to_keys = make_convertor_maps(members)
    convertor = MyConvertor(keys_to_members)

    for key in keys_to_members.keys():
        content.add(key, convertor=convertor)

    assert lookup._storage
    assert lookup._storage._content

    def check_in_storage(obj):
        for pair in lookup._storage._content:
            if pair.get_instance() == obj:
                return True
        else:
            return False

    for member in members:
        assert check_in_storage(member)


def test_convertor_set():
    members = [object, parent, child, other, parent]
    content = InstanceContent()
    lookup = GenericLookup(content)

    keys_to_members, members_to_keys = make_convertor_maps(members)
    convertor = MyConvertor(keys_to_members)

    content.set(keys_to_members.keys(), convertor=convertor)

    assert lookup._storage
    assert lookup._storage._content

    def check_in_storage(obj):
        for pair in lookup._storage._content:
            if pair.get_instance() == obj:
                return True
        else:
            return False

    for member in members:
        assert check_in_storage(member)


def test_convertor_remove():
    members = [object, parent, child, other, parent]
    content = InstanceContent()
    lookup = GenericLookup(content)

    keys_to_members, members_to_keys = make_convertor_maps(members)
    convertor = MyConvertor(keys_to_members)
    content.set(keys_to_members.keys(), convertor=convertor)

    for key in keys_to_members.keys():
        try:
            content.remove(key, convertor=convertor)
        except KeyError:
            print('Could not remove', key)

    assert lookup._storage
    assert lookup._storage._content == set()

    def check_in_storage(obj):
        for pair in lookup._storage._content:
            if pair.get_instance() == obj:
                return True
        else:
            return False

    for member in members:
        assert not check_in_storage(member)


@pytest.mark.parametrize('members, search, expected', MEMBER_FIXTURES)
def test_instance_convertor_lookup(members, search, expected):
    keys_to_members, members_to_keys = make_convertor_maps(members)
    convertor = MyConvertor(keys_to_members)
    content, lookup = setup_lookup(keys_to_members.keys(), convertor)

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


@pytest.mark.parametrize('members, search, expected', MEMBER_FIXTURES)
def test_instance_convertor_lookup_item(members, search, expected):
    def clear_cache():
        for item in lookup._storage._content:
            item._ref = None
        for result in lookup._storage._results.values():
            result.clear_cache()

    keys_to_members, members_to_keys = make_convertor_maps(members)
    convertor = MyConvertor(keys_to_members)
    content, lookup = setup_lookup(keys_to_members.keys(), convertor)

    item = lookup.lookup_item(search)
    check_item(expected, item)
    # Clear, as we want to check just what lookup_item() does
    convertor.reset()
    clear_cache()
    assert item == lookup.lookup_item(search)
    assert convertor.convert_called is None, 'lookup_item() should not convert the instance'
    if expected:
        assert convertor.type_called in members_to_keys[item.get_instance()]
    else:
        assert convertor.convert_called is None
        if members:
            assert isinstance(convertor.type_called, KeyObject)
        else:
            assert convertor.type_called is None


@pytest.mark.parametrize('members, search, expected', MEMBER_FIXTURES)
def test_instance_convertor_lookup_all(members, search, expected):
    def clear_cache():
        for item in lookup._storage._content:
            item._ref = None
        for result in lookup._storage._results.values():
            result.clear_cache()

    keys_to_members, members_to_keys = make_convertor_maps(members)
    convertor = MyConvertor(keys_to_members)
    content, lookup = setup_lookup(keys_to_members.keys(), convertor)

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


@pytest.mark.parametrize('members, search, expected', MEMBER_FIXTURES)
def test_instance_convertor_lookup_result(members, search, expected):
    def clear_cache():
        for item in lookup._storage._content:
            item._ref = None
        for result in lookup._storage._results.values():
            result.clear_cache()

    def swap_object_cls(cls):
        if cls is object:
            return WrapObject
        else:
            return cls

    expected = list(expected) if expected is not None else []
    expected_classes = {swap_object_cls(type(instance)) for instance in expected}
    keys_to_members, members_to_keys = make_convertor_maps(members)
    convertor = MyConvertor(keys_to_members)
    content, lookup = setup_lookup(keys_to_members.keys(), convertor)

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._initialise_called = None
        self._before_lookup_called = None

    def _initialise(self):
        self._initialise_called = True

    def _before_lookup(self, cls):
        self._before_lookup_called = cls


def test_subclass_api():
    content = InstanceContent()
    lookup = MyLookup(content)

    assert not lookup._initialise_called
    assert not lookup._before_lookup_called

    content.add(object())

    assert lookup._initialise_called
    assert not lookup._before_lookup_called

    lookup.lookup(object)

    assert lookup._before_lookup_called == object


# Miscelleanous features


def test_str():
    '''Checks that __str__ don\'t raise exceptions'''
    content, lookup = setup_lookup([])
    assert str(content)
    assert str(lookup)
    assert lookup._storage
    assert str(lookup._storage)
    assert str(lookup.lookup_result(object))

# TODO:
# Test GLResult caches
