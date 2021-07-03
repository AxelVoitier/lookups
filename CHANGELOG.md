CHANGELOG
=========

0.3.0 - XX XXXXXXXX 2021
------------------------

- Adds a EntryPointLookup.
- Adds a DelegatedLookup.
- Adds a ProxyLookup.
- Adds a proper resolution for system default lookup Lookup.get_default().
- Fixes issue with listeners registration disappearing immediately when using object-bound methods.
- Content of a GenericLookup can now behave like a Container (ie. you can do things like "obj in content").
- When an instance is not hashable, provides an alternative using id() of the object in order to be
  able to store it in a hash-based storage (set, dictionary).
- New syntactic sugar: call directly a lookup object as shortcut for the lookup method. Ie.,
  instead of writing "lookup.lookup(...)" you can now write "lookup(...)".
- Missing declared dependency in typing_extensions.
- Abstract methods now raise NotImplementedError

0.2.0 - 06 February 2020
------------------------

- Provides GenericLookup and InstanceContent, based on SetStorage. These are the first dynamic
  lookups. They are based on Netbeans' AbstractLookup, InstanceContent and ArrayStorage.
- Lookup listeners are just simple callables now.
- Follows PEP 561 for packages providing typing information.
- Improved quality assurance process (using Github Workflow as CI).
- First (proto-)documentation.

0.1.0 - 18 May 2019
-------------------

- Initial dump of code.
- Defines the public API for lookups.
- Provides fixed lookup: members are defined at instantiation time and never change.
- Provides singleton lookup: only one member defined at instantiation time and never change.
- Provides empty lookup: a special lookup with nothing in it.
