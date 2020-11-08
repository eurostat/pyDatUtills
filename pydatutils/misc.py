#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
.. _misc

Module implementing useful miscellaneous methods, including filesytem interactions
and date/time objects handling.

**Dependencies**

*require*:      :mod:`datetime`, :mod:`time`, :mod:`calendar`, :mod:`uuid', ':mod:`hashlib`, :mod:`shutil`

*optional*:     :mod:`dateutil`, :mod:`chardet`, :mod:`pytz`

**Contents**
"""

# *credits*:      `gjacopo <gjacopo@ec.europa.eu>`_
# *since*:        Fri May  8 16:48:23 2020


#%% Settings

import os, sys
from os import path as osp
from warnings import warn
import re

import operator

from collections.abc import Mapping, Sequence
from six import string_types

import time
import datetime
import calendar

try:
    import dateutil
except ImportError:
    _is_dateutil_installed = False
    try:
        import pytz
        # warnings.warn('pytz help: https://pypi.python.org/pypi/pytz')
    except: pass
else:
    _is_dateutil_installed = True
    # warnings.warn('dateutil help: https://pypi.python.org/pypi/python-dateutil')
    try:    assert dateutil.parser # issue with IPython
    except:
        import dateutil.parser

import hashlib
import shutil

try:
    import chardet
except ImportError:
    #warnings.warn('\n! missing chardet package (visit https://pypi.org/project/chardet/ !')
    pass

from uuid import uuid3, uuid4, NAMESPACE_DNS


#%% Core functions/classes

#==============================================================================
# Class SysEnv
#==============================================================================

class SysEnv(object):
    """Static system methods.
    """

    ISWIN = os.name=='nt' # sys.platform[0:3].lower()=='win'

    #/************************************************************************/
    @staticmethod
    def run_cmd(cmd, format='s'):
        """Run a command.

            >>> exit_code, stdout, stderr = SysEnv.run_cmd(cmd, format='s')

        Arguments
        ---------
        cmd : str
            command (inc arguments) to run.
        format : str, optional
            ['s','l'] for (string or list format); default is 's'.

        Returns
        -------
        Returns (exit_code,stdout,stderr)
        """
        from subprocess import Popen, PIPE
        proc = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        if format.lower() == 's': # string output
            stdout, stderr = proc.communicate()
        # elif format.lower() == 'f': # file object output: causes python to hang
        #    stdout,stderr=proc.stdout,proc.stderr # doesn't flush IO buffer...
        elif format.lower() == 'l': # list output
            stdout, stderr = proc.stdout.readlines(), proc.stderr.readlines()
        else:
            raise TypeError("fomat argument must be in ['s','l'] (string or list format)")
        # raise TypeError, "fomat argument must be in ['s','f','l'] (string, file, list)"
        exit_code = proc.wait()
        return exit_code, stdout, stderr

    #/************************************************************************/
    @staticmethod
    def is_running(pid):
        """Check that a process given by it PID is running.

            >>> res = SysEnv.is_running(pid)
        """
        if hasattr(os, 'kill'):
            try:        os.kill(pid, 0) #Sending a 0 signal does nothing.
            except:     return False
            else:       return True
        elif SysEnv.ISWIN:
            from win32process import EnumProcesses
            try:        return pid in EnumProcesses()
            except:     return False

    #/************************************************************************/
    @staticmethod
    def file_exists(filepath, as_path=False):
        """A case insensitive file existence checker.

            >>> a, p = SysEnv.file_exists(file, as_path=False)

        Arguments
        ---------
        file : str
            file whose existence is to be checked.
        as_path : bool, optional
            flag set to return the case sensitive path; def.:  as_path=False.

        Returns
        -------
        a : bool
            `True`/`False` answer to the existence.
        p : str
            optional full path to the case sensitive path.
        """
        def file_check(filepath):
            if not osp.exists(filepath):
                raise IOError("Path not found: '%s'" % filepath)
            return filepath.strip()
        if SysEnv.ISWIN: # Windows is case insensitive anyways
            if as_path:             return osp.exists(filepath),filepath
            else:                   return osp.exists(filepath)
        path, name = osp.split(osp.abspath(filepath))
        files = os.listdir(path)
        for f in files:
            if re.search(f, name, re.I):
                if as_path:         return True, osp.join(path,f)
                else:               return True
        if as_path:                 return False, None
        else:                       return False

    #/************************************************************************/
    @staticmethod
    def find_file(directory, pattern):
        """Find files in a directory and all subdirectories that match a given pattern.

            >>> lst_files = SysEnv.find_file(dir, pattern)
        """
        # for root, dirs, files in os.walk(directory):
        #     for basename in files:
        #         if fnmatch.fnmatch(basename, pattern):
        #             filename = osp.join(root, basename)
        #             yield filename
        from fnmatch import filter
        results = []
        for root, dirs, files in os.walk(directory):
            #print(files)
            #print(fnmatch.filter(files, pattern))
            results.extend(osp.join(root, f) for f in filter(files, pattern))
        return results

    #/************************************************************************/
    @staticmethod
    def is_writable(file):
        """Determine if a temporary file can be written in the same directory as a
        given file.

            >>> resp = SysEnv.is_writable(file)
        """
        if not osp.isdir(file):
            file = osp.dirname(file)
        try:
            from tempfile import TemporaryFile
            tmp = TemporaryFile(dir=file) # can we write a temp file there...?
        except: return False
        else:
            del tmp
            return True

    #/************************************************************************/
    @staticmethod
    def guess_type(filepath, option='type'):
        """Coarsely retrieve a file MIME type.

            >>> out = SysEnv.guess_type(file, option)

        Arguments
        ---------
        option : str, optional
            string setting the output to be returned; it is either the 'type', the
            'subtype' or the 'encoding', or the whole 'mime' figure; def.: 'type'.

        Returns
        -------
        out : str, bool
            MIME figure caracterizing the input file as stated by the 'guess_type'
            function of mimetypes; any of the results above depending on the input option;
            if the file does not exist, False is returned, if the MIME type is not
            recognized, True is returned.
        """

        from mimetypes import read_mime_types, guess_type
        if read_mime_types(filepath) is None:
            return False
        mimetype, encoding = guess_type(filepath)
        if mimetype is None:
            return True
        if option == 'type':              return mimetype.split('/')[0]
        elif option == 'subtype':         return mimetype.split('/')[1]
        elif option == 'encoding':        return encoding
        elif option == 'mime':            return mimetype
        else:
            raise IOError("bad option %s provided!" % option)

    #/************************************************************************/
    @staticmethod
    def make_dir(directory):
        """Safe directory creation (mkdir) command.

            >>> SysEnv.make_dir(dir)
        """
        if not osp.exists(directory):
            os.mkdir(directory)
        return directory

    #/************************************************************************/
    @staticmethod
    def remove(filepath, rmdir=False):
        """Safe remove (rm) command.

            >>> SysEnv.remove(file, rmdir=False)
        """
        if osp.exists(filepath):
            os.remove(filepath)
        elif rmdir is True and osp.isdir(filepath):
            shutil.rmtree(filepath)

    #/************************************************************************/
    @staticmethod
    def fill_path(rootpath, relfolderpath, relfilepath):
        """Determine the absolute path of a file given by its relative path wrt
        a folder itself given by a relative path wrt root path.

            >>> path = SysEnv.fill_path(rootpath, relfolderpath, relfilepath)
        """
        folderpath = osp.join(rootpath, relfolderpath)
        return osp.abspath(osp.join(folderpath, relfilepath))

    #/************************************************************************/
    @staticmethod
    def uuid(file):
        """Generate a uuid reproducible based on an empty string or a filename.

            >>> id = SysEnv.uuid(file=None)
        """
        if file in ('', None):
            return uuid4().hex
        else:
            file = SysEnv.norm_case(SysEnv.real_path(file))
            return uuid3(NAMESPACE_DNS,file).hex

    #/************************************************************************/
    @staticmethod
    def file_info(filepath, **kwargs):
        """Provide various information about a file.

            >>> info = SysEnv.file_info(file, **kwargs)

        Keyword Arguments
        -----------------
        date,time,dfmt : str
            see :meth:`datetimeformat`\ .

        Returns
        -------
        info : dict
            dictionary containing various information about :data:`filepath`, namely
            its :data:`uuid`, :data:`size`, date of modification (:data:`datemodified`),
            date of creation (:data:`datecreated`), date of last access (:data:`dateaccessed`),
            the owner's id (:data:`ownerid`) and the owner's name (:data:`ownername`).
        """
        if not osp.exists(filepath):
            raise IOError("File '%s' not found" % filepath)
        fileinfo = {
            'size':0,
            'datemodified':'',
            'datecreated': '',
            'dateaccessed':''
        }
        def _winFileOwner(filepath):
            import win32com.client
            import win32net, win32netcon
            OWNERID=8
            try:
                d=osp.split(filepath)
                oShell = win32com.client.Dispatch("Shell.Application")
                oFolder = oShell.NameSpace(d[0])
                ownerid=str(oFolder.GetDetailsOf(oFolder.parsename(d[1]), OWNERID))
                ownerid=ownerid.split('\\')[-1]
            except: ownerid='0'
            try:
               dc=win32net.NetServerEnum(None,100,win32netcon.SV_TYPE_DOMAIN_CTRL)
               if dc[0]:
                   dcname=dc[0][0]['name']
                   ownername=win32net.NetUserGetInfo(r"\\"+dcname,ownerid,2)['full_name']
               else:
                   ownername=win32net.NetUserGetInfo(None,ownerid,2)['full_name']
            except: ownername='No user match'

            return ownerid,ownername
        def _ixFileOwner(uid): # Posix, Unix, ...
            import pwd
            pwuid = pwd.getpwuid(uid)
            ownerid = pwuid[0]
            ownername = pwuid[4]
            return ownerid,ownername
        try:
            filepath = SysEnv.norm_case(osp.realpath(filepath))
            filestat = os.stat(filepath)
            fileinfo['filename'] = osp.basename(filepath)
            fileinfo['filepath'] = filepath
            fileinfo['size'] = filestat.st_size
            fileinfo['datemodified'] = \
                time.strftime(DateTime.dtformat(**kwargs), time.localtime(filestat.st_mtime))
            fileinfo['datecreated'] = \
                time.strftime(DateTime.dtformat(**kwargs), time.localtime(filestat.st_ctime))
            fileinfo['dateaccessed'] = \
                time.strftime(DateTime.dtformat(**kwargs), time.localtime(filestat.st_atime))
            fileinfo['uuid'] = SysEnv.uuid(filepath)
            #if sys.platform[0:3].lower()=='win':
            if SysEnv.ISWIN:       ownerid, ownername = _winFileOwner(filepath)
            else:           ownerid, ownername = _ixFileOwner(filestat.st_uid)
            fileinfo['ownerid'] = ownerid
            fileinfo['ownername'] = ownername
        finally:
            return fileinfo

    #/************************************************************************/
    @staticmethod
    def norm_case(file):
        """Normalise case of pathname by making all characters lowercase and all slashes
        into backslashes.

            >>> new = SysEnv.norm_case(file)
        """
        #if type(file) in [list,tuple]:
        if not hasattr(file,'__iter__'):
            return osp.normcase(file)
        else:
            return [osp.normcase(i) for i in file] # iterable

    #/************************************************************************/
    @staticmethod
    def base_name(file):
        """Extract the base name of a file.

            >>> base = base_name(file)
        """
        # return osp.splitext(osp.split(file)[1])[0]
        return osp.splitext(osp.basename(file))[0]

    #/****************************************************************************/
    def ext_name(file, newext):
        """Change the extension of a file.

            >>> ext = ext_name(file)
        """
        if not newext.startswith('.'):
            newext = '.' + newext
        base = osp.splitext(file)[0]
        return base + newext

    #/************************************************************************/
    @staticmethod
    def file_name(file):
        """Retrieve the...file name.

            >>> name = file_name(file)
        """
        return osp.split(file)[1]

    #/************************************************************************/
    @staticmethod
    def norm_path(file):
        """Normalize path, eliminating double slashes, etc.

            >>> new = norm_path(file)
        """
        if not hasattr(file,'__iter__'):
            return osp.normpath(file)
        else:
            return [osp.normpath(i) for i in file]

    #/************************************************************************/
    @staticmethod
    def real_path(file):
        """Return the absolute version of a path.

            >>> real = SysEnv.real_path(file)

        Note
        ----
        `osp.realpath/os.path.abspath` returns unexpected results on windows if `filepath[-1]==':'`
        """
        if hasattr(file,'__iter__'): # is iterable
            if SysEnv.ISWIN: # global variable
                realpath=[]
                for f in file:
                    if f[-1] == ':': f += '\\'
                    realpath.append(osp.realpath(f))
            else:
                return [osp.realpath(f) for f in file]
        else:
            if SysEnv.ISWIN and file[-1] == ':':     file += '\\'
            return osp.realpath(file)

    #/************************************************************************/
    @staticmethod
    def default_cache(basename=None):
        platform = sys.platform
        if platform.startswith("win"): # windows
            basedir = os.getenv("LOCALAPPDATA",os.getenv("APPDATA",osp.expanduser("~")))
        elif platform.startswith("darwin"): # Mac OS
            basedir = osp.expanduser("~/Library/Caches")
        else:
            basedir = os.getenv("XDG_CACHE_HOME",osp.expanduser("~/.cache"))
        return osp.join(basedir, SysEnv.uuid(basename))

    #/************************************************************************/
    @staticmethod
    def build_cache(path, cache_store=None):
        if cache_store in (None,''):
            cache_store = './'
        # elif cache_store in (None,'default'):
        #    cache_store = File.default_cache()
        pathname = path.encode('utf-8')
        try:
            pathname = hashlib.md5(pathname).hexdigest()
        except:
            pathname = pathname.hex()
        return osp.join(cache_store, pathname)

    #/************************************************************************/
    @staticmethod
    def is_cached(pathname, time_out): # note: we check a path here
        if not osp.exists(pathname):
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
            warn("\n! %s - last modified: %s !" % (pathname,time.ctime(mtime)))
            resp = cur - mtime < time_out
        return resp

    #/************************************************************************/
    @staticmethod
    def clean_cache(pathname, time_expiration): # note: we clean a path here
        if not osp.exists(pathname):
            resp = False
        elif time_expiration is None or time_expiration <= 0:
            resp = True
        else:
            cur = time.time()
            mtime = os.stat(pathname).st_mtime
            warn("\n! '%s' - last modified: %s !" % (pathname,time.ctime(mtime)))
            resp = cur - mtime >= time_expiration
        if resp is True:
            warn("\n! Removing disk file %s !" % pathname)
            SysEnv.remove(pathname, rmdir=True)

    #/************************************************************************/
    @staticmethod
    def chardet_detect(file):
        try:
            encoding = chardet.detect(file)
        except:
            raise IOError("Could not detect encoding")
        else:
            return encoding

    #/************************************************************************/
    @staticmethod
    def chardet_decorate(fun):
        def file_chardet(file, *args, **kwargs):
            encoding = SysEnv.chardet_detect(file)
            try:
                encoding = encoding['encoding']
            except:
                pass
            else:
                kwargs.update({'encoding': encoding})
            return fun(file, *args, **kwargs)
        return file_chardet

#==============================================================================
# Class DateTime
#==============================================================================

class DateTime(object):
    """Static and class methods for datetime objects manipulation.
    """

    try:
        UTC_TZ  = dateutil.tz.tzutc()
    except:
        try:    UTC_TZ  = pytz.timezone('UTC')
        except: UTC_TZ  = None

    try:    LOCAL_TZ    = dateutil.tz.tzlocal()
    except: LOCAL_TZ    = None #  pytz.localize()

    DICT_TIMEZ          = {'local': LOCAL_TZ, 'utc': UTC_TZ}
    __DEF_TIMEZ           = DICT_TIMEZ['local'] # 'utc'

    ZERO                = datetime.timedelta(0)
    HOUR                = datetime.timedelta(hours=1)
    __DICT_DURATION       = {'zero': ZERO, 'hour': HOUR}

    TODAY               = datetime.date.today # lambda: datetime.date.fromtimestamp(time.time())
    NOW                 = datetime.datetime.now
    UTCNOW              = datetime.datetime.utcnow
    TOMORROW            = lambda: DateTime.TODAY() + datetime.timedelta(1)
    IN24HOURS           = lambda: DateTime.NOW() + datetime.timedelta(1)
    # those are functions
    __DICT_NOW            = {'now': NOW, 'utcnow': UTCNOW, 'today': TODAY,
                             'tomorrow': TOMORROW, 'in24hours': IN24HOURS}

    __YR_TO     = {'sec':31556940,   'mn':525949,    'hr':8765.81, 'd':365.242,  'm':12,               'y':1 }
    __MTH_TO    = {'sec':2629739.52, 'mn':43828.992, 'hr':730.484, 'd':30.4368,  'm':1,                'y':1./12}
    __DAY_TO    = {'sec':86400,      'mn':1440,      'hr':24,      'd':1,        'm':1./__MTH_TO['d'],   'y':1./__YR_TO['d']}
    __HR_TO     = {'sec':3600,       'mn':60,        'hr':1,       'd':1./24,    'm':1./__MTH_TO['hr'],  'y':1./__YR_TO['hr']}
    __MN_TO     = {'sec':60,         'mn':1,         'hr':1./60,   'd':1./1440,  'm':1./__MTH_TO['mn'],  'y':1./__YR_TO['mn']}
    __SEC_TO    = {'sec':1,          'mn':1./60,     'hr':1./3600, 'd':1./86400, 'm':1./__MTH_TO['sec'], 'y':1./__YR_TO['sec']}

    UNITS_TO =  {'y': __YR_TO, 'm': __MTH_TO, 'd': __DAY_TO,
                 'hr': __HR_TO, 'mn': __MN_TO, 'sec': __SEC_TO}

    TIMING_UNITS = ['y', 'm', 'd', 'hr', 'mn', 'sec'] # list(__YR_TO.keys())

    DATETIME_KWARGS = { 'y':'year', 'm' :'month', 'd':'day',
                        'hr':'hour', 'mn':'minute', 'sec':'second'}
    __DATETIME_KWARGS_REV = {v:k for (k,v) in DATETIME_KWARGS.items()}
    __DATETIME_ITEMS = list(DATETIME_KWARGS.keys()) + list(DATETIME_KWARGS.values())

    TIMEDELTA_KWARGS = { 'y':'years', 'm' :'months', 'd':'days',
                         'hr':'hours', 'mn':'minutes', 'sec':'seconds'}
    __TIMEDELTA_KWARGS_REV = {v:k for (k,v) in TIMEDELTA_KWARGS.items()}
    __TIMEDELTA_ITEMS = list(TIMEDELTA_KWARGS.keys()) + list(TIMEDELTA_KWARGS.values())

    #/************************************************************************/
    @classmethod
    def units_to(cls, from_, to, time=1.):
        """Perform simple timing units conversion.

            >>> t = DateTime.units_to(from, to, time=1.)

        Arguments
        ---------
        from,to : str
            'origin' and 'final' units: any strings in :literal:`['y', 'm', 'd', 'hr', 'mn', 'sec']` .
        time : float
            timing value to convert.

        Examples
        --------
        >>> DateTime.units_to('mn', 'hr',  time=60) == 1
            True
        >>> DateTime.units_to('sec', 'd',  10) == 10*DateTime.UNITS_TO['sec']['d']
            True
        >>> DateTime.units_to('hr', 'sec',  5) == 5*DateTime.UNITS_TO['hr']['sec']
            True
        """
        if not(from_ in cls.__TIMEDELTA_ITEMS and to in cls.__TIMEDELTA_ITEMS):
            raise TypeError('Timing units not implemented')
        else:
            if from_ in cls.TIMEDELTA_KWARGS.values():
                from_ = cls.__TIMEDELTA_KWARGS_REV[from_]
            if to in cls.TIMEDELTA_KWARGS.values():
                to = cls.__TIMEDELTA_KWARGS_REV[to]
        return cls.UNITS_TO[from_][to] * time

    #/************************************************************************/
    @classmethod
    def convert_time_units(cls, to='mn', **kwargs):
        """Convert composed timing units to a single one.

            >>> t = DateTime.convert_time_units(to, **kwargs)

        Arguments
        ---------
        to : str
            desired 'final' unit: any string in :literal:`['y', 'm', 'd', 'hr', 'mn', 'sec'] `;
            default to :literal:`'mn' `.

        Keyword Arguments
        -----------------
        kwargs : dict
            dictionary of composed times indexed by their unit, which can be any
            string in :literal:`['y', 'm', 'd', 'hr', 'mn', 'sec'] `.

        Note
        ----
        Quantities to convert are passed either as a dictionary or as positional
        arguments:

        Example
        -------
        >>> DateTime.convert_time_units('mn', **{{'hr':1, 'sec':420}}) == 67
            True
        >>> DateTime.convert_time_units('mn', hr=1,  sec=420) == 67
            True
        """
        if not to in cls.__TIMEDELTA_ITEMS:
            raise IOError("Timing unit '%s' not implemented" % to)
        elif to in cls.TIMEDELTA_KWARGS.values():
            to = cls.__DATETIME_KWARGS_REV[to]
        t = 0
        for u in cls.__TIMEDELTA_ITEMS:
            if u in kwargs: t += cls.units_to(u, to, kwargs.get(u))
        return t

    #/************************************************************************/
    @classmethod
    def date_time(cls, *arg, **kwargs):  # datetime = arg
        """Perform time conversions in between various (not so) standard timing
        formats: unix timestamp, isoformat, ctime, ...

            >>> dt = DateTime.date_time(*dtime, **kwargs)

        Arguments
        ---------
        dtime : datetime.datetime, datetime.date, str, float, dict
            an object specifying a time, e.g. it can be:

            - a :class:`datetime.datetime` (or :class:`datetime.date`) object:
              :literal:`datetime.datetime(2014, 6, 19, 17, 58, 5)`,
            - an iso-formated (ISO 8601) date: :literal:`"2014-06-19T17:58:05"` or
              :literal:`"2014-06-19 17:58:05"`,
            - a string date: :literal:`"Thu Jun 19 17:58:05 2014"`,
            - a float representing a unix timestamp date: :literal:`1403193485`,
            - an explicit string date: :literal:`"45d 34hr 2900mn 4m 500sec 2y"`
              (where order does not matter),
            - a dictionary-like date: :literal:`{{'y':2, 'm':4, 'd':45, 'hr':34, 'mn':2900, 'sec':500}}`.

            When the date is expressed as an 'explicit string' or a dictionary, a time unit
            is any string in :literal:`['y', 'm', 'd', 'hr', 'mn', 'sec'] `.

            'now', 'utcnow' and 'today' are also accepted instead of an explicit date.

        Keyword Arguments
        -----------------
        dfmt : str
            variable specifying the desired output timing format: it can be any string
            among:

            - 'datetime' to output a :class:`datetime.datetime` object,
            - 'dict' to output a dictionary indexed by the timing units, where a key
              is any string in :literal:`['y', 'm', 'd', 'hr', 'mn', 'sec'] `
              (see also :meth:`datetime.timetuple` method)),
            - 'timestamp' to output a unix timestamp (see also :meth:`calendar.timegm`
              method)),
            - 'iso' to output an iso-formated string date (see also
              :meth:`datetime.isoformat` method),
            - 'calendar' to output a calendar (ISO year, week number, and weekday) date
              (see also :meth:`datetime.isocalendar` method),

            as well as:

            - a date formating string (e.g. :literal:`'%Y-%m-%dT%H:%M:%S'`, see :meth:`datetime.strftime`),
            - :literal:`True` to force a string naming (see :meth:`time.ctime` method)).

            When nothing is passed, a default output format is considered, depending
            on the input format of `dtime` (e.g. a :class:`datetime` object is output for a
            :class:`dict` `dtime`, ...).
        no_micro_secs : bool
            set to :literal:`False` to display microseconds as part of the output datetime when the
            chosen output format is the isoformat; default: :literal:`True`.

        Return
        ------
        dt : datetime.datetime, str, float, dict, calendar (tuple)
            a well-formatted (according to `dfmt` specification) object
            representing a datetime equivalent to the input `dtime`.

        Note
        ----
        As for the :class:`dict` format of the input :literal:`dtime`, long time unit names (keys in
        :literal:`['years', 'months', 'days', 'hours', 'minutes', 'seconds']`) are also accepted.

        As for the `timestamp` format, a default timezone is automatically attached
        to the datetime.

        Example
        -------
        >>> import datetime

        Let's construct some datetime objects:

        >>> dt = datetime.datetime(2014, 6, 19, 17, 58, 5)
        >>> dt_dict = {{'y':2014, 'm':6, 'd':19, 'hr':17, 'mn':58,  'sec':5}}

        Again, we can use dictionary of positional arguments to pass the proper format:

        >>> dt == DateTime.date_time(dt_dict, dfmt='datetime')
            True
        >>> dt == DateTime.date_time("Thu Jun 19 17:58:05 2014", dfmt='datetime')
            True

        By default, it behaves 'well' in many circumstances:

        >>> dt == DateTime.date_time(dt_dict)
            True
        >>> DateTime.date_time(dt_dict) == DateTime.date_time(**dt_dict)
            True

        However:

        >>> DateTime.date_time(dt, dfmt='dict')
            {{'second': 5, 'hour': 17, 'year': 2014, 'day': 19, 'minute': 58, 'month': 6}}

        Many more conversions are possible though:

        >>> DateTime.date_time(dt, dfmt='%Y-%m-%dT%H:%M:%S')
            '2014-06-19T17:58:05'
        >>> DateTime.date_time(dt_dict, dfmt='%Y-%m-%dT%H:%M:%S')
            '2014-06-19T17:58:05'
        >>> DateTime.date_time(dt_dict, dfmt=%Y-%m-%d %H:%M:%S+00')
            '2014-06-19 17:58:05+00'
        >>> DateTime.date_time(dt, dfmt='%Y-%m-%d %H:%M:%S')
            '2014-06-19 17:58:05'
        >>> DateTime.date_time(dt_dict, dfmt='%Y-%m-%d')
            '2014-06-19'
        >>> DateTime.date_time(dt, dfmt=True) # use ctime()
            "Thu Jun 19 17:58:05 2014"
        >>> DateTime.date_time(dt_dict, dfmt='calendar')
            (2014, 25, 4)
        >>> DateTime.date_time(dt_dict, dfmt='iso')
            '2014-06-19T17:58:05'
        >>> DateTime.date_time(dt, dfmt='iso')
            '2014-06-19T17:58:05'
        >>> DateTime.date_time("Thu Jun 19 17:58:05 2014")
            {{'second': 5, 'hour': 17, 'year': 2014, 'day': 19, 'minute': 58, 'month': 6}}

        Mind the UTC:

        >>> import dateutil
        >>> utc_tz = dateutil.tz.tzutc() # note: same as timing.UTC_TZ
        >>> dt_utc = dt.replace(tzinfo=utc_tz)
        >>> DateTime.date_time(dt_utc, dfmt=timestamp')
            1403200685

        As desired, the operation is idempotent (when the right parameters are passed!):

        >>> f_dt = DateTime.date_time(dt, dfmt='%Y-%m-%d %H:%M:%S')
        >>> dt == DateTime.date_time(f_dt, dfmt='datetime')
            True
        >>> f_dt_utc = DateTime.date_time(dt_utc, dfmt='timestamp')
        >>> dt_utc == DateTime.date_time(f_dt_utc, dfmt='datetime')
            True

        As for the `no_micro_secs` keyword argument, it is useful to avoid some
        'unpleasant' notation:

        >>> dt = datetime.datetime.now()
        >>> dt
            datetime.datetime(2014, 8, 18, 14, 56, 17, 821000)
        >>> print(dt)
            2014-08-18 14:56:17.821000
        >>> DateTime.date_time(dt, dfmt='iso')
            '2014-08-18T14:56:17'
        >>> DateTime.date_time(dt, dfmt='iso', no_micro_secs=False)
            '2014-08-18T14:56:17.821000'

        Though it does not affect most representations:

        >>> DateTime.date_time(dt, dfmt=True, no_micro_secs=False)
        'Mon Aug 18 14:56:17 2014'
        """
        no_micro_second = kwargs.pop('no_micro_secs',True)
        dtime, unix, isoformat, dict_, isocal = False, False, False, False, False
        dfmt = kwargs.pop('dfmt',False)
        if arg in ((),None):            arg = kwargs
        else:                           arg = arg[0]
        if arg is None:
            return None
        elif isinstance(arg,string_types) and arg in cls.__DICT_NOW.keys():
            arg = cls.__DICT_NOW[arg]()
            if dfmt is False:    dtime = True
        elif isinstance(arg, (int,float)):
            try:    arg = datetime.datetime.fromtimestamp(arg, cls.__DEF_TIMEZ) # we put a tz
            except: raise IOError("Timestamp %s not recognised" % arg)
        elif not isinstance(arg, (string_types,Mapping,datetime.datetime,datetime.date)):
            raise TypeError("Wrong input date time format")
        if dfmt=='datetime':             dfmt, dtime = None, True
        elif dfmt=='timestamp':          dfmt, unix = None, True
        elif dfmt=='iso':                dfmt, isoformat = None, True
        elif dfmt=='dict':               dfmt, dict_ = None, True
        elif dfmt=='calendar':           dfmt, isocal = None, True
        elif dfmt=='default':            dfmt = '%Y-%m-%dT%H:%M:%S' #ISO 8601 same as the one returned by datetime.datetime.isoformat
        elif not isinstance(dfmt,(bool,string_types)):
            raise TypeError("Wrong timing format")
        # special case: already an instance datetime.datetime
        # proceed...
        d_datetime, _datetime = {}, None
        if isinstance(arg,(datetime.datetime,datetime.date)):
            _datetime, arg = arg, arg.ctime()
        # update the possible output formats
        if isinstance(arg,(string_types,datetime.datetime,datetime.date)) and not (dfmt or isoformat or isocal or dict_ or unix):
            dict_ = True
        if isinstance(arg,string_types):
            try:
                if _datetime is None:   _datetime = dateutil.parser.parse(arg)
                [d_datetime.update({unit: getattr(_datetime,unit)}) for unit in cls.DATETIME_KWARGS.values()]
            except:
                for unit in cls.__DATETIME_ITEMS:
                    pattern = r'(.*)\d*\.*\d*\s*' + unit + r'(\d|\s|$)+(.*)' # raw string pattern
                    x = re.search(pattern,arg)
                    if x is None:  continue
                    elif unit in cls.DATETIME_KWARGS.keys():
                        unit = cls.DATETIME_KWARGS[unit]
                    if d_datetime.get(unit) is None:    d_datetime[unit] = 0
                    x = re.match('.*?([.0-9]+\s*)$',x.group(1))
                    if x is None:  continue
                    else:
                        d_datetime[unit] += eval(x.group(1))
        elif isinstance(arg,Mapping):
            for unit in cls.__DATETIME_ITEMS:
                if unit not in arg:         continue
                else:                       t = arg.get(unit)
                if unit in cls.DATETIME_KWARGS.keys():
                    unit = cls.DATETIME_KWARGS[unit]
                if d_datetime.get(unit) is None:    d_datetime[unit] = 0
                d_datetime[unit] += t
        try:                assert _datetime
        except:             _datetime = datetime.datetime(**d_datetime)
        try:                _datetime = _datetime.replace(microsecond=0) if no_micro_second else _datetime
        except:             pass
        if not(dfmt or dtime or isoformat or isocal or dict_ or unix):
            dtime = True
        if isoformat:
            try:    return _datetime.isoformat()
            except: raise IOError("Isoformat not implemented")
        elif isocal:
            try:    return _datetime.isocalendar()
            except: raise IOError("Isocalendar format not implemented")
        elif dfmt:
            if not(isinstance(dfmt,bool) or any([re.search(s,dfmt) for s in ('%Y','%m','%d','%H','%M','%S')])):
                raise IOError("String format is not a standard datetime format")
            try:    return _datetime.ctime() if dfmt is True else _datetime.strftime(dfmt)
            except: raise IOError("Format not implemented")
        elif unix:
            if _datetime.tzinfo is None:
                # _datetime is most likely a naive datetime; we assume it is in fact
                # a default ('local' or 'utc', depending on __DEF_TIMEZ variable) time
                _datetime = _datetime.replace(tzinfo=cls.__DEF_TIMEZ)
            try:
                _datetime = _datetime.astimezone(tz=cls.DICT_TIMEZ['utc'])
            except: pass
             # calendar.timegm() assumes it's in UTC
            try:    return calendar.timegm(_datetime.timetuple())
            except: raise IOError("Unix format not implemented")
            # instead, time.mktime() assumes that the passed tuple is in local time
            # return time.mktime(_datetime.timetuple())
        elif dtime:
            return _datetime
        elif dict_:
            return d_datetime

    #/************************************************************************/
    @classmethod
    def time_delta(cls, *span, **kwargs):
        """Perform some duration calculations and conversions.

            >>> dt = DateTime.time_delta(*span, **kwargs)
            >>>

        Arguments
        ---------
        span : datetime.timedelta, str, float, dict
            an object specifying a duration, e.g. it can be any form likewise:

            - a :class:`datetime.timedelta` object:
              :literal:`datetime.timedelta(2014, 6, 19, 17, 58, 5)`,
            - an explicit duration string:
              :literal:`'2900mn 45d 500sec 34hr 4m 2y'`,
              (where order does not matter),
            - an equivalent dictionary-like date:
              :literal:`{{'{years}':2, '{months}':4, '{days}':45, '{hours}':34, '{minutes}':2900, '{seconds}':500}}`.

            When the date is expressed as an 'explicit string' or a dictionary, a time duration
            unit can be any string in :literal:`['years', 'months', 'days', 'hours', 'minutes', 'seconds']` .

            'zero' and 'hour' are also accepted  instead of an explicit duration, and used
            to represent both null and 1-hour durations.

        Keyword Arguments
        -----------------
        dfmt : str
            variable specifying the desired output duration format: it can be any string
            among:

            - 'timedelta' to output a :class:`datetime` object,
            - 'dict' to output a dictionary indexed by the timing units, where a key
              is any string in :literal:`['years', 'months', 'days', 'hours', 'minutes', 'seconds']`,
            - 'str' to output an explicit duration string (not used).

        timing : str
            if instead, some conversions is expected, this is used to pass the desired
            output format: it can be any string in :literal:`['y', 'm', 'd', 'hr', 'mn', 'sec']` .

        Example
        -------
        >>> import datetime
        >>> DateTime.time_delta('hour')
            '3600.0sec'

        Let's construct some timedelta objects that are equivalent:

        >>> td = datetime.timedelta(900, 57738, 80000)
        >>> td_str = '45d 34hr 2900mn 4m 500sec 2y'
        >>> td_dict = {{'y':2, 'm':4, 'd':45, 'hr': 34, 'mn': 2900, 'sec': 500}}

        as to check the consistency:

        >>> DateTime.time_delta(td_str, dfmt='dict') == td_dict
            True
        >>> td == DateTime.time_delta(td_str, **{{'dfmt': 'timedelta'}}),
            True
        >>> DateTime.time_delta(td_str, dict=True)
            {{'d': 45, 'hr': 34, 'mn': 2900, 'm': 4, 'sec': 500, 'y': 2}}
        >>> DateTime.time_delta(td_dict) == DateTime.time_delta(td_dict_bis)
            True
        >>> DateTime.time_delta(td_str) == DateTime.time_delta('4m 34hr 500sec 2y 2900mn 45d ')
            True
        >>> DateTime.time_delta(td_str, **{{'timing': True}}) == td_dict
            True
        >>> DateTime.time_delta(td_dict, timing=True) == td_str

        Note that these one work too:

        >>> DateTime.time_delta(**td_dict) == td_str
            True
        >>> DateTime.convert_time_units('d', **td_dict) > td.days
            True
        """
        timing = kwargs.pop('timing',None) #
        tdelta, str_, dict_ = False, False, False
        dfmt = kwargs.pop('dfmt',False) # 'dfmt''
        if dfmt=='timedelta':            dfmt, tdelta = None, True
        elif dfmt=='dict':               dfmt, dict_ = None, True
        elif dfmt=='str':                dfmt, _ = None, True#analysis:ignore
        elif not isinstance(dfmt,bool):
            raise   TypeError("Wrong timing format")
        if span in ((),None):           span = kwargs
        else:                           span = span[0]
        if span is None:
            return None
        elif isinstance(span,string_types) and span in cls.__DICT_DURATION.keys():
            span = cls.__DICT_DURATION[span]
        elif not isinstance(span, (string_types, Mapping,datetime.timedelta)):
            raise TypeError("Wrong input timing format")
        # special case: already an instance datetime.timedelta
        if isinstance(span,datetime.timedelta):
            span = {'sec': span.total_seconds()}
        # by default, when no argument is passed, none of the timing/tdelta arguments
        # is passed, we assume  that the return type is not the input one
        dict_ = dict_ or isinstance(span,str)
        # proceed...
        d_span = {}
        if isinstance(span,string_types):
            for unit in cls.__TIMEDELTA_ITEMS:
                pattern = r'(.*)\d*\.*\d*\s*' + unit + r'(\d|\s|$)+(.*)' # raw string pattern
                x = re.search(pattern,span)
                if x is None:       continue
                elif unit in cls.TIMEDELTA_KWARGS.values():
                    unit = cls.__TIMEDELTA_KWARGS_REV[unit]
                if d_span.get(unit) is None:    d_span[unit] = 0
                d_span[unit] += eval(re.match('.*?([.0-9]+\s*)$',x.group(1)).group(1))
        elif isinstance(span,Mapping):
            for unit in cls.__TIMEDELTA_ITEMS:
                if unit not in span:    continue
                else:                       val_span = span.get(unit)
                if unit in cls.TIMEDELTA_KWARGS.values():
                    unit = cls.__TIMEDELTA_KWARGS_REV[unit]
                if d_span.get(unit) is None:    d_span[unit] = 0
                d_span[unit] += val_span
            span = ' '.join([str(v)+k for (k,v) in d_span.items()])
        timing = timing if not tdelta else 'mn'
        if timing in cls.TIMING_UNITS:
            # convert into one single unit
            span = cls.convert_time_units(timing, **d_span)
            if tdelta:
                return datetime.timedelta(**{'minutes': span})
            else:
                return span
        elif dict_:
            return d_span
        else: #if _:
            return span

    #/************************************************************************/
    @classmethod
    def span(cls, **kwargs):
        """Calculate the timing span (duration) in between two given beginning
        and ending date(time)s.

            >>> d = DateTime.span(**kwargs)

        Keyword Arguments
        -----------------
        since,until : datetime.datetime, datetime.date, str, float, dict
            beginning and ending (respectively) time instances whose formats are any
            of those accepted by :meth:`DateTime.date_time` (not necessarly identical
            for both instances).
        dfmt : str
            additional parameter for formatting the output result: see :meth:`~DateTime.time_delta`;
            default is a :class`datetime.datetime` format.

        Returns
        -------
        d : datetime.timedelta, str, float, dict
            duration between the `since` and `until` timing instances, expressed in any
            the format passed in `dfmt` and accepted by :meth:`DateTime.time_delta`\ .

        Example
        -------
        >>> since = datetime.datetime.now()
        >>> print(since)
            2014-08-18 19:30:40.970000
        >>> until = since + datetime.timedelta(10) # 10 days
        >>> until # this is a datetime
            datetime.datetime(2014, 8, 28, 19, 30, 40, 970000)
        >>> print(until) # which displays microseconds
            2014-08-28 19:30:40.970000
        >>> print(until - since)
            10 days, 0:00:00
        >>> DateTime.span(since=since, until=until)
            datetime.timedelta(10)
        >>> DateTime.span(since=since, until=until, dfmt='str')
            '864000.0sec'

        The fact that microseconds are not taken into account ensures the consistency
        of the results when converting in between different formats:

        >>> until_iso = DateTime.date_time(until, dfmt='iso')
        >>> until_iso
            '2014-08-28T19:30:40'
        >>> print(until_iso) # microseconds have been dumped...
            2014-08-28T19:30:40
        >>> DateTime.span(since=since, until=until_iso)
            datetime.timedelta(10) # 10 days as set

        However, if we were precisely taking into account the microseconds:

        >>> DateTime.span(since=since, until=until_iso, no_micro_secs=False)
            datetime.timedelta(9, 86399, 30000)

        while this obviously does not affect the precise calculation:

        >>> DateTime.span(since=since, until=until, no_micro_secs=False)
            datetime.timedelta(10)
        """
        since, until = kwargs.pop('since',None), kwargs.pop('until',None)
        if not(since and until):
            raise IOError("Missing arguments")
        no_micro_second = kwargs.pop('no_micro_secs',True)
        since = cls.date_time(since, dfmt='datetime', no_micro_secs=no_micro_second),
        until = cls.date_time(until, dfmt='datetime', no_micro_secs=no_micro_second)
        if operator.xor(until.tzinfo is None, since.tzinfo is None):
            if until.tzinfo is None:
                until = until.replace(tzinfo=cls.__DEF_TIMEZ)
            else:
                since = since.replace(tzinfo=cls.__DEF_TIMEZ)
        span = until - since
        if not kwargs.get('dfmt') or kwargs.get('dfmt')=='datetime':
            return span
        else:
            return cls.time_delta(span, **kwargs)

    #/************************************************************************/
    @classmethod
    def since(cls, **kwargs):
        """Calculate a beginning date(time) given a duration and an ending date(time).

            >>> s = DateTime.since(**kwargs))

        Keyword Arguments
        -----------------
        until : datetime.datetime, datetime.date, str, float, dict
            ending date instance whose format is any of those accepted by :meth:`DateTime.date_time`.
        span : datetime.timedelta, str, float, dict
            duration expressed in any of the formats accepted by :meth:`DateTime.time_delta`\ .
        dfmt : str
            additional parameter for formatting the output result: see :meth:`DateTime.date_time`\ .

        Returns
        -------
        s : datetime.datetime, str, float, dict
            beginning date estimated from :literal:`until` and :literal:`span` timing
            arguments, expressed in any format as in :literal:`dfmt` and  accepted by
            :meth:`DateTime.date_time`\ .

        Example
        -------
        >>> since = datetime.datetime.now() # this is: datetime.datetime(2014, 8, 19, 16, 27, 41, 629000)
        >>> print(since)
            2014-08-19 16:27:41.629000
        >>> span = '1d'
        >>> until = since + datetime.timedelta(1)
        >>> print(until)
            2014-08-20 16:27:41.629000
        >>> print(DateTime.since(until=until, span=span))
            {{'second': 41, 'hour': 16, 'year': 2014, 'day': 20, 'minute': 27, 'month': 8}}
        >>> since_c = DateTime.since(until=until, span=span, dfmt='datetime')
        >>> print(since_c) # this is: datetime.datetime(2014, 8, 19, 16, 23, 27)
            2014-08-20 16:27:41
        >>> since_c == since
            False
        >>> since_c - since # we missed the microseconds...
            datetime.timedelta(0, 86399, 371000)

        Again, we can ensure precision by including the microseconds in the calculation:

        >>> since_c = DateTime.since(until=until, span=span, dfmt='datetime', no_micro_secs=False)
        >>> print(since_c) # this is datetime.datetime(2014, 8, 20, 16, 27, 41, 629000)
            2014-08-19 16:27:41.629000
        >>> since_c == since
            True

        Other results are as expected, independently of the format of the input arguments:

        >>> until_iso = DateTime.date_time(until, dfmt='iso')
        >>> print(until_iso)
            2014-08-20T16:27:41
        >>> DateTime.since(until=until_iso, span=span, dfmt=dict)
            {{'second': 41, 'hour': 16, 'year': 2014, 'day': 19, 'minute': 27, 'month': 8}}
        """
        until, span = kwargs.pop('until',None), kwargs.pop('span',None)
        if not(until and span):
            raise IOError("Missing arguments")
        # make a precise calculation, up to the microsecond
        since = cls.date_time(until, dfmt='datetime', no_micro_secs=False)  \
            - cls.time_delta(span, dfmt='timedelta')
        # however return as desired
        if (not kwargs.get('dfmt') or kwargs.get('dfmt')=='datetime')      \
            and not kwargs.get('no_micro_secs',True):
            return since
        else:
            return cls.date_time(since, **kwargs)

    #/************************************************************************/
    @classmethod
    def until(cls, **kwargs):
        """Calculate a beginning date(time) given a duration and an ending date(time).

            >>> u = DateTime.until(**kwargs))

        Keyword Arguments
        -----------------
        since : datetime.datetime, datetime.date, str, float, dict
            beginning date instance whose format is any of those accepted by :meth:`DateTime.date_time`\ .
        span,dfmt :
            see :meth:`DateTime.since`.

        Returns
        -------
        u : datetime.datetime, str, float, dict
            ending date estimated from :literal:`since` and :literal:`span`
            timing arguments, expressed in any format as in :literal:`dfmt` and
            accepted by :meth:`DateTime.date_time`\ .

        'second': 41, 'hour': 16, 'year': 2014, 'day': 20, 'minute': 27, 'month': 8

        Example
        -------
        >>> since = datetime.datetime.now() # this is: datetime.datetime(2014, 8, 19, 16, 45, 5, 94000)
        >>> print(since)
            2014-08-19 16:45:05.094000
        >>> span = datetime.timedelta(2) # 2 days
        >>> print(span)
            2 days, 0:00:00
        >>> until = DateTime.until(since=since, span=span, dfmt='iso')
        >>> print(until)
            '2014-08-21T16:45:05'
        >>> DateTime.since(until=until, span=span, dfmt='datetime')
            datetime.datetime(2014, 8, 19, 16, 45, 5)
        """
        since, span = kwargs.pop('since',None), kwargs.pop('span',None)
        if not(since and span):
            raise IOError('missing arguments')
        # make a precise calculation, up to the microsecond
        kw1 = {'dfmt': 'datetime', no_micro_secs: False}
        kw2 = {'dfmt': 'timedelta'}
        until = cls.date_time(since, dfmt='datetime', no_micro_secs=False)  \
            + cls.time_delta(span, dfmt='timedelta')
        # however return as desired
        if (not kwargs.get('dfmt') or kwargs.get('dfmt')=='datetime')      \
            and not kwargs.get('no_micro_secs',True):
            return until
        else:
            return cls.date_time(until, **kwargs)

    #/************************************************************************/
    @classmethod
    def gt(cls, time1, time2):
        """Compare two date/time instances: check that the first entered time instance
        is posterior (after) to the second one.

            >>> resp = DateTime.gt(time1, time2)

        Arguments
        ---------
        time1,time2 : datetime.datetime, datetime.date, str, float, dict
            time instances whose format are any accepted by :meth:`DateTime.date_time`\ .

        Returns
        -------
        resp : bool
            :literal:`True` if `time1`>`time2`, i.e. `time1` represents a time
            posterior to `time2`; :literal:`False` otherwise.

        Example
        -------
        >>> dt = datetime.datetime(2014, 6, 19, 17, 58, 5)
        >>> one_day = {{'y':2014, 'm':6, 'd':19, 'hr':17, 'mn':58,  'sec':5}}
        >>> the_day_after = one_day.copy()
        >>> the_day_after.update({{'d': the_day_after['d']+1}})
        >>> DateTime.gt(the_day_after, one_day)
            True

        See also
        --------
        :meth:`~DateTime.lt`, :meth:`~DateTime.gte`
        """
        t1 = cls.date_time(time1, dfmt='datetime')
        t2 = cls.date_time(time2, dfmt='datetime')
        if t1.tzinfo is None:    t1 = t1.replace(tzinfo=cls.__DEF_TIMEZ)
        if t2.tzinfo is None:    t2 = t2.replace(tzinfo=cls.__DEF_TIMEZ)
        try:
            return t1 - t2 > cls.ZERO
        except: raise IOError("Unrecognised time operation")

    #/************************************************************************/
    @classmethod
    def lt(cls, time1, time2):
        """Compare two date/time instances: check that the first entered time instance
        is prior (before) to the second one.

            >>> resp = DateTime.lt(time1, time2)

        Arguments
        ---------
        time1,time2 : datetime.datetime, str, float, dict
            see :meth:`~DateTime.gt`\ .

        Returns
        -------
        resp : bool
            :literal:`True` if `time1`<`time2`, i.e. `time1` represents a time
            prior to `time2`; :literal:`False` otherwise.

        Example
        -------
        Following :meth:`~DateTime.gt` example:

        >>> DateTime.lt(one_day,the_day_after)
            True
        >>> one_day_iso = DateTime.date_time(one_day, **{{'{KW_FORMAT_DATETIME}': '{KW_ISOFORMAT}'}})
        >>> one_day_iso
            '2014-06-19T17:58:05'
        >>> DateTime.lt(one_day_iso,the_day_after)
            True

        See also
        --------
        :meth:`~DateTime.gt`, :meth:`~DateTime.lte`
        """
        return cls.gt(time2, time1)

    #/************************************************************************/
    @classmethod
    def gte(cls, time1, time2):
        """Compare two date/time instances: check that the first entered time instance
        is posterior to  or simultaneous with the second one the second one.

            >>> resp = DateTime.gte(time1, time2)

        Example
        -------
        .. Following :meth:`~DateTime.lt` and :meth:`~DateTime.gt` examples:

        >>> DateTime.gte(one_day_iso,one_day) and not DateTime.gt(one_day_iso,one_day)
            True

        See also
        --------
        :meth:`~DateTime.gt`, :meth:`~DateTime.lte`
        """
        # return cls.greater(time1, time2) or time1==time2
        t1 = cls.date_time(time1, dfmt='datetime')
        t2 = cls.date_time(time2, dfmt='datetime')
        if not t1.tzinfo:    t1 = t1.replace(tzinfo=cls.__DEF_TIMEZ)
        if not t2.tzinfo:    t2 = t2.replace(tzinfo=cls.__DEF_TIMEZ)
        try:
            return t1 - t2 >= cls.ZERO
        except: raise IOError("Unrecognised time operation")

    #/************************************************************************/
    @classmethod
    def lte(cls, time1, time2):
        """Compare two date/time instances: check that the first entered time instance
        is prior to or simultaneous with the second one.

            >>> resp = DateTime.lte(time1, time2)

        Example
        -------
        .. Following :meth:`~DateTime.lt` :meth:`~DateTime.gt` examples:

        >>> DateTime.lte(one_day_iso,one_day) and not DateTime.lt(one_day_iso,one_day)
            True

        See also
        --------
        :meth:`~DateTime.lt`, :meth:`~DateTime.gte`
        """
        return cls.gte(time2, time1)

    #/************************************************************************/
    @staticmethod
    def dtformat(**kwargs):
        """Determine a datetime format from date and time formats, and their combination.

            >>> dt = DateTime.dtformat(**kwargs)

        Keyword Arguments
        -----------------
        date,time : str
            strings specifying the date and time (written) formats; default is :literal:`'%Y-%m-%d'`
            for :data:`date` and :literal:`'%H:%M:%S'` for :data:`time`.
        dfmt : str
            string specifying how :data:`date` and :data:`time` format are combined;
            default is: :literal:`'%sT%s'`, i.e. the char :literal:`'T'` separates date and time.

        Returns
        -------
        dt : str
            string defining the format of datetime as :literal:`dfmt.format(date,time)`;
            default to ISO 8601 format: :literal:`'%Y-%m-%dT%H:%M:%S'`\ .
        """
        __dateformat = '%Y-%m-%d'               #ISO 8601
        dateformat = kwargs.pop('date',__dateformat)
        __timeformat = '%H:%M:%S'               #ISO 8601
        timeformat = kwargs.pop('time',__timeformat)
        __datetimeformat = '%sT%s'  #('%Y%m%d%H%M%S')
        datetimeformat = kwargs.pop('dfmt',__datetimeformat)
        return datetimeformat % (dateformat,timeformat)

    #/************************************************************************/
    @staticmethod
    def time_stamp(**kwargs):
        """Return a timestamp.

            >>> dtnow = DateTime.time_stamp(**kwargs)

        Keyword Arguments
        -----------------
        date,time,dfmt : str
            see :meth:`datetimeformat`\ .

        Returns
        -------
        dtnow : str
            timestamp estimated as the datetime representation of `now` (i.e. at the
            time the method is called).
        """
        return DateTime.NOW().strftime(DateTime.dtformat(**kwargs))

