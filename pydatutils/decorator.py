#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
.. _decorator

Module implementing miscellaneous decorators for methods and classes that can
also be activated at runtime.

**Dependencies**

*require*:      :mod:`functools`, :mod:`inspect`, :mod:`six`

*optional*:     :mod:`wrapt`

**Contents**
"""

# *credits*:      `gjacopo <gjacopo@ec.europa.eu>`_
# *since*:        Sat May  9 17:47:16 2020

#%% Settings

from functools import wraps
from warnings import warn
from inspect import getmro, isclass
from six import with_metaclass, add_metaclass

try:
    assert False
    import wrapt
except:
    _is_wrapt_imported = False
    #warn('Module wrapt not imported; see https://github.com/GrahamDumpleton/wrapt')
    method_wrapper = wraps
else:
    _is_wrapt_imported = True
    def _enabled_decorators():
        return True
    @wrapt.decorator(enabled=_enabled_decorators)
    def method_wrapper(wrapped, instance, _args, _kwargs):
        return wrapped(*_args, **_kwargs)


#%% Core functions/classes

#==============================================================================
# Function metaclass_maker
#==============================================================================

def metaclass_maker(left_metas=(), right_metas=()):
    """Deal with metaclass conflict, i.e. when "the metaclass of a derived class
    must be a (non-strict) subclass of the metaclasses of all its bases"

        >>> metaclass = metaclass_maker(left_metas=(), right_metas=())

    Arguments
    ---------
    left_metas,right_metas : class
        classes (not strings) representing the metaclasses to 'merge'; note that
        :data:`left_metas` has priority over :data:`right_metas`.

    Note
    ----
    The simplest case where a metatype conflict happens is the following.
    Consider a class :class:`A` with metaclass :class:`M_A` and a class :class:`B`
    with an independent metaclass :class:`M_B`; suppose we derive :class:`C` from
    :class:`A` and :class:`B`.
    The question is: what is the metaclass of :class:`C` ? Is it :class:`M_A` or
    :class:`M_B` ?
    The correct answer is :class:`M_C`, where :class:`M_C` is a metaclass that
    inherits from :class:`M_A` and :class:`M_B`, as in the following graph:

       "M_A" -> "A"
       "M_B" -> "B"
       "A" -> "C"
       "B" -> "C"
       "M_A" -> "M_C"
       "M_B" -> "M_C"
       "M_C" -> "C"
    """
    def skip_redundant(iterable, skipset=None):
        # redundant items are repeated items or items in the original skipset
        if skipset is None: skipset = set()
        for item in iterable:
            if item not in skipset:
                skipset.add(item)
                yield item
    def remove_redundant(metaclasses):
        skipset = set([type]) # object
        for meta in metaclasses: # determines the metaclasses to be skipped
            skipset.update(getmro(meta)[1:])
        return tuple(skip_redundant(metaclasses, skipset))
        # now the core of the function: two mutually recursive functions ##
    memoized_metaclasses_map = {}
    def get_noconflict_metaclass(bases, left_metas, right_metas):
         # make tuple of needed metaclasses in specified priority order
         metas = left_metas + tuple(map(type, bases)) + right_metas
         needed_metas = remove_redundant(metas)
         # return existing confict-solving meta, if any
         if needed_metas in memoized_metaclasses_map:
           return memoized_metaclasses_map[needed_metas]
         # nope: compute, memoize and return needed conflict-solving meta
         elif not needed_metas:         # wee, a trivial case, happy us
             meta = type
         elif len(needed_metas) == 1: # another trivial case
            meta = needed_metas[0]
         # check for recursion, can happen i.e. for Zope ExtensionClasses
         elif needed_metas == bases:
             raise TypeError("Incompatible root metatypes", needed_metas)
         else: # gotta work ...
             metaname = '_' + ''.join([m.__name__ for m in needed_metas])
             meta = classmaker()(metaname, needed_metas, {})
         memoized_metaclasses_map[needed_metas] = meta
         return meta
    def classmaker(left_metas=(), right_metas=()):
        class make_class(type):
            def __new__(meta, name, bases, attrs):
                metaclass = get_noconflict_metaclass(bases, left_metas, right_metas)
                return metaclass(name, bases, attrs)
            #def make_class(name, bases, adict):
            #    metaclass = get_noconflict_metaclass(bases, left_metas, right_metas)
            #    return metaclass(name, bases, adict)
        make_class.__name__ = '__metaclass__'
        return make_class
    return classmaker(left_metas, right_metas)


#==============================================================================
# Function class_decorator
#==============================================================================

def class_decorator(func_decorator, *members, **kwargs):
    """Functional decorator of classes that automatically decorates a family of
    methods within a class.

        >>> new_cls = class_decorator(func_decorator, *members, **kwargs)(cls)

    Arguments
    ---------
    func_decorator : callable
        universal or specific function/class decorator used to decorate methods
        and subclasses of the class :data:`cls`\ .
    members : str, list of str
        list of methods or classes to be decorated in the new class :data:`new_cls`;
        if :literal:`None` or :literal:`()`, all instance/static/class methods as
        well as all classes of :data:`cls` are decorated in :data:`new_cls`, excepted
        those whose names are in :data:`excludes` (if any, see below).

    Keyword Arguments
    -----------------
    exclude_member : str[list]
        list of methods or classes to further exclude from the list of decorated
        ones in the new class :data:`new_cls`\ . it defaults to all "magic" objects
        or attributes that live in user-controlled namespaces (_i.e._ those starting
        and ending with underscores \_\_). Any member in :literal:`exclude_member`
        is added to this list.
    special_member : str[list]
        list of special methods or classes to include; this can be used to override
        all the members excluded by default in :literal:`exclude_member`.
    base_class : str, bool
        variable conveying the name of a parent (base) class of the input decorated
        class :data:`cls` whose attributes will be further decorated; set to
        :literal:`True` to select all parent base classes (_i.e._ all those in
        :data:`cls.__bases__`) and :literal:`False` when the parent class should
        be ignored.

    Returns
    -------
    new_cls : class
        class inherited from :data:`new_cls` where methods and classes whose names
        match :data:`attr_names` (all if :data:`()`) are decorated using the decorator
        :data:`method_decorator`.

    Examples
    --------
    Let's create a method decorator that increments the output of a function on integer:

        >>> increment = lambda x: x+1
        >>> increment(1)
            2
        >>> def decorator_increment(func):
        ...     def decorator(*args, **kwargs):
        ...         return increment(func(*args, **kwargs))
        ...     return decorator

    Let's consider a class with two methods:

        >>> class A(object):
        ...     def increment_twice(self,x):
        ...          return increment(increment(x))
        ...     def multiply_by_2(self, x):
        ...          return 2*x
        >>> a = A()
        >>> a.increment_twice(1)
            3
        >>> a.multiply_by_2(1)
            2

    Let's implement different inherited classes using the class decorator:

        >>> @class_decorator(decorator_increment)
        ... class B(A): # all methods of this class are decorated
        ...     pass
        >>> @class_decorator(decorator_increment, 'multiply_by_2')
        ... class C(A): # only multiply_by_2 method is decorated
        ...     pass

    and test it :

        >>> b = B(); c = C()
        >>> b.increment_twice(1) # decorated with one more call to increment
            4
        >>> c.increment_twice(1) # not decorated
            3
        >>> b.multiply_by_2(1)
            3
        >>> c.multiply_by_2(1) # also decorated
            3

    You can also use it to decorate "callable" classes:

        >>> @class_decorator(decorator_increment, special_member=['__call__'])
        ... class increment_once():
        ...     def __init__(self,x):
        ...         self.x = x
        ...     def __call__(self):
        ...         return increment(self.x)
        >>> increment_once(1)()
            3

    Note in cases like the one above (callable classes, _i.e._ classes with a
    :meth:`__call__` method), it is necessary to add the :meth:`__call__` to the
    list of "special members" (see also note below).

    Note
    ----
    When decorating a magic method of a class (_i.e._ a class starting with \_\_
    and also ending with \_\_), the name of the method needs to be parsed as a
    special member, _i.e._ an item of the :literal:`special_member` keyword list
    argument.

    See also
    --------
    :meth:`method_decorator`, :meth:`metaclass_decorator`, :meth:`generic_decorator`.
    """
    if func_decorator is None:
        return lambda x: x
    # members to exclude
    exclude_members = kwargs.pop('exclude_member',[])
    try:
        assert exclude_members == [] or Type.is_string(exclude_members)  \
            or (Type.is_sequence(exclude_members) and all([Type.is_string(e) for e in exclude_members]))
    except AssertionError:
        raise TypeError("Wrong type for EXCLUDE_MEMBER - must be (list of) method/attribute name(s)")
    else:
        if Type.is_string(exclude_members):
            exclude_members = [exclude_members,]
    exclude_members.extend(['__metaclass__','__module__', '__qualname__',
                            '__weakref__','__dict__','__class__','__doc__'])
    # run a first filtering
    members = list(set(members) - set(exclude_members))
    # members to include
    special_members = kwargs.pop('special_member', [])
    try:
        assert special_members == [] or Type.is_string(special_members)  \
            or (Type.is_sequence(special_members) and all([Type.is_string(s) for s in special_members]))
    except AssertionError:
        raise TypeError("Wrong type for SPECIAL_MEMBER - must be (list of) method/attribute name(s)")
    else:
        if Type.is_string(special_members) :
            special_members = [special_members,]
    # base members to include
    base_classes = kwargs.pop('base_class', True)
    try:
        assert isinstance(base_classes,bool) or Type.is_string(base_classes) \
            or (Type.is_sequence(base_classes) and all([Type.is_string(b) for b in base_classes]))
    except AssertionError:
        raise TypeError("Wrong type for BASE_CLASS - must be a boolean or (list of) base class name(s)")
    else:
        #if base_classes is True:
        #    base_classes = 'Base'
        if base_classes is False:
            base_classes = []
        elif Type.is_string(base_classes) :
            base_classes = [base_classes,]
    # prepare/redefine the decorating method
    ## _new_decorator = method_decorator(func_decorator, *func_names, **func_exclude)
    def _new_decorator(decorated, name):
        # we use method_wrapper = functools.wraps (or a variant of it) to preserve
        # doc and name...
        try:
            return method_wrapper(decorated)(func_decorator(decorated, name))
        except TypeError:
            return method_wrapper(decorated)(func_decorator(decorated))
    def _optional_decorator(decorated, name):
        if (members in ((), [], (None,), None) or name in members or name in special_members)   \
                and name not in exclude_members:
            return _new_decorator(decorated, name)
        return decorated # no change
    # the class rebuilder
    def _class_rebuilder(_cls):
        try:
            assert isclass(_cls)
        except AssertionError:
            raise TypeError("Wrong type for decorated object - must be a class")
        try:
            meta_cls = _cls.__metaclass__
        except:
            meta_cls = type
        class metaclass_decorator(meta_cls):
            # __members = members
            __special_members = special_members
            __base_classes = base_classes
            def __new__(meta, name, bases, attrs):
                members, special_members = meta.__members, meta.__special_members
                base_classes = meta.__base_classes # ??? doesn't work without
                # name = _cls.__name__
                bases = _cls.__bases__
                # attrs = _cls.__dict__
                attrs.update(_cls.__dict__)
                if base_classes is True:
                    base_classes = _cls.__bases__
                for base in base_classes: # loop over parent classes
                    try:
                        [attrs.update({attr: obj}) for (attr, obj) in base.__dict__.items()
                           if not attr in attrs.keys()]
                    except:
                        continue
                # if not base_classes is False:
                #     [attrs.update({attr: obj}) for base in base_classes for (attr,obj) in base.__dict__.items()
                #        if not attr in attrs.keys()]
                for attr, obj in attrs.items(): # variant of vars(meta).items()
                    if (attr.startswith('__') and attr.endswith('__') and attr not in special_members)  \
                            or attr in exclude_members:
                        continue
                    try:
                        new_attr = _optional_decorator(obj, attr)
                    except: pass
                    else:
                        attrs[attr] = new_attr
                return meta_cls.__new__(meta, name, bases, attrs)
        if _cls.__name__ == '__metaclass__':
            class new_cls(_cls):
                # we deal with the super class of _cls
                def __getattribute__(self, attr): # __getattribute__ is run for every attribute
                    try:
                        obj = super(new_cls, self).__getattribute__(attr)
                    except: pass # raise IOError("Wrong attribute name %s" % attr)
                    else:
                        return _new_decorator(obj, attr)
        elif True:
            class new_cls(with_metaclass(metaclass_decorator, _cls)):
                pass
        else: # in case we want to use metaclass_maker at some point...
            class new_cls(with_metaclass(metaclass_maker(right_metas=(metaclass_decorator,)),
                                        _cls)):
                pass
        try:
            new_cls.__module__ = _cls.__module__
        except: pass
        try:
            new_cls.__name__ = _cls.__name__
        except: pass
        else:
            return new_cls
    return _class_rebuilder


#==============================================================================
# Class MethodDecorator
#==============================================================================

class MethodDecorator():
    """Basic method decorator that knows the class the decorated method is bound to.

        >>> class NewDecorator(MethodDecorator):
        ...     def __call__(self, *args, **kwargs):

    Note
    ----
    The new implemented class :meth:`NewDecorator`:

        - knows the class the decorated method is bound to.
        - hides decorator traces by answering to system attributes more correctly
          than another decorator class like :meth:`functools.wraps` does.
        - deals with bound and unbound instance methods, class methods, static
          methods, and plain functions (likewise the original method decorator
          method) as well as properties.
        ...         # override decoration

    See also
    --------
    :class:`method_decorator`, :meth:`class_decorator`, :meth:`generic_decorator`.
    """

    #/************************************************************************/
    def __init__(self, func, obj=None, cls=None, method_type=None, **kwargs):
        try:
            # assert func.__class__ in ('function', 'method', 'property'))
            assert isinstance(func, (staticmethod, classmethod, property)) or callable(func)
        except AssertionError:
            raise TypeError("Wrong type for decorated object - must be a callable (function/method)")
        # these defaults are OK for plain functions  and will be changed by
        # __get__() for methods once a method is dot-referenced
        self.func, self.obj, self.cls = func, obj, cls
        try:
            self.method_type = method_type or self.method_type
        except:
            self.method_type = method_type

    #/************************************************************************/
    def __repr__(self):  # special case: __repr__ ignores __getattribute__
        return self.func.__repr__()

    #/************************************************************************/
    #def __get__(self, obj, objtype):
    #    # support instance methods
    #    return functools.partial(self.__call__, obj)
    def __get__(self, obj=None, cls=None):
        if self.obj == obj and self.cls == cls:
            return self
        method_type = self.method_type =    \
            self.method_type or self.func.__class__.__name__
            # self.method_type or (
            #     'staticmethod' if isinstance(self.func, staticmethod) else
            #     'classmethod' if isinstance(self.func, classmethod) else
            #     'property' if isinstance(self.func, property) else
            #     'function'
            #     )
        if method_type=='property' and obj is not None:
            return self.func.__get__(obj, cls)
        else:
            return object.__getattribute__(self, '__class__')(
                self.func.__get__(obj, cls), obj, cls, method_type)

    #/************************************************************************/
    def __getattribute__(self, attr_name):
        # known names
        if attr_name in ('__init__', '__get__', '__call__', '__getattribute__',
                         'func', 'obj', 'cls', 'method_type'):
            return object.__getattribute__(self, attr_name) # stopping recursion.
        # '__class__' is not included because is used only with explicit object.__getattribute__
        # all other attr_names, including auto-defined by system in self, are searched
        # in decorated self.func, e.g.: __module__, __class__, __name__, __doc__, im_*,
        # func_*, etc.
        try:
            # func = object.__getattribute__(self, 'func')
            return getattr(self.func, attr_name)
        except:
            # raises correct AttributeError if name is not found in decorated self.func
            pass # stop recursion
            try:
                return object.__getattribute__(self, attr_name)
            except:
                pass

    #/************************************************************************/
    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)


#==============================================================================
# Function method_decorator
#==============================================================================

def method_decorator(func_decorator=None, *methods, **kwargs):
    """Generic functional decorator used to automatically decorate methods.

        >>> def some_decorator(method):
        ...     # do decoration
        >>> @method_decorator(some_decorator)
        ... def decorated_function():
        ...     # original function

    Examples
    --------
    We use the following "increment" decorator (see also :meth:`class_decorator`):

        >>> increment = lambda x: x+1
        >>> def decorator_increment(func):
        ...     def decorator(*args, **kwargs):
        ...         return increment(func(*args, **kwargs))
        ...     return decorator

    and use it to decorate different types of methods (static methods, class methods
    or even properties):

        >>> class A:
        ...     _value = 10
        ...
        ...     @method_decorator(decorator_increment)
        ...     @staticmethod
        ...     def increment_twice(x):
        ...         return increment(increment(x))
        ...
        ...     @method_decorator(decorator_increment)
        ...     @classmethod
        ...     def multiply_by_2(cls, x):
        ...         return 2*x
        ...
        ...     @method_decorator(decorator_increment)
        ...     @property
        ...     def value(self):
        ...         return self._value

    Indeed:

        >>> a = A()
        >>> a.increment_twice(1)
            4
        >>> a.multiply_by_2(1)
            3
        >>> a.value
            11

    while the attributes of the decorated methods are unchanged, for instance:

        >>> A.increment_twice.__class__
            function
        >>> A.multiply_by_2.__class__
            method
        >>> A.value.__class__
            property

    Note
    ----
    Likewise :meth:`NewDecorator`, the new implemented class knows the class the
    decorated method is bound to.

    See also
    --------
    :class:`MethodDecorator`, :meth:`class_decorator`, :meth:`metaclass_decorator`,
    :meth:`generic_decorator`.
    """
    if func_decorator is None:
        # return lambda f: f
        return MethodDecorator
    exclude_methods = kwargs.pop('exclude_method',[])
    try:
        assert exclude_methods == [] or Type.is_string(exclude_methods)  \
            or (Type.is_sequence(exclude_methods) and all([Type.is_string(e) for e in exclude_methods]))
    except AssertionError:
        raise TypeError("Wrong type for EXCLUDE_METHOD - must be (list of) method/attribute name(s)")
    else:
        if Type.is_string(exclude_methods) :
            exclude_methods = [exclude_methods,]
    methods = list(set(methods) - set(exclude_methods))
    try:
        assert _is_wrapt_imported is True
    except:
        # # solution 1 : original MethodDecorator
        # method_rebuilder = MethodDecorator(func_decorator)
        # # solution 2 : MethodDecorator with options
        #def method_rebuilder(func):
        #    if (func_names in ((),(None,)) or func in func_names) and func not in func_exclude:
        #        @MethodDecorator
        #        def new_func(*args, **kwargs):
        #            return func(*args, **kwargs)
        #        return new_func
        #    else:
        #        return func
        # the following method_rebuilder is invoked at run time (through __call__)
        def method_rebuilder(method, *args, **kwargs):
            class _Rebuilder(MethodDecorator):
                def __get__(self, obj=None, cls=None):
                    if self.obj == obj and self.cls == cls:
                        return self
                    method_type = self.method_type = self.method_type or self.func.__class__.__name__
                    if method_type=='property' and obj is not None:
                        return func_decorator(self.func.__get__)(obj, cls)
                    else:
                        return object.__getattribute__(self, '__class__')(
                            self.func.__get__(obj, cls), obj, cls, method_type)
                def __call__(self, *args, **kwargs):
                    if (methods in ((), [], (None,), None) or self.func in methods) and self.func not in exclude_methods:
                        return func_decorator(self.func)(*args, **kwargs)
                    else:
                        return self.func(*args, **kwargs)
            try:
                return method_wrapper(method)(_Rebuilder(method, *args, **kwargs))
            except:
                return _Rebuilder(method, *args, **kwargs)
    else:
        #@wrapt.decorator
        #def _method_rebuilder(wrapped, instance, args, kwargs):
        #    return func_decorator(wrapped(*args, **kwargs))
        _method_rebuilder = func_decorator(method_wrapper)
    return _method_rebuilder


#==============================================================================
# Function generic_decorator
#==============================================================================

def generic_decorator(decorator, *args, **kwargs):
    """Generic functional decorator of methods or class of methods.

        >>> def some_method_decorator(method):
        ...     # do decoration of method
        >>> @generic_decorator(some_method_decorator)
        ... def decorated_function():
        ...     # original function
        >>> @generic_decorator(some_method_decorator)
        ... class DecoratedClass():
        ...     # original class

    Note
    ----
    When a class is decorated with :meth:`generic_decorator`, it is actually
    all the methods within this class which are decorated.

    Example
    -------
    Let's consider the example already used for the decorators :meth:`class_decorator`
    and :meth:`method_decorator`:

        >>> increment = lambda x: x+1
        >>> def decorator_increment(func):
        ...     def decorator(*args, **kwargs):
        ...         return increment(func(*args, **kwargs))
        ...     return decorator

    and use it again to decorate a class with one method:

        >>> @generic_decorator(decorator_increment, 'increment_twice')
        ... class A(object):
        ...     def increment_twice(self,x):
        ...          return increment(increment(x))
        ...     def multiply_by_2(self, x):
        ...          return 2*x

    and a method:

        >>> @generic_decorator(decorator_increment)
        >>> def multiply_by_3(x):
        ...     return 3*x

    Let's test it :

        >>> a = A();
        >>> print(a.increment_twice(1)) # decorated
            4
        >>> print(a.multiply_by_2(1)) # not decorated
            2
        >>> print(exclude_methods(2)) # decorated
            7

    See also
    --------
    :meth:`class_decorator`, :meth:`method_decorator`.
    """
    def wrapper(obj):
        if isclass(obj):
            return class_decorator(decorator, *args, **kwargs) (obj)
        else:
            return method_decorator(decorator, *args, **kwargs) (obj)
    return wrapper


#==============================================================================
# Class MetaclassProxy
#==============================================================================

class MetaclassProxy(type):
    """Decorate the class being created & preserve :literal:`__metaclass__` of
    the parent.

    Note
    ----
    It executes two callbacks: before and after creation of a class, that allows
    to decorate them.

    Between two callbacks, it tries to locate any :literal:`__metaclass__` in the
    parents (sorted in MRO).

    If found (with the help of :literal:`__new__` method) it mutates to the found
    base :literal:`__metaclass__`. If not found, it just instantiates the given
    class.

    See also
    --------
    :meth:`metaclass_decorator`, :meth:`class_decorator`.
    """

    #/************************************************************************/
    def __new__(meta, name, bases, attrs):
        # see http://stackoverflow.com/questions/4651729/metaclass-mixin-or-chaining
        mrobases = meta._mrobases(bases)
        name, bases, attrs = meta.pre_new(name, bases, attrs) # Decorate, pre-creation
        newclass = meta._find_parent_metaclass(mrobases)(name, bases, attrs)
        return meta.post_new(newclass) # Decorate, post-creation

    #/************************************************************************/
    @classmethod
    def pre_new(meta, name, bases, attrs):
        """Decorate a class before creation.

            >>> name, bases, attrs = MetaclassProxy.pre_new(meta, name, bases, attrs)

        Returns
        -------
        Inputs :data:`name`, :data:`bases`, and :data:`attrs` are output.
        """
        return (name, bases, attrs)

    #/************************************************************************/
    @classmethod
    def post_new(meta, newclass):
        """Decorate a class after creation.

            >>> newclass = MetaclassProxy.post_new(meta, newclass)

        Returns
        -------
        Input :data:`newclass` is output.
        """
        return newclass

    #/************************************************************************/
    @classmethod
    def _mrobases(meta, bases):
        """Expand tuple of base-classes `bases` in MRO.

            >>> mrobases = MetaclassProxy._mrobases(meta, bases)

        Returns
        -------
        All MROs of base classes listed in :data:`bases`.
        """
        mrobases = []
        for base in bases:
            if base is not None: # We don't like `None` :)
                mrobases.extend(base.mro())
        return mrobases

    #/************************************************************************/
    @classmethod
    def _find_parent_metaclass(meta, mrobases):
        """Find any __metaclass__ callable in ``mrobases``.

            >>> fun = MetaclassProxy._find_parent_metaclass(meta, mrobases)

        Returns
        -------
        A metaclass constructor.
        """
        for base in mrobases:
            if hasattr(base, '__metaclass__'):
                metacls = base.__metaclass__
                if metacls and not issubclass(metacls, meta): # don't call self again
                    return metacls#(name, bases, attrs)
        # Not found: use `type`
        return lambda name, bases, attrs: type.__new__(type, name, bases, attrs)


#==============================================================================
# Function metaclass_decorator
#==============================================================================

def metaclass_decorator(method_decorator, *methods):
    """Metaclass decorator used to automatically decorate the `metaclass` attribute
    of a class.

        >>> new_cls = metaclass_decorator(method_decorator, *methods)(cls)

    Note
    ----
    Note that when the class :data:`cls` is inherited from another one, say :data:`super_cls`,
    all methods :data:`cls` that are inherited from :data:`super_cls` (and not overriden or
    specific to the class) are decorated in the new class :data:`new_cls`.

    See also
    --------
    :class:`MetaclassProxy`, :meth:`method_decorator`, :meth:`class_decorator`.
    """
    # see http://python-3-patterns-idioms-test.readthedocs.org/en/latest/Metaprogramming.html
    #decorator = method_decorator(method_decorator, *methods)
    def _class_rebuilder(_cls):
        #class __metaclass__(type):
        #    def __init__(cls, name, bases, nmspc):
        #        type.__init__(cls, name, bases, nmspc)
        try:
            metaclass = class_decorator(method_decorator, *methods)(MetaclassProxy)
        except:
            warn("Metaclass %s not decorated" % _cls.__name__)
            metaclass = MetaclassProxy
        class new_cls(with_metaclass(metaclass, _cls)):
            pass
        try:
            new_cls.__module__ = _cls.__module__
        except: pass
        try:
            new_cls.__name__ = _cls.__name__ # __metaclass__
        except: pass
        return new_cls
    return _class_rebuilder


#==============================================================================
# Class ActivDecorator
#==============================================================================

class ActivDecorator():
    """Class of activation decorators that can dynamically inhibit (deactivate)
    a decorator at runtime.

    Usage
    -----
    You will will dynamically de/activate a decorator by un/setting the inhibitor
    flag :data:`ignore` parser to the :class:`~Inhibitor`.
    """

    FLAG_IGNORE_DECORATOR = False
    INHIBITOR = 'FLAG_IGNORE_DECORATOR'

    #/************************************************************************/
    @classmethod
    def inhibitor_rule(cls):
        """Boolean inhibitor rule. When set to :literal:`True`, any decorator
        decorated with :class:`~Inhibitor` will be inhibited.

            >>> status = ActivDecorator.inhibitor_rule()

        Returns
        -------
        A boolean flag providing with the state (:literal:`False`: activated or
        :literal:`True`: deactivated) of all decorators further decorated with
        the default :class:`~Inhibitor`.

        Usage
        -----
        This shall be parsed as the :data:`ignore` argument of an inhibitor
        instance of the method decorator :class:`~Inhibitor`.
        """
        try:
            return getattr(cls, cls.INHIBITOR)
        except:
            try:
                return eval(cls.INHIBITOR) # global if it exists
            except:
                try:
                    return cls.FLAG_IGNORE_DECORATOR
                except:
                    return False

    #/************************************************************************/
    @classmethod
    def get_inhibitor(cls):
        """Returns the current (boolean) state of the inhibitor.

            >>> status = ActivDecorator.get_inhibitor()

        Returns
        -------
        Nothing else than :meth:`~inhibitor_rule`.
        """
        return cls.inhibitor_rule()

    #/************************************************************************/
    @classmethod
    def set_inhibitor(cls, flag):
        """Set the (boolean) state of the inhibitor.

            >>> ActivDecorator.set_inhibitor(status)

        Argument
        --------
        state : bool
            Flag used to (re)set the state of all decorators further decorated
            with the default :class:`~Inhibitor`: literal:`False`: for activated
            or :literal:`True`: for deactivated (no decoration).
        """
        try:
            assert isinstance(flag, bool)
        except:
            raise TypeError("Wrong type for inhibitor FLAG")
        try:
            setattr(cls, cls.INHIBITOR, flag)
        except:
            try:
                exec("%s = %s" % (cls.INHIBITOR, flag))
            except:
                try:
                    setattr(cls, FLAG_IGNORE_DECORATOR, flag)
                except:
                    return False

    #/************************************************************************/
    class Inhibitor():
        """Method decorator that can dynamically inhibits a decorator at runtime.

            >>> new_decorator_method = ActivDecorator.Inhibitor(decorator_method, ignore=inhibitor_rule)

        Arguments
        ---------
        decorator_method : callable
            A method decorator.
        ignore : callable
            A callable method returning the state as a boolean flag:: literal:`False`:
            for activated or :literal:`True`: for deactivated (no decoration).

        Returns
        -------
        new_decorator_method : callable
            Same as the input :data:`decorator_method`, but can in addition be
            deactivated at runtime.

        Examples
        --------
        Let's consider again the :meth:`increment` decorator that we decorate with
        the inhibitor:

            >>> increment = lambda x: x+1
            >>> @ActivDecorator.Inhibitor
            ... def decorator_increment(func):
            ...     def decorator(*args, **kwargs):
            ...         return increment(func(*args, **kwargs))
            ...     return decorator

        and use this new (decorated) decorator (which is activated by default)
        to decorate a class of methods:

            >>> @class_decorator(decorator_increment)
            ... class A():
            ...     def increment_twice(self,x):
            ...         return increment(increment(x))
            ...     def multiply_by_2(self, x):
            ...         return 2*x

        and test the decorated methods when activated (default):

            >>> a = A()
            >>> a.increment_twice(1) # decorated with one more call to "increment"
                4
            >>> a.multiply_by_2(1) # decorated
                3

        and deactivated, _i.e._ when the inhibitor is actually activated (set to
        :literal:`True`):

            >>> ActivDecorator.set_inhibitor(True) # deactivate
            >>> a.increment_twice(1)
                3
            >>> a.multiply_by_2(1) # decorated
                2

        Note in particular that we did not need to create a new :class:`A`
        instance.

        See also
        ---------
        :meth:`~inhibitorFactory`, :meth:`class_decorator`\ .
        """
        def __init__(self, decorator, **kwargs):
            try:
                assert callable(decorator)
            except:
                raise TypeError("Wrong type for DECORATOR - must be callable")
            self.decorator = decorator
            ignore = kwargs.pop('ignore', ActivDecorator.inhibitor_rule)
            try:
                assert ignore is None or callable(ignore) or isinstance(ignore,bool)
            except:
                raise TypeError("Wrong type for IGNORE inhibitor")
            if ignore is None or ignore is False:
                ignore = lambda *arg: False
            elif ignore is True:
                # warn("Decorator will be always ignored - it can't be reset at run time")
                ignore = lambda *arg: True
            # lambda's bind to local values, so avoid: lambda *arg: ignore !
            self.ignore = ignore

        def __call__(self, obj):
            if not callable(obj):
                return obj
            # elif self.ignore is not None and self.ignore() is True:
            #     return obj.__call__
            # else:
            #     return self.decorator(obj)
            decorated_obj = self.decorator(obj)
            #@wraps(obj)
            def wrapper(*args, **kwargs):
                if self.ignore() is True:
                    return obj.__call__(*args, **kwargs)
                else:
                    return decorated_obj(*args, **kwargs)
            return wrapper

    #/************************************************************************/
    @classmethod
    def inhibitorFactory(cls, decorator):
        """Build a conditional method decorator that can be inhibited
        at runtime.

            >>> new_decorator_method = inhibitorFactory(decorator_method)
            >>> NewDecoratorClass = inhibitorFactory(DecoratorClass)

        Usage
        -----
        This is used to decorate decorator methods or class of decorator methods
        with dynamic and customised de/activation of these decorators at runtime.

        Examples
        --------
        Let's consider the same decorator as for :class:`~Inhibitor` example,
        but this time using :meth:`~inhibitorFactory` to decorate the decorator:

            >>> increment = lambda x: x+1
            >>> @ActivDecorator.inhibitorFactory
            ... def decorator_increment(func):
            ...     def decorator(*args, **kwargs):
            ...         return increment(func(*args, **kwargs))
            ...     return decorator

        Like in the previous example, we can decorate the entire class:

            >>> @class_decorator(decorator_increment)
            ... class Adummy():
            ...     def increment_twice(self,x):
            ...         return increment(increment(x))
            ...     def multiply_by_2(self, x):
            ...         return 2*x

        but instead we decorate the methods separately, and we also introduce:

            >>> @class_decorator(decorator_increment)
            ... class A():
            ...     @decorator_increment
            ...     def increment_twice(self,x):
            ...         return increment(increment(x))
            ...     @decorator_increment(ignore=True)
            ...     def multiply_by_2(self, x):
            ...         return 2*x

        and test the decorated methods:

            >>> ActivDecorator.set_inhibitor(True) # deactivated
            >>> a = A()
            >>> a.increment_twice(1)
                3
            >>> a.multiply_by_2(1) # actually never decorated
                2
            >>> ActivDecorator.set_inhibitor(False) # reactivate
            >>> a.increment_twice(1)
                4
            >>> a.multiply_by_2(1) # still inhibited/deactivated
                2

        With respect to the :class:`~Inhibitor` class, we can introduce an inhibitor
        rule as a function which is not the default one (:meth:`~inhibitor_rule`),
        hence allowing different rules for different sets of decorators. We proceed
        with decorating "normally" some decorator(s):

            >>> @class_decorator(ActivDecorator.inhibitorFactory)
            ... class Dummy():
            ...     def decorator_increment(func):
            ...         def decorator(*args, **kwargs):
            ...             return increment(func(*args, **kwargs))
            ...         return decorator
            ...     def decorator_increment_twice(func):
            ...         def decorator(*args, **kwargs):
            ...             return increment(increment(func(*args, **kwargs)))
            ...         return decorator

        We can then use these decorators with some customised inhibitors:

            >>> def ignore_decorator():
            ...     return SOME_FLAG
            >>> class B():
            ...     @Dummy.decorator_increment
            ...     def increment_twice(self,x):
            ...         return increment(increment(x))
            ...     @Dummy.decorator_increment_twice(ignore=ignore_decorator)
            ...     def multiply_by_2(self, x):
            ...         return 2*x

        The (non-local) :data:`SOME_FLAG` variable can then be used de/activate
        separately the decorators at runtime:

            >>> b = B()
            >>> SOME_FLAG = False
            >>> b.increment_twice(1) # activated through set_inhibitor
                4
            >>> b.multiply_by_2(1) # activated through ignore_decorator
                4
            >>> SOME_FLAG = True
            >>> b.increment_twice(1) # no change
                4
            >>> b.multiply_by_2(1) # deactivated through ignore_decorator
                2
            >>> ActivDecorator.set_inhibitor(True)
            >>> SOME_FLAG = False
            >>> b.increment_twice(1) # deactivated
                3
            >>> b.multiply_by_2(1) # reactivated
                4

        See also
        ---------
        :class:`~Inhibitor`.
        """
        def new_decorator(obj=None, **kwargs):
            # let's ensure that any derived class also uses its own ihibitor
            if kwargs.get('ignore') is None:
                kwargs.update({'ignore': cls.inhibitor_rule})
            # define the wrapper
            if obj is not None:
                def wrapper(*a, **kw):
                    return cls.Inhibitor(decorator, **kwargs)(obj)(*a, **kw)
            else:
                def wrapper(obj):
                    return cls.Inhibitor(decorator, **kwargs)(obj)
            return wrapper
        return new_decorator


#==============================================================================
# Class CondDecorator
#==============================================================================

class CondDecorator()
    """Base class of function decorators that provide pre-/post-conditions for
    decorated methods.

    Examples
    --------
    Let's just decorate some functions:

        >>> def in_ge20(inval):
        ...     assert inval >= 20
        >>> def out_lt30(retval, inval):
        ...     assert retval < 30
        >>> @CondDecorator.decorator_precondition(in_ge20)
        ... @CondDecorator.decorator_postcondition(out_lt30)
        ... def apply_increment(x):
        ...     return x+1

    Here, :data:`~decorator_precondition(in_ge20)` and :data:`~Conditioning(in_ge20, None)`
    are equivalent. Ibid for :data:`~decorator_postcondition(out_lt30)` and
    :data:`~Conditioning(None, out_lt30)`. Actually, we could  simply write:

        >>> @CondDecorator.Conditioning(in_ge20, out_lt30)
        ... def apply_increment_sim(x):
        ...     return x+1

    Then we simply run:

        >>> print apply_increment(1)
            Traceback (most recent call last):
            ...
            AssertionError
        >>> print apply_increment(29)
            Traceback (most recent call last):
            ...
            AssertionError
        >>> print apply_increment(25)
            26
        >>> print apply_increment_sim(20)
            21
    """

    #/************************************************************************/
    class Conditioning():
        """Class providing pre-/post-conditions as function decorators.

            >>> decorator = CondDecorator.Conditioning(precondition, poscondition)

        See also
        --------
        :meth:`decorator_precondition`, :meth:`decorator_postcondition`
        """
        # see https://wiki.python.org/moin/PythonDecoratorLibrary

        __slots__ = ('_precondition', '_postcondition')

        class wrapper(object):
            def __init__(self, precond, postcond, func):
                self._precond, self._postcond  = precond, postcond
                self._func = func
            def __call__(self, *args, **kwargs):
                if self._precond:
                    self._precond(*args, **kwargs)
                result = self._func(*args, **kwargs)
                if self._postcond :
                    self._postcond(result, *args, **kwargs)
                return result

        def __init__(self, pre, post, use_conditions=True):
            if not use_conditions:
               pre, post = None, None
            self._precondition, self._postcondition  = pre, post

        def __call__(self, function):
            # combine recursive wrappers (@precondition + @postcondition == @conditions)
            pres  = set((self._precondition,))
            posts = set((self._postcondition,))
            # unwrap function, collect distinct pre-/post conditions
            while type(function) is self.wrapper:
                pres.add(function._precond)
                posts.add(function._postcond)
                function = function._func
            # filter out None conditions and build pairs of pre- and postconditions
            conditions = map(None, filter(None, pres), filter(None, posts))
            # add a wrapper for each pair (note that 'conditions' may be empty)
            for pre, post in conditions:
                function = self.wrapper(pre, post, function)
            return function

    #/************************************************************************/
    @classmethod
    def decorator_precondition(cls, precondition, use_conditions=True):
        """Pre-condition decorator.

        See also
        --------
        :class:`Conditioning`, :meth:`decorator_postcondition`
        """
        return cls.Conditioning(precondition, None, use_conditions)

    #/************************************************************************/
    @classmethod
    def decorator_postcondition(cls, postcondition, use_conditions=True):
        """Post-condition decorator.

        See also
        --------
        :class:`Conditioning`, :meth:`decorator_precondition`
        """
        return cls.Conditioning(None, postcondition, use_conditions)


#==============================================================================
# Class FilterDecorator
#==============================================================================

class FilterDecorator():
    pass

