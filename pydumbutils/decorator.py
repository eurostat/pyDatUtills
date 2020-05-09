#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
.. _decorator

Module implementing miscellaneous decorators.

**Dependencies**

*require*:      :mod:`functools`, :mod:`inspect`, :mod:`types`

*optional*:     :mod:`wrapt`  

**Contents**
"""

# *credits*:      `gjacopo <gjacopo@ec.europa.eu>`_ 
# *since*:        Sat May  9 17:47:16 2020

#%% Settings

from functools import wraps
from warnings import warn
from types import ClassType
from inspect import getmro, isclass

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
        
    Arguments:
    left_metas,right_metas : class
        classes (not strings) representing the metaclasses to 'merge'; note that
        :Data:`left_metas` has priority over :data:`right_metas`\ .
        
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

    .. digraph:: metaclass_conflict
    
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
        skipset = set([ClassType])
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

def class_decorator(decorator, *attr_names, **kwargs):
    """Class decorator used to automatically decorate a family of methods of a class.

        >>> new_cls = class_decorator(decorator, *attr_names, **kwargs)(cls)
        
    Arguments
    ---------
    decorator : callable
        universal or specific function/class decorator used to decorate methods
        and subclasses of the class :data:`cls`\ .
    attr_names : str, list of str, optional
        list of methods or classes to be decorated in the new class :data:`new_cls`; 
        if :literal:`None` or :literal:`()`, all instance/static/class methods as
        well as all classes of :data:`cls` are decorated in :data:`new_cls`, excepted 
        those whose names are in :data:`excludes` (if any, see below).
    
    Keyword Arguments
    -----------------
    excludes : list of str, optional
        list of methods or classes to exclude from the list of decorated ones in 
        the new class :data:`new_cls`\ .
    'base' : str, bool, optional
        variable conveying the name of a parent class of the input decorated class 
        :data:`cls` whose attributes will be further decorated; set to :literal:`True` 
        when a default name is selecte (:literal:'Base') and :literal:`False` when the 
        parent class should be ignored.
        
    Returns
    -------
    new_cls : class
        class inherited from :data:`new_cls` where methods and classes whose names 
        match :data:`attr_names` (all if :data:`()`) are decorated using the decorator
        :data:`method_decorator`\ .
    
    Examples
    --------    
    Let's create a method decorator that increments the output of a function on integer:

        >>> increment = lambda x: x+1
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

    Let's implement different inherited classes using the class decorator:

        >>> @class_decorator(decorator_increment)
        ... class B(A): # all methods of this class are decorated
        ...     pass
        >>> @class_decorator(decorator_increment, 'multiply_by_2')
        ... class C(A): # only multiply_by_2 method is decorated
    ...     pass
    
    and test it :
    
        >>> a = A(); b = B(); c = C()
        >>> print a.increment_twice(1)
            3
        >>> print b.increment_twice(1) # decorated with one more call to increment
            4
        >>> print c.increment_twice(1) # not decorated
            3
        >>> print a.multiply_by_2(1)
            2
        >>> print b.multiply_by_2(1)
            3
        >>> print c.multiply_by_2(1) # also decorated
            3
    """
    if decorator is None:       
        return lambda x:x
    base_decorate = kwargs.pop('base', 'Base') 
    if base_decorate is True:   base_decorate = 'Base'
    attr_excludes = kwargs.pop('exclude',())
    attr_names = tuple(set(attr_names)-set(attr_excludes))
    special_members = ['__metaclass__','__module__','__weakref__','__dict__','__class__']
    # prepare/redefine the decorating method
    ## decorator = method_decorator(method_decorator, *func_names, **func_exclude)
    def _new_decorator(decorated, name):
        try:
            return decorator(decorated, name)
        except TypeError:
            return decorator(decorated)        
    def _optional_decorator(decorated, name):
        if (attr_names in ((),(None,)) or name in attr_names) and name not in attr_excludes:
            return _new_decorator(decorated, name) 
        return decorated
    # the class rebuilder
    def class_rebuilder(_cls): 
        #if _cls is None: _cls = object
        # let's find out if there is already a metaclass attribute to build 
        # on the top of...
        try: 
            meta_cls = _cls.__metaclass__
        except:
            meta_cls = type
        #class metaclass_decorator(MetaInheritor):
        #    @classmethod
        #    def pre_new(meta, name, bases, attrs):
        #        (name, bases, attrs) = MetaInheritor.__new__(meta, name, bases, attrs)
        #        ...
        #        return MetaInheritor.pre_new(name, bases, attrs) 
        class metaclass_decorator(meta_cls):
            def __new__(meta, name, bases, attrs):
                # the name new_cls will be bound (in global scope, in this case) 
                # to a class that in fact isn't the "real" _cls, but a subclass
                # (see below assignment new_cls.__name__ = _cls.__name__). So, 
                # any late-bound reference to that name, like in super() calls 
                # will get the subclass that's masquerading by that name -- that 
                # subclass's superclass is of course the "real" _cls, hence this 
                # may create infinite recursion.
                # to avoid this, we set the bases ('__bases__') classes of new_cls
                # to those of _cls
                bases = _cls.__bases__ 
                attrs.update(_cls.__dict__.copy())
                if base_decorate is not False:
                    [attrs.update({attr: obj}) for base in _cls.__bases__ for (attr,obj) in base.__dict__.items()
                        if not attr in attrs.keys() and base.__name__ == base_decorate]
                #print 'attrs.items', attrs.items
                for attr, obj in attrs.items(): # variant of vars(meta).items()
                    if attr in special_members:
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
                    except: pass # raise DecoratorError('wrong attribute name {}'.format(attr))
                    else:
                        return _new_decorator(obj, attr)
        else:
            class new_cls(_cls):
                # __doc__ = _cls.__doc__
                __metaclass__ = metaclass_maker(right_metas=(metaclass_decorator,))
                #__metaclass__ = metaclass_maker(left_metas=(meta_cls,),right_metas=(metaclass_decorator,))
        # complete the inheritance
        try:    
            new_cls.__module__ = _cls.__module__ 
        except: pass
        try:    
            new_cls.__name__ = _cls.__name__
        except: pass
        else:
            return new_cls
    return class_rebuilder
        

#==============================================================================
# Class MethodDecorator
#==============================================================================

class MethodDecorator():
    """Decorator that knows the class the decorated method is bound to.
    
        >>> class NewDecorator(BMethodDecorator):
                ...        
    
    The new implemented class :meth:`NewDecorator`:
        - knows the class the decorated method is bound to.
        - hides decorator traces by answering to system attributes more correctly  
          than another decorator class like :meth:`functools.wraps` does.
        - deals with bound and unbound instance methods, class methods, static
          methods, and plain functions (likewise the original method decorator  
          method) as well as properties.   
    """
    
    #/************************************************************************/
    def __init__(self, func, obj=None, cls=None, method_type='function',
                 **kwargs):
        # these defaults are OK for plain functions  and will be changed by 
        # __get__() for methods once a method is dot-referenced
        self.func, self.obj, self.cls, self.method_type = func, obj, cls, method_type
            
    #/************************************************************************/
    def __repr__(self):  # special case: __repr__ ignores __getattribute__
        return self.func.__repr__()
    
    #/************************************************************************/
    #def __get__(self, obj, objtype):
    #    # support instance methods
    #    return functools.partial(self.__call__, obj)    
    def __get__(self, obj=None, cls=None):
        # it is executed when decorated func is referenced as a method: cls.func 
        # or obj.func
        if self.obj == obj and self.cls == cls:
            return self 
        if self.method_type=='property':
            return self.func.__get__(obj, cls)
        method_type = ( # note that we added 'property'
            'staticmethod' if isinstance(self.func, staticmethod) else
            'classmethod' if isinstance(self.func, classmethod) else
            'property' if isinstance(self.func, property) else 
            'instancemethod'
            )
        return object.__getattribute__(self, '__class__')( 
            # use bound or unbound method with this underlying func
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

def method_decorator(func_decorator=None, *func_names, **func_exclude):
    """Generic method decorator used to automatically decorate methods.
    """
    func_exclude = func_exclude.pop('exclude',())
    func_names = tuple(set(func_names) - set(func_exclude))
    try:
        assert _is_wrapt_imported is True
    except:   
        if func_decorator is None:
            return MethodDecorator
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
        class method_rebuilder(MethodDecorator):
            def __init__(self, func, obj=None, cls=None, method_type='function'):
                MethodDecorator.__init__(self, func, obj=obj, cls=cls, method_type=method_type)
                setattr(self,'__doc__',object.__getattribute__(func_decorator(self.func), '__doc__'))
            def __call__(self, *args, **kwargs):
                if (func_names in ((),(None,)) or self.func in func_names) and self.func not in func_exclude:
                    return func_decorator(self.func)(*args, **kwargs)                
                else:
                    return self.func(*args, **kwargs)                
            def __getattribute__(self, attr_name): 
                if attr_name in ('__init__','__get__', '__call__', '__getattribute__','__doc__','func', 'obj', 'cls', 'method_type'): 
                    return object.__getattribute__(self, attr_name) # ibid
                return getattr(self.func, attr_name)
    else:
        if func_decorator is None:
            return lambda f: f
        #@wrapt.decorator
        #def method_rebuilder(wrapped, instance, args, kwargs):
        #    return func_decorator(wrapped(*args, **kwargs))
        method_rebuilder = func_decorator(method_wrapper)
    return method_rebuilder


  
#==============================================================================
# Function generic_decorator
#==============================================================================

def generic_decorator(*args, **kwargs):
    def decorator(obj):
        if isclass(obj):
            return class_decorator(*args, **kwargs) (obj)                      
        else:
            return method_decorator(*args, **kwargs) (obj)                      
    return decorator


#==============================================================================
# Class MetaclassProxy
#==============================================================================

class MetaclassProxy(type):
    """Decorate the class being created & preserve :literal:`__metaclass__` of the 
    parent.
    
    Algorithm
    ---------
    It executes two callbacks: before and after creation of a class, that allows to
    decorate them.

    Between two callbacks, it tries to locate any :literal:`__metaclass__` in the 
    parents (sorted in MRO). 
    
    If found — with the help of :literal:`__new__` method - it mutates to the found
    base :literal:`__metaclass__`. 
    If not found, it just instantiates the given class.
    """
    # see http://stackoverflow.com/questions/4651729/metaclass-mixin-or-chaining

    #/************************************************************************/
    @classmethod
    def pre_new(meta, name, bases, attrs):
        """Decorate a class before creation."""
        return (name, bases, attrs)

    #/************************************************************************/
    @classmethod
    def post_new(meta, newclass):
        """Decorate a class after creation."""
        return newclass

    #/************************************************************************/
    @classmethod
    def _mrobases(meta, bases):
        """Expand tuple of base-classes ``bases`` in MRO."""
        mrobases = []
        for base in bases:
            if base is not None: # We don't like `None` :)
                mrobases.extend(base.mro())
        return mrobases

    #/************************************************************************/
    @classmethod
    def _find_parent_metaclass(meta, mrobases):
        """Find any __metaclass__ callable in ``mrobases``."""
        for base in mrobases:
            if hasattr(base, '__metaclass__'):
                metacls = base.__metaclass__
                if metacls and not issubclass(metacls, meta): # don't call self again
                    return metacls#(name, bases, attrs)
        # Not found: use `type`
        return lambda name,bases,attrs: type.__new__(type, name, bases, attrs)

    #/************************************************************************/
    def __new__(meta, name, bases, attrs):
        mrobases = meta._mrobases(bases)
        name, bases, attrs = meta.pre_new(name, bases, attrs) # Decorate, pre-creation
        newclass = meta._find_parent_metaclass(mrobases)(name, bases, attrs)
        return meta.post_new(newclass) # Decorate, post-creation

        
#==============================================================================
# Function metaclass_decorator
#==============================================================================

def metaclass_decorator(method_decorator, *func_names):
    """Metaclass decorator used to automatically decorate the `metaclass` attribute 
    of a class. 

        >>> new_cls = metaclass_decorator(method_decorator, *func_names)(cls)

    Note
    ----
    Note that when the class :data:`cls` is inherited from another one, say :data:`super_cls`, 
    all methods :data:`cls` that are inherited from :data:`super_cls` (and not overriden or
    specific to the class) are decorated in the new class :data:`new_cls`.
    
    See http://python-3-patterns-idioms-test.readthedocs.org/en/latest/Metaprogramming.html
    """

    #decorator = method_decorator(func_decorator, *func_names)
    def class_rebuilder(cls): 
        #class __metaclass__(type):
        #    def __init__(cls, name, bases, nmspc):
        #        type.__init__(cls, name, bases, nmspc)
        class new_cls(cls):
            __metaclass__ = MetaclassProxy # Inheritor 
        try:    
            new_cls.__metaclass__ = class_decorator(method_decorator, *func_names)(new_cls.__metaclass__)
        except:
            raise IOError("%s metaclass not decorated" % cls.__name__)
        try:    
            new_cls.__module__ = cls.__module__ 
        except: pass
        try:    
            new_cls.__name__ = cls.__name__ # __metaclass__
        except: pass
        return new_cls         
    return class_rebuilder
  

#==============================================================================
# Class Conditioning
#==============================================================================

class Conditioning(object):
    """Provide pre-/postconditions as function decorators.

    Example
    -------

        >>> def in_ge20(inval):
        ...     assert inval >= 20
        >>> def out_lt30(retval, inval):
        ...     assert retval < 30        
        >>> @decorator_precondition(in_ge20) # equivalent to: Conditioning(in_ge20, None)
        ... @decorator_postcondition(out_lt30) # equivalent to: Conditioning(None, out_lt30)
        ... def apply_increment(x): 
        ...     return x+1      
        
        >>> @Conditioning(in_ge20, out_lt30)
        ... def apply_increment_sim(x): 
        ...     return x+1             

    and simply run:

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

        self._precondition  = pre
        self._postcondition = post

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
        

#==============================================================================
# Function decorator_precondition
#==============================================================================

def decorator_precondition(precondition, use_conditions=True):
    """
    See also
    --------
    :meth:`decorator_postcondition`
    """
    return Conditioning(precondition, None, use_conditions)


#==============================================================================
# Function decorator_postcondition
#==============================================================================

def decorator_postcondition(postcondition, use_conditions=True):
    """
    See also
    --------
    :meth:`decorator_precondition`
    """
    return Conditioning(None, postcondition, use_conditions)

