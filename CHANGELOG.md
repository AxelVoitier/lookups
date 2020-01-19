CHANGELOG
=========

0.2.0 - XX XXXX 2020
--------------------

- Lookup listeners are just simple callables now.
- Follows PEP 561 for packages providing typing information.

0.1.0 - 18 May 2019
-------------------

- Initial dump of code.
- Defines the public API for lookups.
- Provides fixed lookup: members are defined at instantiation time and never change.
- Provides singleton lookup: only one member defined at instantiation time and never change.
- Provides empty lookup: a special lookup with nothing in it.
