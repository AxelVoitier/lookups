# Copyright (c) 2019 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

# System imports
from abc import ABC, abstractmethod
from collections.abc import Container
from contextlib import contextmanager
from threading import RLock
from typing import TYPE_CHECKING, Any, Callable, TypeVar

# Third-party imports
from listeners import Observable
from typing_extensions import override

# Local imports
from .lookup import Item, Lookup, Result

T = TypeVar('T')
if TYPE_CHECKING:
    from collections.abc import Collection, Iterable, Iterator, MutableSequence, Sequence, Set
    from concurrent.futures import Executor


class GenericLookup(Lookup):
    """
    Implementation of the lookup from OpenAPIs that is based on the insertion of Item.

    This class should provide the default way of how to store (Class, Object) pairs in the lookups.
    It offers protected methods for subclasses to register the pairs.

    Note:
    - GenericLookup is the API for users of the lookup.
    - Content is the API for owner/creator of the lookup.
    - Storage is the actual internal place where (Class, Object) pairs are stored.
    """

    def __init__(self, content: Content) -> None:
        """
        Constructor to create this lookup and associate it with given Content.

        The content then allows the creator to invoke protected methods which are not accessible for
        any other user of the lookup.

        :param content: The content to associate with.
        """
        super().__init__()

        self._storage: Storage | None = None
        self._storage_lock = RLock()
        self._storage_is_used = False

        content._attach(self)

    @contextmanager
    def _storage_for_lookup(self) -> Iterator[Storage]:
        from .set_storage import SetStorage  # noqa: PLC0415

        with self._storage_lock:
            # Enter storage
            if (storage := self._storage) is None:
                self._storage = storage = SetStorage()
                self._initialise()

            yield storage

    @contextmanager
    def _storage_for_modification(
        self,
        ensure: int,
        notify_in: Executor | None = None,
    ) -> Iterator[Transaction]:
        with self._storage_for_lookup() as storage:
            if self._storage_is_used:
                msg = 'You are trying to modify a lookup from a lookup query!'
                raise RuntimeError(msg)
            self._storage_is_used = True

            try:
                transaction = storage.begin_transaction(ensure)
                yield transaction
                to_notify = storage.end_transaction(transaction)
            finally:
                # Exit storage
                self._storage_is_used = False

            self._notify_in(notify_in, to_notify)

    def _initialise(self) -> None:
        """Method for subclasses to initialize themselves."""

    def _before_lookup(self, cls: type[object]) -> None:
        """
        Notifies subclasses that a query is about to be processed.

        :param cls: Class or type of the objects searched for.
        """

    def _add_pair(self, pair: Pair[T], notify_in: Executor | None = None) -> bool:
        """
        The method to add instance to the lookup with.

        :param pair: Class/instance pair.
        :param notify_in: The executor that will handle the notification of events.
        :return: True if the pair has been added for the first time or False if some other pair
        equal to this one already existed in the lookup
        """
        with self._storage_for_modification(-2, notify_in) as transaction:
            return transaction.add(pair)

    def _remove_pair(self, pair: Pair[T], notify_in: Executor | None = None) -> None:
        """
        Remove instance.

        :param pair: Class/instance pair.
        :param notify_in: The executor that will handle the notification of events.
        """
        with self._storage_for_modification(-1, notify_in) as transaction:
            transaction.remove(pair)

    def _set_pairs(self, pairs: Collection[Pair[T]], notify_in: Executor | None = None) -> None:
        """
        Changes all pairs in the lookup to new values, notifies listeners using provided executor.

        :param pairs: The collection of class/instance pairs.
        :param notify_in: The executor that will handle the notification of events.
        """
        with self._storage_for_modification(len(pairs), notify_in) as transaction:
            transaction.set_all(pairs)

    def _notify_in(self, notify_in: Executor | None, listeners: Iterable[Result[T]]) -> None:
        if not notify_in:
            for result in listeners:
                result.listeners(result)
        else:
            notify_in.map(
                Observable.__call__,
                [result.listeners for result in listeners],
                listeners,
            )

    @override
    def lookup(self, cls: type[T]) -> T | None:
        item = self.lookup_item(cls)
        return item.get_instance() if item is not None else None

    @override
    def lookup_result(self, cls: type[T]) -> Result[T]:
        self._before_lookup(cls)
        with self._storage_for_lookup() as storage:
            result = storage.find_result(cls)
            if result:
                return result

            result = GLResult(self, cls)
            storage.register_result(result)

            return result

    @override
    def lookup_item(self, cls: type[T]) -> Item[T] | None:
        self._before_lookup(cls)
        with self._storage_for_lookup() as storage:
            for pair in storage.lookup(cls):
                return pair
            return None

    @override
    def __str__(self) -> str:
        return repr(self)

    @override
    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(<content>)'


# For Java folks ;)
AbstractLookup = GenericLookup


class Pair(Item[T]):
    """
    Extension to the default lookup item that offers additional information for the data structures
    used in GenericLookup.
    """


