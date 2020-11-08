#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
.. _online

.. Links

..

Module implementing miscenalleous methods for online data fetching.

**Dependencies**

*require*:      :mod:`requests`

*optional*:

*call*:         :mode:`pydatutils.misc`

**Contents**
"""

# *credits*:      `gjacopo <jacopo.grazzini@ec.europa.eu>`_
# *since*:        Sun May 31 16:53:05 2020

#%% Settings

try:
    import requests # urllib2
except ImportError:
    # warnings.warn("missing requests module", ImportWarning)
    _is_requests_installed = False
else:
    _is_requests_installed = True

from pydatutils.misc import SysEnv


PROTOCOLS       = ('http', 'https', 'ftp')
"""Recognised protocols (APIs, websites, data repositories...).
"""

RESPONSE_FORMATS = ['resp', 'zip', 'raw', 'text', 'stringio', 'content', 'bytes', 'bytesio', 'json']



#==============================================================================
# Class Response
#==============================================================================

class Response():

    HTTP_ERROR_STATUS = { # Informational.
                         100: {'name':'Continue', 'desc':'Continue with the request.'
                               },
                         101: {'name':'Switching Protocols', 'desc':'Server is switching to a different protocol.'
                               },
                         102: {'name':'Processing', 'desc':'Server has received and is processing the request, but no response is available yet.'
                               },
                         # Success
                         200: {'name' 'OK', 'desc':'Request was successful.'
                               },
                         201: {'name':'Created', 'desc':'Request was successful, and a new resource has been created.'
                               },
                         202: {'name':'Accepted', 'desc':'Request has been accepted but not yet acted upon.'
                               },
                         203: {'name':'Non-Authoritative Information', 'desc':'Request was successful, but server is returning information that may be from another source.'
                               },
                         204: {'name':'No Content', 'desc':'There is no content to send for this request, but the headers may be useful.'
                               },
                         205: {'name':'Reset Content', 'desc':'Server successfully processed the request, but is not returning any content.'
                               },
                         206: {'name':'Partial Content', 'desc':'Download is separated into multiple streams, due to range header.'
                               },
                         207: {'name':'Multi-Status', 'desc':'Message body that follows is an XML message and can contain a number of separate response codes.'
                               },
                         208: {'name':'Already Reported', 'desc':'Response is a representation of the result of one or more instance-manipulations applied to the current instance.'
                               },
                         226: {'name':'IM Used', 'desc':'The server has fulfilled a GET request for the resource, and the response is a representation of the result of one or more instance-manipulations applied to the current instance.'
                               },
                         # Redirection.
                         300: {'name':'Multiple Choices', 'desc':'Request has more than one possible response.'
                               },
                         301: {'name':'Moved Permanently', 'desc':'URI of this resource has changed.'
                               },
                         302: {'name':'Found', 'desc':'URI of this resource has changed, temporarily.'
                               },
                         303: {'name':'See Other', 'desc':'Client should get this resource from another URI.'
                               },
                         304: {'name':'Not Modified', 'desc':'Response has not been modified, client can continue to use a cached version.'
                               },
                         305: {'name':'Use Proxy', 'desc':'Requested resource may only be accessed through a given proxy.'
                               },
                         306: {'name':'Switch Proxy', 'desc':'No longer used. Requested resource may only be accessed through a given proxy.'
                               },
                         307: {'name':'Temporary Redirect', 'desc':'URI of this resource has changed, temporarily. Use the same HTTP method to access it.'
                               },
                         308: {'name':'Permanent Redirect', 'desc':'The request, and all future requests should be repeated using another URI.'
                               },
                         # Client Error.
                         400: {'name':'Bad Request', 'desc':'Server could not understand the request, due to invalid syntax.'
                               },
                         401: {'name':'Unauthorized', 'desc':'Authentication is needed to access the given resource.'
                               },
                         402: {'name':'Payment Required', 'desc':'Some form of payment is needed to access the given resource.'
                               },
                         403: {'name':'Forbidden', 'desc':'Client does not have rights to access the content.'
                               },
                         404: {'name':'Not Found', 'desc':'Server cannot find requested resource.'
                               },
                         405: {'name':'Method Not Allowed', 'desc':'Server has disabled this request method and cannot be used.'
                               },
                         406: {'name':'Not Acceptable', 'desc':'Requested resource is only capable of generating content not acceptable according to the Accept headers sent.'
                               },
                         407: {'name':'Proxy Authentication Required', 'desc':'Authentication by a proxy is needed to access the given resource.'
                               },
                         408: {'name':'Request Timeout', 'desc':'Server would like to shut down this unused connection.'
                               },
                         409: {'name':'Conflict', 'desc':'Request could not be processed because of conflict in the request, such as an edit conflict.'
                               },
                         410: {'name':'Gone', 'desc':'Requested content has been delected from the server'
                               },
                         411: {'name':'Length Required', 'desc':'Server requires the Content-Length header to be defined.'
                               },
                         412: {'name':'Precondition Failed', 'desc':'Client has indicated preconditions in its headers which the server does not meet.'
                               },
                         413: {'name':'Request Entity Too Large', 'desc':'Request entity is larger than limits defined by server.'
                               },
                         414: {'name':'Request-URI Too Long', 'desc':'URI requested by the client is too long for the server to handle.'
                               },
                         415: {'name':'Unsupported Media Type', 'desc':'Media format of the requested data is not supported by the server.'
                               },
                         416: {'name':'Requested Range Not Satisfiable', 'desc':'Range specified by the Range header in the request can''t be fulfilled.'
                               },
                         417: {'name':'Expectation Failed', 'desc':'Expectation indicated by the Expect header can''t be met by the server.'
                               },
                         418: {'name':'I\'m a Teapot', 'desc':'HTCPCP server is a teapot; the resulting entity body may be short and stout.'
                               },
                         419: {'name':'Authentication Timeout', 'desc':'Authentication Timeout.'
                               },
                         422: {'name':'Unprocessable Entity', 'desc':'Request was well-formed but was unable to be followed due to semantic errors.'
                               },
                         423: {'name':'Locked', 'desc':'Resource that is being accessed is locked.'
                               },
                         424: {'name':'Failed Dependency', 'desc':'Request failed due to failure of a previous request (e.g. a PROPPATCH).'
                               },
                         #425: {'name':'Unordered Collection', 'desc':'unordered'
                         #     },
                         426: {'name':'Upgrade Required', 'desc':'Client should switch to a different protocol such as TLS/1.0.'
                               },
                         428: {'name':'Precondition Required', 'desc':'Origin server requires the request to be conditional.'
                               },
                         429: {'name':'Too Many Requests', 'desc':'User has sent too many requests in a given amount of time.'
                               },
                         431: {'name':'Header Fields Too Large', 'desc':'Server rejected the request because either a header, or all the headers collectively, are too large.'
                               },
                         440: {'name':'Login Timeout', 'desc':'Your session has expired. (Microsoft)'
                               },
                         444: {'name':'No Response', 'desc':'Server has returned no information to the client and closed the connection (Ngnix).'
                               },
                         449: {'name':'Retry With', 'desc':'Request should be retried after performing the appropriate action (Microsoft).'
                               },
                         450: {'name':'Blocked By Windows Parental Controls', 'desc':'Windows Parental Controls are turned on and are blocking access to the given webpage.'
                               },
                         451: {'name':'Unavailable For Legal Reasons', 'desc':'You attempted to access a Legally-restricted Resource. This could be due to censorship or government-mandated blocked access.'
                               },
                         494: {'name':'Request Header Too Large', 'desc':'Nginx internal code'
                               },
                         495: {'name':'Cert Error', 'desc':'SSL client certificate error occurred.'
                               },
                         496: {'name':'No Cert', 'desc':'Client did not provide certificate.'
                               },
                         497: {'name':'HTTP to HTTPS', 'desc':'Plain HTTP request sent to HTTPS port.'
                               },
                         499: {'name':'Client Closed Request', 'desc':'Connection has been closed by client while the server is still processing its request.'
                               },
                         # Server Error.
                         500: {'name':'Internal Server Error', 'desc':'Server has encountered a situation it doesn''t know how to handle.'
                               },
                         501: {'name':'Not Implemented', 'desc':'Request method is not supported by the server and cannot be handled.'
                               },
                         502: {'name':'Bad Gateway', 'desc':'Server, while working as a gateway to get a response needed to handle the request, got an invalid response.'
                               },
                         503: {'name':'Service Unavailable', 'desc':'Server is not yet ready to handle the request.'
                               },
                         504: {'name':'Gateway Timeout', 'desc':'Server is acting as a gateway and cannot get a response in time.'
                               },
                         505: {'name':'HTTP Version Not Supported', 'desc':'HTTP version used in the request is not supported by the server.'
                               },
                         506: {'name':'Variant Also Negotiates', 'desc':'Transparent content negotiation for the request results in a circular reference.'
                               },
                         507: {'name':'Insufficient Storage', 'desc':'Server is unable to store the representation needed to complete the request.'
                               },
                         508: {'name':'Loop Detected', 'desc':'The server detected an infinite loop while processing the request'
                               },
                         #509: {'name':'Bandwidth Limit Exceeded', 'desc':'This status code, while used by many servers, is not specified in any RFCs.'
                         #     },
                         510: {'name':'Not Extended', 'desc':'Further extensions to the request are required for the server to fulfill it.'
                               },
                         511: {'name':'Network Authentication', 'desc':'The client needs to authenticate to gain network access.'
                               }
    }
    """Descriptions of HTTP status codes. See https://en.wikipedia.org/wiki/List_of_HTTP_status_codes.
    """


#%% Core functions/classes

#==============================================================================
# Class _CachedResponse
#==============================================================================

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
        path = kwargs.pop('path','')
        try:
            assert Type.is_string(url) and Type.is_string(path) \
                and isinstance(r,(bytes,requests.Response,aiohttp.ClientResponse))
        except:
            raise happyError('parsed initialising parameters not recognised')
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
# Class Requests
#==============================================================================

class Requests():

    #/************************************************************************/
    @staticmethod
    def cache_response(url, force=True, store=None, expire=0):
        """Build cache environment for caching request responses.

            >>> resp = Requests.cache_response(urlname, force, store, expire)

        Arguments
        ---------
        urlname : str
            Plain URL name.
        force : bool
            Boolean flag set to force caching; def.: :data:`force=True`.
        store : str
            Path to the cache; def.: :data:`store=None`, _i.e._ a default path
            will be used.
        expire : int,datetime.timedelta
            Lifetime of the caching; def.: :data:`expire=0`.

        Returns
        -------
        response : requests.Response
            Response object associated to the input :data:`urlname`.

        See also
        --------
        :meth:`~Requests.parse_url`, :meth:`~Requests.parse_response`, :meth:`~Requests.cache_response`,
        :meth:`SysEnv.build_cache`, :meth:`SysEnv.is_cached`, :meth:`requests.get`.
        """
        # sequential implementation of cache_response
        pathname = SysEnv.build_cache(url, store)
        is_cached = SysEnv.is_cached(pathname, expire)
        if force is True or is_cached is False or store in (None, False):
            response = requests.get(url)
            content = response.content
            if store not in (None, False):
                # write "content" to a given pathname
                with open(pathname, 'wb') as f:
                    f.write(content)
        else:
            # read "content" from a given pathname.
            with open(pathname, 'rb') as f:
                content = f.read()
        return content, pathname

    #/************************************************************************/
    @staticmethod
    def get_response(url, caching=False, **kwargs):
        """Get the response of a given URL.

            >>> resp = Requests.get_response(urlname, caching=False, force=True, store=None, expire=0)

        Argument
        --------
        urlname : str
            Plain URL name.

        Keyword arguments
        -----------------
        caching : bool
            Boolean flag set for caching; def.: :data:`caching=False`.
        force,store,expire :
            See :meth:`Requests.cache_response`.

        Returns
        -------
        response : requests.Response
            Response object associated to the input :data:`urlname`.

        See also
        --------
        :meth:`~Requests.parse_url`, :meth:`~Requests.parse_response`, :meth:`~Requests.cache_response`,
        :meth:`requests.get`.
        """
        if caching is False or store is None:
            try:
                response = requests.get(url)
                response.raise_for_status()
            except: # (requests.URLRequired,requests.HTTPError,requests.RequestException):
                raise IOError("Wrong request formulated")
        else:
            force, store, expire = kwargs.pop('cache_force', True), kwargs.pop('cache_store', None),
                kwargs.pop('cache_expire', 0)
            try:
                response, _ = Requests.cache_response(url, force, store, expire)
                response.raise_for_status()
            except:
                raise IOError("Wrong request formulated")
        try:
            assert response is not None
        except:
            raise IOError("Wrong response retrieved")
        return response

    #/************************************************************************/
    @staticmethod
    def parse_response(response, stream=None):
        """Extract buffer data from a requests response.

            >>> data = Requests.parse_response(response, stream=None)

        Argument
        --------
        response : requests.Response
            Response object.

        Keyword arguments
        -----------------
        stream : str
            Type of stream. Any string in
            :literal:`['json','jsontext','jsonbytes','zip','resp','content','text','stringio','bytes','bytesio','raw']`.

        Returns
        -------
        data :
            Buffer/stream of data.

        See also
        --------
        :meth:`~Requests.parse_url`, :meth:`~Requests.get_response`.
        """
        if stream is None:
            try:
                url = response.url
            except:
                stream = 'json'
            else:
                stream = 'zip' if any([url.endswith(z) for z in ('zip', 'gzip', 'gz')]) else 'json'
        if stream in ('resp','response'):
            return response
        try:
            assert isinstance(stream, string_types)
        except:
            raise TypeError("Wrong format for STREAM parameter")
        else:
            stream = stream.lower()
        try:
            assert stream in ['jsontext', 'jsonbytes', 'resp', 'zip', 'raw', 'content',
                              'text', 'stringio', 'bytes', 'bytesio', 'json']
        except:
            raise IOError("Wrong value for STREAM parameter")
        else:
            if stream == 'content':
                stream = 'bytes'
        if stream.startswith('json'):
            try:
                assert stream not in ('jsontext', 'jsonbytes')
                data = response.json()
            except:
                try:
                    assert stream != 'jsonbytes'
                    data = response.text
                except:
                    try:
                        data = response.content
                    except:
                        raise IOError("Error JSON-encoding of response")
                    else:
                        stream = 'jsonbytes' # force
                else:
                    stream = 'jsontext' # force
            else:
                return data
        elif stream == 'raw':
            try:
                data = response.raw
            except:
                raise IOError("Error accessing ''raw'' attribute of response")
        elif stream in ('text', 'stringio'):
            try:
                data = response.text
            except:
                raise IOError("Error accessing ''text'' attribute of response")
        elif stream in ('bytes', 'bytesio', 'zip'):
            try:
                data = response.content
            except:
                raise IOError("Error accessing ''content'' attribute of response")
        if stream == 'stringio':
            try:
                data = io.StringIO(data)
            except:
                raise IOError("Error loading StringIO data")
        elif stream in ('bytesio', 'zip'):
            try:
                data = io.BytesIO(data)
            except:
                raise IOError("Error loading BytesIO data")
        elif stream == 'jsontext':
            try:
                data = json.loads(data)
            except:
                raise IOError("Error JSON-encoding of str text")
        elif stream == 'jsonbytes':
            try:
                data = json.loads(data.decode())
            except:
                try:
                     # assert _is_chardet_installed is True
                    data = json.loads(data.decode(chardet.detect(data)["encoding"]))
                except:
                    raise IOError("Error JSON-encoding of bytes content")
        return data

    #/************************************************************************/
    @staticmethod
    def parse_url(urlname, **kwargs):
        """Extract buffer data associated to a given URL.

            >>> data = Requests.parse_url(urlname, **kwargs)

        Argument
        --------
        urlname : str
            Plain URL name.

        Keyword arguments
        -----------------
        stream : str
            See :meth:`Requests.parse_response`.
        caching,force,store,expire :
            See :meth:`Requests.get_response`.

        Returns
        -------
        data :
            Buffer/stream of data.

        See also
        --------
        :meth:`~Requests.parse_response`, :meth:`~Requests.get_response`.
        """
        stream = kwargs.pop('stream', None)
        caching = kwargs.pop('caching', False)
        force, store, expire = kwargs.pop('cache_force', True), kwargs.pop('cache_store', None), kwargs.pop('cache_expire', 0)
        try:
            assert any([urlname.startswith(p) for p in ['http', 'https', 'ftp']]) is True
        except:
            #raise IOError ?
            warn("\n! Protocol not encoded in URL !")
        try:
            response = Requests.get_response(urlname, caching=caching, force=force,
                                             store=store, expire=expire)
        except:
            raise IOError("Wrong request for data from URL '%s'" % urlname)
        try:
            data = Requests.parse_response(response, stream=stream)
        except:
            raise IOError("Impossible reading data from URL '%s'" % urlname)
        return data



#==============================================================================
# Class Service
#==============================================================================

class Service(object):
    """Base class for web-based geospatial services.

    This class is used to defined a web-session and simple connection operations
    called by a web-service.

       >>> serv = online.Service()
    """

    ZIP_OPERATIONS  = ['extract', 'extractall', 'getinfo', 'namelist', 'read', 'infolist']

    #/************************************************************************/
    def __init__(self, **kwargs):
        self.__session           = None
        self.__cache_store       = True
        self.__expire_after      = None # datetime.deltatime(0)
        self.__cache_backend     = None
        # update with keyword arguments passed
        if kwargs != {}:
            attrs = (_Decorator.KW_CACHE,_Decorator.KW_EXPIRE,_Decorator.KW_FORCE)
            for attr in list(set(attrs).intersection(kwargs.keys())):
                setattr(self, '%s' % attr, kwargs.pop(attr))
        # determine appropriate setting for a given session, taking into account
        # the explicit setting on that request, and the setting in the session.
        self.__cache_backend = 'File'
        if isinstance(self.__cache_store, bool):
            self.__cache_store = self.__default_cache() if self.cache_store else None
        # determine appropriate setting for a given session, taking into account
        # the explicit setting on that request, and the setting in the session.
        if ASYNCIO_AVAILABLE is False:
            try:
                # whether requests_cache is defined or not, no matter
                self.__session = requests.Session()
                # session = requests.session(**kwargs)
            except:
                raise happyError('wrong requests setting - SESSION not initialised')
            if CACHECONTROL_INSTALLED is True and self.cache_store is not None:
                try:
                    if self.expire_after is None or int(self.expire_after) > 0:
                        cache_store = FileCache(os.path.abspath(self.cache_store))
                    else:
                        cache_store = FileCache(os.path.abspath(self.cache_store), forever=True)
                except:
                    pass
                else:
                    self.__session = CacheControl(self.session, cache_store)
            try:
                assert self.session is not None
            except:
                raise happyError('wrong definition for SESSION parameters - SESSION not initialised')
        else:
            self.__session = None

    #/************************************************************************/
    @property
    def session(self):
        """Session property (:data:`getter`/:data:`setter`) of an instance of
        a class :class:`_Service`. :data:`session` is itself an instance of a
        :class:`requests.session.Session` class.
        """ # A session type is :class:`requests.session.Session`.
        return self.__session
    @session.setter#analysis:ignore
    def session(self, session):
        if session is not None and not isinstance(session, requests.sessions.Session, aiohttp.client.ClientSession):
            raise happyError('wrong type for SESSION parameter')
        self.__session = session

    #/************************************************************************/
    @property
    def cache_store(self):
        """Cache property (:data:`getter`/:data:`setter`) of an instance of
        a class :class:`_Service`. :data:`cache_store` is set to the physical
        location (*i.e.* on the drive) of the repository used to cache the
        downloaded datasets/responses.
        """
        return self.__cache_store
    @cache_store.setter
    def cache_store(self, cache_store):
        if not(cache_store is None or isinstance(cache_store, (str,bool))):
            raise happyError('wrong type for %s parameter' % _Decorator.KW_CACHE.upper())
        else:
            #if cache_store not in (False,'',None) and requests_cache is None and CACHECONTROL_INSTALLED is False:
            #    raise happyError('caching not supported in the absence of modules requests_cache and cachecontrol')
            pass
        self.__cache_store = cache_store

    #/************************************************************************/
    @property
    def cache_backend(self):
        return self.__cache_backend
    # note: no setter ...

    #/************************************************************************/
    @property
    def expire_after(self):
        """Expiration property (:data:`getter`/:data:`setter`) of an instance of
        a class :class:`_Service`. :data:`expire_after` represents the time after
        which datasets downloaded and cached through this instance shall be
        downloaded again.
        """
        return self.__expire_after
    @expire_after.setter
    def expire_after(self, expire_after):
        if expire_after is None or isinstance(expire_after, (int, datetime.timedelta)) \
                and (int(expire_after)>=0 or expire_after==-1):
            self.__expire_after = expire_after
        elif not isinstance(expire_after, (int, datetime.timedelta)):
            raise happyError('wrong type for %s parameter' % _Decorator.KW_EXPIRE.upper())
        #elif isinstance(expire_after, int) and expire_after<0:
        #    raise happyError('wrong time setting for %s parameter' % _Decorator.KW_EXPIRE.upper())

    #/************************************************************************/
    def __get_status(self, url):
        # sequential implementation of get_status
        try:
            response = self.session.head(url)
        except requests.ConnectionError:
            raise happyError('connection failed - a Connection error occurred')
        except requests.HTTPError:
            raise happyError('request failed - an HTTP error occurred.')
        else:
            status = response.status_code
        try:
            name = settings.HTTP_ERROR_STATUS[status]['name']
            desc = settings.HTTP_ERROR_STATUS[status]['desc']
        except KeyError:
            name = desc = 'Unknown error'#analysis:ignore
        happyVerbose('response status from web-service: %s ("%s")' % (status,name))
        try:
            response.raise_for_status()
        except:
            raise happyError('wrong request - %s status ("%s") returned' % (status,name))
        else:
            response.close()
        return status

    #/************************************************************************/
    async \
    def __async_get_status(self, session, url):
        # asynchronous implementation of get_status
        try:
            response = await session.head(url)
        except Exception as e: # aiohttp.ClientConnectionError:
            raise happyError('connection failed', errtype=e)
        else:
            status = response.status
        try:
            name = settings.HTTP_ERROR_STATUS[status]['name']
            desc = settings.HTTP_ERROR_STATUS[status]['desc']
        except KeyError:
            name = desc = 'Unknown error'#analysis:ignore
        happyVerbose('response status from web-service: %s ("%s")' % (status,name))
        async with response:
            try:
                response.raise_for_status()
            except:
                raise happyError('wrong request - %s status ("%s") returned' % (status,name))
                #happyVerbose('response status from web-service: %s' % status)
        return status

    #/************************************************************************/
    @_Decorator.parse_url
    def get_status(self, *url, **kwargs):
        """Retrieve the header of a URL and return the server's status code.

            >>> status = serv.get_status(*url)

        Arguments
        ---------
        url : str
            complete URL name(s) whom status will be checked.

        Returns
        -------
        status : int
            response status code(s).

        Raises
        ------
        happyError
            error is raised in the cases:

                * the request is wrongly formulated,
                * the connection fails.

        Examples
        --------
        We can see the response status code when connecting to different web-pages
        or services:

            >>> serv = base._Service()
            >>> serv.get_status('http://dumb')
                Cannot connect to host dumb:80 ssl:None [nodename nor servname provided, or not known]: connection failed
            >>> serv.get_status('http://www.dumbanddumber.com')
                301

        Let us actually check that the status is ok when connecting to |Eurostat| website:

            >>> stat = serv.get_status(settings.ESTAT_URL)
            >>> print(stat)
                200
            >>> import requests
            >>> stat == requests.codes.ok
                True

        See also
        --------
        :meth:`~_Service.get_response`, :meth:`~_Service.build_url`.
        """
        try:
            assert _Decorator.KW_URL in kwargs
        except:
            pass
        else:
            url = kwargs.pop(_Decorator.KW_URL)
        #if len(urls)==1 and happyType.issequence(urls[0]):
        #    urls = urls[0]
        #try:
        #    assert all([happyType.isstring(url) for url  in urls])
        #except:
        #    raise happyError('wrong type for input URLs')
        if ASYNCIO_AVAILABLE is False:
            try:
                status = [self.__get_status(u) for u in url]
            except happyError as e:
                raise happyError(errtype=e) # 'sequential status extraction error'
        else:
            asyncio.set_event_loop(asyncio.new_event_loop())
            loop = asyncio.get_event_loop() # event loop
            async def aio_get_all_status(loop, url):
                async with aiohttp.ClientSession(loop=loop, raise_for_status=True) as session:
                    # tasks to do
                    tasks = [self.__async_get_status(session, u) for u in url]
                    # gather task responses
                    return await asyncio.gather(*tasks, return_exceptions=True)
            try:
                future = asyncio.ensure_future(aio_get_all_status(loop, url))
                # future = loop.create_task(aio_get_all_status(urls))
                status = loop.run_until_complete(future) # loop until done
                # status = future.result()
            except happyError as e:
                raise happyError(errtype=e) # 'asynchronous status extraction error'
            finally:
                loop.close()
        status = [s if isinstance(s,int) else -1 for s in status]
        return status if status in ([],None) or len(status)>1 else status[0]

    #/************************************************************************/
    @staticmethod
    def __default_cache():
        #ignore-doc
        # create default pathname for cache directory depending on OS platform.
        # inspired by `Python` package `mod:wbdata`: default path defined for
        # `property:path` property of `class:Cache` class.
        platform = sys.platform
        if platform.startswith("win"): # windows
            basedir = os.getenv("LOCALAPPDATA",os.getenv("APPDATA",os.path.expanduser("~")))
        elif platform.startswith("darwin"): # Mac OS
            basedir = os.path.expanduser("~/Library/Caches")
        else:
            basedir = os.getenv("XDG_CACHE_HOME",os.path.expanduser("~/.cache"))
        return os.path.join(basedir, settings.PACKAGE)

    #/************************************************************************/
    @staticmethod
    def __build_cache(url, cache_store):
        #ignore-doc
        # build unique filename from URL name and cache directory, e.g. using
        # hashlib encoding.
        # :param url:
        # :param cache_store:
        # :returns: a unique pathname representing the input URL
        pathname = url.encode('utf-8')
        try:
            pathname = hashlib.md5(pathname).hexdigest()
        except:
            pathname = pathname.hex()
        return os.path.join(cache_store or './', pathname)

    #/************************************************************************/
    @staticmethod
    def __is_cached(pathname, time_out): # note: we check a path here
        #ignore-doc
        if not os.path.exists(pathname):
            resp = False
        elif time_out is None:
            resp = True
        elif time_out < 0:
            resp = True
        elif time_out == 0:
            resp = False
        else:
            cur = time.time()
            mtime = os.stat(pathname).st_mtime
            happyVerbose("%s - last modified: %s" % (pathname,time.ctime(mtime)))
            resp = cur - mtime < time_out
        return resp

    #/************************************************************************/
    @_Decorator.parse_url
    def is_cached(self, *url, **kwargs):
        """Check whether a URL has been already cached.

        Returns
        -------
        ans : bool, list[bool]
            True if the input URL(s) can be retrieved from the disk (cache).,
        """
        try:
            assert _Decorator.KW_URL in kwargs
        except:
            pass
        else:
            url = kwargs.pop(_Decorator.KW_URL)
        cache_store = kwargs.get(_Decorator.KW_CACHE) or self.cache_store or True
        if isinstance(cache_store, bool) and cache_store is True:
            cache_store = self.__default_cache()
        expire_after = kwargs.get(_Decorator.KW_EXPIRE) or self.expire_after
        ans = [self.__is_cached(self.__build_cache(u, cache_store), expire_after)
                for u in url]
        return ans if len(ans)>1 else ans[0]

    #/************************************************************************/
    @staticmethod
    def __clean_cache(pathname, time_expiration): # note: we clean a path here
        #ignore-doc
        if not os.path.exists(pathname):
            resp = False
        elif time_expiration is None or time_expiration <= 0:
            resp = True
        else:
            cur = time.time()
            mtime = os.stat(pathname).st_mtime
            happyVerbose("%s - last modified: %s" % (pathname,time.ctime(mtime)))
            resp = cur - mtime >= time_expiration
        if resp is True:
            happyVerbose("removing disk file %s" % pathname)
            if os.path.isfile(pathname):
                os.remove(pathname)
            elif os.path.isdir(pathname):
                shutil.rmtree(pathname)

    #/************************************************************************/
    @_Decorator.parse_url
    def clean_cache(self, *url, **kwargs):
        """Clean a cached file or a cached repository.

        Examples
        --------

            >>> serv = services.GISCOService()
            >>> serv.clean_cache()

        To be sure, one can enfore the :data:`expire_after` parameter:

            >>> serv.clean_cache(expire_after=0)

        """
        try:
            assert _Decorator.KW_URL in kwargs
        except:
            pass
        else:
            url = kwargs.pop(_Decorator.KW_URL,None)
        cache_store = kwargs.get(_Decorator.KW_CACHE) or self.cache_store or True
        if isinstance(cache_store, bool) and cache_store is True:
            cache_store = self.__default_cache()
        expire_after = kwargs.get(_Decorator.KW_EXPIRE) or self.expire_after
        if url in ((),None):
            pathnames = os.scandir(cache_store)
        else:
            pathnames = [self.__build_cache(u, cache_store) for u in url]
        for pathname in pathnames:
            if pathname.is_dir():
                self.__clean_cache(pathname, expire_after)
        #try:
        #    os.rmdir(cache_store)
        #except OSError:
        #    pass # the directory was not empty
        if url in ((),None):
            shutil.rmtree(cache_store)

    #/************************************************************************/
    def __sync_cache_response(self, url, force_download, cache_store, expire_after):
        # sequential implementation of cache_response
        pathname = self.__build_cache(url, cache_store)
        is_cached = self.__is_cached(pathname, expire_after)
        if force_download is True or is_cached is False or cache_store in (None,False):
            response = self.session.get(url)
            content = response.content
            if cache_store not in (None,False):
                # write "content" to a given pathname
                with open(pathname, 'wb') as f:
                    f.write(content)
        else:
            # read "content" from a given pathname.
            with open(pathname, 'rb') as f:
                content = f.read()
        return content, pathname

    #/************************************************************************/
    async \
    def __async_cache_response(self, session, url, force_download, cache_store, expire_after):
        # asynchronous implementation of cache_response
        pathname = self.__build_cache(url, cache_store)
        is_cached = self.__is_cached(pathname, expire_after)
        if force_download is True or is_cached is False or cache_store in (None,False):
            response = await session.get(url)
            content = await response.content.read()
            if cache_store not in (None,False):
                try:
                    assert aiofiles
                except:  # we loose the benefits of the async ... but ok
                    print('__async open')
                    with open(pathname, 'wb') as f:
                        f.write(content)
                else:
                    async with aiofiles.open(pathname, 'wb') as f:
                        await f.write(content)
        else:
            try:
                assert aiofiles
            except:
                with open(pathname, 'rb') as f:
                    content = f.read()
            else:
                async with aiofiles.open(pathname, 'rb') as f:
                    content = await f.read()
        return content, pathname

    #/************************************************************************/
    @_Decorator.parse_url
    def cache_response(self, *url, **kwargs):
        """Download URL from internet and store the downloaded content into
        <cache>/file.
        If <cache>/file already exists, it returns content from disk.

            >>> page = serv.cache_response(url, cache_store=False,
                                           _force_download_=False, _expire_after_=-1)
        """
        try:
            assert _Decorator.KW_URL in kwargs
        except:
            pass
        else:
            url = kwargs.pop(_Decorator.KW_URL)
        #if len(urls)==1 and happyType.issequence(urls[0]):
        #    urls = urls[0]
        #try:
        #    assert all([happyType.isstring(url) for url  in urls])
        #except:
        #    raise happyError('wrong type for input URLs')
        cache_store = kwargs.get(_Decorator.KW_CACHE) or self.cache_store or False
        if isinstance(cache_store, bool) and cache_store is True:
            cache_store = self.__default_cache()
        # create cache directory only the fist time it is needed
        if cache_store not in (False, None):
            if not os.path.exists(cache_store):
                os.makedirs(cache_store)
            elif not os.path.isdir(cache_store):
                raise happyError('cache %s is not a directory' % cache_store)
        force_download = kwargs.get(_Decorator.KW_FORCE) or False
        if not isinstance(force_download, bool):
            raise happyError('wrong type for %s parameter' % _Decorator.KW_FORCE.upper())
        expire_after = kwargs.get(_Decorator.KW_EXPIRE) or self.expire_after
        if ASYNCIO_AVAILABLE is False:
            try:
                resp, path = zip(*[self.__sync_cache_response(u, force_download, cache_store, expire_after)              \
                                        for u in url])
            except happyError as e:
                raise happyError(errtype=e) # 'sequential status extraction error'
        else:
            asyncio.set_event_loop(asyncio.new_event_loop())
            loop = asyncio.get_event_loop() # event loop
            async def async_cache_all_response(loop, url):
                async with aiohttp.ClientSession(loop=loop, raise_for_status=True) as session:
                    # tasks to do
                    tasks = [self.__async_cache_response(session, u,
                                                         force_download, cache_store, expire_after)         \
                                for u in url]
                    # gather task responses
                    return await asyncio.gather(*tasks, return_exceptions=True)
            try:
                future = asyncio.ensure_future(async_cache_all_response(loop, url))
                # future = loop.create_task(aio_get_all_status(urls))
                resp, path = zip(*loop.run_until_complete(future)) # loop until done
                # status = future.result()
            except happyError as e:
                raise happyError(errtype=e) # 'asynchronous status extraction error'
            finally:
                loop.close()
        return (resp, path) if resp in ([],None) or len(resp)>1 else (resp[0], path[0])

    #/************************************************************************/
    def __sync_get_response(self, url, force_download, caching, cache_store, expire_after, **kwargs):
        if caching is False or cache_store is None:
            try:
                if REQUESTS_CACHE_INSTALLED is True:
                    with requests_cache.disabled():
                        resp = self.session.get(url)
                else:
                    resp = self.session.get(url)
            except:
                raise happyError('wrong request formulated')
        else:
            path = ''
            try:
                if CACHECONTROL_INSTALLED is True:
                    resp = self.session.get(url)
                    path = cache_store
                elif REQUESTS_CACHE_INSTALLED is True:
                    with requests_cache.enabled(cache_store, **kwargs):
                        resp = self.session.get(url)
                    path = cache_store
                else:
                    resp, path = self.__sync_cache_response(url, force_download, cache_store, expire_after)
            except:
                raise happyError('wrong request formulated')
            else:
                resp = _CachedResponse(resp, url, path=path)
        try:
            assert resp is not None
        except:
            raise happyError('wrong response retrieved')
        return resp

    #/************************************************************************/
    async \
    def __async_get_response(self, session, url, force_download, caching, cache_store, expire_after):
        if caching is False or cache_store is None:
            try:
                resp = await session.get(url)
            except:
                raise happyError('wrong request formulated')
        else:
            try:
                resp, path = await self.__async_cache_response(session, url, force_download, cache_store, expire_after)
            except:
                raise happyError('wrong request formulated')
            else:
                print('url=%s' % url)
                resp = _CachedResponse(resp, url, path=path)
        try:
            assert resp is not None
            # yield from response.raise_for_status()
        except:
            raise happyError('wrong response retrieved')
        return resp

    #/************************************************************************/
    @_Decorator.parse_url
    def get_response(self, *url, **kwargs):
        """Retrieve the GET response of a URL.

            >>> response = serv.get_response(*url, **kwargs)

        Arguments
        ---------
        url : str
            complete URL name(s) whose response(s) is(are) retrieved.

        Keyword arguments
        -----------------
        cache_store : str
            physical location (*i.e.* on the drive) of the repository used to
            cache the datasets/responses to be downloaded; when not set, the
            internal :data:`~_Service.cache_store` location already set for the
            service is used.
        _expire_after_ : int,datetime
            time after which the already cached datasets shall be downloaded again;
            when not set, the internal :data:`~_Service.expire_after` value already
            set for the service is used.
        _force_download_ : bool
            flag set to force the downloading of the datasets/responses even if
            those are already cached, and independently of the value of the
            :data:`_expire_after_` argument above; default: :data:`_force_download_=False`.
        _caching_ : bool
            flag set to actually use caching when fetching the response; default:
            :data:`_caching_=True`, the cache is used and downloaded datasets/responses
            are stored on the disk.

        Returns
        -------
        response : :class:`requests.models.Response`
            response(s) fetched from the input :data:`url` addresses.

        Raises
        ------
        happyError
            error is raised in the cases:

                * the request is wrongly formulated,
                * a bad response is retrieved.

        Examples
        --------
        Some simple tests:

            >>> serv = base._Service()
            >>> serv.get_response('http://dumb')
                happyError: wrong request formulated
            >>> resp = serv.get_response('http://www.example.com')
            >>> print(resp.text)
                <!doctype html>
                <html>
                <head>
                    <title>Example Domain</title>
                    <meta charset="utf-8" />
                    <meta http-equiv="Content-type" content="text/html; charset=utf-8" />
                    <meta name="viewport" content="width=device-width, initial-scale=1" />
                    ...

        We can view the server’s response headers when connecting to |Eurostat|
        webpage:

            >>> resp = serv.get_response(settings.ESTAT_URL)
            >>> print(resp.headers)
                {   'Date': 'Wed, 18 Apr 2018 11:54:40 GMT',
                    'X-Content-Type-Options': 'nosniff',
                    'X-Frame-Options': 'SAMEORIGIN',
                    'X-XSS-Protection': '1',
                    'Content-Type': 'text/html;charset=UTF-8',
                    'Transfer-Encoding': 'chunked',
                    'Server': 'Europa',
                    'Connection': 'Keep-Alive',
                    'Content-Encoding': 'gzip' }

        We can also access the response body as bytes (though that is usually
        adapted to non-text requests):

            >>> print(resp.content)
                b'<!DOCTYPE html PUBLIC " ...

        See also
        --------
        :meth:`~_Service.get_status`, :meth:`~_Service.build_url`.
        """
        try:
            assert _Decorator.KW_URL in kwargs
        except:
            pass
        else:
            url = kwargs.pop(_Decorator.KW_URL)
        caching = kwargs.pop(_Decorator.KW_CACHING, True)
        cache_store = kwargs.pop(_Decorator.KW_CACHE,None) or self.cache_store or False
        if isinstance(cache_store, bool) and cache_store is True:
            cache_store = self.__default_cache()
        # create cache directory only the fist time it is needed
        if cache_store not in (False, None):
            if not os.path.exists(cache_store):
                os.makedirs(cache_store)
            elif not os.path.isdir(cache_store):
                raise happyError('cache %s is not a directory' % cache_store)
        force_download = kwargs.pop(_Decorator.KW_FORCE, False)
        if not isinstance(force_download, bool):
            raise happyError('wrong type for %s parameter' % _Decorator.KW_FORCE.upper())
        expire_after = kwargs.get(_Decorator.KW_EXPIRE) or self.expire_after
        #expire_after = kwargs.pop(_Decorator.KW_EXPIRE,None) or self.expire_after or 0
        if isinstance(cache_store, bool) and cache_store is True:
            cache_store = self.__default_cache()
        if ASYNCIO_AVAILABLE is False:
            try:
                response = [self.__sync_get_response(u, force_download, caching, cache_store, expire_after)              \
                            for u in url]
            except happyError as e:
                raise happyError(errtype=e) # 'sequential status extraction error'
        else:
            asyncio.set_event_loop(asyncio.new_event_loop())
            loop = asyncio.get_event_loop() # event loop
            async def async_get_all_response(loop, url):
                async with aiohttp.ClientSession(loop=loop, raise_for_status=True) as session:
                    # tasks to do
                    tasks = [self.__async_get_response(session, u, force_download, caching, cache_store, expire_after)  \
                             for u in url]
                    # gather task responses
                    return await asyncio.gather(*tasks, return_exceptions=True)
            try:
                future = asyncio.ensure_future(async_get_all_response(loop, url))
                # future = loop.create_task(aio_get_all_status(urls))
                response = loop.run_until_complete(future) # loop until done
                # status = future.result()
            except happyError as e:
                raise happyError(errtype=e) # 'asynchronous status extraction error'
            finally:
                loop.close()
        return response if response in ([],None) or len(response)>1 else response[0]

    #/************************************************************************/
    def __sync_read_response(self, response, **kwargs):
        if not _Decorator.KW_OFORMAT in kwargs:
            try:
                url = response.url
            except:
                fmt = 'json'
            else:
                fmt = 'zip' if any([url.endswith(z) for z in ('zip','gzip','gz')]) else 'json'
        else:
            fmt = kwargs.pop(_Decorator.KW_OFORMAT, None)
        if fmt in (None,'resp','response'):
            return response
        try:
            assert fmt is None or happyType.isstring(fmt)
        except:
            raise happyError('wrong format for %s parameter' % _Decorator.KW_OFORMAT.upper())
        else:
            fmt = fmt.lower()
        try:
            assert fmt in ['jsontext', 'jsonbytes'] + self.RESPONSE_FORMATS # only for developers
        except:
            raise happyError('wrong value for FMT parameter - must be in %s' % self.RESPONSE_FORMATS)
        else:
            if fmt == 'content':
                fmt = 'bytes'
        if fmt.startswith('json'):
            try:
                assert fmt not in ('jsontext', 'jsonbytes')
                data = response.json()
            except:
                try:
                    assert fmt != 'jsonbytes'
                    data = response.text
                except:
                    try:
                        data = response.content
                    except:
                        raise happyError('error JSON-encoding of response')
                    else:
                        fmt = 'jsonbytes' # force
                else:
                    fmt = 'jsontext' # force
            else:
                return data
        elif fmt == 'raw':
            try:
                data = response.raw
            except:
                raise happyError('error accessing ''raw'' attribute of response')
        elif fmt in ('text', 'stringio'):
            try:
                data = response.text
            except:
                raise happyError('error accessing ''text'' attribute of response')
        elif fmt in ('bytes', 'bytesio', 'zip'):
            try:
                data = response.content
            except:
                raise happyError('error accessing ''content'' attribute of response')
        if fmt == 'stringio':
            try:
                data = io.StringIO(data)
            except:
                raise happyError('error loading StringIO data')
        elif fmt in ('bytesio', 'zip'):
            try:
                data = io.BytesIO(data)
            except:
                raise happyError('error loading BytesIO data')
        elif fmt == 'jsontext':
            try:
                data = json.loads(data)
            except:
                raise happyError('error JSON-encoding of str text')
        elif fmt == 'jsonbytes':
                try:
                    data = json.loads(data.decode())
                except:
                    try:
                        assert CHARDET_INSTALLED is True
                        data = json.loads(data.decode(chardet.detect(data)["encoding"]))
                    except:
                        raise happyError('error JSON-encoding of bytes content')
        if fmt != 'zip':
            return data
        # deal with special case
        operators = [op for op in self.ZIP_OPERATIONS if op in kwargs.keys()]
        try:
            assert operators in ([],[None]) or sum([1 for op in operators]) == 1
        except:
            raise happyError('only one operation supported per call')
        else:
            if operators in ([],[None]):
                operator = 'extractall'
                kwargs.update({operator: self.cache_store})
            else:
                operator = operators[0]
        members, path = None, None
        if operator in ('extract', 'getinfo', 'read'):
            members = kwargs.pop(operator, None)
        elif operator == 'extractall':
            path = kwargs.pop('extractall', None)
        else: # elif operator in ('infolist','namelist'):
            try:
                assert kwargs.get(operator) not in (False,None)
            except:
                raise happyError('no operation parsed')
        if operator.startswith('extract'):
            happyWarning('data extracted from zip file will be physically stored on local disk')
        if members is not None and not happyType.issequence(members):
            members = [members,]
        with zipfile.ZipFile(data) as zf:
            #if not zipfile.is_zipfile(zf): # does not work
            #    raise happyError('file not recognised as zip file')
            if operator in  ('infolist','namelist'):
                return getattr(zf, operator)()
            elif members is not None:
                if not all([m in zf.namelist() for m in members]):
                    raise happyError('impossible to retrieve member file(s) from zipped data')
            if operator in ('extract', 'getinfo', 'read'):
                data = [getattr(zf, operator)(m) for m in members]
                return data if data in ([],[None]) or len(data)>1 else data[0]
            elif operator == 'extractall':
                return zf.extractall(path=path)

    #/************************************************************************/
    async \
    def __async_read_response(self, response, **kwargs):
        if not _Decorator.KW_OFORMAT in kwargs:
            try:
                url = response.url
            except:
                fmt = 'json'
            else:
                fmt = 'zip' if any([url.endswith(z) for z in ('zip','gzip','gz')]) else 'json'
        else:
            fmt = kwargs.pop(_Decorator.KW_OFORMAT, None)
        if fmt in (None,'resp','response'):
            return response
        try:
            assert fmt is None or happyType.isstring(fmt)
        except:
            raise happyError('wrong format for %s parameter' % _Decorator.KW_OFORMAT.upper())
        else:
            fmt = fmt.lower()
        try:
            assert fmt in ['jsontext', 'jsonbytes'] + self.RESPONSE_FORMATS # only for developers
        except:
            raise happyError('wrong value for FMT parameter - must be in %s' % self.RESPONSE_FORMATS)
        else:
            if fmt == 'content':
                fmt = 'bytes'
        if fmt.startswith('json'):
            try:
                assert fmt not in ('jsontext', 'jsonbytes')
                data = await response.json()
            except:
                try:
                    assert fmt != 'jsonbytes'
                    data = await response.text
                except:
                    try:
                        data = await response.content
                    except:
                        raise happyError('error JSON-encoding of response')
                    else:
                        fmt = 'jsonbytes' # force
                else:
                    fmt = 'jsontext' # force
            else:
                return data
        elif fmt == 'raw':
            try:
                data = await response.raw
            except:
                raise happyError('error accessing ''raw'' attribute of response')
        elif fmt in ('text', 'stringio'):
            try:
                data = await response.text
            except:
                raise happyError('error accessing ''text'' attribute of response')
        elif fmt in ('bytes', 'bytesio', 'zip'):
            try:
                data = await response.content
            except:
                raise happyError('error accessing ''content'' attribute of response')
        if fmt == 'stringio':
            try:
                data = await io.StringIO(data)
            except:
                raise happyError('error loading StringIO data')
        elif fmt in ('bytesio', 'zip'):
            try:
                data = await io.BytesIO(data)
            except:
                raise happyError('error loading BytesIO data')
        elif fmt == 'jsontext':
            try:
                data = await json.loads(data)
            except:
                raise happyError('error JSON-encoding of str text')
        elif fmt == 'jsonbytes':
                try:
                    data = json.loads(data.decode())
                except:
                    try:
                        assert CHARDET_INSTALLED is True
                        data = await json.loads(data.decode(chardet.detect(data)["encoding"]))
                    except:
                        raise happyError('error JSON-encoding of bytes content')
        if fmt != 'zip':
            return data
        # deal with special case
        operators = [op for op in self.ZIP_OPERATIONS if op in kwargs.keys()]
        try:
            #assert set(kwargs.keys()).difference(set(self.ZIP_OPERATIONS)) == set()
            assert operators in ([],[None]) or sum([1 for op in operators]) == 1
        except:
            raise happyError('only one operation supported per call')
        else:
            if operators in ([],[None]):
                operator = 'extractall'
                kwargs.update({operator: self.cache_store})
            else:
                operator = operators[0]
        members, path = None, None
        if operator in ('extract', 'getinfo', 'read'):
            members = kwargs.pop(operator, None)
        elif operator == 'extractall':
            path = kwargs.pop('extractall', None)
        else: # elif operator in ('infolist','namelist'):
            try:
                assert kwargs.get(operator) not in (False,None)
            except:
                raise happyError('no operation parsed')
        if operator.startswith('extract'):
            happyWarning('data extracted from zip file will be physically stored on local disk')
        if members is not None and not happyType.issequence(members):
            members = [members,]
        # whatever comes next is actually not asynchronous
        async with zipfile.ZipFile(data) as zf:
            #if not zipfile.is_zipfile(zf): # does not work
            #    raise happyError('file not recognised as zip file')
            if operator in  ('infolist','namelist'):
                return await getattr(zf, operator)()
            elif members is not None:
                if not all([m in zf.namelist() for m in members]):
                    raise happyError('impossible to retrieve member file(s) from zipped data')
            if operator in ('extract', 'getinfo', 'read'):
                data = await [getattr(zf, operator)(m) for m in members]
                return data if data in ([],[None]) or len(data)>1 else data[0]
            elif operator == 'extractall':
                return await zf.extractall(path=path)

    #/************************************************************************/
    @_Decorator._parse_class((_CachedResponse, aiohttp.ClientResponse, requests.Response), _Decorator.KW_RESPONSE)
    def read_response(self, *response, **kwargs):
        """Read the response of a given request.

            >>> data = serv.read_response(*response, **kwargs)

        Arguments
        ---------
        response : :class:`_CachedResponse`,:class:`requests.Response`,:class:`aiohttp.ClientResponse`,
            response(s) from an online request.

        Keyword arguments
        -----------------
        ofmt : str
        kwargs :

        Returns
        -------
        data :
            data associated to the input argument :data:`response`, formatted
            according to what is parsed through the keyword arguments.

        Raises
        ------
        happyError
            error is raised in the cases:

                * the input keyword parameters are wrongly set,
                * there is an error in reading the response,
                * there is an error in encoding the response.

        Examples
        --------

        See also
        --------
        :meth:`~_Service.read_url`.
        """
        try:
            assert _Decorator.KW_RESPONSE in kwargs
        except:
            pass
        else:
            response = kwargs.pop(_Decorator.KW_RESPONSE)
        if ASYNCIO_AVAILABLE is False:
            try:
                data = [self.__sync_read_response(resp, **kwargs) for resp in response]
            except happyError as e:
                raise happyError(errtype=e) # 'sequential status extraction error'
        else:
            asyncio.set_event_loop(asyncio.new_event_loop())
            loop = asyncio.get_event_loop() # event loop
            async def async_read_all_response(loop, response):
                # tasks to do
                tasks = [self.__async_read_response(resp, **kwargs) for resp in response]
                # gather task responses
                return await asyncio.gather(*tasks, return_exceptions=True)
            try:
                future = asyncio.ensure_future(async_read_all_response(loop, response))
                # future = loop.create_task(aio_get_all_status(urls))
                data = loop.run_until_complete(future) # loop until done
                # status = future.result()
            except happyError as e:
                raise happyError(errtype=e) # 'asynchronous status extraction error'
            finally:
                loop.close()
        return data if data in ([],None) or len(data)>1 else data[0]

    #/************************************************************************/
    @_Decorator.parse_url
    def read_url(self, *url, **kwargs):
        """Returns the (possibly formatted) response of a given URL.

            >>> data = serv.read_url(*url, **kwargs)

        Arguments
        ---------
        url : str
            complete URL name(s) from which data will be fetched.

        Keyword arguments
        -----------------
        kwargs :
            see keyword arguments of :meth:`~_Service.read_response` method.

        Returns
        -------
        data :
            data fetched from the input :data:`url`, formatted according to what
            is parsed through the keyword arguments.

        Raises
        ------
        happyError
            error is raised in the cases:

                * there is a wrong URL status,
                * data cannot be loaded.

        Examples
        --------

        Note
        ----
        A mix of sequential/asynchronous implementations...

        See also
        --------
        :meth:`~_Service.get_status`, :meth:`~_Service.get_response`,
        :meth:`~_Service.read_response`.
        """
        try:
            assert _Decorator.KW_URL in kwargs
        except:
            pass
        else:
            url = kwargs.pop(_Decorator.KW_URL)
        try:
            assert self.get_status(url) is not None
        except happyError as e:
            raise happyError(errtype=e)
        except:
            raise happyError('error API request - wrong URL status')
        try:
            response = self.get_response(url, **kwargs)
        except happyError as e:
            raise happyError(errtype=e)
        except:
            raise happyError('URL data for %s not loaded' % url)
        return self.read_response(response, **kwargs)

    #/************************************************************************/
    @classmethod
    def build_url(cls, domain=None, **kwargs):
        """Create a complete query URL to be used by a web-service.

            >>> url = _Service.build_url(domain, **kwargs)

        Arguments
        ---------
        domain : str
            domain of the URL; default: :data:`domain` is left empty.

        Keyword arguments
        -----------------
        protocol : str
            web protocol; default to :data:`settings.DEF_PROTOCOL`, *e.g.* :literal:`http`\ .
        domain : str
            this keyword can be used when :data:`domain` is not passed as a
            positional argument already.
        path : str
            path completing the domain to form the URL: it will actually be concatenated
            to :data:`domain` so as to form the composite string :data:`domain/path`; hence,
            :data:`path` could simply be concatenated with :data:`domain` in input already.
        query : str
            query of the URL: it is concatenated to the string :data:`domain/path` so
            as to form the string :data:`domain/path/query?`\ .
        kwargs : dict
            any other keyword argument can be added as further "filters" to the output
            URL, *e.g.* when :data:`{'par': 1}` is passed as an additional keyword argument,
            the string :literal:`par=1` will be concatenated at the end of the URL formed
            by the other parameters.

        Returns
        -------
        url : str
            URL uniquely defined by the input parameters; the generic form of :data:`url`
            is :data:`protocol://domain/path/query?filters`, when all parameters above
            are passed.

        Examples
        --------
        Let us, for instance, build a URL query to *Eurostat* Rest API (just enter
        the output URL in your browser to check the output):

            >>> from happygisco.base import _Service
            >>> _Service.build_url(settings.ESTAT_URL,
                                   path='wdds/rest/data/v2.1/json/en',
                                   query='ilc_li03',
                                   precision=1,
                                   indic_il='LI_R_MD60',
                                   time='2015')
                'http://ec.europa.eu/eurostat/wdds/rest/data/v2.1/json/en/ilc_li03?precision=1&indic_il=LI_R_MD60&time=2015'

        Note that another way to call the method is:

            >>> _Service.build_url(domain=settings.ESTAT_URL,
                                   path='wdds/rest/data/v2.1/json/en',
                                   query='ilc_li01',
                                   **{'precision': 1, 'hhtyp': 'A1', 'time': '2010'})
                'http://ec.europa.eu/eurostat/wdds/rest/data/v2.1/json/en/ilc_li01?precision=1&hhtyp=A1&time=2010'

        Similarly, we will be able to access to |GISCO| service (see :meth:`GISCOService.url_geocode`
        below):

            >>> _Service.build_url(domain=settings.GISCO_URL,
                                   query='api',
                                   **{'q': 'Berlin+Germany', 'limit': 2})
                'http://europa.eu/webtools/rest/gisco/api?q=Berlin+Germany&limit=2'

        See also
        --------
        :meth:`~_Service.get_status`, :meth:`~_Service.get_response`.
        """
        # retrieve parameters/build url
        if domain is None:      domain = kwargs.pop('domain','')
        url = domain.strip("/")
        protocol = kwargs.pop('protocol', settings.DEF_PROTOCOL)
        if protocol not in settings.PROTOCOLS:
            raise happyError('web protocol not recognised')
        if not url.startswith(protocol):
            url = "%s://%s" % (protocol, url)
        path = kwargs.pop('path','')
        if path not in (None,''):
            url = "%s/%s" % (url, path)
        query = kwargs.pop('query','')
        if query not in (None,''):
            url = "%s/%s" % (url, query)
        if kwargs != {}:
            #_izip_replicate = lambda d : [(k,i) if isinstance(d[k], (tuple,list))        \
            #        else (k, d[k]) for k in d for i in d[k]]
            _izip_replicate = lambda d : [[(k,i) for i in d[k]] if isinstance(d[k], (tuple,list))        \
                else (k, d[k])  for k in d]
            # filters = '&'.join(['{k}={v}'.format(k=k, v=v) for (k, v) in _izip_replicate(kwargs)])
            filters = urllib.parse.urlencode(_izip_replicate(kwargs))
            # filters = '&'.join(map("=".join,kwargs.items()))
            sep = '?'
            try:
                last = url.rsplit('/',1)[1]
            except:
                pass
            else:
                if any([last.endswith(c) for c in ('?', '/')]):     sep = ''
            url = "%s%s%s" % (url, sep, filters)
        return url

