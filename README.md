[![PyPI version shields.io](https://img.shields.io/pypi/v/lookups?style=for-the-badge)](https://pypi.python.org/pypi/lookups)
[![PyPI download shields.io](https://img.shields.io/pypi/dm/lookups?style=for-the-badge)](https://pypi.python.org/pypi/lookups)
[![PyPI Python version shields.io](https://img.shields.io/pypi/pyversions/lookups?style=for-the-badge)](https://pypi.python.org/pypi/lookups)
[![GitHub license shields.io](https://img.shields.io/github/license/AxelVoitier/lookups?style=for-the-badge)](https://github.com/AxelVoitier/lookups/blob/master/LICENSE)

[![GitHub commits since shields.io](https://img.shields.io/github/commits-since/AxelVoitier/lookups/0.1.0?style=for-the-badge)](https://github.com/AxelVoitier/lookups/commits/master)
[![GitHub build shields.io](https://img.shields.io/github/workflow/status/AxelVoitier/lookups/Python%20package?style=for-the-badge)](https://github.com/AxelVoitier/lookups/actions)
[![Codecov shields.io](https://img.shields.io/codecov/c/gh/AxelVoitier/lookups?style=for-the-badge)](https://codecov.io/gh/AxelVoitier/lookups)

# lookups - Find object instances

[DCI](https://en.wikipedia.org/wiki/Data,_context_and_interaction) lookups for Python (inspired by Netbeans Platform [Lookups API](http://wiki.netbeans.org/DevFaqLookup))

## Principle

A lookup is like a dict where you can store object instances as values. And the search keys are their type classes.

Simply.

But `lookups` implements a bit more than that:
* You can also lookup by parent class and not just the most subclasses of an instance.
* You can get hold of a `lookups.Result`, which allows you to register a listener for a given class search. You will be notified when an instance of that class is added/removed from the lookup.
* Deferred instanciation with `lookups.Convertor`. That is, an 'instance' can appear in a lookup but not be instanciated until it is actually used (ie. looked up). Useful for heavy objects or plugins.
* `lookups.Item` can provide you with additional info on an instance: display string, persistence ID string, type, and instance itself.

## `lookups.GenericLookup`

This is the most basic but versatile and dynamic lookup. (HINT: For Java folks, it corresponds to your AbstractLookup ;-) ).

It comes in two main parts:
- `lookups.InstanceContent` provide write-access to the lookup: add/set/remove instances.
- `lookups.GenericLookup` provide read-access to search in the lookup.

```python
from lookups import InstanceContent, GenericLookup

my_content = InstanceContent()
my_lookup = GenericLookup(my_content)

# Adds some objects
class ParentClass:
    pass

class ChildClass(ParentClass):
    pass

parent = ParentClass()
my_content.add(parent)
child1 = ChildClass()
my_content.add(child1)
child2 = ChildClass()
my_content.add(child2)

...

# lookup(cls): get first matching instance
# a_match will be any of parent, child1 or child2
a_parent_match = my_lookup.lookup(ParentClass)

# lookup_all(cls): get all matching instances
# all_parent_matches is an immutable sequence
#     of parent, child1 and child2
all_parent_matches = my_lookup.lookup_all(ParentClass)
# all_children_matches is an immutable sequence
#     of child1 and child2
all_children_matches = my_lookup.lookup_all(ChildClass)

# lookup_result(cls): get a Result object for the searched class
parent_result = my_lookup.lookup_result(ParentClass)
# all_instances(): all instances corresponding to the searched
#     class (ie. similar to plain lookup_all())
parent_result.all_instances()
# all_classes(): Immutable set of all types in the result.
#     Here it would be set(ParentClass, ChildClass)
parent_result.all_classes()

# Lookup result listener
def call_me_back(result):
    print('Result changed. Instances are now', result.all_instances())

parent_result.add_lookup_listener(call_me_back)

...

my_content.remove(child1)
# -> This will invoke call_me_back()
# You can also provide a `concurrent.futures.Executor` when
# creating the content to control how the listeners are called:
#     InstanceContent(notify_in: Executor = None).
```

## Other lookups

* `lookups.fixed`: Simple unmodifiable lookup. Content is set at creation time.
* `lookups.singleton`: Unmodifiable lookup that contains just one fixed object.
* `lookups.EmptyLookup`: A lookup containing nothing.
