#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
.. _log


Basic stdout log classes: Error, Verbose and Warning.

**Content**
"""

# *credits*:      `gjacopo <jacopo.grazzini@ec.europa.eu>`_ 
# *since*:        Fri May  8 15:21:31 2020
                                                                                                                     
#%% Settings

import os, sys, warnings
import inspect
import functools
import six
   
DEFVERBOSE          = False # True

REDUCE_ANSWER       = False # ! used for testing purpose: do not change !
EXCLUSIVE_ARGUMENTS = False # ! used for settings: do not change !


#%% Core functions/classes

#==============================================================================
# Class Warning
#==============================================================================

class Warnings(Warning):
    """Dummy class for warnings in this package.
    
        >>> Warnings(warnmsg, expr=None)

    Arguments
    ---------
    warnmsg : str
        warning message to display.
        
    Keyword arguments
    -----------------
    expr : str 
        input expression in which the warning occurs; default: :data:`expr` is 
        :data:`None`.
        
    Example
    -------

        >>> Warnings('This is a very interesting warning');
            Warnings: ! This is a very interesting warning !
    """
    def __init__(self, msg='', **kwargs):    
        self.msg = msg
        expr = kwargs.pop('expr',None)
        if expr is not None:    self.expr = expr
        else:                   self.expr = '' 
        # warnings.warn(self.msg)
        print(self)
    def __repr__(self):             return self.msg
    def __str__(self):              
        #return repr(self.msg)
        return ( 
                "! %s%s%s !" %
                (self.msg, 
                 ' ' if self.msg and self.expr else '',
                 self.expr
                 )
            )
    
    
#==============================================================================
# Class Verbose
#==============================================================================

class Verbose(object):
    """Dummy class for verbose printing mode in this package.
    
        >>> Verbose(msg, verb=True, expr=None)

    Arguments
    ---------
    msg : str
        verbose message to display.
        
    Keyword arguments
    -----------------
    verb : bool
        flag set to :data:`True` when the string :literal:`[verbose] -` is added
        in front of each verbose message displayed.
    expr : str 
        input expression in which the verbose mode is called; default: :data:`expr` is 
        :data:`None`.
        
    Example
    -------

        >>> Verbose('The more we talk, we less we do...', verb=True);
            [verbose] - The more we talk, we less we do...
    """
    def __init__(self, msg='', **kwargs):    
        expr = kwargs.pop('expr','')
        verb = kwargs.pop('verb', DEFVERBOSE)
        self.msg = msg
        if verb is True:
            print('\n! [verbose] - %s !' % self.msg)
        if expr is not None:    self.expr = expr
    #def __repr__(self):             
    #    return self.msg
    def __str__(self):              
        return repr(self.msg)
 
        
#==============================================================================
# Class Error
#==============================================================================

class Error(Exception):
    """Dummy class for exception raising in this package.
    
        >>> raise Error(msg, type=None, code=None, expr='')

    Arguments
    ---------
    errmsg : str
        message -- explanation of the error.
        
    Keyword arguments
    -----------------
    type : object
        error type; when :data:`errtype` is left to :data:`None`, the system tries
        to retrieve automatically the error type using :data:`sys.exc_info()`.
    code : (float,int)
        error code; default: :data:`errcode` is :data:`None`.
    expr : str 
        input expression in which the error occurred; default: :data:`expr` is 
        :data:`None`.
        
    Example
    -------
        
        >>> try:
                assert False
            except:
                raise Error('It is False')
            Traceback ...
            ...
            Error: !!! AssertionError: It is False !!!
    """
    
    def __init__(self, msg='',  **kwargs):
        self.msg = msg
        typ = kwargs.pop('type',None)
        code = kwargs.pop('code',None)
        expr = kwargs.pop('expr','')
        if expr is not None:                self.expr = expr
        else:                               self.expr = '' 
        if typ is None:
            try:            typ = sys.exc_info()[0]
            except:         pass
        if inspect.isclass(typ):            self.type = typ.__name__
        elif isinstance(typ, (int,float)):  self.type = str(typ)
        else:                               self.type = typ
        if code is not None:                self.code = str(code)
        else:                               self.code = ''
        # super(Error,self).__init__(self, msg)

    def __str__(self):              
        # return repr(self.msg)
        str_ = ("%s%s%s%s%s%s%s" %
                (self.type or '', 
                 ' ' if self.type and self.code else '',
                 self.code or '',
                 ': ' if (self.type or self.code) and (self.msg or self.expr) else '',
                 self.msg or '', 
                 ' ' if self.msg and self.expr else '',
                 self.expr or '' #[' ' + self.expr if self.expr else '']
                 )
                )
        return ( "%s%s%s" % 
                ('' if str_.startswith('!!!') else '!!! ',
                 str_,
                 '' if str_.endswith('!!!') else ' !!!'
                 )
                )


#==============================================================================
# Method deprecated
#==============================================================================

def deprecated(reason, run=True):
    """This is a decorator which can be used to mark functions as deprecated. 
        
        >>> new = deprecated(reason)  
        
    Arguments
    ---------
    reason : str
        optional string explaining the deprecation.
        
    Keywords arguments
    ------------------
    run : bool
        set to run the function/method/... despite being deprecated; default: 
        :data:`False` and the decorated method/function/... is not run.
        
    Examples
    --------
    The deprecated function can be used to decorate different objects:
        
        >>> @deprecated("use another function")
        ... def old_function(x, y):
        ...     return x + y
        >>> old_function(1, 2)        
            __main__:1: DeprecationWarning: Call to deprecated function old_function (use another function).        
            3
        >>> class SomeClass(object):
        ... @deprecated("use another method", run=False)
        ... def old_method(self, x, y):
        ...     return x + y
        >>> SomeClass().old_method(1, 2)
            __main__:1: DeprecationWarning: Call to deprecated function old_method (use another method).       
        >>> @deprecated("use another class")
        ... class OldClass(object):
        ...     pass
        >>> OldClass()
            __main__:1: DeprecationWarning: Call to deprecated class OldClass (use another class).  
            <__main__.OldClass at 0x311e410f0>
            
    Note
    ----
    It will result in a warning being emitted when the function is used and when
    a :data:`reason` is passed.
    """
    # see https://stackoverflow.com/questions/2536307/decorators-in-the-python-standard-lib-deprecated-specifically
    if isinstance(reason, six.string_types): # happyType.isstring(reason):
        def decorator(func1):
            if inspect.isclass(func1):
                fmt1 = "Call to deprecated class {name} ({reason})."
            else:
                fmt1 = "Call to deprecated function {name} ({reason})."
            @functools.wraps(func1)
            def new_func1(*args, **kwargs):
                warnings.simplefilter('always', DeprecationWarning)
                warnings.warn(
                    fmt1.format(name=func1.__name__, reason=reason),
                    category=DeprecationWarning,
                    stacklevel=2
                )
                warnings.simplefilter('default', DeprecationWarning)
                if run is True:
                    return func1(*args, **kwargs)
            return new_func1
        return decorator
    elif inspect.isclass(reason) or inspect.isfunction(reason):
        func2 = reason
        if inspect.isclass(func2):
            fmt2 = "Call to deprecated class {name}."
        else:
            fmt2 = "Call to deprecated function {name}."
        @functools.wraps(func2)
        def new_func2(*args, **kwargs):
            warnings.simplefilter('always', DeprecationWarning)
            warnings.warn(
                fmt2.format(name=func2.__name__),
                category=DeprecationWarning,
                stacklevel=2
            )
            warnings.simplefilter('default', DeprecationWarning)
            if run is True:
                return func2(*args, **kwargs)
        return new_func2
    else:
        raise Error('wrong type for input reason - %s not supported' % repr(type(reason)))
        
