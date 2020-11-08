#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
.. _struct

Module introducing various structure manipulations.

**Dependencies**

*require*:      :mod:`numpy`, :mod:`pandas`, :mod:`datetime`

*call*:         :mod:`pydumbutils.log`

**Contents**
"""

# *credits*:      `gjacopo <gjacopo@ec.europa.eu>`_
# *since*:        Fri May  8 15:56:40 2020

#%% Settings

from collections import OrderedDict
from collections.abc import Mapping, Sequence
from six import string_types

from itertools import product, cycle
from itertools.chain import from_iterable
from functools import reduce
from copy import copy, deepcopy
import inspect

import re
from warnings import warn

import datetime

import numpy as np
import pandas as pd

from pydatutils.log import deprecated


#%% Core functions/classes

#==============================================================================
# Class Type
#==============================================================================

class Type():

    # Variables of useful types conversions
    __PYTYPES = {'object':'object', \
                 'int':'uint8', 'uint8':'uint8', 'uint16':'uint16', 'int16':'int16',    \
                 'long': 'uint32', 'uint32':'uint32', 'int32':'int32',                  \
                 'float':'float32', 'float32':'float32', 'float64':'float64'            \
                 }

    # Python pack types names
    __PPTYPES = ['B', 'b', 'H', 'h', 'I', 'i', 'f', 'd'] # personal selection
    #=========   ==============  =================   =====================
    #Type code   C Type          Python Type         Minimum size in bytes
    #=========   ==============  =================   =====================
    #'c'         char            character           1
    #'u'         Py_UNICODE      Unicode character   2
    #'B'         unsigned char   int                 1
    #'b'         signed char     int                 1
    #'H'         unsigned short  int                 2
    #'h'         signed short    int                 2
    #'I'         unsigned int    long                2
    #'i'         signed int      int                 2
    #'L'         unsigned long   long                4
    #'l'         signed long     int                 4
    #'f'         float           float               4
    #'d'         double          float               8
    #=========   ==============  =================   =====================
    #See http://www.python.org/doc//current/library/struct.html and
    #http://docs.python.org/2/library/array.html.

    # NumPy types names
    __NPTYPES         = [np.dtype(n).name for n in __PPTYPES+['l','L','c']]

    # Pandas types names
    __PDTYPES         = [np.dtype(n).name for n in ['b', 'i', 'f', 'O', 'S', 'U', 'V' ]]
    #=========   ==============
    #Type code   C Type
    #=========   ==============
    #'b'         boolean
    #'i'         (signed) integer
    #'u'         unsigned integer
    #'f'         floating-point
    #'c'         complex-floating point
    #'O'         (Python) objects
    #'S', 'a'    (byte-)string
    #'U'         Unicode
    #'V'         raw data (void)

    # Dictionary of Python pack types -> Numpy
    __PPT2NPT = {n:np.dtype(n).name for n in __PPTYPES}
    # See http://docs.scipy.org/doc/numpy/reference/arrays.dtypes.html and
    # http://docs.scipy.org/doc/numpy/reference/arrays.scalars.html.

    # Dictionary of Python -> Numpy
    __NPT2PYT = { np.dtype('b'):                bool,
                  np.dtype('i'):                bool,
                  np.dtype('O'):                str, # not object
                  np.dtype('U'):                str,
                  object:                       object,
                  np.dtype('i'):                int,
                  np.dtype('uint32'):           int,
                  np.dtype(int):                int,
                  np.dtype('f'):                float,
                  np.dtype(float):              float,
                  np.dtype('datetime64'):       datetime.datetime,
                  np.dtype('datetime64[ns]'):   datetime.datetime
                 }

    # Dictionary of Python -> Numpy
    def __rev_dict_unique_values(d):
        dd = {}
        [dd.setdefault(v, []).append(k) for (k,v) in d.items()]
        return dd
    __PYT2NPT = __rev_dict_unique_values(__NPT2PYT)
    #__PY2NPT = { bool:      [np.dtype('b'), np.dtype('i')],
    #             str:        [np.dtype('O'), object],
    #             int:        [np.dtype('i'), np.dtype('uint32'), np.dtype(int)],
    #             float:      [np.dtype('f'), np.dtype(float)],
    #             datetime.datetime:   [np.dtype('datetime64'), np.dtype('datetime64[ns]')],
    #             }

    #/************************************************************************/
    ppt2npt = lambda t: Type.__PPT2NPT[t]
    """Conversion method Python pack <-> Numpy types.
    """
    # note regarding np.dtype:
    #   np.dtype('B')           -> dtype('uint8')
    #   np.dtype('uint8')       -> dtype('uint8')
    #   np.dtype(np.uint8)      -> dtype('uint8')
    # so that on the current machine where it is implemented
    # assert ppt2npy == {'B':'uint8','b': 'int8','H':'uint16','h':'int16','I':'uint32',
    #   'i':'int32', 'f':'float32', 'd':'float64'}
    # but... in the future?!

    #/************************************************************************/
    npt2ppt = lambda t: dict(Type.__PPT2NPT.values(), Type.__PPT2NPT.keys())[t]
    """Conversion method Numpy -> Python pack types.
    """

    #/************************************************************************/
    npt2pyt = lambda t: Type.__NPT2PYT[t]
    """Conversion method Numpy -> Python types.
    """

    #/************************************************************************/
    pdt2pyt = npt2pyt
    """Conversion method Pandas -> Python types.
    """

    #/************************************************************************/
    pyt2npt = lambda t: Type.__PYT2NPT[t]
    """Conversion method Python -> Numpy types.
    """

    __UPYT2NPT = { bool:                       np.dtype('b'),
                   str:                        np.dtype('U'),
                   int:                        np.dtype(int), #np.dtype('i')
                   float:                      np.dtype(float), # np.dtype('f')
                   datetime.datetime:          np.dtype('datetime64'),
                   object:                     np.dtype('O')
                   }

    #/************************************************************************/
    upyt2npt = lambda t: Type.__UPYT2NPT[t]
    """Conversion method Python -> unique Numpy type.
    """

    #/************************************************************************/
    upyt2pdt = upyt2npt
    """Conversion method Python -> unique Pandas type.
    """

    #/************************************************************************/
    pyt2pdt = pyt2npt
    """Conversion method Python -> Pandas types.
    """

    # Dictionary of Numpy type -> unique Python name
    __NPT2UPYN = {k:v.__name__ for (k,v) in __NPT2PYT.items()}

    # Dictionary of Python name -> unique Numpy type
    __UPYN2NPT = {k.__name__:v for (k,v) in __UPYT2NPT.items()}

    upytname2npt = lambda n: Type.__UPYN2NPT[n]
    """Conversion method Python type name -> unique Numpy type.
    """

    unpt2pytname = lambda t: Type.__NPT2UPYN[t]
    """Conversion method Numpy type -> unique Python type name.
    """

    upytname2pdt = upytname2npt
    """Conversion method Python type name -> unique Pandas type.
    """

    #/************************************************************************/
    pytname2npt = lambda n: {k.__name__:v for (k,v) in Type.__PYT2NPT.items()}[n]
    """Conversion method Python type name -> Numpy types list.
    """

    #/************************************************************************/
    pytname2pdt = pytname2npt
    """Conversion method Python type name -> Pandas types list.
    """

    #/************************************************************************/
    @staticmethod
    def is_numeric(cls, arg):
        """Check whether an argument is a number.

            >>> ans = Type.is_numeric(arg)

        Arguments
        ---------
        arg :
            any input to test.

        Returns
        -------
        ans : bool
            :data:`True` if the input argument :data:`arg` is a number, :data:`False`
            otherwise.
        """
        try:
            float(arg)
            return True
        except (ValueError, TypeError):
            return False

    #/************************************************************************/
    @staticmethod
    def is_string(cls, arg):
        """Check whether an argument is a string.

            >>> ans = Type.is_string(arg)

        Arguments
        ---------
        arg :
            any input to test.

        Returns
        -------
        ans : bool
            :data:`True` if the input argument :data:`arg` is a string, :data:`False`
            otherwise.
        """
        return isinstance(arg, string_types)

    #/************************************************************************/
    @classmethod
    def is_sequence(cls, arg):
        """Check whether an argument is a "pure" sequence (*e.g.*, a :data:`list`
        or a :data:`tuple`), *i.e.* an instance of the :class:`collections.Sequence`
        (strings excluded).

            >>> ans = Type.is_sequence(arg)

        Arguments
        ---------
        arg :
            any input to test.

        Returns
        -------
        ans : bool
            :data:`True` if the input argument :data:`arg` is an instance of the
            :class:`collections.Sequence` class, but not a string (*i.e.,* not an
            instance of the :class:`six.string_types` class), :data:`False`
            otherwise.
        """
        return (isinstance(arg, Sequence) and not cls.is_string(arg))

    #/************************************************************************/
    @classmethod
    def is_mapping(cls, arg):
        """Check whether an argument is a true dictionary (strings excluded).

            >>> ans = Type.is_mapping(arg)

        Arguments
        ---------
        arg :
            any input to test.

        Returns
        -------
        ans : bool
            :data:`True` if the input argument :data:`arg` is an instance of the
            :class:`collections.Mapping` class, but not a string .
        """
        return (isinstance(arg, Mapping) and not cls.is_string(arg))

    #/************************************************************************/
    @staticmethod
    def is_type(obj, cls):
        """Determine whether an object (as an instance is) of a given type defined
        by a class or a class name.

            >>> ans = Type.is_type(obj, cls)

        Arguments
        ---------
        obj : object
            an instance of a class.
        cls : str,type[list]
            the (list of) class(es) or its(their) name(s) to test.

        Returns
        -------
        ans : bool
            :data:`True` when :data:`inst` class name is :data:`str_cls`, :data:`False`
            otherwise.
        """
        if not isinstance(cls, (type,string_types)):
            raise TypeError("is_type() arg 2 must be a class or a class name")
        try:
            if isinstance(cls, type):
                return isinstance(obj, cls) or issubclass(obj.__class__, cls)
            else: # isinstance(aclass, string_types)
                # return Type.type_name(inst) == cls
                return obj.__class__.__name__ == cls
        except:
            raise IOError("Unrecognised is_type() arg 1")

    #/************************************************************************/
    @staticmethod
    def is_subclass(obj, cls):
        """Check whether an object is an instance or a subclass of a given class.

            >>> res = Type.is_subclass(obj, cls))
        """
        try:
            assert (isinstance(cls, Sequence) and all([isinstance(c, type) for c in cls])) \
                or isinstance(cls, type)
        except:
            raise TypeError("is_subclass() arg 2 must be a (list of) class(es)")
        if isinstance(cls, type):
            cls = [cls,]
        if isinstance(obj, type):
            return any([issubclass(obj, c) for c in cls])
        else:
            try:
                return any([issubclass(obj.__class__, c) for c in cls])
            except:
                raise IOError("Unrecognised is_subclass() arg 1")

    #/************************************************************************/
    @staticmethod
    def type_name(obj):
        """Return the class name of an object given as an instance: nothing else
        than :literal:`obj.__class__.__name__`\ .

            >>> name = Type.type_name(obj)

        Arguments
        ---------
        inst : object
            an instance of a class.

        Returns
        -------
        name : str
            name of the class of the instance :data:`inst`.
        """
        try:
            return obj.__class__.__name__
        except:
            raise IOError('input not recognised as an instance')

    #/************************************************************************/
    @staticmethod
    def subdtypes(dtype):
        """
        Example
        -------

            >>> Type.subdtypes(np.generic)
        """
        subs = dtype.__subclasses__()
        if not subs:
            return dtype
        return [dtype, [Type.subdtypes(dt) for dt in subs]]

    #/************************************************************************/
    @classmethod
    def to_type(cls, data, dtype, view=None):
        """Perform type conversions of various structures (either :class:`list`,
        :class:`tuple`, :class:`array` or :class:`dict`).

            >>> output = Type.to_type(data, dtype, view=None)

        Arguments
        ---------
        dtype : str
            string indicating the desired output type; this can be any string.
        """
        def totypearray(x): # dtype, kwargs defined 'outside'
            if x.dtype=='object':                           return x
            elif dtype is not None and x.dtype!=dtype:      return x.astype(dtype)
            elif view is not None and x.dtype!=view:        return x.view(dtype=view)
            else:                                           return x
        def totype(x): # dtype, kwargs defined 'outside'
            if np.isscalar(x):
                if any([re.search(t, dtype) for t in ('int8','int16')]): return int(x)
                # elif re.search('int32', dtype):                         return long(x)
                elif re.search('float', dtype):                         return float(x)
            elif isinstance(x, np.ndarray):
                return totypearray(x)
            elif cls.is_sequence(x) or cls.is_mapping(x):
                return cls.to_type(x, dtype, view) # recursive call
            else:
                return x
        if isinstance(data, (np.ndarray, pd.DataFrame, pd.Series)):
            return totypearray(data)
        elif cls.is_mapping(data):
            return dict(zip(data.keys(), map(totype, data.values())))
        elif cls.is_sequence(data):
            return map(totype, data)
        else:
            return data


#==============================================================================
# Class Struct
#==============================================================================

class Struct():

    #/************************************************************************/
    @staticmethod
    def inspect_kwargs(kwargs, method):
        """Clean keyword parameters prior to be passed to a given method/function by
        deleting all the keys that are not present in the signature of the method/function.
        """
        if kwargs == {}: return {}
        kw = kwargs.copy() # deepcopy(kwargs)
        parameters = inspect.signature(method).parameters
        keys = [key for key in kwargs.keys()                                          \
                if key not in list(parameters.keys()) or parameters[key].KEYWORD_ONLY.value == 0]
        [kw.pop(key) for key in keys]
        return kw

    #/************************************************************************/
    @staticmethod
    def update_instance(instance, flag, args, **kwargs):
        """Update or retrieve an instance (field) of the data class through the
        parameters passed in kwargs.

            >>> res = Struct.update_instance(instance, flag, args, **kwargs)

        Arguments
        ---------
        instance : object
            instance of a class with appropriated fields (eg. 'self' is passed).
        flag : bool
            flag set to `True` when the given instance(s) is (are) updated from the
            parameters passed in kwargs when the parameters are not `None`, `False`
            when they are retrieved from `not None` instance(s);
        args : dict
            provide for each key set in kwargs, the name of the instance to consider.

        Keyword Arguments
        -----------------
        kwargs : dict
            dictionary with values used to set/retrieve instances in/from the data.

        Returns
        -------
        res : dict

        Note
        ----
        This is equivalent to perform:

            >>> key = args.keys()[i]
            >>> val = kwargs.pop(key,None)
            >>> if flag is False and val is None:
            ...     val = getattr(self,args[key])
            >>> if flag is True and val is not None:
            ...     setattr(self,args[key]) = val
            >>> res = val

        for all keys :literal:`i` of :literal:`args`.

        Examples
        --------

            >>> param = { my_key: 'name_of_my_instance' }
            >>> kwarg = { my_key: my_not_None_value }

        Set the :data:`name_of_my_instance` attribute of the class to :data:`my_value` and return
        :data:`my_not_None_value`:

        >>> res = Struct.update_instance(instance, True, param, **kwarg)

        Retrieve :data:`name_of_my_instance` attribute:

        >>> res = Struct.update_instance(instance, False, param, **kwarg)
        """
        if not Type.is_mapping(args):
            raise IOError("Dictionary requested in input")
        res = {} # res = []
        for key in args.keys():     # while not(_isonlyNone(args))
            attr = args.pop(key)
            if not(Type.is_string(key) and Type.is_string(attr)):
                raise IOError("String keys and values expected")
            elif not hasattr(instance, attr): # getattr(instance,attr)
                raise IOError("Unrecognised attribute")
            val = kwargs.pop(key, None)
            if flag is False and val is None:
                val =  instance.__getattribute__(attr)
            elif flag is True and val is not None:
                instance.__setattr__(attr, val)
            res.update({key: val}) # res.append(val)
        return res

    #/************************************************************************/
    @staticmethod
    def to_format(data, outform, inform=None):
        """Perform structure conversions from/to: :class:`list`, :class:`tuple`,
        :class:`array` and :class:`dict`\ .

            >>> output = Struct.to_format(data, outform, inform=None)

        Arguments
        ---------
        outform : str
            string specifying the desired output format; it can any string in
            :literal:`['array', 'dict', 'list', 'tuple']`\ .
        """
        if inform == outform:                               return data
        def tolist(data):
            if data is None:                                return None
            elif isinstance(data, list):                    return data
            elif isinstance(data, tuple):                   return list(data)
            elif isinstance(data, dict):                    return data.values()
            elif isinstance(data, np.ndarray):              return list(data)
            elif isinstance(data, pd.Series):               return data.to_list()
            elif isinstance(data, pd.DataFrame):            return list(data.values)
            else:                                           return data#raise IOError
        def totuple(data):
            if data is None:                                return None
            elif isinstance(data, tuple):                   return data
            elif isinstance(data, list):                    return tuple(data)
            elif isinstance(data, dict):                    return tuple(data.values())
            elif isinstance(data, np.ndarray):              return tuple(list(data))
            elif isinstance(data, pd.Series):               return tuple(data.to_list())
            elif isinstance(data, pd.DataFrame):            return tuple(data.values)
            else:                                           return data#raise IOError
        def toarray(data):
            if data is None:                                return None
            if isinstance(data, dict):
                if len(data) == 1:                   data = data.values()[0]
                else:                               data = data.values()
            if isinstance(data, (list, tuple)):     data = np.asarray(data)
            if isinstance(data, np.ndarray):                return data
            elif isinstance(data, (pd.Series, pd.DataFrame)):
                                                            return data.to_numpy()
            else:                                           return data#raise IOError
        def todict(data):
            if data is None:                                return None
            elif isinstance(data, dict):
                newkeys = range(len(data))
                if data.keys() == newkeys:                  return data
                else:           return dict(zip(newkeys, data.values()))
            elif isinstance(data, np.ndarray):
                if data.ndim == 2:                          return dict([(0, data)])
                else:        return dict([(i, data[i]) for i in range(0, len(data))])
            elif isinstance(data, (pd.Series, pd.DataFrame)):
                                                            return data.to_dict()
            elif not isinstance(data, (list, tuple)):       return data
            else:            return dict([(i, data[i]) for i in range(0, len(data))])
        formatf = {'array': toarray,  'dict': todict,             \
                    'list': tolist,   'tuple': totuple            \
                    }
        return formatf[outform](data)

    #/************************************************************************/
    @staticmethod
    def flat(*obj):
        """Flatten a structure recursively.

            >>> res = Struct.flat(*obj)

        See also
        --------
        :meth:`~Struct.flatten_seq`, :meth:`~Struct.flatten`.
        """
        for item in obj:
            if hasattr(item, '__iter__') and not Type.is_string(item): #
            #if isinstance(item, (Sequence, Mapping, set))  and not Type.is_string(item):
                yield from Struct.flat(*item)
                # for y in Struct.flat(*item):    yield y
            else:
                yield item

    #/************************************************************************/
    @staticmethod
    def flatten(structure, key="", path="", flattened=None, indexed=False):
        """Flatten any structure of any type (list, dict, tuple) and any depth in
        a recursive manner.

            >>> res = Struct.flatten(structure, key="", path="",
                                     flattened=None, indexed=False)

        See also
        --------
        :meth:`~Struct.flatten_seq`, :meth:`~Struct.flat`.
        """
        if indexed is False:
            if flattened is None:                   flattened = []
            elif not isinstance(flattened, list):   flattened = Struct.to_format(flattened,'list')
            for st in structure:
                if hasattr(st, "__iter__") and not Type.is_string(st):
                    flattened.extend(Struct.flatten(st))
                else:
                    flattened.append(st)
        else:
            if flattened is None:                   flattened = {}
            if not isinstance(structure, (dict, list)):
                flattened[((path + "_") if path else "") + key] = structure
            elif isinstance(structure, list):
                for i, item in enumerate(structure):
                    Struct.flatten(item, "%d" % i, path + "_" + key, flattened)
            else:
                for new_key, value in structure.items():
                    Struct.flatten(value, str(new_key), path + "_" + key, flattened)
        return flattened

    #/************************************************************************/
    @staticmethod
    def flatten_seq(arg, rec=False):
        """Flatten a list of lists (one-level only).

            >>> flat = Struct.flatten_seq(arg, rec = False)

        Arguments
        ---------
        arg : list[list]
            a list of nested lists.

        Keyword arguments
        -----------------
        rec : bool
            :data:`True` when the flattening shall be applied recursively over
            nested lists; default: :data:`False`.

        Returns
        -------
        flat : list
            a list from which all nested elements have been flatten from 1 "level"
            up (case :data:`rec=False`) or through all levels (otherwise).

        Examples
        --------
        A very basic way to flatten a list of lists:

            >>> Struct.flatten_seq([[1],[[2,3],[4,5]],[6,7]])
                [1, [2, 3], [4, 5], 6, 7]
            >>> Struct.flatten_seq([[1,1],[[2,2],[3,3],[[4,4],[5,5]]]])
                [1, 1, [2, 2], [3, 3], [[4, 4], [5, 5]]]

        As for the difference between recursive and non-recursive calls:

            >>> seq = [[1],[[2,[3.5,3.75]],[[4,4.01],[4.25,4.5],5]],[6,7]]
            >>> Struct.flatten_seq(seq, rec=True)
                [1, [2, [3.5, 3.75]], [[4, 4.01], [4.25, 4.5], 5], 6, 7]
            >>> Struct.flatten_seq(seq, rec=True)
                [1, 2, 3.5, 3.75, 4, 4.01, 4.25, 4.5, 5, 6, 7]

        See also
        --------
        :meth:`~Struct.flatten`, :meth:`~Struct.flat`.
        """
        if not Type.is_sequence(arg):
            arg = [arg,]
        def _recurse(alist):
            if not any([Type.is_sequence(a) for a in alist]):
                return alist
            if all([Type.is_sequence(a) for a in alist]):
               nlist  = list(from_iterable(alist))
            else:
                nlist = alist
            if any([Type.is_sequence(nlist) for a in nlist]):
                res = []
                for item in nlist:
                    if Type.is_sequence(item):
                        res += _recurse(item)
                    else:
                        res.append(item)
            else:
                res = nlist
            return res
        if rec is True:
            return _recurse(arg)
        else:
            return list(from_iterable(arg))

    #/************************************************************************/
    @staticmethod
    def flatten_uniq(obj, key="", path="", flattened=None, indexed=False):
        """'Uniqify' and flatten the values of a structure of any type (list, dict,
        tuple) and any depth in a recursive manner.

            >>> res = Struct.flatten_uniq(obj, key="", path="", flattened=None)

        See also
        --------
        :meth:`~Struct.uniq_seq`, :meth:`~Struct.uniq_items`.
        """
        obj =  Struct.flatten(obj, key=key, path=path,
                              flattened=flattened, indexed=indexed)
        return obj if indexed is False else list(set(obj.values()))

    #/************************************************************************/
    @staticmethod
    def uniq_seq(lst, order=False):
        """

            >>> res = Struct.uniq_seq(list, order=False)

        See also
        --------
        :meth:`~Struct.flatten_uniq`, :meth:`~Struct.uniq_items`.
        """
        if order is False:
            return list(set(lst))
        else:
            # return functools.reduce(lambda l, x: l.append(x) or l if x not in l else l, lst, [])
            # return [x for i, x in enumerate(lst) if i == lst.index(x)]
            return [x for i, x in enumerate(lst) if x not in lst[:i]]# unique, ordered

    #/************************************************************************/
    @staticmethod
    def uniq_items(*arg, items={}, order=False):
        """

            >>> res = Struct.uniq_items(*arg, items={}, order=False)

        See also
        --------
        :meth:`~Struct.flatten_uniq`, :meth:`~Struct.uniq_seq`.
        """
        if len(arg) == 1:
            arg = arg[0]
        try:
            assert Type.is_sequence(items) or Type.is_mapping(items)
        except:
            raise TypeError("Wrong type for item(s)")
        if Type.is_mapping(items):
            allkvs = Struct.uniq_seq(Struct.flat(items.items()))
            allvals = Struct.uniq_seq(Struct.flat(items.values()))
        else:
            allvals = allkvs = Struct.uniq_seq(Struct.flat(items))
        try:
            assert (not Type.is_sequence(arg) and arg in allkvs)    \
                or (Type.is_sequence(arg) and all([a in allkvs for a in arg]))
        except:
            res = list(set(arg).intersection(set(allkvs)))
            try:
                assert res not in (None, [])
            except:
                raise IOError("Item(s) not recognised")
            else:
                warn("\n! Item(s) not  all recognised !")
        else:
            res = [arg,] if Type.is_string(arg) else list(arg)
        for i, a in enumerate(res):
            if a in allvals:    continue
            res.pop(i)
            try:        a = items[a]
            except:     pass
            res.insert(i, list(a)[0] if isinstance(a, (tuple, list, set)) else a)
        res = Struct.uniq_list(res, order=order)
        return res if len(res)>1 or res is None else res[0]


#==============================================================================
# Class NestedDict
#==============================================================================

class NestedDict(dict):
    """A dictionary-like structure that enables nested indexing of the dictionary
    contents and merging of multiply nested dictionaries along given dimensions.

        >>> dnest = NestedDict(*args, **kwargs)
        >>> dnest = NestedDict(mapping, **kwargs)
        >>> dnest = NestedDict(iterables, **kwargs)

    Arguments
    ---------
    mapping :
        (an)other dictionar(y)ies; optional.
    iterables :
        (an)other iterable object(s) in a form of key-value pair(s) where keys should
        be immutable; optional.

    Keyword arguments
    -----------------
    order : list
        provides the depth order of the dimensions in the output dictionary;
        default: :data:`order` is :data:`None` and is ignored and the order
        of the dimensions in the output dictionary depends on their extraction
        as (key,value) items; unless the input :data:`dict` is an instance of
        the :class:`collections.OrderedDict` class, it is highly recommended
        to use this keyword argument.
    values : list,tuple
    _nested_ : dict

    Returns
    -------
    dnest : dict
        an empty nested dictionary whose (key,value) pairs are defined and
        ordered according to the arguments :data:`dic` and :data:`order`; say
        for instance that :data:`dic = {'dim1': 0, 'dim2': [1, 2]}, then:

            * :data:`NestedDict(dic)` returns :data:`nestdic={0: {1: {}, 2: {}}}`.
            * :data:`NestedDict(dic, order=['dim2', 'dim1'])` returns :data:`nestdic={1: {0: {}}, 2: {0: {}}}`.

    Examples
    --------
    Note the initialisation that completely differs from a "normal" :obj:`dict`
    data structure:

        >>> dic = NestedDict({'a': 1, 'b': 2})
        >>> dic
            {1: {2: {}}}
        >>> dic.order
            ['a', 'b']
        >>> dic.dimensions
            OrderedDict([('a', [1]), ('b', [2])])
        >>> dic = NestedDict([('a',1),('b',2)])
        >>> dic
            {'a': {'b': {}, 2: {}}, 1: {'b': {}, 2: {}}}
        >>> dic.order
            [0, 1]
        >>> dic.dimensions

        >>> NestedDict(a=1, b=2)
            {'a': 1, 'b': 2}

    However, in addition the data structure enables nested key settings, like adding a numeric key:

        >>> dic = {'a': [1,2], 'b': [3,4]}
        >>> NestedDict(dic)
            {1: {3: {}, 4: {}}, 2: {3: {}, 4: {}}}
        >>> NestedDict(dic, order = ['b', 'a'])
            {3: {1: {}, 2: {}}, 4: {1: {}, 2: {}}}
        >>> dic = collections.OrderedDict({'b': [3,4], 'a': [1,2]})
        >>> NestedDict(dic)
            {3: {1: {}, 2: {}}, 4: {1: {}, 2: {}}}
        >>> NestedDict(dic, values=[None])
            {3: {1: None, 2: None}, 4: {1: None, 2: None}}
        >>> NestedDict(dic, values=[10,20,30,40])
            {3: {1: 10, 2: 20}, 4: {1: 30, 2: 40}}

    Note
    ----
    See also `Python` module :mod:`AttrDict` that handles complex dictionary data
    structures (source available `here <https://github.com/bcj/AttrDict>`_).

    See also
    --------
    :meth:`Type.is_mapping`.
    """

    #/************************************************************************/
    def __init__(self, *args, **kwargs):
        self.__order = []
        self.__xlen = {}
        # self.__dimensions = {}
        self.__cursor = 0
        self.__dimensions = {}
        if args in ((),({},),(None,)) and kwargs == {}:
            super(NestedDict, self).__init__({})
            return
        order = kwargs.get('order') or True
        try:
            assert order is None or isinstance(order,bool) or Type.is_sequence(order)
        except:
            raise TypeError("Wrong format/value for ORDER argument")
        dic = kwargs.pop('_nested_', {})
        try:
            assert dic in (None,{}) or args in ((),(None,))
        except:
            raise TypeError("Incompatible positional arguments with _NESTED_ keyword argument")
        if dic in (None,{}):
            try:
                dic, dimensions = self._deep_create(*args, **kwargs)
            except:
                raise IOError("Error creating nested dictionary")
        else:
            try:
                depth = max(list(self.__depth(dic).values()))
                ndim = len(order) if order is not None else depth
                dimensions = dict(zip(range(ndim), [[]]*len(range(ndim))))
            except:
                raise IOError("Error setting nested dictionary")
        super(NestedDict, self).__init__(dic)
        self.__dimensions = dimensions
        if order is not False:
            self.__order = order if order is not True else list(dimensions.keys())
        else:
            self.__order = [str(i) for i in range(len(dimensions))]
        self.__xlen = {k: len(v) if Type.is_sequence(v) else 1 for k,v in dimensions.items()}
        values = kwargs.pop('values', None)
        if values is None:
            return
        elif not Type.is_sequence(values):
            values = [values,]
        try:
            assert len(values) == 1 or len(values) == self.xlen()
        except:
            raise TypeError("Wrong format/value for VALUES argument")
        else:
            if len(values) == 1:
                values = values * self.xlen()
        try:
            self.xupdate(*zip(self.xkeys(_force_list_=True), values))
        except:
            raise IOError("Error loading dictionary values")

    #/************************************************************************/
    def __getattr__(self, attr):
        # ugly trick here...
        if attr in inspect.getmembers(self.__class__, predicate=inspect.ismethod):#analysis:ignore
            return object.__getattribute__(self, attr)
        try:
            xkeys = self.xkeys(_force_list_=True)
            xvalues = [getattr(v, attr) for v in self.xvalues(_force_list_=True)]
            # res = [getattr(v, attr) for v in self.xvalues(_force_list_=True)]
        except:
            raise AttributeError("Attribute %s not recognised" % attr)
        if len(xkeys)>1:
            try:
                cls = self.__class__
                res = cls(list(zip(xkeys, xvalues)))
            except:
                raise AttributeError("Wrong nested data structure" % attr)
        else:
            res = xvalues if xvalues in ([],[None],None) or (Type.is_sequence(xvalues) and len(xvalues)>1) \
            else xvalues[0]
        return res

    #/************************************************************************/
    def __copy__(self):
        cls = self.__class__
        result = cls.__new__(cls)
        result.__dict__.update(self.__dict__)
        return result

    #/************************************************************************/
    def __deepcopy__(self, memo):
        cls = self.__class__
        # return cls(copy.deepcopy(dict(self)), order=self.order)
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            setattr(result, k, copy.deepcopy(v, memo))
        return result

    #/************************************************************************/
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            try:
                assert self.order == other.order
                #assert self.xkeys() == other.xkeys()
                #assert self.xvalues() == other.xvalues()
                assert self.__dict__ == other.__dict__
            except:
                return False
            else:
                return True
        else:
            return False

    #/************************************************************************/
    def __iter__(self):
        return self

    #/************************************************************************/
    def __next__(self):
        if self.__cursor >= self.xlen():
            self.__cursor = 0
            raise StopIteration
        _next = list(self.xvalues())[self.__cursor]
        self.__cursor += 1
        return _next

    #/************************************************************************/
    def __repr__(self):
        rep = super(NestedDict, self).__repr__()
        try:
            assert False
            return rep.replace("'", "\"") # does actually make no sense
        except:
            return rep

    #/************************************************************************/
    def __str__(self):
        if self.xlen() == 1:
            val = self.xvalues(**self.dimensions)
        if self.xlen() > 1 or val in (None, [], {},' '):
            return super(NestedDict, self).__str__()
        else:
            return "%s" % val

    #/************************************************************************/
    @property
    def order(self):
        # return list(self.__dimensions.keys())
        return self.__order

    @property
    def dimensions(self):
        """Dimensions property (:data:`getter`/:data:`setter`) of a :class:`NestedDict`
        instance.
        """
        #ndim = len(self.order)
        #dic = dict(zip(range(ndim),[[]]*ndim))
        #def recurse(items, depth):
        #    for k, v in items:
        #        if dic[depth] in ([],None):     dic[depth] = [k,]
        #        else:                           dic[depth].append(k)
        #        dic[depth] = list(set(dic[depth]))
        #        if Type.is_mapping(v):
        #            recurse(v.items(), depth+1)
        #recurse(self.items(), 0)
        #return collections.OrderedDict((self.order[k],v) for k,v in list(dic.items()))
        return OrderedDict({k : v[0] if Type.is_sequence(v) and len(v) == 1 else v    \
                                        for k,v in self.__dimensions.items()})
    @dimensions.setter
    def dimensions(self, dimensions):
        if not (dimensions is None or Type.is_mapping(dimensions)):
            raise TypeError('wrong type for DIMENSIONS parameter')
        self.__dimensions = dimensions

    @classmethod
    @deprecated('use depth property instead', run=True)
    def __depth(self, dic):
        depth = {}
        def _recurse(v, i):
            if Type.is_mapping(v):
                yield from _recurse(v.values(), i+1)
            else:
                yield i
        depth.update({k: list(_recurse(v, 1))[0] for k, v in dic.items()})
        return depth

    @property
    def depth(self):
        # return len(self.dimensions) #-1
        return len(self.order) #-1

    #/************************************************************************/
    @classmethod
    def _deep_create(cls, *args, **kwargs):
        """Initialise a deeply nested dictionary from input (dimension,key) pairs
        parsed as dictionary or list, or (key,value) pairs parsed as a list of
        items.

            >>> new_dnest, dimensions = NestedDict._deep_create(*args, **kwargs)

        Arguments
        ---------

        Keyword arguments
        -----------------

        Returns
        -------
        new_dnest : dict
        dim : collections.OrderedDict

        Examples
        --------
        it is useful to initialise a data structure as an empty nested dictionary:

            >>> NestedDict._deep_create(a=1, b=2)
                ({1: {2: {}}},
                OrderedDict([('a', 1), ('b', 2)]))
            >>> d = {'a': [1,2], 'b': [3,4,5]}
            >>> NestedDict._deep_create(d)
                ({1: {3: {}, 4: {}, 5: {}}, 2: {3: {}, 4: {}, 5: {}}},
                 OrderedDict([('a', [1, 2]), ('b', [3, 4, 5])]))
            >>> NestedDict._deep_create(d, order=['b','a'])
                ({3: {1: {}, 2: {}}, 4: {1: {}, 2: {}}, 5: {1: {}, 2: {}}},
                 OrderedDict([('b', [3, 4, 5]), ('a', [1, 2])]))
            >>> l1 = (('a',[1,2]), ('b',[3,4,5]))
            >>> NestedDict._deep_create(l1)
                ({1: {3: {}, 4: {}, 5: {}}, 2: {3: {}, 4: {}, 5: {}}},
                 OrderedDict([('a', [1, 2]), ('b', [3, 4, 5])]))
            >>> NestedDict._deep_create(l1, order=['b','a'])
                ({3: {1: {}, 2: {}}, 4: {1: {}, 2: {}}, 5: {1: {}, 2: {}}},
                 OrderedDict([('b', [3, 4, 5]), ('a', [1, 2])]))
            >>> l2 = ([1,2], [3,4,5])
            >>> NestedDict._deep_create(l2)
                ({1: {3: {}, 4: {}, 5: {}}, 2: {3: {}, 4: {}, 5: {}}},
                 OrderedDict([(0, [1, 2]), (1, [3, 4, 5])]))

        while it is also possible to fill it in with values:

            >>> items = [(('a',1,'x'), 1), (('a',2,'y'), 2),
                         (('b',1,'y'), 3), (('b',2,'z'), 4),
                         (('b',1,'x'), 5)]
            >>> NestedDict._deep_create(items)
                ({'a': {1: {'x': 1}, 2: {'y': 2}}, 'b': {1: {'x': 5, 'y': 3}, 2: {'z': 4}}},
                 OrderedDict([(0, ['a', 'b']), (1, [1, 2]), (2, ['y', 'z', 'x'])])

        See also
        --------
        :meth:`~NestedDict._deep_merge`, :meth:`~NestedDict._deep_insert`.
        """
        order = kwargs.pop('order', None)
        try:
            assert order is None or isinstance(order, bool) or Type.is_sequence(order)
        except:
            raise TypeError("Wrong type/value for ORDER keyword argument")
        if args in ((),(None,)):
            if kwargs == {}:
                return OrderedDict()
            else:
                args = kwargs.items()
        try:
            assert (len(args)==1 and Type.is_mapping(args[0]))          \
                or all([Type.is_sequence(a) for a in args])
        except:
            raise TypeError("Wrong format for input arguments")
        else:
            if len(args)==1: # and, obviously: Type.is_mapping(args[0]))
                args = args[0]
        try:
            assert not Type.is_mapping(args) or all([Type.is_sequence(v) for v in args.values()])
        except:
            raise TypeError("Wrong format for input nesting dictionary - impossible to resolve dimension ambiguity without []")
        #if Type.is_mapping(args):
        #    if order is True:
        #        order =  list(args.keys())
        #    if order is not None:
        #        args = sorted(args.items(), key = lambda t: order.index(t[0]))
        #    args = OrderedDict(args)
        #    if order is None and order is not False: # that should actually never happen at this stage
        #        order =  list(args.keys())
        #    [args.update({k: [v,] for k,v in args.items() if not Type.is_sequence(v)})]
        #    value = {} # None
        #    dimensions = OrderedDict(dict(zip(order,[None]*len(order))))
        #    try:
        #        for attr in order[::-1]:
        #            argattr = args[attr]
        #            if type(argattr)==tuple:    argattr = list(argattr)
        #            dic = {a: copy.deepcopy(value) for a in argattr}
        #            dimensions.update({attr: argattr.copy()})
        #            value = dic
        #    except TypeError:
        #        raise IOError("Input dictionary argument not supported")
        #elif all([Type.is_sequence(a[0]) for a in args]):
        #    if order is None or isinstance(order,bool):
        #        order = list(range(len(args[0][0])))
        #    attrs = [list(set(a[0][i] for a in args)) for i in range(len(order))]
        #    dimensions = dict(zip(order, attrs))
        #    if order is not False:
        #        dimensions = OrderedDict(dimensions)
        #    dic = {}
        #    try:
        #        for item in args:
        #            d = {item[0][-1]: item[1]}
        #            for key in item[0][:-1][::-1]:
        #                d = {key: d.copy()}
        #            cls._deep_merge(dic, d, in_place=True)
        #    except TypeError:
        #        raise IOError("Input item arguments not supported")
        #try:
        #    assert dic
        #except:
        #    dic, dimensions = {}, {}
        #return dic, dimensions
        if Type.is_mapping(args):
            args = list(args.items())
        if not all([len(a) == 2 for a in args]):
            args = [(str(i),a) for i,a in enumerate(args)]
        if all([Type.is_sequence(a[0]) for a in args]):
            if order is None or isinstance(order,bool):
                order = [str(i) for i in range(len(args[0][0]))]
            dimensions = OrderedDict(zip(order,
                                         [list(set(v)) for v in zip(*[a[0] for a in args])]))
        else:
            dimensions = OrderedDict(args)
            if order is None:
                order = [a[0] for a in args]
            try:
                keys = list(product(*[item[1] for item in args]))
            except:
                try:
                    keys = list(product(*[[item[1]] for item in args]))
                except:
                    keys = list(product(*args[1]))
            args = list(zip(keys, [{}] * len(keys)))
        return cls._deep_insert({}, args), dimensions

    #/************************************************************************/
    @classmethod
    def _deep_merge(cls, *dics, **kwargs):
        """Deep merge (recursively) an arbitrary number of (nested or not) dictionaries.

            >>> new_dnest = NestedDict._deep_merge(*dics, **kwargs)

        Arguments
        ---------
        dics : dict
            an arbitrary number of (possibly nested) dictionaries.

        Keyword arguments
        -----------------
        in_place : bool
            flag set to update the first dictionary from the input list :data:`dicts`
            of dictionaries; default: :data:`in_place=False`.

        Returns
        -------
        new_dnest : dict
            say that only two dictionaries are parsed, :data:`d1` and :data:`d2`
            through :data:`dics` (in this order); first, :data:`d1` is "deep"-copied
            into :data:`new_dnest` (we consider the default case :data:`in_place=False`),
            then for each :data:`k,v` in :data:`d2`:

                * if :data:`k` doesn't exist in :data:`new_dnest`, it is deep copied
                  from :data:`d2` into :data:`new_dic`;

            otherwise:

                * if :data:`v` is a list, :data:`new_dnest[k]` is extended with :data:`d2[k]`,
                * if :data:`v` is a set, :data:`new_dnest[k]` is updated with :data:`v`,
                * if :data:`v` is a dict, it is recursively "deep"-updated,

        Examples
        --------
        The method can be used to deep-merge dictionaries storing many different
        data structures:

            >>> d1 = {1: 2, 3: 4, 10: 11}
            >>> d2 = {1: 6, 3: 7}
            >>> NestedDict._deep_merge(d1, d2)
                {1: [2, 6], 3: [4, 7], 10: 11}
            >>> d1 = {1: 2, 3: {4: {5:6, 7:8}, 9:10}, 11: 12}
            >>> d2 = {1: -2, 3: {4: {-5:{-6:-7}}}, 8:-9}
            >>> NestedDict._deep_merge(d1, d2)
                {1: [2, -2], 3: {4: {-5: {-6: -7}, 5: 6, 7: 8}, 9: 10}, 8: -9, 11: 12}
            >>> d1 = {'a': {'b': {'x': '1', 'y': '2'}}}
            >>> d2 = {'a': {'c': {'gg': {'m': '3'},'xx': '4'}}}
            >>> NestedDict._deep_merge(d1, d2, in_place = True)
            >>> print(d1)
                {'a': {'b': {'x': '1','y': '2'}, 'c': {'gg': {'m': '3'}, 'xx': '4'}}}

        See also
        --------
        :meth:`~NestedDict._deepcreate`, :meth:`~NestedDict._deep_insert`,
        :meth:`~NestedDict.xupdate`.
        """
        # Note: This code is inspired by F.Boender's original source code available at
        # `this address <https://www.electricmonk.nl/log/2017/05/07/merging-two-python-dictionaries-by-deep-updating/>`_
        # under a *MIT* license.
        in_place = kwargs.pop('in_place', False)
        try:
            assert isinstance(in_place, bool)
        except:
            raise TypeError("Wrong format/value for IN_PLACE keyword argument")
        try:
            assert all([Type.is_mapping(dic) for dic in dics])
        except:
            raise TypeError("Wrong format/value for input arguments")
        def _recurse(target, src):
            for k, v in src.items():
                #if Type.is_sequence(v):
                #    if k in target:         target[k].extend(v)
                #    else:                   target[k] = copy.deepcopy(v)
                #elif Type.is_mapping(v):
                #    if k in target:         recurse(target[k], v)
                #    else:                   target[k] = copy.deepcopy(v)
                #elif type(v) == set:
                #    if k in target:         target[k].update(v.copy())
                #    else:                   target[k] = v.copy()
                #else:
                #    if k in target:
                #        if type(target[k]) == tuple:        target.update({k: list(target[k])})
                #        elif not type(target[k]) == list:   target[k] = [target[k],]
                #        target[k].append(v)
                #    else:
                #        target[k] = copy.copy(v)
                if k in target:
                    if type(v) != type(target[k]):
                        if type(target[k]) == tuple:
                            target.update({k: list(target[k])})
                        elif type(target[k]) != list:
                            target[k] = [target[k],]
                    elif not(Type.is_mapping(target[k]) or Type.is_sequence(target[k])):
                        target[k] = [target[k],]
                #elif type(v)!=type(target[k]):              target[k] = []
                if Type.is_sequence(v):
                    if k in target:
                        try:
                            target[k].extend(v)
                        except:
                            target[k] = target[k] + v
                    else:
                        target[k] = deepcopy(v)
                elif Type.is_mapping(v):
                    if k in target:
                        _recurse(target[k], v)
                    else:
                        target[k] = deepcopy(v)
                elif type(v) == set:
                    if k in target:
                        try:
                            target[k].update(v.copy())
                        except:
                            target[k].append(v)
                    else:
                        target[k] = v.copy()
                else:
                    if k in target:
                        target[k].append(v)
                    else:
                        try:
                           target[k] = copy(v)
                        except:
                            target[k] = v
        def _reduce(*dics):
            if in_place is False:
                dd = deepcopy(dics[0])
                reduce(_recurse, (dd,) + dics[1:]) # this is: functools.reduce here
            else:
                dd = None
                reduce(_recurse, dics) # ibid: functools.reduce here
            return dd # or dicts[0]
        return _reduce(*dics)

    #/************************************************************************/
    @classmethod
    def _deep_insert(cls, dic, *items, **kwargs):
        """Deep merge (recursively) a (nested or not) dictionary with items.

            >>> new_dnest = NestedDict._deep_insert(dic, *items, **kwargs)

        Arguments
        ---------
        dic : dict
            a (possibly nested) dictionary.
        items : tuple,list
            items of the form :literal:`(key,value)` pairs

        Keyword arguments
        -----------------
        in_place : bool
            flag set to update the first dictionary from the input list :data:`dicts`
            of dictionaries; default: :data:`in_place=False`.

        Returns
        -------
        new_dnest : dict

        Examples
        --------
        First simple examples:

            >>> NestedDict._deep_insert({}, (1,2))
                {1: 2}
            >>> NestedDict._deep_insert({}, (1,2), (3,4))
                {1: 2, 3: 4}
            >>> NestedDict._deep_insert({}, ((1,2),(3,4)))
                {1: {2: (3, 4)}}
            >>> NestedDict._deep_insert({}, ((1, 2), 3), ((4, 5), 6))
                {1: {2: 3}, 4: {5: 6}}

        Note the various way/syntax items can be parsed, and the different possible
        outputs:

            >>> NestedDict._deep_insert({}, (1,2), (1,3) )
                {1: 3} # the last inserted
            >>> NestedDict._deep_insert({}, (1,2), (3,(4,5)) )
                {1: 2, 3: (4, 5)}
            >>> NestedDict._deep_insert({}, (1,2), ((3,4),5) )
                {1: 2, 3: {4: 5}}
            >>> NestedDict._deep_insert({}, ((1,2)), (3,(4,5)) )
                {1: 2, 3: (4, 5)}
            >>> NestedDict._deep_insert({}, (((1,2)), (3,(4,5))) )
                {1: {2: (3, (4, 5))}}
            >>> NestedDict._deep_insert({}, (((1,2)), (3,4)), (5,6))
                {1: {2: (3, 4)}, 5: 6}
            >>> NestedDict._deep_insert({}, (1,(2,(3,4),(5,6),7)) )
                {1: (2, (3, 4), (5, 6), 7)}

        The method can be used to deep-insert items into a (possibly nested) dictionary
        data structure:

            >>> d = {1: 6, 3: 7, 10: 11}
            >>> items = ((1,2), (3,4))
            >>> NestedDict._deep_insert(d, items)
                {1: {2: (3, 4)}, 3: 7, 10: 11}
            >>> NestedDict._deep_insert(d, *items)
                1: 2, 3: 4, 10: 11}
            >>> items2 = ((1,2), ((3,4,5),6), ((3,4,7),8), ((3,4,9),10), (11,12))
            >>> d2 = {1: -2, 3: {4: {-5:{-6:-7}}}, 8:-9}
            >>> NestedDict._deep_insert(d2, *items2)
                {1: 2, 3: {4: {-5: {-6: -7}, 5: 6, 7: 8, 9: 10}}, 8: -9, 11: 12}

        The keyword argument :data:`in_place` can be used for in-place update:

            >>> items = ((1,2), (3,(4,5)))
            >>> d = {}
            >>> NestedDict._deep_insert(d, items, in_place=True)
            >>> print(d)
                {1: {2: (3, (4, 5))}}
            >>> d = {}
            >>> NestedDict._deep_insert(d, *items, in_place=True)
            >>> print(d)
                {1: 2, 3: (4, 5)}
            >>> items = [(('a',1,'x'), 1), (('a',2,'y'), 2),
                         (('b',1,'y'), 3), (('b',2,'z'), 4),
                         (('b',1,'x'), 5)]
            >>> d = {}
            >>> NestedDict._deep_insert(d, items, in_place=True)
            >>> print(d)
                {'a': {1: {'x': 1}, 2: {'y': 2}}, 'b': {1: {'x': 5, 'y': 3}, 2: {'z': 4}}}

        See also
        --------
        :meth:`~NestedDict._deepcreate`, :meth:`~NestedDict._deep_merge`,
        :meth:`~NestedDict.xupdate`.
        """
        in_place = kwargs.pop('in_place', False)
        try:
            assert isinstance(in_place, bool)
        except:
            raise TypeError("Wrong format/value for IN_PLACE keyword argument")
        try:
            assert Type.is_mapping(dic) and all([Type.is_sequence(item) for item in items])
        except:
            raise TypeError("Wrong format/value for input arguments")
        # we speculate a lot here... probably not the best way...
        if len(items) == 1:
            if not(Type.is_sequence(items[0]) and len(items[0]) == 2)     \
                    or all([Type.is_sequence(i) and Type.is_sequence(i[0]) for i in items[0]]):
                items = items[0]
            else:
                pass
        try:
            assert len(items) == 2 or all([len(item) == 2 for item in items])
        except:
            raise TypeError("Wrong format/value for item arguments")
        def _recurse(target, src):
            key, v = src
            k = key[0] if Type.is_sequence(key) else key
            if Type.is_sequence(key) and len(key)>1:
                if k not in target:
                    target[k] = None
                if not Type.is_mapping(target[k]):
                    #if type(target[k]) == tuple:        target.update({k: list(target[k])})
                    #elif not type(target[k]) == list:   target[k] = [target[k],]
                    temp = {}
                    _recurse(temp, (key[1:],v))
                    target[k] = temp
                else:
                    _recurse(target[k], (key[1:],v))
            else:
                #if k in target:
                #    if type(v)!=type(target[k]):
                #        if type(target[k]) == tuple:
                #            target.update({k: list(target[k])})
                #        elif not type(target[k]) == list:
                #            target[k] = [target[k],]
                #    elif not(Type.is_mapping(target[k]) or Type.is_sequence(target[k])):
                #        target[k] = [target[k],]
                ##elif type(v)!=type(target[k]):              target[k] = []
                if Type.is_sequence(v):
                    target[k] = v #deepcopy(v)
                elif Type.is_mapping(v):
                    target[k] = deepcopy(v)
                elif type(v) == set:
                    target[k] = v.copy()
                else:
                    try:
                       target[k] = copy(v)
                    except:
                        target[k] = v
        dd = None
        if in_place is False:
            dd = deepcopy(dic)
        for item in items:
            _recurse(dd if dd is not None else dic, item)
        return dd

    #/************************************************************************/
    def _deep_search(self, attr, *arg, **kwargs):
        """
        """
        try:
            assert attr in ('get', 'keys', 'dimensions', 'values')
        except:
            raise IOError("Wrong parsed attribute")
        try:
            assert self.order is not None
        except:
            raise IOError("Dimensions not supported with unordered dictionary")
        try:
            assert set(kwargs.keys()).difference(set(self.order)) == set()
        except:
            raise IOError("Parsed dimensions are not recognised")
        order = self.order.copy()
        if attr == 'keys':
            if arg not in ((), ([],), (None,)):
                dic = dict(self.items())
                for dim in order:
                    if dim != arg[0]:       dic = list(dic.values())[0]
                    else:                   break
                return list(dic.keys())
            else:
                pass
        elif attr == 'get':
            while True:
                if order[-1] not in kwargs.keys():
                    order.pop(-1)
                else:
                    break
        else:
            pass
        val = [self.copy()]
        for i, dim in enumerate(order):
            val = Struct.flatten_seq([list(v.items()) for v in val])
            if dim in kwargs.keys():
                keys = kwargs.get(dim)
                if not Type.is_sequence(keys):
                    keys = [keys,]
                [val.remove(v) for v in list(val) if v[0] not in keys]
            if attr == 'keys' and i == len(order)-1:
                val = [v[0] for v in val]
            else:
                val = [v[1] for v in val]
        return val[0] if Type.is_sequence(val) and len(val)==1 else val

    #/************************************************************************/
    @classmethod
    @deprecated('use generic method _deep_merge instead', run=True)
    def __nest_merge(cls, *dicts):
        #ignore-doc
        """Recursively merge an arbitrary number of nested dictionaries.

            >>> new_dnest = NestedDict.__nest_merge(*dicts)

        Arguments
        ---------
        dicts : dict
            an arbitrary number of (possibly nested) dictionaries.

        Examples
        --------

            >>> d1 = {'a': {'b': {'x': '1', 'y': '2'}}}
            >>> d2 = {'a': {'c': {'gg': {'m': '3'},'xx': '4'}}}
            >>> Type.__nest_merge(d1, d2)
                {'a': {'b': {'x': '1','y': '2'}, 'c': {'gg': {'m': '3'}, 'xx': '4'}}}
        """
        keys = set(k for d in dicts for k in d)
        def _vals(key):
            withkey = (d for d in dicts if key in d.keys())
            return [d[key] for d in withkey]
        def _recurse(*values):
            if Type.is_mapping(values[0]):
                return cls.__nest_merge(*values)
            if len(values) == 1:
                return values[0]
            raise IOError("Multiple non-dictionary values for a key")
        return dict((key, _recurse(*_vals(key))) for key in keys)


    #/************************************************************************/
    @classmethod
    def _deep_reorder(cls, dic, **kwargs):
        """Reorder a deeply nested dictionary.

            >>> new_dnest = NestedDict._deep_reorder(dic, **kwargs)

        Example
        -------

            >>> d = {'a': [1,2], 'b': [3,4,5]}
            >>> r = NestedDict(d, values = list(range(6)))
            >>> print(r)
                {1: {3: 0, 4: 1, 5: 2}, 2: {3: 3, 4: 4, 5: 5}}
            >>> NestedDict._deep_reorder(r, order= ['b', 'a'])
                {3: {1: 0, 2: 3}, 4: {1: 1, 2: 4}, 5: {1: 2, 2: 5}}
            >>> NestedDict._deep_reorder(r, order= ['b', 'a'], in_place=True)
            >>> print(r)
                {3: {1: 0, 2: 3}, 4: {1: 1, 2: 4}, 5: {1: 2, 2: 5}}
        """
        in_place = kwargs.pop('in_place', False)
        try:
            assert isinstance(in_place, bool)
        except:
            raise TypeError("Wrong format/value for IN_PLACE keyword argument")
        try:
            assert isinstance(dic, Mapping)
        except:
            raise TypeError("Wrong type/value for input argument")
        order = kwargs.pop('order', None)
        try:
            assert order is None or isinstance(order, bool) or Type.is_sequence(order)
        except:
            raise TypeError("Wrong type/value for ORDER keyword argument")
        else:
            if order is None:
                # Verbose('nothing to do')
                return dic
        try:
            inorder = getattr(dic, 'order')
        except AttributeError:
            inorder = list(dic.keys())
        try:
            assert set(order) == set(inorder) # assert set(order).difference(set(inorder)) == set()
        except:
            raise IOError("Keys parsed as ORDER keyword argument not present in input dictionary")
        else:
            if order == inorder:
                # Verbose('new order key equal to the original one')
                return dic
        xkeys, xvalues = dic.xkeys(), dic.xvalues()
        newxkeys = [sorted(key, key=lambda x: order.index(inorder[key.index(x)])) for key in xkeys]
        # new_xitems = [(sorted(item[0], key=lambda t: order.index(inorder[item[0].index(t)])), item[1]) for item in xitems]
        newxitems = zip(newxkeys, xvalues)
        if in_place is True:
            # dic = NestedDict(newxitems, order = order)
            [dic.pop(k) for k in list(dic.keys())]
            # [dic.xpop(k) for k in xkeys]
            dic.xupdate(list(newxitems))
            try:
                dic.order = order # let's make sure this works with any derived class
            except:
                try:
                    setattr(dic, 'NestedDict__order', order) # let's make sure this works with any derived class
                except:
                    pass
            return
        else:
            return cls(list(newxitems), order = order)

    #/************************************************************************/
    @classmethod
    def _deepest(cls, dic, item='values'):
        """Extract the deepest keys, values or both (items) from a nested dictionary.

            >>> l = NestedDict._deepest(dic, item='values')

        Arguments
        ---------
        dic : dict
            a (possibly nested) dictionary.

        Keyword arguments
        -----------------
        item : str
            flag used to define the deepest items to extract from the input dictionary
            :data:`dic`; it can be :literal:`keys`, :literal:`values` or :literal:`items`
            to represent both; default is :literal:`values`, hence the deepest values
            are extracted.

        Returns
        -------
        l : list
            contains the deepest keys, values or items extracted from :data:`dic`,
            depending on the keyword argument :data:`item`.

        Examples
        --------

            >>> d = {4:1, 6:2, 7:{8:3, 9:4, 5:{10:5}, 2:6, 6:{2:7, 1:8}}}
            >>> NestedDict._deepest(d)
                [1, 2, 3, 4, 5, 6, 7, 8]
            >>> NestedDict._deepest(d, item='keys')
                [4, 6, 8, 9, 10, 2, 2, 1]
            >>> NestedDict._deepest(d, item='items')
                [(4, 1), (6, 2), (8, 3), (9, 4), (10, 5), (2, 6), (2, 7), (1, 8)]
        """
        try:
            assert Type.is_mapping(dic)
        except:
            raise TypeError("Wrong format/value for input argument")
        try:
            assert item in (None,'') or item in ('items','keys','values')
        except:
            raise TypeError("Wrong format/value for ITEM argument")
        if isinstance(dic, cls):
            depth = dic.depth
        else:
            depth = -1
        def _recurse(d, inc):
            for k, v in d.items():
                if depth>0 and inc<depth and Type.is_mapping(v) and v!={}:
                    yield from _recurse(v, inc+1)
                else:
                    if item == 'items':           yield (k, v)
                    elif item == 'keys':          yield k
                    elif item == 'values':        yield v
        return list(_recurse(dic, 1))

    #/************************************************************************/
    def xget(self, *args, **kwargs):
        """Retrieve value from deep nested dictionary.

            >>> val = dnest.xget(*args, **kwargs)

        Examples
        --------
        """
        __force_list = kwargs.pop('_force_list_', False)
        if args in ((), (None,)) and kwargs == {}:
            return self._deepest(self, item='values')
        if args != ():
            if len(args) > 1 or Type.is_sequence(args[0]):
                if len(args) == 1:    args = args[0]
                kwargs.update({k: v for k,v in zip(self.order, args)})
        if kwargs == {}:
            return super(NestedDict, self).get(*args)
        # let us check the complexive lenght of the dimensions that have been left out
        xlen = self.xlen(list(set(self.order).difference(set(kwargs))))
        if Type.is_mapping(xlen):
            xlen = reduce(lambda x, y: x*y, xlen.values())
        def _deep_get(dic):
            rdic = deepcopy(dic)
            while Type.is_mapping(rdic):
                rdic = list(rdic.values())[0]
            return rdic
        res = self._deep_search('get', *args, **kwargs)
        return res if __force_list is True or res is None or xlen>1 else _deep_get(res)

    #/************************************************************************/
    def pop(self, *args):
        """
        """
        if args in ((),(None,)):
            raise TypeError('pop expected at least 1 arguments, got 0')
        key = args[0]
        dimensions, order = self.dimensions, self.order
        order = order or [str(i) for i in range(len(dimensions))]
        try:
            dimensions[order[0]].remove(key)
        except:
            dimensions[order[0]] = set([dimensions[order[0]]]).difference(set([key]))
        #.update({order[0]: list(dimensions[order[0]]).remove(key)})
        if dimensions[order[0]] == []:
            dimensions = OrderedDict()
        super(NestedDict,self).pop(*args)

    #/************************************************************************/
    def xpop(self, *arg):
        """Pop values out of deep nested dictionary.

            >>> dnest.xpop(*arg)

        Examples
        --------

            >>> d = {'a': [1,2], 'b': [3,4,5]}
            >>> r = NestedDict(d)
            >>> print(r)
                {1: {3: {}, 4: {}, 5: {}}, 2: {3: {}, 4: {}, 5: {}}}
            >>> r.xpop([1,3])
                {}
            >>> print(r)
                {1: {4: {}, 5: {}}, 2: {3: {}, 4: {}, 5: {}}}
        """
        try:
            assert len(arg)==1 and (Type.is_numeric(arg[0]) or Type.is_mapping(arg[0]))
        except:
            raise TypeError("Wrong format/value for ITEM to delete")
        else:
            arg = arg[0]
            if not Type.is_sequence(arg):
                arg = [arg,]
        d = self
        try:
            for i, item in enumerate(arg):
                if i<len(arg)-1:     d = d[item]
        except KeyError:
            raise KeyError("Deep keys not known")
        dimensions, order = self.dimensions, self.order
        if dimensions != {}:
            order = order or [str(i) for i in range(len(dimensions))]
            for i, item in enumerate(arg[::-1]):
                if dimensions[order[i]] == [arg]:
                    dimensions.pop(arg)
                    order.remove(arg)
                else:
                    break
        return d.pop(item)

    #/************************************************************************/
    def update(self, *arg, **kwargs):
        newkeys = []
        if arg not in ((),(None,)):
            newkeys += list(arg[0].keys())
        if kwargs != {}:
            newkeys += list(kwargs.keys())
        dimensions, order = self.dimensions, self.order
        order = order or [str(i) for i in range(len(dimensions))]
        try:
            assert set(newkeys).difference(set(dimensions[order[0]])) == set()
        except:
            self.dimensions.update({order[0]: list(set(dimensions[order[0]] + newkeys))})
        super(NestedDict,self).update(*arg, **kwargs)

    #/************************************************************************/
    def xupdate(self, *arg, **kwargs):
        """Update a deep nested dictionary.

            >>> dnest.xupdate(*arg, **kwargs)

        Examples
        --------

            >>> d = {'a': [1,2], 'b': [3,4,5]}
            >>> r = NestedDict(d)
            >>> print(r)
                {1: {3: {}, 4: {}, 5: {}}, 2: {3: {}, 4: {}, 5: {}}}
            >>> r.xupdate(((1,3),5))
            >>> print(r)
                {1: {3: 5, 4: {}, 5: {}}, 2: {3: {}, 4: {}, 5: {}}}
            >>> r.xupdate(((1,4),10), ((2,4),15))
            >>> print(r)
                {1: {3: 5, 4: 10, 5: {}}, 2: {3: {}, 4: 15, 5: {}}}
            >>> r.xupdate(20, a=2, b=3)
            >>> print(r)
                {1: {3: 5, 4: 10, 5: {}}, 2: {3: 20, 4: 15, 5: {}}}

            >>> d = NestedDict()
            >>> items = ((1,2), (3,(4,5)))
            >>> d.xupdate(items)
            >>> print(d)
                {1: 2, 3: (4, 5)}
            >>> d = NestedDict()
            >>> items = [(('a',1,'x'), 1), (('a',2,'y'), 2),
                        (('b',1,'y'), 3), (('b',2,'z'), 4),
                        (('b',1,'x'), 5)]
            >>> d.xupdate(items)
            >>> print(d)
                {'a': {1: {'x': 1}, 2: {'y': 2}}, 'b': {1: {'x': 5, 'y': 3}, 2: {'z': 4}}}

        """
        if arg in((),(None,)) and kwargs == {}:
            return
        try:
            len(arg) == 1 or len(arg)==2
        except:
            raise TypeError("Wrong type/value for input argument")
        try:
            assert kwargs == {} or not Type.is_mapping(arg)
        except:
            raise IOError("No keyword argument requested with input dictionary argument")
        try:
            assert kwargs != {} or Type.is_sequence(arg)
        except:
            raise IOError("Items and keyword arguments incompatible when updating")
        #if kwargs == {}:
        #    try:
        #        xkeys = [a[0] for a in arg]
        #        xvalues = [a[1] for a in arg]
        #    except:
        #        xkeys, xvalues = arg
        #    else:
        #        if len(xkeys)==1:
        #            xkeys, xvalues = xkeys[0], xvalues[0]
        #else:
        #    kwargs.update({Parser.KW_FORCE_LIST: True})
        #    xkeys = self.xkeys(**kwargs)
        #    xvalues = arg
        #if not Type.is_sequence(xvalues):
        #    xkeys, xvalues = [xkeys,], [xvalues,]
        #try:
        #    assert (len(xvalues)==1 or len(xvalues)==len(xkeys))            \
        #        and all([len(k)==len(self.order) for k in xkeys])
        #except:
        #    raise Error('wrong number of assignments in dictionary')
        #else:
        #    if len(xvalues)==1 and len(xkeys)>1:
        #        xvalues = xvalues * len(xkeys)
        #for i, xk in enumerate(xkeys):
        #    rdic = self
        #    try:
        #        for j, x in enumerate(xk):
        #            if j<len(xk)-1:     rdic = rdic[x]
        #    except:
        #        raise Error('key %s not found' % x)
        #    else:
        #        rdic.update({x: xvalues[i]})
        dimensions, order= self.dimensions.copy(), self.order
        if kwargs != {}:
            kwargs.update({'_force_list_': True})
            arg = list(zip(self.xkeys(**kwargs),arg))
        if Type.is_sequence(arg):
            if len(arg)==1:
                arg = arg[0]
            try:
                keys = zip(*[a[0] for a in arg])
            except:
                try:
                    keys = [[a[0]] for a in arg]
                except:
                    keys = arg[0]
            else:
                keys = [list(set(k)) for k in keys]
            if order is None or dimensions == {}:
                dimensions = OrderedDict([(str(i),k) for i,k in enumerate(keys)])
            else:
                dimensions = OrderedDict(zip(dimensions.keys(),
                                             list(dimensions.values()) + list(keys)))
            self._deep_insert(self, arg, in_place=True)
        elif Type.is_mapping(arg):
            if isinstance(arg,self.__class__):
                [dimensions.update({k: dimensions.get(k,[])+v}) for k,v in arg.items()]
            # elif isinstance(arg,(dict,OrderedDict)): pass
            self._deep_merge(self, arg, in_place=True)
        self.dimensions = dimensions
        return

    #/************************************************************************/
    def keys(self, *arg, **kwargs):
        """Retrieve deepest (outmost) keys from a nested dictionary.

            >>> keys = dnest.keys(**kwargs)
        """
        try:
            assert arg in ((),([],),(None,)) or kwargs == {}
        except:
            raise TypeError("Both argument or keyword arguments cannot be accepted simultaneously")
        if arg in ((), ([],), (None,)) and kwargs == {}:
            return super(NestedDict, self).keys()
        else:
            return self._deep_search('keys', *arg, **kwargs)

    #/************************************************************************/
    def xkeys(self, **kwargs):
        """Retrieve composed nested keys from a nested dictionary.

            >>> keys = dnest.xkeys(**kwargs)

        Examples
        --------

            >>> dic = {'a': [1,2], 'b': [3,4,5], 'c':[6,7,8,9]}
            >>> res = NestedDict(dic, order = ['b', 'c', 'a'])
            >>> res.xkeys()
                [(3, 6, 1), (3, 6, 2), (3, 7, 1), (3, 7, 2), (3, 8, 1), (3, 8, 2), (3, 9, 1), (3, 9, 2),
                 (4, 6, 1), (4, 6, 2), (4, 7, 1), (4, 7, 2), (4, 8, 1), (4, 8, 2), (4, 9, 1), (4, 9, 2),
                 (5, 6, 1), (5, 6, 2), (5, 7, 1), (5, 7, 2), (5, 8, 1), (5, 8, 2), (5, 9, 1), (5, 9, 2)]
            >>> res.xkeys(c=7)
                [(3, 7, 1), (3, 7, 2), (4, 7, 1), (4, 7, 2), (5, 7, 1), (5, 7, 2)]
            >>> res.xkeys(c=7, a=2)
                [(3, 7, 2), (4, 7, 2), (5, 7, 2)]
        """
        #if kwargs=={}:
        #    return self._deepest(self, item='keys')
        __force_list = kwargs.pop('_force_list_', False)
        try:
            assert set(kwargs.keys()).difference(set(self.order)) == set()
        except:
            raise IOError("Parsed dimensions are not recognised")
        dimensions = [[dim] if not Type.is_sequence(dim) else dim
                      for dim in [self.dimensions[k] for k in self.order]]
        xkeys = list(product(*dimensions))
        if xkeys in ([], [None,]):
            return []
        if kwargs != {}:
            for i, dim in enumerate(self.order):
                if dim in kwargs.keys():
                    keys = kwargs.get(dim)
                    if not Type.is_sequence(keys):
                        keys = [keys,]
                    [xkeys.remove(k) for k in list(xkeys) if k[i] not in keys]
        return xkeys if __force_list is True or xkeys in ([],None) or len(xkeys)>1 else xkeys[0]

    #/************************************************************************/
    def values(self, *arg, **kwargs):
        """Retrieve (outmost) end-values of nested dictionary.

            >>> values = dnest.values(*arg, **kwargs)
        """
        try:
            assert arg in ((),([],),(None,)) or kwargs == {}
        except:
            raise TypeError("Both argument or keyword arguments cannot be accepted simultaneously")
        try:
            assert arg in ((),([],),(None,)) or Type.is_sequence(arg[0])
        except:
            raise TypeError("Wrong format/values for input argument")
        if arg != ():
            kwargs.update({k: v for k,v in zip(self.order, arg[0])})
        if kwargs == {}:
            return super(NestedDict, self).values()
        return self._deep_search('values', **kwargs)

    #/************************************************************************/
    def xvalues(self, **kwargs):
        """Retrieve nested values of nested dictionary.

            >>> values = dnest.xvalues(*arg, **kwargs)

        Examples
        --------

            >>> dic = {'a':[1,2], 'b':[4,5]}
            >>> ord = ['a', 'b']
            >>> val = [{1:{2:3}}, {4:{5:6}, 7:{8:{9:10}}}, [11,12], 13]
            >>> nd = NestedDict(dic, values=val, order=ord)
            >>> print(nd)
                {1: {4: {1: {2: 3}}, 5: {4: {5: 6}, 7: {8: {9: 10}}}}, 2: {4: [11, 12], 5: 13}}
            >>> values = nd.xvalues()
            >>> values == val
                True
        """
        __force_list = kwargs.pop('_force_list_', False)
        if kwargs == {}:
            values = self._deepest(self, item='values')
        else:
            values = []
            for xk in self.xkeys(_force_list_=True):
                rdic = self.copy() # copy.deepcopy(self)
                for x in xk:
                    if x not in rdic:
                        rdic.update({x: {}})
                    rdic = rdic[x]
                values.append(rdic)
        if values == []: values = None
        return values if __force_list is True or values in ([],None) or len(values)>1 else values[0]

    #/************************************************************************/
    def items(self, **kwargs):
        """Retrieve items of nested dictionary.

            >>> items = dnest.items(**kwargs)
        """
        if kwargs == {}:
            return super(NestedDict, self).items()
        return list(zip(cycle(self.keys(**kwargs)), self.values(**kwargs)))

    #/************************************************************************/
    def xitems(self, **kwargs):
        """Retrieve nested items of nested dictionary.

            >>> items = dnest.xitems(**kwargs)

        Examples
        --------

            >>> dic = {'a': [1,2], 'b': [3,4,5], 'c': [6,7,8,9]}
            >>> r = NestedDict(dic, order = ['b', 'c', 'a'])
            >>> print(r)
                {3: {6: {1: {}, 2: {}}, 7: {1: {}, 2: {}}, 8: {1: {}, 2: {}}, 9: {1: {}, 2: {}}},
                 4: {6: {1: {}, 2: {}}, 7: {1: {}, 2: {}}, 8: {1: {}, 2: {}}, 9: {1: {}, 2: {}}},
                 5: {6: {1: {}, 2: {}}, 7: {1: {}, 2: {}}, 8: {1: {}, 2: {}}, 9: {1: {}, 2: {}}}}
            >>> r.xitems(b=4)
                [((4, 6, 1), {}), ((4, 6, 2), {}), ((4, 7, 1), {}), ((4, 7, 2), {}),
                 ((4, 8, 1), {}), ((4, 8, 2), {}), ((4, 9, 1), {}), ((4, 9, 2), {})]
            >>> r.xitems(c=6, a=2)
                [((3, 6, 2), {}), ((4, 6, 2), {}), ((5, 6, 2), {})]
        """
        return list(zip(self.xkeys(_force_list_=True),
                        self.xvalues(_force_list_=True)))

    #/************************************************************************/
    def xlen(self, *arg):
        """Retrieve depth lenght of the various dimensions of a nested dictionary.

            >>> len = dnest.xlen(*arg)


        Examples
        --------

            >>> dic = {'a': [1,2], 'b': [3,4,5], 'c': [6,7,8,9]}
            >>> r = NestedDict(dic, order = ['b', 'c', 'a'])
            >>> print(r)
                {3: {6: {1: {}, 2: {}}, 7: {1: {}, 2: {}}, 8: {1: {}, 2: {}}, 9: {1: {}, 2: {}}},
                 4: {6: {1: {}, 2: {}}, 7: {1: {}, 2: {}}, 8: {1: {}, 2: {}}, 9: {1: {}, 2: {}}},
                 5: {6: {1: {}, 2: {}}, 7: {1: {}, 2: {}}, 8: {1: {}, 2: {}}, 9: {1: {}, 2: {}}}}
            >>> r.xlen('a')
                2
            >>> r.xlen('a','b','c')
                {'a': 2, 'b': 3, 'c': 4}
            >>> r.xlen()
                24
        """
        if arg in ((),([],),(None,)):       dimensions = self.order
        elif Type.is_sequence(arg[0]):      dimensions = arg[0]
        else:                               dimensions = arg
        try:
            assert set(dimensions).difference(set(self.order)) == set()
        except:
            raise TypeError("Wrong type/value for input argument")
        try:
            xlen = {k: v for k,v in self.__xlen.items() if k in dimensions}
        except:
            xlen = {}
            dic = [self.__dict__]
            for dim in self.order:
                if dim in dimensions:
                    xlen.update({dim: len(dic[0].keys())})
                dic = list(dic[0].values())
        if arg == ():
            return reduce(lambda x,y: x*y, xlen.values())
        else:
            return xlen if len(xlen)>1 else list(xlen.values())[0]

    #/************************************************************************/
    def reorder(self, order):
        """Reorder the nested structure of a nested dictionary.

            >>> dnest.reorder(order)

        Example
        -------

            >>> d = {'a': [1,2], 'b': [3,4,5]}
            >>> r = NestedDict(d, values = list(range(6)))
            >>> r.order
                ['a', 'b']
            >>> print(r)
                {1: {3: 0, 4: 1, 5: 2}, 2: {3: 3, 4: 4, 5: 5}}
            >>> r.reorder(['b', 'a'])
            >>> print(r)
                {3: {1: 0, 2: 3}, 4: {1: 1, 2: 4}, 5: {1: 2, 2: 5}}
            >>> r.order
                ['b', 'a']
        """
        try:
            assert order is None or Type.is_sequence(order)
        except:
            raise TypeError("Wrong argument for ORDER attribute")
        # reassign self.__dimensions
        if self.order not in (None,[],()) and self.order != order:
            self._deep_reorder(self, order=order, in_place=True)

    #/************************************************************************/
    def merge(self, *dics, **kwargs):
        order = self.order
        def _umerge(dic):
            try:
                dorder = dic.order
                assert order not in (False,None)
            except:
                pass
            else:
                ndic = None
                norder = sorted([o for o in dorder if o in order], key=lambda x: order.index(x))     \
                    + [o for o in dorder if o not in order]
                if norder != dorder:
                    ndic = dic._deep_reorder(norder)
                self._deep_merge(self.__dict__, ndic or dic, in_place=True)
        reduce(_umerge, dics)


#==============================================================================
# Class DictDiffer
#==============================================================================

class DictDiffer():
    """A dictionary difference calculator.

        >>> diff = DictDiffer(current_dict, past_dict)

    Algorithm
    ---------
    Calculate the difference between two dictionaries as:
        (1) items added
        (2) items removed
        (3) keys same in both but changed values
        (4) keys same in both and unchanged values

    Example
    -------

        >>> past = {'a': 1, 'b': 1, 'c': 0}
        >>> cur = {'a': 1, 'b': 2, 'd': 0}
        >>> diff = DictDiffer(cur, past)
        >>> print("Added: %s" % diff.added())
            Added: set(['d'])
        >>> print("Removed: %s" % diff.removed())
            Removed: set(['c'])
        >>> print("Changed: %s" % diff.changed())
            Changed: set(['b'])
        >>> print("Unchanged: %s" % diff.unchanged())
            Unchanged: set(['a'])
    """
    def __init__(self, current_dict, past_dict):
        self.current_dict, self.past_dict = current_dict, past_dict
        self.current_keys, self.past_keys = [
            set(d.keys()) for d in (current_dict, past_dict)
        ]
        self.intersect = self.current_keys.intersection(self.past_keys)

    def added(self):
        """List items added (added keys)."""
        return self.current_keys - self.intersect

    def removed(self):
        """List items removed (removed keys)."""
        return self.past_keys - self.intersect

    def changed(self):
        """List items changed (same keys with different values)"""
        return set(o for o in self.intersect
                   if self.past_dict[o] != self.current_dict[o])

    def unchanged(self):
        """List unchanged items (same keys, same values)."""
         return set(o for o in self.intersect
                    if self.past_dict[o] == self.current_dict[o])

