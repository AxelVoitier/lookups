# Copyright (c) 2019 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

# System imports
import weakref
from abc import ABC, abstractmethod
from threading import RLock
from typing import TYPE_CHECKING, Generic, TypeVar

# Third-party imports
from typing_extensions import override

# Local imports
from .generic_lookup import Content, Pair
from .lookups import LookupItem

K = TypeVar('K')
T = TypeVar('T')
if TYPE_CHECKING:
    from collections.abc import Collection
    from typing import Any


class InstanceContent(Content):
    """API for an owner of a lookup to be able to add and remove object instances to it.
    add/set/remove methods also support an optional parameter `convertor` in order to only add
    lightweight objects to the content and return the real, possibly heavy objects, only when
    someone access their instance through a lookup.

    Typical usage:
    > ic = InstanceContent()
    > lookup = GenericLookup(ic)
    > ic.add(an_object)
    > ic.set(a_sequence_of_objects)
    """

    def add(self, instance: T, convertor: Convertor[T, Any] | None = None) -> bool:
        """
        Adds an instance to the lookup.

        If convertor is None:
            If instance already exists in the lookup (duplication is determined by object equality)
            then the new instance replaces the old one in the lookup but listener notifications are
            NOT delivered in such case.

        else:
            The instance argument is just a key, not the actual value to appear in the lookup.
            The value will be created on demand, later when it is really needed by calling convertor
            methods.

            This method is useful to delay creation of heavy weight objects. Instead just register
            lightweight key and a convertor.

            To remove registered object from lookup use remove() with the same arguments.

        :param instance: The instance.
        :param convertor: Convertor which postpone an instantiation. If None then the instance is
        registered directly.
        :return: True if the instance has been added for the first time or False if some other
        instance equal to this one already existed in the content
        """
        if convertor is None:
            return self._add_pair(SimpleItem(instance))
        else:
            return self._add_pair(ConvertingItem(instance, convertor))

    def remove(self, instance: T, convertor: Convertor[T, Any] | None = None) -> None:
        """
        Remove instance.

        :param instance: The instance.
        :param convertor: Convertor, for an instance added with one.
        """
        if convertor is None:
            self._remove_pair(SimpleItem(instance))
        else:
            self._remove_pair(ConvertingItem(instance, convertor))

    def set(self, instances: Collection[Any], convertor: Convertor[Any, Any] | None = None) -> None:
        """
        Changes all pairs in the lookup to new values.

        Converts collection of instances to collection of pairs.

        :param instances: The collection of (Item) objects.
        :param convertor: The convertor to use or None.
        """
        pairs: Collection[Pair[Any]]

        if convertor is None:
            pairs = tuple(SimpleItem(instance) for instance in instances)
        else:
            pairs = tuple(ConvertingItem(instance, convertor) for instance in instances)

        self._set_pairs(pairs)

    @override
    def __contains__(self, item: object) -> bool:
        return super().__contains__(SimpleItem(item))


class Convertor(Generic[K, T], ABC):
    """Convertor postpones an instantiation of an object."""

    @abstractmethod
    def convert(self, obj: K) -> T:
        """
        Convert obj to other object.

        There is no need to implement cache mechanism. It is provided by Item.get_instance() method
        itself. However the method can be called more than once because instance is held just by
        weak reference.

        :param obj: The registered object.
        :return: The object converted from this object.
        """
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def type(self, obj: K) -> type[T]:
        """
        Return type of converted object.

        Accessible via Item.get_type().

        :param obj: The registered object.
        :return: The class that will be produced from this object (class or superclass of
        convert(obj))
        """
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def id(self, obj: K) -> str:
        """
        Computes the ID of the resulted object.

        Accessible via Item.getId().

        :param obj: The registered object.
        :return: The ID for the object.
        """
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def display_name(self, obj: K) -> str:
        """
        The human presentable name for the object.

        Accessible via Item.getDisplayName().

        :param obj: The registered object.
        :return: The name representing the object for the user.
        """
        raise NotImplementedError  # pragma: no cover


class SimpleItem(LookupItem[T], Pair[T]):
    """Instance of one item representing an object."""


class ConvertingItem(Pair[T], Generic[K, T]):
    """Instance of one item convertible to an object."""

    def __init__(self, key: K, convertor: Convertor[K, T]) -> None:
        super().__init__()

        if key is None:
            msg = 'None cannot be a lookup member'
            raise ValueError(msg)

        self._key = key
        self._convertor = convertor
        self._ref: weakref.ReferenceType[T] | None = None
        self._lock = RLock()

    def _get_converted(self) -> T | None:
        if (ref := self._ref) is None:
            return None
        else:
            return ref()

    @override
    def get_display_name(self) -> str:
        return self._convertor.display_name(self._key)

    @override
    def get_id(self) -> str:
        return self._convertor.id(self._key)

    @override
    def get_instance(self) -> T | None:
        with self._lock:
            converted = self._get_converted()

            if converted is None:
                converted = self._convertor.convert(self._key)
                self._ref = weakref.ref(converted)

            return converted

    @override
    def get_type(self) -> type[T]:
        converted = self._get_converted()

        if converted is None:
            return self._convertor.type(self._key)
        else:
            return type(converted)

    @override
    def __eq__(self, other: object) -> bool:
        if isinstance(other, type(self)):
            return self._key == other._key
        else:
            return False

    @override
    def __hash__(self) -> int:
        try:
            return hash(self._key)
        except TypeError:  # Mutable, cannot be hashed
            return id(self._key)
