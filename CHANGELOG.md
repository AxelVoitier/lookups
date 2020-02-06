CHANGELOG
=========

0.2.0 - 06 February 2020
--------------------

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
