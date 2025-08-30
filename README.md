[![PyPI version shields.io](https://img.shields.io/pypi/v/lookups?style=for-the-badge)](https://pypi.python.org/pypi/lookups)
[![PyPI download shields.io](https://img.shields.io/pypi/dm/lookups?style=for-the-badge)](https://pypi.python.org/pypi/lookups)
[![PyPI Python version shields.io](https://img.shields.io/pypi/pyversions/lookups?style=for-the-badge)](https://pypi.python.org/pypi/lookups)
[![GitHub license shields.io](https://img.shields.io/github/license/AxelVoitier/lookups?style=for-the-badge)](https://github.com/AxelVoitier/lookups/blob/master/LICENSE)

[![GitHub commits since shields.io](https://img.shields.io/github/commits-since/AxelVoitier/lookups/0.3.0?style=for-the-badge)](https://github.com/AxelVoitier/lookups/commits/master)
[![GitHub build shields.io](https://img.shields.io/github/workflow/status/AxelVoitier/lookups/Python%20package?style=for-the-badge)](https://github.com/AxelVoitier/lookups/actions)
[![Codecov shields.io](https://img.shields.io/codecov/c/gh/AxelVoitier/lookups?style=for-the-badge)](https://codecov.io/gh/AxelVoitier/lookups)

# lookups - Find object instances

[DCI](https://en.wikipedia.org/wiki/Data,_context_and_interaction) context lookups for Python (inspired by Netbeans Platform [Lookups API](https://netbeans.apache.org/wiki/main/netbeansdevelopperfaq/DevFaqLookup/))

## Principle

A lookup is like a mapping where you can store object instances as values. And the search keys are their type classes.

Simply.

But `lookups` implements a bit more than that:
* You can also lookup by parent class and not just the most subclasses of an instance.
* You can get hold of a `lookups.Result`, which allows you to register a listener for a given class search. You will be notified when an instance of that class is added/removed from the lookup.
* Deferred instantiation with `lookups.Convertor`. That is, an 'instance' can appear in a lookup but not be instantiated until it is actually used (ie. looked up). Useful for heavy objects or plugins.
* `lookups.Item` can provide you with additional info on an instance: display string, persistence ID string, type, and instance itself.

## Relations to DCI paradigm

In DCI a Context selects objects to play its Role at runtime. It is described as being comprised of a mapping from Role to Data objects, and Context objects are supposed to know how to find Data objects based on certain Roles. It also says that Context regards objects only in terms of their identities and the interfaces they provide. Their actual construction is irrelevant.

Lookup is *one* pattern to assist Context in their "know how to find" responsibility.

DCI also states a Role method creates an ephemeral extension of object functionality while it is needed at runtime. Earlier descriptions of DCI were speaking about binding, and method injection. However, we postulate that there not necessarily be a need for this temporary extension. Or at least that one does not necessarily have to resort to complex dynamic manipulations of object types to achieve this conceptual effect of temporarily binding a Role onto an object. And rather that the concept of temporary object extension, a form of dynamic polymorphism, can be spiritually met by using an intermediary object that *presents* the various Roles an object can have at certain times, and under certain conditions.
(Later descriptions of DCI did indeed relaxed that binding notion to something akin to "a select operation in database terms", with "the Context as a whole [...] seen as a kind of external view on the Data.". Though, the same document gave a glimpse on a reason for injection: being sure that the intended Role method are not overridden by the base class or something else. Ie. Role methods should have priority at the time they are needed.)

We topple the extension interpretation and consider that Data objects may already have the Roles (dynamically, or simply by inheritance). But most importantly that the Context, instead of finding objects to *then* binds Roles onto it, would instead search for objects *by* the Roles it needs. And that the actual binding and unbinding of potential Roles on objects can be done by other parts of a System. But only at times and in conditions that presently and contextually make sense for a particular System Use Case (eg. as the outcome of another Interaction, or by any other system action, or external force). These Roles are exposed on a particular interface that a Context can use (or Observe) for its searching.

Here, this particular interface for exposing Roles is nothing else than types mapping to instances. That is what Lookups embody. Regardless if the types are abstract or concrete actually.

Note also that when DCI says a context has to "find" objects, it is in itself not specific about how it does it. It may have pre-knowledge of the instances. Or it may instantiate them on the spot. Or they may be contextually provided by a higher level Controller (ie. in a MVC paradigm), themselves coming from an Interaction with a View. Or it may have access to a pool of instances, and maybe have some additional filtering logic to select the right ones.

Here with Lookups, we define (or restrict) that act of finding to a search by a type. And it becomes the responsibility of the Lookup owner to choose which Role types to exposes, with which instances, and when. Instead of the Context (or a higher level Controller) having to somehow decide it.

In practice a Lookup owner can be any part of a System. It can be a Controller that knows about the current user Interaction, a View that knows about what it shows to user, or a Data object that knows what are its current capabilities. Or anything else that can provide a particular *source of context*. Lookups externalise the assignment of Roles out of Context objects. Context is then only bothered in putting things together for its particular Use Case.

Or said differently, Data objects are what-objects-are, Lookups are what-objects-can, Roles are what-objects-do. And Contexts pick and orchestrate the can-dos.

A side effect of the Context having to search for instances is that it is one way to solve dependency injection. The instance may be a long-lived one, or on the contrary created on the spot. It does not matter to the Context, as Lookups decouple the Data object lifecycle from its uses. No need for spaghetti code of propagating instances. And by searching by type, the responsibilities can be split. You can have neat API+SPI separation of concerns. Very fitting for modular applications.

The Lookup pattern does impose some conceptual restrictions (doing search by type, and having the contextual mapping of Role to objects external to the Context itself). If those restrictions does not fit your particular use case (eg. you are better off passing those instances to the Context as parameters directly), then Lookups will not be the answer. Maybe have a look at the [Roles package](https://pypi.org/project/roles/) for instance?

The rest of what this package propose is just bonus to implement complex and modular DCI systems:
- Lookup Result objects are like virtual key-values (or role-objects) entries. They allow you to get more informations on the matched instances. They can even exists before any matching instance appears in the lookup. And more importantly, you can Observe them, such as being notified when the list of matching instances change.
- Lookup Convertor interface allows for on-demand/lazy instantiations of Data objects.
- Proxy lookups or delegated lookups allow for easier swapping in and out of exposed Roles. Or building bigger contextual Lookups to search into (which is a pathway to Nested Context).
- The default lookup is for an easy access to a global source of context.
- Entry point lookup is for modular customisation of contexts (think plugins exposing Roles to Context that are not even aware plugins can exists).
- Fixed lookups are for simple static situations where it needs to be consistent with the rest of a system using Lookups.

## `lookups.GenericLookup`

This is the most basic but versatile and dynamic lookup.

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

parent_result.listeners += call_me_back

...

my_content.remove(child1)
# -> This will invoke call_me_back()
# You can also provide a `concurrent.futures.Executor` when
# creating the content to control how the listeners are called:
#     InstanceContent(notify_in: Executor = None).
```

## Other lookups

* `lookups.Lookup.get_default()`: The default lookup in a system.
* `lookups.ProxyLookup`: A lookup that merge results from several lookups.
* `lookups.DelegatedLookup`: A lookup that redirects to another (dynamic) lookup, through a LookupProvider.
* `lookups.EntryPointLookup`: A lookup loading its instances from a setuptools entry point group (ie. provided by any installed package).
* `lookups.fixed`: Simple unmodifiable lookup. Content is set at creation time. Will be one of:
    * `lookup.SimpleLookup`: A basic lookup with a static content.
    * `lookups.singleton`: Unmodifiable lookup that contains just one fixed object.
    * `lookups.EmptyLookup`: A lookup containing nothing.
