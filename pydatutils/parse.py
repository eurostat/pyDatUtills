#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
.. _parse

.. Links

**Dependencies**

*require*:      :mod:`os`, :mod:`sys`, :mod:`io`, :mod:`asyncio`, :mod:`itertools`, :mod:`functools`, :mod:`collections`, :mod:`time`, :mod:`hashlib`, :mod:`zipfile`, :mod:`copy`, :mod:`json`

*optional*:     :mod:`datetime`, :mod:`requests`,  :mod:`requests_cache`,  :mod:`cachecontrol`, :mod:`aiohttp`, :mod:`aiofiles`, :mod:`chardet`, :mod:`zipstream`

*call*:         :mod:`pydatutils.log`, :mod:`pydatutils.type`

**Contents**
"""

# *credits*:      `gjacopo <jacopo.grazzini@ec.europa.eu>`_
# *since*:        Fri May  8 15:28:06 2020

#%% Settings

import io, os

from warnings import warn

from pydatutils.struct import Type, Struct
from pydatutils.decorator import MethodDecorator, ActivDecorator

__DEFFLAG_PARSER_IGNORE     = False
FLAG_PARSER_IGNORE          = __DEFFLAG_PARSER_IGNORE

#%% Core functions/classes


#==============================================================================
# Class BaseParserDecorator
#==============================================================================

class BaseParserDecorator(MethodDecorator):
    """Base decorating class for methods. All parsing classes shall inherit
    from this class.
    """

    def __init__(self, func, obj=None, cls=None, method_type='function',
                 **kwargs):
        # super(BaseDecorator,self)...
        MethodDecorator.__init__(self, func, obj=obj, cls=cls, method_type=method_type, **kwargs)
        # ...
        if self.ignore_parser is True:
            return None
        self._key = kwargs.pop('_key_', None)
        try:
            assert self._key is None or Type.is_string(self._key)
        except:
            raise TypeError("Wrong type for _KEY_ argument")
        self._parse_cls = kwargs.pop('_parse_cls_',None)
        if self._parse_cls is not None and not Type.is_sequence(self._parse_cls):
            self._parse_cls = [self._parse_cls,]
        try:
            assert self._parse_cls is None or (Type.is_sequence(self._parse_cls)    \
                and all([isinstance(c,type) for c in self._parse_cls]))
        except:
            raise TypeError("Wrong type for _PARSE_CLS_ argument")
        if '_values_' in kwargs:
            self._values = kwargs.pop('_values_')
            if self._values is not None and not Type.is_mapping(self._values):
                self._values = {v:v for v in self._values}
            try:
                assert self._values is None or Type.is_mapping(self._values)
            except:
                raise TypeError("Wrong type for _VALUES_ argument")
        if '_key_default_' in kwargs:
            self._key_default = kwargs.pop('_key_default_')

    def __getattribute__(self, attr_name):
        if attr_name in ('_parse_cls', '_key', '_values', '_key_default'):
            return object.__getattribute__(self, attr_name)
        return MethodDecorator.__getattribute__(self, attr_name)

    #def __call__(self, *args, **kwargs):
    #    return self.func(*args, **kwargs)
    def __call__(self, *args, **kwargs):
        if self._key is not None:
            try:
                assert hasattr(self,'_key_default')
            except:
                value = kwargs.pop(self._key, None)
            else:
                value = kwargs.pop(self._key, self._key_default)
            try:
                assert value is None or self._parse_cls is None or \
                    any([isinstance(value,c) for c in self._parse_cls])
            except:
                raise TypeError("Wrong format for %s argument"
                                % self._key.upper())
            else:
                if value is None:
                    return self.func(*args, **kwargs)
            if self._values is not None:
                # try:
                #     # could check: list,tuple in self._parse_cls
                #     _all_values = Struct.flatten_seq(list(self._values.items()))
                #     assert (Type.is_sequence(value) and set(value).difference(set(_all_values))==set())   \
                #         or value in _all_values
                # except:
                #     raise IOError("Wrong value for %s argument - %s not supported"
                #                 % (self._key.upper(), value))
                # else:
                #     if Type.is_sequence(value):
                #         value = [self._values[v] if v in self._values.keys() else v for v in value]
                #     elif value in self._values.keys():
                #         value = self._values[value]
                value = Struct.uniq_items(value, items=self._values.items())
                try:
                    assert value is not None
                except:
                    raise IOError("Wrong value for %s argument - %s not supported"
                                % (self._key.upper(), value))
            kwargs.update({self._key: value})
        return MethodDecorator.__call__(self, *args, **kwargs)


#==============================================================================
# Class BaseParserCollection
#==============================================================================

class BaseParserCollection():
    """Generic class implementing dummy decorators of methods and functions used
    to parse and check arguments.
    """

    # session/service parameters
    KW_SESSION      = 'session'
    KW_CACHING      = '_caching_'
    KW_CACHE        = 'cache_store'
    KW_EXPIRE       = 'expire_after'
    KW_FORCE        = '_force_download_'
    KW_BACKEND      = 'cache_backend'

    KW_REST_URL     = 'rest_url'
    KW_CACHE_URL    = 'cache_url'

    # input vector data
    KW_DATA         = 'data'
    KW_CODE         = 'code'
    KW_UNIT         = 'unit'

    # dimensions
    KW_YEAR         = 'year'
    KW_IFORMAT      = 'ifmt'
    KW_OFORMAT      = 'ofmt'

    KW_NAME         = 'name'
    KW_ID           = 'id'
    KW_TILE         = 'tile'
    KW_ATTR         = 'attr' # 'attribution'

    KW_ORDER        = 'order'
    KW_KEYS         = 'keys'
    KW_VALUES       = 'values'
    KW_FORCE_LIST   = '_force_list_'

    KW_DATE         = 'date'
    KW_TIME         = 'time'
    KW_TIMING       = 'timing'
    KW_SINCE        = 'since'
    KW_UNTIL        = 'until'
    KW_SPAN         = 'span'
    KW_DFORMAT      = 'dfmt' # 'datefmt'
    KW_DATEFMT      = 'datefmt'
    KW_NOMICROSEC   = 'no_micro_secs'

    KW_NO_WIDGET    = '_no_widget_'


    #/************************************************************************/
    @classmethod
    def parse_class(cls, parse_cls, key, **_kwargs):
        """Generic method that enables defining a class decorator of functions
        and methods that can parse any parameter of a given class.

            >>> decorator = BaseParserCollection.parse_class(parse_cls, key,
                                                   _values_=None, _key_default_=None)

        Arguments
        ---------
        parse_cls : class
            a custom class that is the type of the parsed argument.
        key : str
            keyword argument used to parse the argument.

        Keyword arguments
        -----------------
        _values_ : dict,list
            list of values accepted for the key; can be a list or a dictionary;
            in the latter case, the argument parsed will be mapped to its
            corresponding value in the dictionary; default is :literal:`None`.
        _key_default_ :
            default value parsed for the :data:`key` parameter.

        Returns
        -------
        decorator : :class:`~BaseParserDecorator`
            A parsing class that can be used to decorate any method or function
            that accepts :data:`key` as a keyword argument to parse an argument
            of type :data:`myclass`.

        Examples
        --------
        Let say for instance we want to parse a :class:`str` argument that can
        take values in :literal:`['a','b','c']` only with a :literal:`dummy_key`
        key:

            >>> key = 'dummy_key'
            >>> parse_cls = str
            >>> values = ['a', 'b', 'c']
            >>> func = lambda *args, **kwargs: kwargs.get(key)

        we then use:

            >>> decorator = BaseParserCollection.parse_class(parse_cls, key, _values_=values)
            >>> decorator(func)(dummy_key=0)
                AssertionError: wrong format for DUMMY_KEY argument
            >>> decorator(func)(dummy_key='dumb')
                OSError: wrong value for DUMMY_KEY argument - 'dumb' not supported
            >>> decorator(func)(dummy_key='a')
                'a'

        what if we use a dictionary for :data:`values` instead:

            >>> values = {'a':1, 'b':2, 'c':3}
            >>> decorator = Parser.parse_class(parse_cls, key, _values_=values)
            >>> decorator(func)(dummy_key='b')
                2
        """
        class _parse_class(BaseParserDecorator):
            def __init__(self, *args, **kwargs):
                kwargs.update({'_parse_cls_': parse_cls, '_key_': key})
                if '_values_' in _kwargs:
                    kwargs.update({'_values_': _kwargs.get('_values_')})
                if '_key_default_' in _kwargs:
                    kwargs.update({'_key_default_': _kwargs.get('_key_default_')})
                super(_parse_class,self).__init__(*args, **kwargs)
        return _parse_class

    #/************************************************************************/
    @classmethod
    def parse_default(cls, dimensions, **kwargs):
        """Class method decorator defining default parsing arguments.

            >>> decorator = parse_default(dimensions, **kwargs)
            >>> new_func = decorator(func)

        Arguments
        ---------
        dimensions : str, list
            a list of dimensions defining parsing parameters for which default
            values have been set.

        Keyword arguments
        -----------------
        _force_list_ : bool
            flag set to :literal:`True` so as to force the output default value(s)
            to be of the type :obj:`list`; default: :data:`_force_list_=False`.

        Returns
        -------
        decorator :
            a method decorator that parse a dictionary of default values for all
            the parsing parameters listed in the :data:`dimensions` list; all other
            keyword arguments are preserved.

        Examples
        --------
        Given a subclass of :class:`BaseParserCollection`:

            >>> class SomeParser(BaseParserCollection):
                    class parse_dumb(BaseParserDecorator):
                        def __call__(self, *args, **kwargs):
                            kwargs.update({'dumb' : 0})
                            return self.func(*args, **kwargs)
                    class parse_dumber(BaseParserDecorator):
                        def __call__(self, *args, **kwargs):
                            kwargs.update({'dumber' : 1})
                            return self.func(*args, **kwargs)

        The default class returns a decorator that parses default value(s) for
        the selected dimension:

            >>> SomeParser.parse_default('DULL')
                Traceback (most recent call last):
                ...
                IOError: Dimension 'DULL' not recognised
            >>> SomeParser.parse_default('DUMB')
                SomeParser.parse_default.<locals>.decorator

        It can be used to decorate any method accepting keyword arguments:

            >>> @SomeParser.parse_default('DUMB')
            ... def func(*args,**kwargs):
            ...     print(kwargs)
            >>> func()
                {'dumb' : 0}
            >>> @SomeParser.parse_default(['dumb', 'DUMBER'])
            ... def func(*args,**kwargs):
            ...     print(kwargs)
            >>> func(key = 'dull')
                {key = 'dull', 'dumb' : 0, 'dumber' : 1}

        The use of the :data:`_force_list_` keyword argument can help reformat the
        output default values into list(s).

        Note
        ----
        * For each dimension :data:`dim` in the input list :data:`dimensions`, both
          a variable :data:`KW_<dim>` and a parsing method :data:`<dim>` need
          to be defined in the class :class:`Parser`.
        * The parsing methods :data:`parse_<dim>` need to define default values when
          no keyword argument is parsed.

        See also
        --------
        :meth:`~parse_class`.
        """
        __force_list = kwargs.pop('_force_list_', False)
        try:
            assert Type.is_string(dimensions)   \
                or (Type.is_sequence(dimensions) and all([Type.is_sequence(d) for d in dimensions]))
        except:
            raise TypeError("Wrong format for DIMENSIONS arguments")
        else:
            if not Type.is_sequence(dimensions):
                dimensions = [dimensions,]
        def_kwargs = {}
        for dim in dimensions:
            try:
                dim = dim.lower()
                parse = getattr(cls, dim)
            except:
                # raise IOError("Parse method parse_%s not recognised" % dim)
                warn("Parse method '%s' not recognised" % dim)
                continue # pass
            try:
                func = lambda *a, **kw: [kw.get(dim)]
                if __force_list is True:
                    def_kwargs.update({dim: parse(func)()})
                else:
                    val = parse(func)()
                    def_kwargs.update({dim: val[0] if val is not None and Type.is_sequence(val) and len(val)==1 \
                                            else val})
            except:
                raise IOError("Error while parsing dimension %s" % dim)
            if def_kwargs == {}:
                if len(dimensions) == 1:
                    raise IOError("Dimension '%s' not recognised" % dimensions)
                else:
                    raise IOError("Dimension(s) in '%s' not recognised" % dimensions)
        # return def_kwargs
        class decorator(BaseParserDecorator):
            def __call__(self, *args, **_kwargs):
                _kwargs.update(def_kwargs)
                return self.func(*args, **_kwargs)
        return decorator

    #/************************************************************************/
    @classmethod
    def get_kwargs(cls, kwarg=None):
        if kwarg is None:
            return [attr for attr in cls.__dict__.keys() if attr.startswith('KW_')]
        else:
            try:
                assert Type.is_string(kwarg)
                return getattr(cls, 'KW_' + kwarg.upper())
            except AssertionError:
                raise IOError("Wrong type for KeyWord ARGument - must be a string")
            except:
                raise IOError("Keyword argument %s not recognised" % kwarg)


#==============================================================================
# Class ActivParser
#==============================================================================

class ActivParser(ActivDecorator):

    INHIBITOR = 'FLAG_PARSER_IGNORE'
    FLAG_PARSER_IGNORE = False

    #/************************************************************************/
    @classmethod
    def inhibitor_rule(cls):
        return FLAG_PARSER_IGNORE


#==============================================================================
# Class IOParser
#==============================================================================

class IOParser(BaseParserCollection):

    KW_SOURCE                   = 'source'
    KW_SRC                      = 'src'
    KW_DEST                     = 'dest'
    KW_FILENAME = KW_FILE       = 'file'
    KW_PATHNAME = KW_PATH       = 'path'
    KW_DIRNAME = KW_DIR         = 'dir'
    KW_BASENAME = KW_BASE       = 'base'

    KW_CONTENT                  = 'content'
    KW_RESPONSE                 = 'resp'
    KW_INFO                     = 'info'
    KW_DOMAIN                   = 'domain'

    KW_SREAM                    = 'stream'
    KW_URL                      = 'url'
    PROTOCOLS                   = ['http', 'ftp', 'https']

    #/************************************************************************/
    @class_decorator(ActivParser.inhibitorFactory, special_member=['__call__'])
    class file(BaseParserDecorator):
        """Class decorator of functions and methods used to parse a filename.

            >>> new_func = IOParser.file(func)

        Arguments
        ---------
        func : callable
            the function to decorate that accepts, say, the input arguments
            :data:`*args, **kwargs`.

        Keyword arguments
        -----------------
        method_type : str
            type of the method decorated; can be any string from
            :literal:`['function', 'staticmethod', 'classmethod', 'property','instancemethod']`;
            default is :literal:`'function'`.
        obj :
            instance whose method is decorated when the decorated function is an
            :literal:`'instancemethod'`; default is :data:`None`.
        cls :
            class whose method is decorated when the decorated function is any
            among :literal:`['staticmethod', 'classmethod', 'property','instancemethod']`;
            default is :data:`None`.

        Returns
        -------
        new_func : callable
            the decorated function that now accepts :data:`dir`, :data:`base`, and
            :data:`file` as a keyword argument to parse the complete full path of
            a file.

        Examples
        --------

            >>> func = lambda *args, **kwargs: kwargs.get('file')
            >>> IOParser.file(func)(file='test.txt')
                test.txt
            >>> IOParser.file(func)(dir='/home/sweet/home/',base='test.txt')
                '/home/sweet/home/test.txt'

        See also
        --------
        :meth:`~IOParser.stream`, :meth:`~IOParser.url`.
        """
        def __call__(self, *args, **kwargs):
            dirname, basename, filename = None, None, None
            if args not in (None,()):
                if len(args) == 1 and Type.is_sequence(args[0]):
                    if len(args[0])==2 and all([Type.is_string(args[0][i]) for i in (0,1)]):
                        dirname, basename = args[0]
                    elif all([Type.is_string(args[0][i]) for i in range(len(args[0]))]):
                        filename = args[0]
                elif len(args) == 1 and Type.is_string(args[0]):
                    filename = args[0]
                elif len(args) == 2                                         \
                    and all([Type.is_string(args[i]) or not hasattr(args[i],'__len__') for i in (0,1)]):
                    dirname, basename = args
                else:
                    raise IOError("Input file argument(s) not recognised")
            if dirname is None and basename is None and filename is None:
                dirname = kwargs.pop(IOParser.KW_DIR, '')
                basename = kwargs.pop(IOParser.KW_BASE, '')
                filename = kwargs.pop(IOParser.KW_FILE, '')
            elif not (kwargs.get(IOParser.KW_DIR) is None and       \
                      kwargs.get(IOParser.KW_BASE) is None and      \
                      kwargs.get(IOParser.KW_FILE) is None):
                raise IOError("Don''t mess up with me - duplicated argument parsed")
            try:
                assert not(filename in ('',None) and basename in ('',None))
            except AssertionError:
                # raise ValueError('no input file arguments passed')
                return self.func(*args, **kwargs)
            try:
                assert filename in ('',None) or basename in ('',None)
            except AssertionError:
                raise IOError("Too many input file arguments parsed")
            if filename in ('',None):
                try:
                    filename = os.path.join(os.path.realpath(dirname or ''), basename)
                except:
                    raise IOError("Wrong input file argument(s) parsed")
            if not Type.is_sequence(filename):
                filename = [filename,]
            kwargs.update({IOParser.KW_FILE: filename})
            return self.func(*args, **kwargs)

    #/************************************************************************/
    @class_decorator(ActivParser.inhibitorFactory, special_member=['__call__'])
    class url(BaseParserDecorator):
        """Class decorator of functions and methods used to parse a url.

            >>> new_func = IOParser.url(func)

        Arguments
        ---------
        func : callable
            the function to decorate that accepts, say, the input arguments
            :data:`*args, **kwargs`.

        Keyword arguments
        -----------------
        method_type,obj,cls :
            see :meth:`~IOParser.file`.

        Returns
        -------
        new_func : callable
            the decorated function that now accepts  :data:`url` as a keyword
            argument to parse a simple URL; the URL must support any of the
            protocols :literal:`'http', 'https'`, or :literal:`'ftp'`, as listed
            in :data:`settings.PROTOCOLS`.

        Examples
        --------

            >>> func = lambda *args, **kwargs: kwargs.get('url')
            >>> IOParser.url(func)(url=0)
                !!! Wrong format for URL argument !!!
            >>> IOParser.url(func)(url='dumb')
                !!! Wrong value for URL argument - level 'dumb' not supported !!!
            >>> IOParser.url(func)(url='http://dumb.com')
                ['http://dumb.com']
            >>> IOParser.url(func)('http://dumb1.com', 'https://dumb2.com')
                ['http://dumb1.com', 'https://dumb2.com']

        See also
        --------
        :meth:`~IOParser.file`, :meth:`~IOParser.stream`.
        """
        def __call__(self, *args, **kwargs):
            url = None
            if args not in (None,()):
                if len(args) == 1:
                    if Type.is_string(args[0]):
                        url = list(args)
                    elif Type.is_sequence(args[0]) \
                            and all([Type.is_string(args[0][i]) for i in range(len(args[0]))]):
                        url = args[0]
                elif all([Type.is_string(args[i]) for i in range(len(args))]):
                    url = list(args)
                else:
                    raise IOError("Input URL argument(s) not recognised")
            if not(url is None or kwargs.get(IOParser.KW_URL) is None):
                raise IOError("Don''t mess up with me - duplicated argument parsed")
        elif url is None:
                url = kwargs.pop(IOParser.KW_URL, '')
            try:
                assert url not in ('',None,[])
            except AssertionError:
                # raise ValueError("No input %s argument passed" % IOParser.KW_URL.upper())
                return self.func(*args, **kwargs)
            if not Type.is_sequence(url):
                url = [url,]
            try:
                assert all([any([u.startswith(s) for s in IOParser.PROTOCOLS]) \
                            for u in url])
            except:
                raise IOError("Wrong value for %s argument - url %s not supported" % (IOParser.KW_URL.upper(),url))
            kwargs.update({IOParser.KW_URL: url})
            return self.func(*args, **kwargs)

    #/************************************************************************/
    @class_decorator(ActivParser.inhibitorFactory, special_member=['__call__'])
    class stream(BaseParserDecorator):
        """Class decorator of functions and methods used to parse a url.

            >>> new_func = IOParser.stream(func)

        Arguments
        ---------
        func : callable
            the function to decorate that accepts, say, the input arguments
            :data:`*args, **kwargs`.

        Keyword arguments
        -----------------
        method_type,obj,cls :
            see :meth:`~IOParser.file`.

        Returns
        -------
        new_func : callable
            the decorated function that now accepts  :data:`stream` as a keyword
            argument to parse a stream; the stream is typically a :class:`BytestIO`
            or  :class:`StringIO`.

        Examples
        --------

            >>> func = lambda *args, **kwargs: kwargs.get('stream')
            >>> IOParser.stream(func)(stream=0)
                !!! wrong format for STREAM argument !!!
            >>> IOParser.stream(func)(io.BytesIO(b'dumb'))
                [<_io.BytesIO at 0x11d1d09b0>]

        See also
        --------
        :meth:`~IOParser.url`, :meth:`~IOParser.file`.
        """
        def __call__(self, *args, **kwargs):
            stream = None
            if args not in (None,()):
                if len(args) == 1:
                    if isinstance(args[0],(bytes,io.BytesIO,io.StringIO)):
                        stream = list(args)
                    elif Type.is_sequence(args[0]) \
                            and all([isinstance(args[0][i],(bytes,io.BytesIO,io.StringIO)) for i in range(len(args[0]))]):
                        stream = args[0]
                elif all([Type.is_string(args[i]) for i in range(len(args))]):
                    stream = list(args)
                else:
                    raise IOError("Input %s argument(s) not recognised" % IOParser.KW_STREAM.upper())
            if not(stream is None or kwargs.get(IOParser.KW_STREAM) is None):
                raise IOError("Don''t mess up with me - duplicated argument parsed")
            elif stream is None:
                stream = kwargs.pop(IOParser.KW_STREAM, '')
            try:
                assert stream not in ('',None,[])
            except AssertionError:
                # raise ValueError("No input %s argument passed" % IOParser.KW_STREAM.upper())
                return self.func(*args, **kwargs)
            if not Type.is_sequence(stream):
                stream = [stream,]
            kwargs.update({IOParser.KW_STREAM: stream})
            return self.func(*args, **kwargs)

    try:
        assert SERVICE_AVAILABLE is True
    except:
        class _CachedResponse():
            #doc-ignore
            pass
    else:
        class _CachedResponse(requests.Response):
            """Generic class used for representing a cached response.

                >>> resp = base._CachedResponse(resp, url, path='')
            """
            # why not derive this class from aiohttp.ClientResponse in the case
            # ASYNCIO_AVAILABLE is True? actually, we refer here to aiohttp doc,
            # namely http://docs.aiohttp.org/en/stable/client_reference.html:
            #   "User never creates the instance of ClientResponse class but gets
            #   it from API calls"
            __attrs__ = requests.Response.__attrs__ + ['_cache_path', 'cache_store']
            def __init__(self, *args, **kwargs):
                r, url = args
                path = kwargs.pop(IOParser.KW_PATH,'')
                try:
                    assert Type.is_string(url) and Type.is_string(path) \
                        and isinstance(r,(bytes,requests.Response,aiohttp.ClientResponse))
                except:
                    raise TypeError("Parsed initialising parameters not recognised")
                super(_CachedResponse,self).__init__()
                self.url = url
                self._cache_path = self.cache_store = path
                if isinstance(r,bytes):
                    self.reason, self.status_code = "OK", 200
                    self._content, self._content_consumed = r, True
                elif isinstance(r,(requests.Response,aiohttp.ClientResponse)):
                    # self.__response = r
                    for attr in r.__dict__:
                        setattr(self, attr, getattr(r, attr))
                # self._encoding = ?
            def __repr__(self):
                return '<Response [%s]>' % (self.status_code)


#==============================================================================
# Class GeoParser
#==============================================================================

class GeoParser(BaseParserCollection):

    KW_LATITUDE = KW_LAT        = 'lat'
    KW_LONGITUDE = KW_LON       = 'Lon'
    KW_LATLON                   = 'lL'
    KW_LONLAT                   = 'Ll'
    KW_X                        = 'x' # 'X'
    KW_Y                        = 'y' # 'X'
    KW_COORDINATES = KW_COORD   = 'coord'
    KW_PROJECTION = KW_PROJ     = 'proj'  # 'projection'

    KW_PLACE                    = 'place'
    KW_ADDRESS                  = 'address'
    KW_CITY                     = 'city'
    KW_COUNTRY                  = 'country'
    KW_POSTCODE = KW_ZIPCODE    = 'zip'

    KW_LOCATION = KW_LOC        = 'location'
    KW_AREA                     = 'area'

    KW_VEC = KW_VECTOR          = 'vector'
    KW_GEOM = KW_GEOMETRY       = 'geom' # 'geometry'
    KW_LAYER                    = 'layer'
    KW_FEAT = KW_FEATURE        = 'feat' # 'feature'
    KW_POLYLINE                 = 'polyline'

    KW_CODER                    = 'coder'

    KW_CENTER                   = 'center'
    KW_ZOOM                     = 'zoom'
    KW_SIZE                     = 'size'

    #/************************************************************************/
    @class_decorator(ActivParser.inhibitorFactory, special_member=['__call__'])
    class coordinate(BaseParserDecorator):
        """Class decorator of functions and methods used to parse place :literal:`(lat,Lon)`
        coordinates.

            >>> new_func = GeoParser.coordinate(func)

        Arguments
        ---------
        func : callable
            the function to decorate that accepts, say, the input arguments
            :data:`*args, **kwargs`.

        Keyword arguments
        -----------------
        method_type : str
            type of the method decorated; can be any string from
            :literal:`['function', 'staticmethod', 'classmethod', 'property','instancemethod']`;
            default is :literal:`'function'`.
        obj :
            instance whose method is decorated when the decorated function is an
            :literal:`'instancemethod'`; default is :data:`None`.
        cls : class
            class whose method is decorated when the decorated function is any
            among :literal:`['staticmethod', 'classmethod', 'property','instancemethod']`;
            default is :data:`None`.

        Returns
        -------
        new_func : callable
            the decorated function that now accepts geographic coordinates as
            positional argument(s), plus some additional keyword arguments (see
            *Notes* below).

        Examples
        --------
        Some dummy examples:

            >>> func = lambda coord, *args, **kwargs: coord
            >>> new_func = GeoParser.coordinate(func)
            >>> new_func(coord=[[1,-1],[2,-2]], order='Ll')
                [[-1, 1], [-2, 2]]
            >>> new_func(**{'lat':[1,2], 'Lon': [-1,-2]})
                [[1, -1], [2, -2]]
            >>> new_func(lat=[1,2], Lon=[-1,-2], order='Ll')
                [[-1, 1], [-2, 2]]
            >>> new_func(**{'y':[1,2], 'x': [-1,-2]})
                [[1, -1], [2, -2]]

        Note that the new decorated method also supports the parsing of the coordinates
        as positional arguments (usage not recommended):

            >>> new_func([1,-1])
                [[1,-1]]
            >>> new_func([1,2],[-1,-2])
                [[1, -1], [2, -2]]
            >>> new_func(coord=[[1,-1],[2,-2]])
                [[1, -1], [2, -2]]

        Therefore, things like that should be avoided:

            >>> new_func([[1,-1],[2,-2]], lat=[1,2], Lon=[-1,-2])
                !!! dont mess up with me - duplicated coordinate argument parsed !!!
            >>> new_func(coord=[[1,-1],[2,-2]], lat=[1,2], Lon=[-1,-2])
                !!! AssertionError: too many input coordinate arguments !!!

        Notes
        -----

        * The decorated method/function :data:`new_func` accepts the same :data:`*args`
          positional arguments as :data:`func` and, in addition to the arguments
          in :data:`**kwargs` already supported by the input method/function :data:`func`,
          an extra keyword argument:
              + :data:`order` : a flag used to define the order of the output parsed
                geographic coordinates; it can be either :literal:`'lL'` for
                :literal:`(lat,Lon)` order or :literal:`'Ll'` for a :literal:`(Lon,lat)`
                order; default is :literal:`'lL'`.
        * The output decorated method :data:`new_func` can parse the following keys:
          :literal:`['lat', 'Lon', 'x', 'y', 'coord']` from any input keyword argument.
          See the examples above.

        See also
        --------
        :meth:`~GeoParser.place`, :meth:`~GeoParser.place_or_coordinate`,
        :meth:`~GeoParser.geometry`.
        """
        try:
            import polyline
        except:
            polyline = False
            #Warnings('POLYLINE (https://pypi.python.org/pypi/polyline/) not loaded')
        else:
            #Warnings('POLYLINE help: https://github.com/hicsail/polyline')
            pass
        def __call__(self, *args, **kwargs):
            order = kwargs.pop('order', GeoParser.KW_LATLON)
            if not Type.is_string(order) or not order in (GeoParser.KW_LONLAT,GeoParser.KW_LATLON):
                raise IOError("Wrong order parameter")
            coord, lat, lon, poly = None, None, None, None
            if args not in ((None,),()):
                if all([isinstance(a,_Feature) for a in args]):
                    try:
                        coord = [a.coord for a in args]
                    except:
                        raise IOError("Parsed coordinates feature not recognised")
                elif all([Type.is_mapping(a) for a in args]):
                    coord = list(args)
                elif len(args) == 1 and Type.is_sequence(args[0]):
                    if len(args[0])==2                                      \
                        and all([Type.is_sequence(args[0][i]) or not hasattr(args[0][i],'__len__') for i in (0,1)]):
                        lat, lon = args[0]
                    elif all([Type.is_mapping(args[0][i]) for i in range(len(args[0]))]):
                        coord = args[0]
                    elif all([len(args[0][i])==2 for i in range(len(args[0]))]):
                        coord = args[0]
                elif len(args) == 2                                         \
                    and all([Type.is_sequence(args[i]) or not hasattr(args[i],'__len__') for i in (0,1)]):
                    lat, lon = args
                else:
                    raise IOError("Input coordinate arguments not recognised")
            if lat is None and lon is None and coord is None:
                coord = kwargs.pop(GeoParser.KW_COORD, None)
                lat = kwargs.pop(GeoParser.KW_LAT, None) or kwargs.pop(GeoParser.KW_Y, None)
                lon = kwargs.pop(GeoParser.KW_LON, None) or kwargs.pop(GeoParser.KW_X, None)
                try:
                    poly = self.polyline and kwargs.get(GeoParser.KW_POLYLINE)
                except:
                    pass
            elif not (kwargs.get(GeoParser.KW_LAT) is None and \
                      kwargs.get(GeoParser.KW_LON) is None and \
                      kwargs.get(GeoParser.KW_COORD) is None):
                raise IOError("Don''t mess up with me - duplicated coordinate argument parsed")
            try:
                assert not(coord is None and lat is None and lon is None and poly in (False,None))
            except AssertionError:
                # return self.func(*args, **kwargs)
                raise ValueError("No input coordinate arguments passed")
            try:
                assert coord is None or (lat is None and lon is None)
            except AssertionError:
                raise IOError("Too many input coordinate arguments")
            if poly not in (False,None):
                # coord = self.polyline.decode(poly)
                return self.func(None, None, **kwargs)
            if not (lat is None and lon is None):
                if not isinstance(lat,(list,tuple)):
                    lat, lon = [lat,], [lon,]
                if not len(lat) == len(lon):
                    raise IOError("Incompatible geographic coordinates")
                coord = [list(_) for _ in zip(lat, lon)]
            elif all([Type.is_mapping(coord[i]) for i in range(len(coord))]):
                coord = [[coord[i].get(GeoParser.KW_LAT), coord[i].get(GeoParser.KW_LON)]     \
                          for i in range(len(coord))]
            elif Type.is_sequence(coord) \
                    and not any([hasattr(coord[i],'__len__') for i in range(len(coord))]):
                coord = [coord]
            if coord in ([],None):
                raise IOError("Wrong geographic coordinates")
            if order != GeoParser.KW_LATLON:          coord = [_[::-1] for _ in coord] # order = KW_LONLAT
            if REDUCE_ANSWER and len(coord)==1:     coord = coord[0]
            return self.func(coord, **kwargs)

    #/************************************************************************/
    @class_decorator(ActivParser.inhibitorFactory, special_member=['__call__'])
    class place(BaseParserDecorator):
        """Class decorator of functions and methods used to parse place (topo,geo)
        names.

            >>> new_func = GeoParser.place(func)

        Arguments
        ---------
        func : callable
            the function to decorate that accepts, say, the input arguments
            :data:`*args, **kwargs`.

        Keyword arguments
        -----------------
        method_type,obj,cls :
            see :meth:`~GeoParser.coordinate`.

        Returns
        -------
        new_func : callable
            the decorated function that now accepts a place as a positional
            argument.

        Examples
        --------
        Very basic parsing examples:

            >>> func = lambda place, *args, **kwargs: place
            >>> new_func = GeoParser.place(func)
            >>> new_func(place='Bruxelles, Belgium')
                ['Bruxelles, Belgium']
            >>> new_func(city=['Athens','Heraklion'],country='Hellas')
                ['Athens, Hellas', 'Heraklion, Hellas']
            >>> new_func(**{'address':['72 avenue Parmentier','101 Avenue de la République'],
                            'city':'Paris',
                            'country':'France'})
                ['72 avenue Parmentier, Paris, France',
                '101 Avenue de la République, Paris, France']
            >>> new_func(place=['Eurostat', 'DIGIT', 'EIB'],
                         city='Luxembourg')
                ['Eurostat, Luxembourg', 'DIGIT, Luxembourg', 'EIB, Luxembourg']

        Note that the new decorated method also supports the parsing of the place
        (topo)name as a positional argument (usage not recommended):

            >>> new_func('Athens, Hellas')
                ['Athens, Hellas']

        Therefore, things like that should be avoided:

            >>> new_func('Athens, Hellas', place='Berlin, Germany')
                !!! Dont mess up with me - duplicated place argument parsed !!!

        Note
        ----
        The output decorated method :data:`new_func` can parse the following keys:
        :literal:`['place', 'address', 'city', 'zip', 'country']` from any input
        keyword argument. See the examples above.

        See also
        --------
        :meth:`~GeoParser.coordinate`, :meth:`~GeoParser.place_or_coordinate`,
        :meth:`~GeoParser.geometry`.
        """
        def __call__(self, *args, **kwargs):
            place, address, city, country, zipcode = '', '', '', '', ''
            if args not in ((None,),()):
                if all([isinstance(a,_Feature) for a in args]):
                    try:
                        place = [a.place for a in args]
                    except:
                        raise IOError("Parsed place feature not recognised")
                elif all([Type.is_string(a) for a in args]):
                    place = list(args)
                elif len(args) == 1 and Type.is_sequence(args[0]):
                    place = args[0]
                else:
                    raise IOError("Input arguments not recognised")
            if place in ('',None):
                place = kwargs.pop(GeoParser.KW_PLACE, None)
                address = kwargs.pop(GeoParser.KW_ADDRESS, None)
                city = kwargs.pop(GeoParser.KW_CITY, None)
                country = kwargs.pop(GeoParser.KW_COUNTRY, None)
                zipcode = kwargs.pop(GeoParser.KW_POSTCODE, None)
            elif not (kwargs.get(GeoParser.KW_PLACE) is None and   \
                      kwargs.get(GeoParser.KW_ADDRESS) is None and \
                      kwargs.get(GeoParser.KW_CITY) is None and    \
                      kwargs.get(GeoParser.KW_COUNTRY) is None and \
                      kwargs.get(GeoParser.KW_POSTCODE) is None):
                raise IOError("Don''t mess up with me - duplicated place argument parsed")
            try:
                assert not(place in ('',None) and country in ('',None) and city in ('',None))
            except AssertionError:
                # return self.func(*args, **kwargs)
                raise ValueError("No input place arguments passed")
            try:
                assert place in ('',None) or address in ('',None)
            except AssertionError:
                raise IOError("Too many place arguments")
            if address not in ('',None):        place = address
            if place in ('',None):              place = []
            if Type.is_string(place): place = [place,]
            if city not in ('',None):
                if Type.is_string(city):
                    city = [city,]
                if place == []:                 place = city
                else:
                    if len(city) > 1:
                        raise IOError("Inconsistent place with multiple cities")
                    place = [', '.join(_) for _ in zip(place, itertools.cycle(city))]
            if zipcode not in ('',None):
                if Type.is_string(zipcode):
                    zipcode = [zipcode,]
                if place == []:                 place = zipcode
                else:
                    if len(zipcode) > 1:
                        raise IOError("Inconsistent place with multiple zipcodes")
                    place = [', '.join(_) for _ in zip(place, itertools.cycle(zipcode))]
            if country not in ('',None):
                if Type.is_string(country):
                    country = [country,]
                if place == []:                 place = country
                else:
                    if len(country) > 1:
                        raise IOError("Inconsistent place with multiple countries")
                    place = [', '.join(_) for _ in zip(place, itertools.cycle(country))]
            if place in (None,[],''):
                raise IOError("No input arguments passed")
            if REDUCE_ANSWER and len(place)==1:    place = place[0]
            if not all([Type.is_string(p) for p in place]):
                raise TypeError("Wrong format for input place")
            return self.func(place, **kwargs)

    #/************************************************************************/
    @class_decorator(ActivParser.inhibitorFactory, special_member=['__call__'])
    class place_or_coordinate(BaseParserDecorator):
        """Class decorator of functions and methods used to parse place :literal:`(lat,Lon)`
        coordinates or place names.

            >>> new_func = GeoParser.place_or_coordinate(func)

        Arguments
        ---------
        func : callable
            the function to decorate that accepts, say, the input arguments
            :data:`*args, **kwargs`.

        Keyword arguments
        -----------------
        method_type,obj,cls :
            see :meth:`~GeoParser.coordinate`.

        Returns
        -------
        new_func : callable
            the decorated function that now accepts  :data:`coord` or :data:`lat`
            and :data:`Lon` as new keyword argument(s) to parse geographic
            coordinates, plus some additional keyword argument (see *Notes* of
            :meth:`~GeoParser.coordinate` method).

        Examples
        --------
        Some dummy examples:

            >>> func = lambda *args, **kwargs: [kwargs.get('coord'), kwargs.get('place')]
            >>> new_func = GeoParser.place_or_coordinate(func)
            >>> new_func(lat=[1,2], Lon=[-1,-2])
                [[[1, -1], [2, -2]], None]
            >>> new_func(place='Bruxelles, Belgium')
                [None, ['Bruxelles, Belgium']]

        Note
        ----
        The output decorated method :data:`new_func` can parse all of the keys
        already supported by :meth:`~GeoParser.place` and
        :meth:`~GeoParser.coordinate` from any input keyword argument,
        *i.e.,* :literal:`['lat', 'Lon', 'x', 'y', 'coord', 'place', 'address', 'city', 'zip', 'country']`.
        See the examples above.

        See also
        --------
        :meth:`~GeoParser.place`, :meth:`~GeoParser.coordinate`,
        :meth:`~GeoParser.geometry`.
        """
        def __call__(self, *args, **kwargs):
            try:
                place = GeoParser.place(lambda p, **kw: p)(*args, **kwargs)
            except:
                place = None
            else:
                kwargs.update({GeoParser.KW_PLACE: place})
            try:
                coord = GeoParser.coordinate(lambda c, **kw: c)(*args, **kwargs)
            except:
                coord = None
            else:
                kwargs.update({GeoParser.KW_COORD: coord})
            try:
                assert not(place in ('',None) and coord in ([],None))
            except:
                # return self.func(*args, **kwargs)
                raise ValueError('no geographic entity parsed to define the place')
            if EXCLUSIVE_ARGUMENTS is True:
                try:
                    assert place in ('',None) or coord in ([],None)
                except:
                    raise IOError("Too many geographic entities parsed to define the place")
            return self.func(*args, **kwargs)

    #/************************************************************************/
    @class_decorator(ActivParser.inhibitorFactory, special_member=['__call__'])
    class geometry(BaseParserDecorator):
        """Class decorator of functions and methods used to parse either :literal:`(lat,Lon)`
        coordinate(s) or (topo)name(s) from JSON-like dictionary parameters (geometry
        features) formated according to |GISCO| geometry responses (see |GISCOWIKI|).

            >>> new_func = GeoParser.geometry(func)

        Arguments
        ---------
        func : callable
            the function to decorate that accepts, say, the input arguments
            :data:`*args, **kwargs`.

        Keyword arguments
        -----------------
        method_type,obj,cls :
            see :meth:`~GeoParser.coordinate`.

        Returns
        -------
        new_func : callable
            the decorated function that now accepts :data:`geom` as a keyword
            argument to parse geographic coordinates, plus some additional keyword
            arguments (see *Notes* below).

        Examples
        --------
        Some dummy examples:

            >>> func = lambda *args, **kwargs: kwargs.get('geom')
            >>> geom = {'A': 1, 'B': 2}
            >>> GeoParser.geometry(func)(geom=geom)
                !!! Geometry attributes not recognised !!!
            >>> geom = {'geometry': {'coordinates': [1, 2], 'type': 'Point'},
                        'properties': {'city': 'somewhere',
                                       'country': 'some country',
                                       'street': 'sesame street',
                                       'osm_key': 'place'},
                        'type': 'Feature'}
            >>> GeoParser.geometry(func)(geom=geom)
                [[2, 1]]
            >>> func = lambda *args, **kwargs: kwargs.get('place')
            >>> GeoParser.geometry(func)(geom=geom, filter='place')
                ['sesame street, somewhere, some country']

        Also note that the argument can be parsed as a positional argument (usage
        not recommended):

            >>> GeoParser.geometry(func)(geom)
                []
            >>> GeoParser.geometry(func)(geom, order='Ll')
                [[1, 2]]

        and an actual one:

            >>> serv = services.GISCOService()
            >>> geom = serv.place2geom(place='Berlin,Germany')
            >>> print(geom)
                [{'geometry': {'coordinates': [13.3888599, 52.5170365], 'type': 'Point'},
                  'properties': {'city': 'Berlin', 'country': 'Germany',
                   'name': 'Berlin',
                   'osm_id': 240109189, 'osm_key': 'place', 'osm_type': 'N', 'osm_value': 'city',
                   'postcode': '10117', 'state': 'Berlin'},
                  'type': 'Feature'},
                 {'geometry': {'coordinates': [13.4385964, 52.5198535], 'type': 'Point'},
                  'properties': {'country': 'Germany',
                   'extent': [13.08835, 52.67551, 13.76116, 52.33826],
                   'name': 'Berlin',
                   'osm_id': 62422, 'osm_key': 'place', 'osm_type': 'R', 'osm_value': 'state'},
                  'type': 'Feature'},
                 {'geometry': {'coordinates': [13.393560634296435, 52.51875095], 'type': 'Point'},
                  'properties': {'city': 'Berlin', 'country': 'Germany',
                   'extent': [13.3906703, 52.5200704, 13.3948782, 52.5174944],
                   'name': 'Humboldt University in Berlin Mitte Campus',
                   'osm_id': 120456814, 'osm_key': 'amenity', 'osm_type': 'W', 'osm_value': 'university',
                   'postcode': '10117', 'state': 'Berlin', 'street': 'Dorotheenstraße'},
                  'type': 'Feature'},
                 ...
                  {'geometry': {'coordinates': [13.3869856, 52.5156648], 'type': 'Point'},
                  'properties': {'city': 'Berlin', 'country': 'Germany',
                   'housenumber': '55-57',
                   'name': 'Komische Oper Berlin',
                   'osm_id': 318525456, 'osm_key': 'amenity', 'osm_type': 'N', 'osm_value': 'theatre',
                   'postcode': '10117', 'state': 'Berlin', 'street': 'Behrenstraße'},
                  'type': 'Feature'}]

        We can for instance use the :meth:`geometry` to parse (filter) the
        data :data:`geom` and retrieve the coordinates:

            >>> func = lambda **kwargs: kwargs.get('coord')
            >>> new_func = GeoParser.geometry(func)
            >>> hasattr(new_func, '__call__')
                True
            >>> new_func(geom=geom, filter='coord')
                [[52.5170365, 13.3888599], [52.5198535, 13.4385964]]
            >>> new_func(geom=geom, filter='coord', unique=True, order='Ll')
                [[13.3888599, 52.5170365]]

        One can also similarly retrieve the name of the places:

            >>> func = lambda **kwargs: kwargs.get('place')
            >>> new_func = GeoParser.geometry(func)
            >>> hasattr(new_func, '__call__')
                True
            >>> new_func(geom=geom, filter='place')
                ['Berlin, 10117, Germany', 'Germany', 'Dorotheenstraße, Berlin, 10117, Germany',
                'Unter den Linden, Berlin, 10117, Germany', 'Olympischer Platz, Berlin, 14053, Germany',
                'Sauerbruchweg, Berlin, 10117, Germany', 'Eingangsebene, Berlin, 10557, Germany',
                'Niederkirchnerstraße, Berlin, 10117, Germany', 'Friedrichstraße, Berlin, 10117, Germany',
                'Bismarckstraße, Berlin, 10627, Germany', 'Berlin Ostbahnhof, Berlin, 10243, Germany',
                'Pflugstraße, Berlin, 10115, Germany', 'Unter den Linden, Berlin, 10117, Germany',
                'Hanne-Sobek-Platz, Berlin, 13357, Germany', 'Behrenstraße, Berlin, 10117, Germany']

        Notes
        -----

        * The decorated method/function :data:`new_func` accepts the same :data:`*args`
          positional arguments as :data:`func` and, in addition to the arguments
          in `data:`**kwargs` already supported by the input method/function :data:`func`,
          some extra keyword arguments:
              + :data:`geom` to parse a geometry;
              + :data:`filter` - a flag used to define the output of the decorated
                function; it is either :literal:`place` or :literal:`coord`;
              + :data:`unique` - when set to :data:`True`, a single geometry is
                filtered out, the first available one; default to :data:`False`,
                hence all geometries are parsed;
              + :data:`order` - a flag used to define the order of the output filtered
                geographic coordinates; it can be either :literal:`'lL'` for
                :literal:`(lat,Lon)` order or :literal:`'Ll'` for a :literal:`(Lon,lat)`
                order; default is :literal:`'lL'`.
        * When passed to the decorated method :data:`new_func` with input arguments
          :data:`*args, **kwargs`, the remaining parameters in :data:`kwargs` are
          actually filtered out to extract geometry features, say :data:`g`, that
          are formatted like the JSON :literal:`geometries` output by |GISCO|
          geocoding web-service (see method :meth:`services.GISCOService.place2area`)
          and which verify the following match:
          ::
              g['type']='Feature' and g['geometry']['type']='Point' and g['properties']['osm_key']='place'

        * When extracting the coordinates from a geometry feature, say :data:`g`,
          output by |GISCO| web-service, the original order in the composite key
          :data:`g['geometry']['coordinates']` is :literal:`(Lon,lat)`. Note that
          for |OSM| output, the keyword :data:`lat` and :data:`Lon` are directly
          defined.

        See also
        --------
        :meth:`~GeoParser.place`, :meth:`~GeoParser.coordinate`,
        :meth:`~GeoParser.place_or_coordinate`.
        """
        KW_LAT          = 'lat' # not to be confused with GeoParser.KW_LAT
        KW_LON          = 'lon' # ibid
        KW_FEATURES     = 'features'
        KW_GEOMETRY     = 'geometry'
        KW_PROPERTIES   = 'properties'
        KW_TYPE         = 'type'
        KW_OSM_KEY      = 'osm_key'
        KW_COORDINATES  = 'coordinates'
        KW_CITY         = 'city' # not to be confused with GeoParser.KW_CITY
        KW_COUNTRY      = 'country' # ibid
        KW_POSTCODE     = 'postcode'
        KW_STATE        = 'state'
        KW_STREET       = 'street'
        KW_EXTENT       = 'extent'
        KW_DISPLAYNAME  = 'display_name'
        KW_NAME         = 'name'
        def __call__(self, *args, **kwargs):
            filt = kwargs.pop('filter',GeoParser.KW_COORD)
            if filt not in ('',None) \
                and not (Type.is_string(filt) and filt in (GeoParser.KW_PLACE,GeoParser.KW_COORD)):
                raise TypeError("Wrong "filer" parameter")
            unique = kwargs.pop('unique',False)
            if not isinstance(unique, bool):
                raise TypeError("Wrong "unique" parameter")
            order = kwargs.pop('order', 'lL')
            if not Type.is_string(order) or not order in ('Ll','lL'):
                raise TypeError("Wrong "order" parameter")
            geom = None
            if args not in ((None,),()):
                __key_area = False
                if all([isinstance(a,_Feature) for a in args]):
                    try:
                        geom = [a.geometry for a in args]
                    except:
                        raise IOError("Parsed geometry feature not recognised")
                elif all([Type.is_mapping(a) for a in args]):
                    geom = args
                elif len(args) == 1 and Type.is_sequence(args[0]):
                    if all([Type.is_mapping(args[0][i]) for i in range(len(args[0]))]):
                        geom = args[0]
            if geom is None:
                __key_area = True
                geom = kwargs.pop(GeoParser.KW_GEOMETRY, None)
            elif not kwargs.get(GeoParser.KW_GEOMETRY) is None:
                raise IOError("Don''t mess up with me - duplicated geometry argument parsed")
            if geom is None:
                # raise ValueError('not input geometry parsed')
                return self.func(*args, **kwargs)
            if Type.is_mapping(geom):
                geom = [geom,]
            elif not Type.is_sequence(geom):
                raise TypeError("Wrong geometry definition")
            if not all([Type.is_mapping(g) for g in geom]):
                raise TypeError("Wrong formatting/typing of geometry")
            if filt in ('',None):
                kwargs.update({GeoParser.KW_GEOMETRY: geom})
            elif filt == GeoParser.KW_COORD:
                try: # geometry is formatted like an OSM output
                    coord = [[float(g[GeoParser.geometry.KW_LAT]),
                              float(g[GeoParser.geometry.KW_LON])] for g in geom]
                    assert coord not in ([],None,[None])
                except: # geometry is formatted like a GEOJSON output
                    coord = [g for g in geom                                                    \
                       if GeoParser.geometry.KW_GEOMETRY in g                            \
                           and GeoParser.geometry.KW_PROPERTIES in g                     \
                           and GeoParser.geometry.KW_TYPE in g                           \
                           and g[GeoParser.geometry.KW_TYPE]=='Feature'                  \
                       ]
                    _coord = [c for c in coord                                              \
                              if (not(settings.CHECK_TYPE) or c[GeoParser.geometry.KW_GEOMETRY][GeoParser.geometry.KW_TYPE]=='Point')]
                    try:    assert _coord != []
                    except: pass
                    else:
                        coord = _coord
                        _coord = [c for c in coord                                              \
                                  if (not(settings.CHECK_OSM_KEY) or c[GeoParser.geometry.KW_PROPERTIES][GeoParser.geometry.KW_OSM_KEY]=='place')]
                        try:    assert _coord != []
                        except: pass
                        else:   coord = _coord
                    #coord = dict(zip(['lon','lat'],                                                 \
                    #                  zip(*[c[self.KW_GEOMETRY][self.KW_COORDINATES] for c in coord])))
                    coord = [_[GeoParser.geometry.KW_GEOMETRY][GeoParser.geometry.KW_COORDINATES][::-1]   \
                             for _ in coord]
                if __key_area and coord in ([],None):
                    raise IOError ("Geometry attributes not recognised")
                if order != 'lL':   coord = [_[::-1] for _ in coord]
                if unique:          coord = [coord[0],]
                #elif len(coord)==1:          coord = coord[0]
                kwargs.update({GeoParser.KW_COORD: coord})
            elif filt == GeoParser.KW_PLACE:
                try: # geometry is formatted like an OSM output
                    place = [g[GeoParser.geometry.KW_DISPLAYNAME] for g in geom]
                    assert place not in ([],[''],None,[None])
                except: # geometry is formatted like an OSM output
                    place = [g.get(GeoParser.geometry.KW_PROPERTIES) for g in geom \
                             if GeoParser.geometry.KW_PROPERTIES in g]
                    place = [', '.join(filter(None, [p.get(GeoParser.geometry.KW_STREET) or '',
                                        p.get(GeoParser.geometry.KW_CITY) or '',
                                        '(' + p.get(GeoParser.geometry.KW_STATE) + ')'               \
                                            if p.get(GeoParser.geometry.KW_STATE) not in (None,'')   \
                                            and p.get(GeoParser.geometry.KW_STATE)!=p.get(GeoParser.geometry.KW_CITY) else '',
                                        p.get(GeoParser.geometry.KW_POSTCODE) or '',
                                        p.get(GeoParser.geometry.KW_COUNTRY) or ''])) \
                            or p.get(GeoParser.geometry.KW_NAME) or '' for p in place]
                if unique:          place = [place[0],]
                if REDUCE_ANSWER and len(place)==1:    place=place[0]
                kwargs.update({'place': place})
            return self.func(**kwargs)

    #/************************************************************************/
    @class_decorator(ActivParser.inhibitorFactory, special_member=['__call__'])
    class projection(BaseParserDecorator):
        """Class decorator of functions and methods used to parse a projection
        reference system.

            >>> new_func = GeoParser.projection(func)

        Arguments
        ---------
        func : callable
            the function to decorate that accepts, say, the input arguments
            :data:`*args, **kwargs`.

        Keyword arguments
        -----------------
        method_type,obj,cls :
            see :meth:`~GeoParser.coordinate`.

        Returns
        -------
        new_func : callable
            the decorated function that now accepts  :data:`proj` as a keyword
            argument to parse the geographic projection system; the currently
            supported projections are :literal:`'WGS84','ETRS89','LAEA'` and
            :literal:`'EPSG3857'` or their equivalent EPSG codes (4326, 4258, 3857
            and 3035 respectively), *e.g* the ones listed in
            :data:`settings.GISCO_PROJECTIONS`.

        Examples
        --------
        It can be used to check that the projection is actually one of those accepted
        by |GISCO| services:

            >>> func = lambda *args, **kwargs: kwargs.get('proj')
            >>> GeoParser.projection(func)(proj='dumb')
                !!! AssertionError: wrong value for PROJ argument - projection dumb not supported !!!
            >>> GeoParser.projection(func)(proj='WGS84')
                4326
            >>> GeoParser.projection(func)(proj='EPSG3857')
                3857
            >>> GeoParser.projection(func)(proj=3857)
                3857
            >>> GeoParser.projection(func)(proj='LAEA')
                3035

        Note also that the default projection can be parsed:

            >>> GeoParser.projection(func)()
                4326

        See also
        --------
        :meth:`~GeoParser.coordinate`, :meth:`~GeoParser.iformat`.
        """
        ## PROJECTION      = dict(happyType.seqflatten([[(k,v), (v,v)] for k,v in settings.GISCO_PROJECTIONS.items()]))
        def __init__(self, *args, **kwargs):
            kwargs.update({'_parse_cls_':   [int, str, list],
                           '_key_':         GeoParser.KW_PROJECTION,
                           '_values_':      settings.GISCO_PROJECTIONS,
                           '_key_default_': settings.DEF_GISCO_PROJECTION})
            super(GeoParser.projection,self).__init__(*args, **kwargs)
        #pass

    #/************************************************************************/
    @class_decorator(ActivParser.inhibitorFactory, special_member=['__call__'])
    class iformat(BaseParserDecorator):
        """Class decorator of functions and methods used to parse a vector format.

            >>> new_func = GeoParser.iformat(func)

        Arguments
        ---------
        func : callable
            the function to decorate that accepts, say, the input arguments
            :data:`*args, **kwargs`.

        Keyword arguments
        -----------------
        method_type,obj,cls :
            see :meth:`~GeoParser.coordinate`.

        Returns
        -------
        new_func : callable
            the decorated function that now accepts :data:`fmt` as a keyword
            argument to parse a vector format (*e.g.*, for downloading datasets);
            the supported vector formats (*i.e.* parsed to :data:`fmt`) are
            :literal:`'shp','geojson','topojson','gdb'` and :literal:`'pbf'`, *e.g.*
            any of those listed in :data:`settings.GISCO_FORMATS`.

        Examples
        --------
        The formats supported by |GISCO| are parsed/checked through the call to
        this class:

            >>> func = lambda *args, **kwargs: kwargs.get('fmt')
            >>> GeoParser.iformat(func)(fmt='1)
                !!! Wrong format for FMT argument !!!
            >>> GeoParser.iformat(func)(fmt='csv')
                !!! Wrong value for FMT argument - vector format 'csv' not supported !!!
            >>> GeoParser.iformat(func)(fmt='geojson')
                'geojson'
            >>> GeoParser.iformat(func)(fmt='topojson')
                'json'
            >>> GeoParser.iformat(func)(fmt='shapefile')
                'shx'

        A default format shall be parsed as well:

            >>> GeoParser.iformat(func)()
                'geojson'

        See also
        --------
        :meth:`~GeoParser.coordinate`, :meth:`~GeoParser.projection`.
        """
        def __init__(self, *args, **kwargs):
            _kwargs = {'shapefile': 'shx'} # we cheat...
            _kwargs.update(settings.GISCO_FORMATS.copy())
            kwargs.update({'_parse_cls_':   [str, list],
                           '_key_':         GeoParser.KW_IFORMAT,
                           '_values_':      _kwargs,
                           '_key_default_': settings.DEF_GISCO_FORMAT})
            super(GeoParser.iformat,self).__init__(*args, **kwargs)


#==============================================================================
# Class TextParser
#==============================================================================

class TextParser(BaseParserCollection):
    pass

