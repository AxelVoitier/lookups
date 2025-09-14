# Copyright (c) 2019 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

# System imports
import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Callable, Generic, TypeVar

# Third-party imports
from typing_extensions import override

# Local imports
# from . import global_

T = TypeVar('T')
if TYPE_CHECKING:
    from collections.abc import Sequence, Set

    from listeners import Listeners

_logger = logging.getLogger(__name__)


class Lookup(ABC):
    """
    A general registry permitting clients to find instances of services (implementation of a given
    interface).

    This class is inspired by Netbeans Platform lookup mechanism. The Lookup API concentrates on the
    lookup, not on the registration.
    """

    _DEFAULT_LOOKUP: Lookup | None = None
    _DEFAULT_LOOKUP_PROVIDER: LookupProvider | None = None
    _DEFAULT_ENTRY_POINT_GROUP: str = 'lookup.default'

    @classmethod
    def get_default(cls) -> Lookup:
        """
        Method to obtain the global lookup in the whole system.

        The actual returned implementation can be different in different systems, but the default
        one is based on lookups.ProxyLookup.

        The resolution is the following:
        - If there is already a default lookup provider defined, returns its lookup.
        - If there is already a default lookup defined, returns it.
        - Loads on EntryPointLookup on 'lookup.default' group:
          - If it finds a lookup which happens to also be a lookup provider, returns its lookup.
          - If it finds a lookup, returns it.
          - If it finds a lookup provider, returns DelegatedLookup from it.
        - Otherwise, returns a ProxyLookup with just the EntryPointLookup as source.

        :return: The global lookup in the system
        :rtype: Lookup
        """

        if (dflt_prov := cls._DEFAULT_LOOKUP_PROVIDER) is not None:
            return dflt_prov.get_lookup()
        if (dflt := cls._DEFAULT_LOOKUP) is not None:
            return dflt

        from .entry_point import EntryPointLookup  # noqa: PLC0415

        epl = EntryPointLookup(cls._DEFAULT_ENTRY_POINT_GROUP)
        cls._DEFAULT_LOOKUP = dflt = epl.lookup(Lookup)
        if dflt is not None:
            if isinstance(dflt, LookupProvider):
                cls._DEFAULT_LOOKUP_PROVIDER = dflt
                return cls._DEFAULT_LOOKUP_PROVIDER.get_lookup()

            return dflt

        provider = epl.lookup(LookupProvider)
        if provider is not None:
            from .delegated_lookup import DelegatedLookup  # noqa: PLC0415

            cls._DEFAULT_LOOKUP = DelegatedLookup(provider)

            return cls._DEFAULT_LOOKUP

        from .proxy_lookup import ProxyLookup  # noqa: PLC0415

        cls._DEFAULT_LOOKUP = ProxyLookup(epl)

        return cls._DEFAULT_LOOKUP

    @abstractmethod
    def lookup(self, cls: type[T]) -> T | None:
        """
        Look up an object matching a given type.

        If more than one object matches, the first will be returned.
        The template class may be a class or a type.
        The instance is guaranteed to be of the same type.

        :param cls: Class or type of the object we are searching for.
        :return: An object implementing the given type or None if no such implementation is found.
        """
        raise NotImplementedError  # pragma: no cover

    def __call__(self, cls: type[T]) -> T | None:
        return self.lookup(cls)

    @abstractmethod
    def lookup_result(self, cls: type[T]) -> Result[T]:
        """
        Find a result corresponding to a given class.

        Equivalent to calling Lookup.Template but slightly more convenient.
        Subclasses may override this method to produce the same semantics more efficiently.

        :param cls: Class or type of the objects we are searching for.
        :return: A live object representing instances of that type.
        """
        raise NotImplementedError  # pragma: no cover

    def lookup_item(self, cls: type[T]) -> Item[T] | None:
        """
        Look up the first item matching a given class.

        Includes not only the instance but other associated information.

        :param cls: Class or type of the objects we are searching for.
        :return: A matching item or None.
        """
        result = self.lookup_result(cls)
        it = iter(result.all_items())
        return next(it, None)

    def lookup_all(self, cls: type[T]) -> Sequence[T]:
        """
        Find all instances corresponding to a given class.

        Equivalent to calling lookup_result().all_instances(), but slightly more convenient.
        Subclasses may override this method to produce the same semantics more efficiently.

        > for service in Lookup.get_default().lookup_all(type(MyService)):
        >     service.use_me()

        :param cls: Class or type of the objects we are searching for.
        :return: All currently available instances of that type.
        """
        return self.lookup_result(cls).all_instances()


class Item(Generic[T], ABC):
    """
    A single item in a lookup result.

    This wrapper provides unified access to not just the instance, but its class, a possible
    persistent identifier, and so on.
    """

    @abstractmethod
    def get_display_name(self) -> str:
        """
        Get a human presentable name for the item.

        This might be used when summarizing all the items found in a lookup result
        in some part of a GUI.

        :return: The string suitable for presenting the object to a user.
        """
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def get_id(self) -> str:
        """
        Get a persistent identifier for the item.

        This identifier should uniquely represent the item within its containing lookup (and if
        possible within the global lookup as a whole). For example, it might represent the source of
        the instance as a file name. The ID may be persisted and in a later session used to find the
        same instance as was encountered earlier, by means of passing it into a lookup template.

        :return: A string ID of the item.
        """
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def get_instance(self) -> T | None:
        """
        Get the instance itself.

        :return: The instance or None if the instance cannot be created.
        """
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def get_type(self) -> type[T]:
        """
        Get the implementing class of the instance.

        :return: The class of the item.
        """
        raise NotImplementedError  # pragma: no cover

    @override
    def __str__(self) -> str:
        """Show ID for debugging."""
        return self.get_id()


class Result(Generic[T], ABC):
    """
    Result of a lookup request.

    Allows access to all matching instances at once.
    Also permits listening to changes in the result.
    Result can contain duplicate items.
    """

    listeners: Listeners[Callable[[Result[T]], Any]]
    """
    Observable on which you can register listeners for possible changes in this result.

    Remember to keep a strong reference to the Result object you are attaching the listener to.
    """

    @abstractmethod
    def all_classes(self) -> Set[type[T]]:
        """
        Get all classes represented in the result.

        That is, the set of concrete classes used by instances present in the result.
        All duplicate classes will be omitted.

        :return: Immutable set of class objects.
        """
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def all_instances(self) -> Sequence[T]:
        """
        Get all instances in the result.

        :return: Immutable sequence of all instances.
        """
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def all_items(self) -> Sequence[Item[T]]:
        """
        Get all registered items.

        This should include all pairs of instances together with their classes, IDs, and so on.

        :return: Immutable sequence of Item.
        """
        raise NotImplementedError  # pragma: no cover


class LookupProvider(ABC):
    """
    Classes implementing interface lookup.Provider are capable of
    and willing to provide a lookup (usually bound to the object).
    """

    @abstractmethod
    def get_lookup(self) -> Lookup:
        """
        Returns lookup associated with the object.

        :return: Fully initialized lookup instance provided by this object
        """
        raise NotImplementedError  # pragma: no cover
