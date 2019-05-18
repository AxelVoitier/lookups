# -*- coding: utf-8 -*-
# Copyright (c) 2019 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from __future__ import annotations  # noqa: T484

# System imports
import logging
from abc import ABC, abstractmethod
from typing import Sequence, AbstractSet, Type, Optional

# Third-party imports

# Local imports


_logger = logging.getLogger(__name__)


class Lookup(ABC):
    '''
    A general registry permitting clients to find instances of services (implementation of a given
    interface).

    This class is inspired Netbeans Platform lookup mechanism. The Lookup API concentrates on the
    lookup, not on the registration.
    '''

    @classmethod
    def get_default(cls) -> Lookup:
        '''
        Method to obtain the global lookup in the whole system.

        The actual returned implementation can be different in different systems, but the default
        one is based on lookup.Lookups.???.

        :return: The global lookup in the system
        :rtype: Lookup
        '''
        return None

    @abstractmethod
    def lookup(self, cls: Type[object]) -> Optional[object]:
        '''
        Look up an object matching a given type.

        If more than one object matches, the first will be returned.
        The template class may be a class or a type.
        The instance is guaranteed to be of the same type.

        :param cls: Class or type of the object we are searching for.
        :return: An object implementing the given type or None if no such implementation is found.
        '''

    @abstractmethod
    def lookup_result(self, cls: Type[object]) -> Result:
        '''
        Find a result corresponding to a given class.

        Equivalent to calling Lookup.Template but slightly more convenient.
        Subclasses may override this method to produce the same semantics more efficiently.

        :param cls: Class or type of the objects we are searching for.
        :return: A live object representing instances of that type.
        '''

    def lookup_item(self, cls: Type[object]) -> Optional[Item]:
        '''
        Look up the first item matching a given class.

        Includes not only the instance but other associated information.

        :param cls: Class or type of the objects we are searching for.
        :return: A matching item or None.
        '''
        result = self.lookup_result(cls)
        it = iter(result.all_items())
        return next(it, None)

    def lookup_all(self, cls: Type[object]) -> Sequence[object]:
        '''
        Find all instances corresponding to a given class.

        Equivalent to calling lookup_result().all_instances(), but slightly more convenient.
        Subclasses may override this method to produce the same semantics more efficiently.

        > for service in Lookup.get_default().lookup_all(type(MyService)):
        >     service.use_me()

        :param cls: Class or type of the objects we are searching for.
        :return: All currently available instances of that type.
        '''
        return self.lookup_result(cls).all_instances()


class Item(ABC):
    '''
    A single item in a lookup result.

    This wrapper provides unified access to not just the instance, but its class, a possible
    persistent identifier, and so on.
    '''

    @abstractmethod
    def get_display_name(self) -> str:
        '''
        Get a human presentable name for the item.

        This might be used when summarizing all the items found in a lookup result
        in some part of a GUI.

        :return: The string suitable for presenting the object to a user.
        '''

    @abstractmethod
    def get_id(self) -> str:
        '''
        Get a persistent identifier for the item.

        This identifier should uniquely represent the item within its containing lookup (and if
        possible within the global lookup as a whole). For example, it might represent the source of
        the instance as a file name. The ID may be persisted and in a later session used to find the
        same instance as was encountered earlier, by means of passing it into a lookup template.

        :return: A string ID of the item.
        '''

    @abstractmethod
    def get_instance(self) -> Optional[object]:
        '''
        Get the instance itself.

        :return: The instance or None if the instance cannot be created.
        '''

    @abstractmethod
    def get_type(self) -> Type[object]:
        '''
        Get the implementing class of the instance.

        :return: The class of the item.
        '''

    def __str__(self) -> str:
        '''Show ID for debugging.'''
        return self.get_id()


class Result(ABC):
    '''
    Result of a lookup request.

    Allows access to all matching instances at once.
    Also permits listening to changes in the result.
    Result can contain duplicate items.
    '''

    @abstractmethod
    def add_lookup_listener(self, listener: LookupListener) -> None:
        '''
        Registers a listener that is invoked when there is a possible change in this result.

        LookupListener protocol is to implement the following method:

            def result_changed(self, event: LookupEvent) -> None: ...

        Remember to keep a strong reference to the object you are attaching listener to.

        :param listener: The listener to add.
        '''

    @abstractmethod
    def remove_lookup_listener(self, listener: LookupListener) -> None:
        '''
        Unregisters a listener previously added.

        :param listener: The listener to remove.
        '''

    @abstractmethod
    def all_classes(self) -> AbstractSet[Type[object]]:
        '''
        Get all classes represented in the result.

        That is, the set of concrete classes used by instances present in the result.
        All duplicate classes will be omitted.

        :return: Immutable set of class objects.
        '''

    @abstractmethod
    def all_instances(self) -> Sequence[object]:
        '''
        Get all instances in the result.

        :return: Immutable sequence of all instances.
        '''

    @abstractmethod
    def all_items(self) -> Sequence[Item]:
        '''
        Get all registered items.

        This should include all pairs of instances together with their classes, IDs, and so on.

        :return: Immutable sequence of Item.
        '''


class LookupProvider(ABC):
    '''
    Classes implementing interface lookup.Provider are capable of
    and willing to provide a lookup (usually bound to the object).
    '''

    @abstractmethod
    def get_lookup(self) -> Lookup:
        '''
        Returns lookup associated with the object.

        :return: Fully initialized lookup instance provided by this object
        '''


class LookupListener(ABC):
    '''
    General listener for changes in lookup.
    '''

    @abstractmethod
    def result_changed(self, event: LookupEvent) -> None:
        '''
        A change in lookup occured.

        Please note that this method should never block since it might be called from lookup
        implementation internal threads. If you block here you are in risk that the thread you wait
        for might in turn wait for the lookup internal thread to finish its work.

        :param event: Event describing the change.
        '''


class LookupEvent(object):
    '''
    An event describing the change in the lookup's result.
    '''

    def __init__(self, source: Result) -> None:
        '''
        :param source: The lookup result which has changed.
        '''
        self.source = source
