#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
.. _io

.. Links

.. _bs4: https://pypi.python.org/pypi/beautifulsoup4
.. |bs4| replace:: `beautiful soup <bs4_>`_
.. _chardet: https://pypi.org/project/chardet/
.. |chardet| replace:: `chardet <chardet_>`_
.. _xmltree: https://docs.python.org/3/library/xml.etree.elementtree.html
.. |xmltree| replace:: `xml.tree <xmltree_>`_

Module implementing miscenalleous Input/Output methods.

**Dependencies**

*require*:      :mod:`requests`, :mod:`zipfile`,
                :mod:`hashlib`, :mod:`shutil`, :mod:`json`

*optional*:     :mod:`bs4`, :mod:`chardet`, :mod:`xml.etree`

*call*:         :mod:`pydatutils.misc`, :mod:`pydatutils.struct`, :mod:`pydatutils.online`

**Contents**
"""

# *credits*:      `gjacopo <jacopo.grazzini@ec.europa.eu>`_
# *since*:        Thu Apr  9 09:56:45 2020

#%% Settings

import io
from os import path as osp
from warnings import warn

from collections import OrderedDict
from collections.abc import Mapping, Sequence
from six import string_types

import zipfile

try:
    import simplejson as json
except ImportError:
    try:
        import json
    except ImportError:
        class json:
            def dump(self, f, arg):
                with open(arg, 'w') as f:   f.write(arg)
            def dumps(self, arg):           return '%s' % arg
            def load(self, arg):
                with open(arg, 'r') as f:   return f.read()
            def loads(self,arg):            return '%s' % arg

try:
    import chardet
except ImportError:
    #warnings.warn('\n! missing chardet package (visit https://pypi.org/project/chardet/ !')
    pass

try:
    import xml.etree.cElementTree as et
except ImportError:
    _is_xml_installed = False
else:
    _is_xml_installed = True

from pydatutils.misc import SysEnv
from pydatutils.struct import Struct
from pydatutils.online import Requests


#%% Core functions/classes

#==============================================================================
# Class File
#==============================================================================

class File():

    FORMATS         = { 'csv':          'csv',
                        'json':         'json',
                        'excel':        ['xls', 'xlsx'],
                        'table':        'table',
                        'xml':          'xml',
                        'html':         'html',
                        'sql':          'sql',
                        'sas':          'sas'
                        }

    #/************************************************************************/
    @staticmethod
    def check_format(fmt, infer_fmt=False):
        """
            >>> fmt = File.check_format(fmt, infer_fmt=False)
        """
        try:
            assert fmt is None or isinstance(fmt, string_types)  \
                or (isinstance(fmt, Sequence) and all([isinstance(f, string_types) for f in fmt]))
        except: raise IOError("Wrong format for FMT parameter: '%s'" % fmt)
        if fmt is None:                             fmt = list(File.FORMATS.values())
        elif isinstance(fmt, string_types):         fmt = [fmt,]
        try:
            assert isinstance(infer_fmt, (bool, string_types)) \
                or (isinstance(infer_fmt, Sequence) and all([isinstance(f, string_types) for f in infer_fmt]))
        except:
            raise IOError("Wrong format for INFER_FMT flag: '%s'" % infer_fmt)
        if infer_fmt is True: # extend... with all besides those parsed
            infer_fmt = File.FORMATS.keys()   # default
        elif isinstance(infer_fmt, string_types):
            infer_fmt = [infer_fmt,]
        if not infer_fmt is False: # extend... with all besides those parsed
            fmt.extend(infer_fmt) # test all!
        try:
            fmt.insert(fmt.index('xlsx'), 'xls') or fmt.remove('xlsx')
        except: pass
        fmt = Struct.uniq_items(fmt, items=File.FORMATS)
        try:
            assert fmt not in (None, [], '')
        except:
            raise IOError("Data format FMT not recognised: '%s'" % fmt)
        if isinstance(fmt, string_types):
            fmt = [fmt,]
        return fmt

    #/****************************************************************************/
    @staticmethod
    def pick_lines(file, rows):
        """Pick numbered lines from file.

            >>> lines = File.pick_lines(file, rows)
        """
        return [x for i, x in enumerate(file) if i in rows]

    #/************************************************************************/
    @staticmethod
    def unzip(file, **kwargs):
        """Unzip file on-disk.

            >>> res = File.unzip(file, **kwargs)
        """
        # try:
        #     assert isinstance(file, (io.BytesIO,string_types))
        # except:
        #     raise TypeError("Zip file '%s' not recognised" % file)
        try:
            assert zipfile.is_zipfile(file)
        except:
            raise IOError("Zip file '%s' not recognised" % file)
        path = kwargs.pop('path') if 'path' in kwargs else SysEnv.default_cache()
        operators = [op for op in ['open', 'extract', 'extractall', 'getinfo', 'namelist', 'read', 'infolist'] \
                     if op in kwargs.keys()]
        try:
            assert operators in ([], [None]) or sum([1 for op in operators]) == 1
        except:
            raise IOError("Only one operation supported per call")
        else:
            if operators in ([], [None]):
                operator = 'extractall'
            else:
                operator = operators[0]
        if operator in ('infolist','namelist'):
            try:
                assert kwargs.get(operator) not in (False,None)
            except:
                raise IOError("No operation parsed")
        else:
            members = kwargs.pop(operator, None)
        #if operator.startswith('extract'):
        #    warn("\n! Data extracted from zip file will be physically stored on local disk !")
        if isinstance(members, string_types):
            members = [members,]
        with zipfile.ZipFile(file) as zf:
            namelist, infolist = zf.namelist(), zf.infolist()
            if operator == 'namelist':
                return namelist if len(namelist) > 1 else namelist[0]
            elif operator == 'infolist':
                return infolist if len(infolist) > 1 else infolist[0]
            elif operator == 'extractall':
                if members in (None, True):     members = namelist
                return zf.extractall(path=path, members=members)
            if members is None and len(namelist) == 1:
                members = namelist
            elif members is not None:
                for i in reversed(range(len(members))):
                    m = members[i]
                    try:
                        assert m in namelist
                    except:
                        try:
                            _mem = [n for n in namelist if n.endswith(m)]
                            assert len(_mem) == 1
                        except:
                            if len(_mem) > 1:
                                warn("\n! Mulitple files machting in zip source - ambiguity not resolved !" % m)
                            else: # len(_mem) == 0 <=> _mem = []
                                warn("\n! File '%s' not found in zip source !" % m)
                            members.pop(i)
                        else:
                            members[i] = _mem[0]
                    else:
                        pass # continue
            # now: operator in ('extract', 'getinfo', 'read')
            if members in ([], None):
                raise IOError("Impossible to retrieve member file(s) from zipped data")
            nkw = Struct.inspect_kwargs(kwargs, getattr(zf, operator))
            if operator == 'extract':
                nkw.update({'path': path})
            results = {m: getattr(zf, operator)(m, **nkw) for m in members}
        return results
        # raise IOError("Operation '%s' failed" % operator)


#==============================================================================
# Class Buffer
#==============================================================================

class Buffer():

    #/************************************************************************/
    @staticmethod
    def from_url(urlname, **kwargs): # dumb function
        """
            >>> res = Buffer.from_url(urlname, **kwargs)
        """
        try:
            return Requests.parse_url(urlname, **kwargs)
        except:
            raise IOError("Wrong request for data from URL '%s'" % urlname)

    #/************************************************************************/
    @staticmethod
    def from_zip(file, src=None, **kwargs): # dumb function
        """
            >>> res = Buffer.from_zip(file, src=None, **kwargs)
        """
        try:
            assert file is None or isinstance(file, string_types)
        except:
            raise TypeError("Wrong type for file parameter '%s' - must be a string" % file)
        try:
            assert src is None or isinstance(src, string_types)
        except:
            raise TypeError("Wrong type for data source parameter '%s' - must be a string" % src)
        if src is None:
            src, file = file, None
        if zipfile.is_zipfile(src) or any([src.endswith(p) for p in ['zip', 'gz', 'gzip', 'bz2'] ]):
            try:
                # file = File.unzip(content, namelist=True)
                kwargs.update({'open': file}) # when file=None, will read a single file
                results = File.unzip(src, **kwargs)
            except:
                raise IOError("Impossible unzipping content from zipped file '%s'" % src)
        else:
            results = {src: file}
        return results if len(results.keys())>1 else list(results.values())[0]

    #/************************************************************************/
    @classmethod
    def from_file(cls, file, src=None, **kwargs):
        """
            >>> res = Buffer.from_file(file, src=None, **kwargs)
        """
        try:
            assert file is None or isinstance(file, string_types)     \
                 or (isinstance(file, Sequence) and all([isinstance(f,string_types) for f in file]))
        except:
            raise TypeError("Wrong format for filename - must be a (list of) string(s)")
        try:
            assert src is None or isinstance(src, string_types)
        except:
            raise TypeError("Wrong type for data source parameter '%s' - must be a string" % src)
        if src is None:
            src, file = file, None
        if any([src.startswith(p) for p in ['http', 'https', 'ftp'] ]):
            try:
                content = cls.from_url(src, **kwargs)
            except:
                raise IOError("Wrong request for data source from URL '%s'" % src)
        else:
            try:
                assert osp.exists(src) is True
            except:
                raise IOError("Data source '%s' not found on disk" % src)
            else:
                content = src
        # opening and parsing files from zipped source to transform
        # # them into dataframes -
        if kwargs.get('on_disk',False) is True:
            # path = kwargs.pop('store') if 'store' in kwargs else File.default_cache()
            path = kwargs.pop('store',None) or SysEnv.default_cache()
            kwargs.update({'extract': file, 'path': path})
        else:
            kwargs.update({'open': file}) # when file=None, will read a single file
        if zipfile.is_zipfile(content) or any([src.endswith(p) for p in ['zip', 'gz', 'gzip', 'bz2'] ]):
            try:
                # file = File.unzip(content, namelist=True)
                results = File.unzip(content, **kwargs)
            except:
                raise IOError("Impossible unzipping content from zipped file '%s'" % src)
        else:
            results = {file: content}
        # with 'extract', the normalised path to the file is returned
        #if kwargs.get('on_disk',False) is True:
        #    [results.update({f: osp.join(p,f)}) for f,p in results.items()]
        return results if len(results.keys())>1 else list(results.values())[0]


#==============================================================================
# Class Json
#==============================================================================

class Json():

    #/************************************************************************/
    @classmethod
    def serialize(cls, data):
        """
        """
        if data is None or isinstance(data, (type, bool, int, float, str)):
            return data
        elif isinstance(data, Sequence):
            if isinstance(data, list):          return [cls.serialize(val) for val in data]
            elif isinstance(data, tuple):       return {"tup": [cls.serialize(val) for val in data]}
        elif isinstance(data, Mapping):
            if isinstance(data, OrderedDict):   return {"odic": [[cls.serialize(k), cls.serialize(v)] for k, v in data.items()]}
            elif isinstance(data, dict):
                if all(isinstance(k, str) for k in data):
                    return {k: cls.serialize(v) for k, v in data.items()}
                return {"dic": [[cls.serialize(k), cls.serialize(v)] for k, v in data.items()]}
        elif isinstance(data, set):             return {"set": [cls.serialize(val) for val in data]}
        raise TypeError("Type %s not data-serializable" % type(data))

    #/************************************************************************/
    @classmethod
    def restore(cls, dct):
        """
        """
        if "dic" in dct:            return dict(dct["dic"])
        elif "tup" in dct:          return tuple(dct["tup"])
        elif "set" in dct:          return set(dct["set"])
        elif "odic" in dct:         return OrderedDict(dct["odic"])
        return dct

    #/************************************************************************/
    @classmethod
    def dump(cls, data, f, **kwargs):
        serialize = kwargs.pop('serialize', False)
        # note: when is_order_preserved is False, this entire class can actually be
        # ignored since the dump/load methods are exactly equivalent to the original
        # dump/load method of the json package
        nkwargs = Struct.inspect_kwargs(kwargs, json.dump)
        try:        assert serialize is True
        except:     json.dump(data, f, **nkwargs)
        else:       json.dump(cls.serialize(data), f, **nkwargs)

    #/************************************************************************/
    @classmethod
    def dumps(cls, data, **kwargs):
        """
        """
        serialize = kwargs.pop('serialize', False)
        nkwargs = Struct.inspect_kwargs(kwargs, json.dumps)
        try:        assert serialize is True
        except:     return json.dumps(data, **nkwargs)
        else:       return json.dumps(cls.serialize(data), **nkwargs)

    #/************************************************************************/
    @classmethod
    def load(cls, s, **kwargs):
        """
        """
        serialize = kwargs.pop('serialize', False)
        nkwargs = Struct.inspect_kwargs(kwargs, json.load)
        try:        assert serialize is True
        except:     return json.load(s, **nkwargs)
        else:       return json.load(s, object_hook=cls.restore, **nkwargs)

    #/************************************************************************/
    @classmethod
    def loads(cls, s, **kwargs):
        """
        """
        serialize = kwargs.pop('serialize', False)
        nkwargs = Struct.inspect_kwargs(kwargs, json.loads)
        try:        assert serialize is True
        except:     return json.loads(s, **kwargs)
        else:       return json.loads(s, object_hook=cls.restore, **nkwargs)

    #/************************************************************************/
    @staticmethod
    def to_string(arg, rec=True):
        """Format a dictionary into a JSON-compliant string where property names
        are enclosed in double quotes :data:`"`.

            >>> ans = Json.to_string(arg, rec=True)

        Arguments
        ---------
        arg : dict
            an input argument to parse as a JSON dictionary.

        Keyword arguments
        -----------------
        rec : bool
            :data:`True` when the formatting shall be applied recursively over
            nested dictionary; default: :data:`False`.

        Returns
        -------
        ans : str
            string representing the input dictionary :data:`arg` where all property
            names are enclosed in double quotes :data:`"`.

        Examples
        --------
        All keys in the dictionary are transformed in double quoted strings:

            >>> a = {1:'a', 2:{"b":3, 4:5}, "6":'d'}
            >>> print(Json.to_string(a, rec=False))
                {1: "a", 2: {"b": 3, 4: 5}, "6": "d"}
            >>> print(Json.to_string(a))
                {"1": "a", "2": {"b": 3, "4": 5}, "6": "d"}

        The method can be used to parse the input dictionary as a properly formatted
        string that can be loaded into a dictionary through :mod:`json`:

            >>> import json
            >>> b = {'a':1, 'b':{'c':2, 'd':3}, 'e':4}
            >>> json.loads("%s" % b)
                Traceback (most recent call last):
                ...
                JSONDecodeError: Expecting property name enclosed in double quotes
            >>> s = Json.to_string(b)
            >>> print(s)
                '{"a": 1, "b": {"c": 2, "d": 3}, "e": 4}'
            >>> json.loads(s)
                {'a': 1, 'b': {'c': 2, 'd': 3}, 'e': 4}
        """
        if isinstance(arg,string_types) or not isinstance(arg,Sequence):
            arg = [arg,]
        def _recurse(dic):
            ndic = dic.copy()
            for k, v in dic.items():
                if not isinstance(k,string_types):
                    ndic.update({"%s" % k:v}) or  ndic.pop(k)
                    k = "%s" % k
                if isinstance(v,Mapping):
                    ndic[k] = _recurse(v)
            return ndic
        if rec is True:
            arg = ["""%s""" % _recurse(a) for a in arg]
        else:
            arg = ["""%s""" % a if not isinstance(a,string_types) else a for a in arg]
        arg = [a.replace("'","\"") for a in arg]
        #try:
        #    arg = [JSson.loads(a) for a in arg]
        #except:
        #    raise IOError("Impossible conversion of vector entry")
        return arg if arg is None or len(arg)>1 else arg[0]