class GLResult(Result[T]):
    def __init__(self, lookup: GenericLookup, cls: type[T]) -> None:
        super().__init__()

        self._lookup = lookup
        self._cls = cls

        self._classes_cache: Set[type[T]] | None = None
        self._items_cache: Sequence[Item[T]] | None = None
        self._instances_cache: Sequence[T] | None = None

        self.listeners = Observable[Callable[[Result[T]], Any]]()

    def clear_cache(self) -> None:
        """To be called when a result is affected by a change during a transaction."""
        self._classes_cache = None
        self._items_cache = None
        self._instances_cache = None

    @override
    def all_classes(self) -> Set[type[T]]:
        self._lookup._before_lookup(self._cls)

        if (classes := self._classes_cache) is not None:
            return classes

        classes = frozenset([item.get_type() for item in self._all_items_without_before_lookup()])

        self._classes_cache = classes
        return classes

    @override
    def all_instances(self) -> Sequence[T]:
        self._lookup._before_lookup(self._cls)

        if instances := self._instances_cache:
            return instances

        instances = [item.get_instance() for item in self._all_items_without_before_lookup()]
        instances = tuple([instance for instance in instances if instance is not None])

        self._instances_cache = instances
        return instances

    @override
    def all_items(self) -> Sequence[Item[T]]:
        self._lookup._before_lookup(self._cls)
        return self._all_items_without_before_lookup()

    def _all_items_without_before_lookup(self) -> Sequence[Item[T]]:
        if items := self._items_cache:
            return items

        with self._lookup._storage_for_lookup() as storage:
            pairs = tuple(storage.lookup(self._cls))
            self._items_cache = pairs
            return pairs

    @override
    def __str__(self) -> str:
        return repr(self)

    @override
    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self._lookup!r}, {self._cls!r})'


class Content(Container[Any]):
    """
    A class that can be used by the creator of the GenericLookup to control its content (a kind of
    Privileged API giving creator of the lookup more rights than subsequent users of the lookup).

    Note that a Content does not store any lookup item!
    The Storage instanciated by GenericLookup does.
    """

    def __init__(self, notify_in: Executor | None = None) -> None:
        """
        Creates a content associated with an executor to handle dispatch of changes.

        :param notify_in: The executor to notify changes in (ie. to listeners of lookup results).
        """
        super().__init__()

        self._notify_in: Executor | None = notify_in  # Do not serialize
        self._generic_lookup: GenericLookup | None = None
        self._early_pairs: MutableSequence[Pair[Any]] = []

    def _attach(self, lookup: GenericLookup) -> None:
        """
        A lookup attaches to this object.
        """
        if self._generic_lookup is None:
            self._generic_lookup = lookup

            if pairs := self._early_pairs:
                self._set_pairs(pairs)
                self._early_pairs = []

        else:
            msg = (
                f'Trying to use content for {lookup!r} '
                f'but it is already used for {self._generic_lookup!r}'
            )
            raise RuntimeError(msg)

    def _add_pair(self, pair: Pair[Any]) -> bool:
        """
        The method to add a pair to the associated GenericLookup.

        Preferably call this method when lookup is already associated with this content (association
        is done by passing this object to some GenericLookup's constructor once).

        :param pair: Class/instance pair.
        :return: True if the pair has been added for the first time or False if some other pair
        equal to this one already existed in the lookup
        """
        if lookup := self._generic_lookup:
            return lookup._add_pair(pair, self._notify_in)
        else:
            present = pair in self._early_pairs
            self._early_pairs.append(pair)
            return present

    def _remove_pair(self, pair: Pair[Any]) -> None:
        """
        Remove instance.

        :param pair: Class/instance pair.
        """
        if lookup := self._generic_lookup:
            lookup._remove_pair(pair, self._notify_in)
        else:
            self._early_pairs.remove(pair)

    def _set_pairs(self, pairs: Collection[Pair[Any]]) -> None:
        """
        Changes all pairs in the lookup to new values.

        :param pairs: The collection of class/instance pairs.
        """
        if lookup := self._generic_lookup:
            lookup._set_pairs(pairs, self._notify_in)
        else:
            self._early_pairs = list(pairs)

    @override
    def __contains__(self, item: object) -> bool:
        if lookup := self._generic_lookup:
            with lookup._storage_for_lookup() as storage:
                return item in storage
        else:
            return item in self._early_pairs


class Storage(ABC, Container[Any]):
    """Storage to keep the internal structure of Pairs and to answer different queries."""

    @abstractmethod
    def begin_transaction(self, ensure: int) -> Transaction:
        """
        Initializes a modification operation by creating an object that will be passsed to all add,
        remove, retainAll methods and should collect enough information about the change to notify
        listeners about the transaction later.

        :param ensure: The amount of items that will appear in the storage after the modifications:
         * -1 == remove one
         * -2 == add one
         * >= 0: the amount of objects at the end
        :return: A transaction object
        """
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def end_transaction(self, transaction: Transaction) -> Iterable[GLResult[Any]]:
        """
        Collects all affected results that were modified in the given transaction.

        :param transaction: The transaction object.
        :return: The results affected by a change.
        """
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def lookup(self, cls: type[T]) -> Iterable[Pair[T]]:
        """
        Queries for instances of given class.

        :param cls: The class to search for.
        :return: Iterable of Item
        """
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def register_result(self, result: GLResult[T]) -> None:
        """
        Registers a result with the storage.

        :param result: The new result to remember.
        """
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def find_result(self, cls: type[T]) -> GLResult[T] | None:
        raise NotImplementedError  # pragma: no cover


class Transaction(ABC):
    """Keeps track of changes happening in a Storage"""

    @abstractmethod
    def add(self, pair: Pair[Any]) -> bool:
        """
        Adds an item into the storage.

        :param item: Item to add.
        :return: True if the Item has been added for the first time or False if some other item
        equal to this one already existed in the lookup
        """
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def remove(self, pair: Pair[Any]) -> None:
        """
        Removes an item.

        :param item: Item to remove.
        """
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def set_all(self, pairs: Collection[Pair[Any]]) -> None:
        """
        Changes all pairs to new values.

        :param pairs: The collection of class/instance pairs.
        """
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def new_content(
        self,
        prev: Collection[Pair[Any]],
    ) -> tuple[Collection[Pair[Any]], Set[Pair[Any]]]:
        """
        Return the new content once a transaction is finished.

        :param prev: The previous content.
        :return: Tuple of new content, set of changes.
        """
        raise NotImplementedError  # pragma: no cover
