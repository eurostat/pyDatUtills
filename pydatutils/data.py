#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
.. _data

.. Links

.. _geojson: https://github.com/jazzband/geojson
.. |geojson| replace:: `geojson <geojson_>`_
.. _bs4: https://pypi.python.org/pypi/beautifulsoup4
.. |bs4| replace:: `beautiful soup <bs4_>`_
.. _chardet: https://pypi.org/project/chardet/
.. |chardet| replace:: `chardet <chardet_>`_
.. _xmltree: https://docs.python.org/3/library/xml.etree.elementtree.html
.. |xmltree| replace:: `xml.tree <xmltree_>`_

Module implementing miscenalleous Input/Output methods.

**Dependencies**

*require*:      :mod:`os`, :mod:`six`, :mod:`collections`, :mod:`numpy`, :mod:`pandas`,
                :mod:`time`, :mod:`requests`, :mod:`hashlib`, :mod:`shutil`

*optional*:     :mod:`simplejson`, :mod:`json`, :mod:`geojson`, :mod:`zipfile`, :mod:`bs4`,
                :mod:`datetime`, :mod:`chardet`, :mod:`xml.etree`

*call*:         :mod:`pyeudatnat.misc`

**Contents**
"""

# *credits*:      `gjacopo <jacopo.grazzini@ec.europa.eu>`_
# *since*:        Thu Apr  9 09:56:45 2020

#%% Settings

from os import path as osp
import warnings#analysis:ignore

from abc import ABCMeta, abstractmethod
from six import with_metaclass

from collections.abc import Mapping, Sequence
from six import string_types

from datetime import datetime
import zipfile

try:
    import numpy as np
    import pandas as pd
except:
    raise IOError("Missing essential data handling packages")

try:
    import geopandas as gpd
except:
    _is_geopandas_imported = False
    class gpd():
        @staticmethod
        def notinstalled(meth):
            raise IOError("Package GeoPandas not installed = method '%s' not available" % meth)
        def to_file(self,*args, **kwargs):      self.notinstalled('to_file')
        def read_file(self,*args, **kwargs):    self.notinstalled('read_file')
else:
    _is_geopandas_imported = True

try:
    import simplejson as json
except ImportError:
    try:
        import json
    except ImportError:
        class json:
            def dump(f, arg):
                with open(arg,'w') as f:    f.write(arg)
            def dumps(arg):                 return '%s' % arg
            def load(arg):
                with open(arg,'r') as f:    return f.read()
            def loads(arg):                 return '%s' % arg

# Beautiful soup package
try:
    import bs4
except ImportError:
    # warnings.warn("missing beautifulsoup4 module - visit https://pypi.python.org/pypi/beautifulsoup4", ImportWarning)
    _is_bs4_imported = False
else:
    _is_bs4_imported = True

try:
    import geojson#analysis:ignore
except ImportError:
    #warnings.warn('\n! missing geosjon package (https://github.com/jazzband/geojson) !')
    _is_geojson_imported = False
else:
    #warnings.warn('\n! geojson help: https://github.com/jazzband/geojson !')
    _is_geojson_imported = True
    from geojson import Feature, Point, FeatureCollection

try:
    import xml.etree.cElementTree as et
except ImportError:
    _is_xml_imported = False
else:
    _is_xml_imported = True

from pydatutils.struct import Struct
from pydatutils.misc import SysEnv
from pydatutils.io import FORMATS as IoFORMATS, DEFFORMAT
from pydatutils.geo import FORMATS as GeoFORMATS, DEFFORMAT
from pydatutils.io import File, Buffer
from pydatutils.online import Requests


#%% Core functions/classes

#==============================================================================
# Abstract class _Data
#==============================================================================

class _Data(with_metaclass(ABCMeta)):
    """Abstract class methods for generic Input/Output dataframe processing, e.g.
    reading from / writing into a table.
    """

    # See Pandas supported IO formats: https://pandas.pydata.org/pandas-docs/stable/user_guide/io.html
    # See also GDAL supported drivers (or fiona.supported_drivers)

    ENCODINGS = {'utf-8':       'utf-8',
                 'latin':       'ISO-8859-1',
                 'ISO-8859-1':  'ISO-8859-1',
                 'latin1':      'ISO-8859-2',
                 'ISO-8859-2':  'ISO-8859-2'
                 }
    # 'latin1' accept any possible byte as input (and convert it to the unicode character of same code)

    #/************************************************************************/
    @abstractclass
    @classmethod
    def to_file(cls, *args, **kwargs):
        raise NotImplementedError

    #/************************************************************************/
    @abstractclass
    @classmethod
    def from_data(cls, *args, **kwargs):
        raise NotImplementedError

    #/************************************************************************/
    @classmethod
    def from_url(cls, urlname, **kwargs):
        """
        """
        try:
            data = Requests.parse_url(urlname, **kwargs)
        except:
            raise IOError("Wrong request for data from URL '%s'" % urlname)
        try:
            return cls.from_data(data, **kwargs)
        except:
            raise IOError("Wrong formatting of online data into dataframe")

    #/************************************************************************/
    @classmethod
    def from_zip(cls, file, members, **kwargs):
        """
        """
        try:
            assert zipfile.is_zipfile(file)
        except:
            raise TypeError("Zip file '%s' not recognised" % file)
        #kwargs.update({'read': kwargs.pop('file', None)})
        #try:
        #    data = File.unzip(file, **kwargs) # when None, and single file, read it
        #except:
        #    raise IOError("Impossible unzipping data from zipped file '%s'" % file)
        #try:
        #    return cls.from_data(data, **kwargs)
        #except:
        #    raise IOError("Wrong formatting of zipped data into dataframe")
        try:
            assert members is None or isinstance(members,string_types) \
                or (isinstance(members,Sequence) and all([isinstance(m,string_types) for m in members]))
        except:
            raise TypeError("Wrong member '%s' not recognised" % members)
        else:
            if isinstance(members,string_types):
                members = [members,]
        results = {}
        with zipfile.ZipFile(file) as zf:
            namelist = zf.namelist()
            if members is None and len(namelist)==1:
                members = namelist
            elif members is not None:
                for i in reversed(range(len(members))):
                    m = members[i]
                    try:
                        assert m in namelist
                    except:
                        try:
                            _mem = [n for n in namelist if n.endswith(m)]
                            assert len(_mem)==1
                        except:
                            members.pop(i)
                        else:
                            members[i] = _mem[0]
                    else:
                        pass # continue
            if members in ([],None):
                raise IOError("Impossible to retrieve member file(s) from zipped data")
            for m in members:
                try:
                    with zf.open(m) as zm:
                        df = cls.from_data(zm, **kwargs)
                except:
                    raise IOError("Data %s cannot be read in source file... abort!" % m)
                else:
                    results.update({m: df})
        return results if len(results.keys())>1 else list(results.values())[0]

    #/************************************************************************/
    @classmethod
    def from_file(cls, file, src=None, **kwargs):
        """
        Keyword arguments
        -----------------
        on_disk : bool
        stream : 'str'
        infer_fmt : bool
        fmt : str
        """
        ifmt = kwargs.pop('fmt', None)
        infer_fmt = kwargs.pop('infer_fmt', False)
        # stream = kwargs.pop('stream', None)'
        # on_disk = kwargs.pop('on_disk', False)'
        if infer_fmt is True:
            # note that the default infer_fmt here may differ from the one
            # in from_data method
            infer_fmt = ['csv', 'json', 'excel', 'html', 'geojson', 'shapefile', 'table'] # list(FORMATS.values())
        try:
            ifmt = File.check_format(ifmt, infer_fmt = infer_fmt)
        except:
            raise IOError("Data format FMT not recognised: '%s'" % ifmt)
        else:
            infer_fmt = False # update to avoid doing it again in from_data method
        # try:
        #     assert src is None or isinstance(src, string_types)
        # except:
        #     raise TypeError("Wrong type for data source parameter '%s' - must be a string" % src)
        # try:
        #     assert file is None or isinstance(file, string_types)
        # except:
        #     raise TypeError("Wrong type for file parameter '%s' - must be a string" % file)
        # if src is None:
        #     src, file = file, None
        # if any([src.startswith(p) for p in ['http', 'https', 'ftp'] ]):
        #     try:
        #         data = Requests.parse_url(src, **kwargs)
        #     except:
        #         raise IOError("Wrong request for data source from URL '%s'" % src)
        # else:
        #     try:
        #         assert osp.exists(src) is True
        #     except:
        #         raise IOError("Data source '%s' not found on disk" % src)
        #     else:
        #         data = src
        ## transforming files in zipped source directly into dataframe while
        ## unziping with from_zip
        # if zipfile.is_zipfile(data) or any([src.endswith(p) for p in ['zip', 'gz', 'gzip', 'bz2'] ]):
        #     try:
        #         return cls.from_zip(data, file, **kwargs)
        #     except:
        #         raise IOError("Impossible unzipping data from zipped file '%s'" % src)
        # else:
        #     try:    fmt = os.path.splitext(src)[-1].replace('.','')
        #     except: pass
        #     else:   kwargs.update({'fmt':fmt, 'infer_fmt': False})
        #     try:
        #         return cls.from_data(data, **kwargs)
        #     except:
        #         raise IOError("Wrong formatting of source data into dataframe")
        # fetching opening and parsing files from source to transform them into
        # dataframes
        buffer = Buffer.from_file(file, src=src, **kwargs)
        if isinstance(buffer,string_types) or not isinstance(buffer,Mapping):
            buffer = {file: buffer}
        results = {}
        for file, data in buffer.items():
            ext = osp.splitext(file)[-1].replace('.','').lower()
            if not(ifmt is None or ext in ifmt):
                warnings.warn("\n! File '%s' will not be loaded !" % file)
                continue
            else:
                fmt = ext
            kwargs.update({'fmt': fmt, 'infer_fmt': infer_fmt})
            try:
                results.update({file: cls.from_data(data, **kwargs)})
                # not that this will work for zipfile but it is not generic, contraty
                # to the one above:
                #  results.update({file: Frame.from_data(io.BytesIO(data.read()), **kwargs)})
            except:
                raise IOError("Wrong formatting of source data into dataframe")
        return results if len(results.keys())>1 else list(results.values())[0]


#==============================================================================
# Class Frame
#==============================================================================

class Frame(_Data):
    """Static methods for Input/Output dataframe processing, e.g. writing
    into a table.
    """

    #/************************************************************************/
    @staticmethod
    def cast(df, column, otype=None, odfmt=None, idfmt=None):
        """Cast the column of a dataframe into special type or date format.

            >>> dfnew = DataFrame.cast(df, column, otype=None, odfmt=None, idfmt=None)
        """
        try:
            assert column in df.columns
        except:
            raise IOError("Wrong input column - must be in the dataframe")
        try:
            assert otype is None or (odfmt is None and idfmt is None)
        except:
            raise IOError("Incompatible option OTYPE with IDFMT and ODFMT")
        try:
            assert (otype is None or isinstance(otype, type) is True)
        except:
            raise TypeError("Wrong format for input cast type")
        try:
            assert (odfmt is None or isinstance(odfmt, string_types))     \
                and (idfmt is None or isinstance(idfmt, string_types))
        except:
            raise TypeError("Wrong format for input date templates")
        if otype is not None:
            if otype == df[column].dtype:
                return df[column]
            else:
                try:
                    return df[column].astype(otype)
                except:
                    return df[column].astype(object)
        else:
             # odfmt='%d/%m/%Y', ifmt='%d-%m-%Y %H:%M'
            if idfmt in (None,'') :
                kwargs = {'infer_datetime_format': True}
            else:
                kwargs = {}
            if odfmt in (None,'') or odfmt == '':
                return df[column].astype(str)
            else:
                try:
                    f = lambda s: datetime.strptime(s, idfmt, **kwargs).strftime(odfmt)
                    return df[column].astype(str).apply(f)
                except:
                    return df[column].astype(str)

    #/************************************************************************/
    @staticmethod
    def to_json(df, columns=None):
        """JSON output formatting.
        """
        try:
            assert columns is None or isinstance(columns, string_types)     or \
                (isinstance(columns, Sequence) and all([isinstance(c,string_types) for c in columns]))
        except:
            raise IOError("Wrong format for input columns")
        if isinstance(columns, string_types):
            columns == [columns,]
        if columns in (None,[]):
            columns = df.columns
        columns = list(set(columns).intersection(df.columns))
        df.reindex(columns = columns)
        return df[columns].to_dict('records')

    #/************************************************************************/
    @staticmethod
    def to_xml(filename):
        """
        """
        warnings.warn("\n! Method 'to_xml' for xml data writing not implemented !")
        pass

    #/************************************************************************/
    @classmethod
    def to_file(cls, df, dest, **kwargs):
        ofmt = kwargs.pop('fmt', None)
        infer_fmt = kwargs.pop('infer_fmt', False)
        if infer_fmt is True:
            infer_fmt = ['csv', 'json', 'excel', 'geojson', 'xls'] # list(FORMATS.values())
        try:
            ofmt = File.check_format(ofmt, infer_fmt = infer_fmt)
        except:
            raise IOError("Data format FMT not recognised: '%s'" % ofmt)
        encoding = kwargs.pop('encoding', None) or kwargs.pop('enc', None) or 'utf-8'
        def _to_csv(df, d, **kw):
            nkw = Struct.inspect_kwargs(kw, pd.to_csv)
            df.to_csv(d, **nkw)
        def _to_excel(df, d, **kw):
            nkw = Struct.inspect_kwargs(kwargs, pd.to_excel)
            df.to_excel(d, **nkw)
        def _to_json(df, d, **kw):
            nkw = Struct.inspect_kwargs(kwargs, Frame.to_json)
            res = cls.to_json(df, **nkw)
            with open(d, 'w', encoding=encoding) as f:
                json.dump(res, f, ensure_ascii=False)
        def _to_geojson(df, d, **kw):
            if _is_geojson_imported is True:
                nkw = Struct.inspect_kwargs(kwargs, gpd.to_file)
                df.to_file(d, driver='GeoJSON', **nkw)
            else:
                nkw = Struct.inspect_kwargs(kwargs, Frame.to_json)
                res = cls.to_json(df, **nkw)
                with open(d, 'w', encoding=encoding) as f:
                    json.dump(res, f, ensure_ascii=False)
        def _to_geopackage(df, d, **kw):
            nkw = Struct.inspect_kwargs(kwargs, gpd.to_file)
            df.to_file(d, driver='GPKG', **nkw)
        fundumps = {'csv':      _to_csv,
                    'xls':      _to_excel,
                    'json':     _to_json,
                    'geojson':  _to_geojson,
                    'gpkg':     _to_geopackage
                    }
        for f in ofmt:
            try:
                assert not osp.exists(dest)
            except:
                warnings.warn("\n! Output file '%s' already exist - will be overwritten")
            try:
                fundumps[f](dest, **kwargs)
            except:
                warnings.warn("\n! Impossible to write to %s !" % f.upper())
            else:
                if ofmt == f:       return
                else:               ofmt.remove(f)
        raise IOError("Impossible to save data - input format not recognised")

    #/************************************************************************/
    @staticmethod
    def from_html_table(htmlname, **kwargs):
        """
        """
        try:
            assert _is_bs4_imported is True
        except:
            raise IOError("'from_html' method not available")
        parser = kwargs.get('kwargs','html.parser')
        if parser not in ('html.parser','html5lib','lxml'):
            raise IOError("Unknown soup parser")
        try:
            raw = bs4.BeautifulSoup(htmlname, parser)
            #raw = bs4.BeautifulSoup(html, parser).get_text()
        except:
            raise IOError("Impossible to read HTML page")
        try:
            tables = raw.findAll('table', **kwargs)
        except:
            raise IOError("Error with soup from HTML page")
        headers, rows = [], []
        for table in tables:
            try:
                table_body = table.find('tbody') # may be None
                headers.append(table_body.find_all('th'))
                rows.append(table_body.find_all('tr'))
            except:
                headers.append(table.findAll('th'))
                rows.append(table.findAll('tr'))
        return pd.DataFrame(rows, columns = headers)

    #/************************************************************************/
    @staticmethod
    def from_xml_tree(xmlname, **kwargs):
        """
        """
        try:
            assert _is_xml_imported is True
        except:
            raise IOError("'from_xml' method not available")
        #root = et.XML(filename) # element tree
        #records = []
        #for i, child in enumerate(root):
        #    record = {}
        #    for subchild in child:
        #        record[subchild.tag] = subchild.text
        #    records.append(record)
        #return pd.DataFrame(records)
        def iter_records(records):
            for record in records:
                dtmp = {}   # temporary dictionary to hold values
                for var in record: # iterate through all the fields
                   dtmp.update({var.attrib['var_name']: var.text})
                yield dtmp # generate the value
        with open(xmlname, 'r') as fx:
            tree = et.parse(fx) # read the data and store it as a tree
            root = tree.getroot() # get the root of the tree
            return pd.DataFrame(list(iter_records(root)))

    #/************************************************************************/
    @classmethod
    def from_data(src, **kwargs):
        """Load data from a stream/buffer in any of the supported formats.

            >>> df = Frame.from_data(src, **kwargs)
        """
        ifmt = kwargs.pop('fmt', None)
        infer_fmt= kwargs.pop('infer_fmt', False)
        if infer_fmt is True:
            # note that the default infer_fmt here may differ from the one in
            # from_file method
            infer_fmt = ['csv', 'json', 'excel', 'sql', 'html', 'table']
        try:
            ifmt = File.check_format(ifmt, infer_fmt = infer_fmt)
        except:
            raise IOError("Data format FMT not recognised: '%s'" % ifmt)
        def _read_csv(s, **kw):
            nkw = Struct.inspect_kwargs(kw, pd.read_csv)
            try:
                return pd.read_csv(s, **nkw)
            except:
                return SysEnv.chardet_decorate(pd.read_csv)(s, **nkw)
        def _read_excel(s, **kw):
            nkw = Struct.inspect_kwargs(kw, pd.read_excel)
            return pd.read_excel(s, **nkw)
        def _read_json(s, **kw):
            nkw = Struct.inspect_kwargs(kw, pd.read_json)
            return pd.read_json(s, **nkw)
        def _read_sql(s, **kw):
            nkw = Struct.inspect_kwargs(kw, pd.read_sql)
            return pd.read_sql(s, **nkw)
        def _read_sas(s, **kw):
            nkw = Struct.inspect_kwargs(kw, pd.read_sas)
            return pd.read_sas(s, **nkw)
        def _read_geojson(s, **kw):
            if _is_geopandas_imported is True:
                nkw = Struct.inspect_kwargs(kw, gpd.read_file)
                nkw.update({'driver': 'GeoJSON'})
                return gpd.read_file(s, **nkw)
            else:
                nkw = Struct.inspect_kwargs(kw, geojson.load)
                # note that geojson.load is a wrapper around the core json.load function
                # with the same name, and will pass through any additional arguments
                return geojson.load(s, **nkw)
        def _read_topojson(s, **kw):
            nkw = Struct.inspect_kwargs(kw, gpd.read_file)
            nkw.update({'driver': 'TopoJSON'})
            #with fiona.MemoryFile(s) as f:  #with fiona.ZipMemoryFile(s) as f:
            #    return gpd.GeoDataFrame.from_features(f, crs=f.crs, **nkw)
            return gpd.read_file(s, **nkw)
        def _read_shapefile(s, **kw):
            try:
                assert osp.exists(s) is True # Misc.File.file_exists(s)
            except:
                warnings.warn("\n! GeoPandas reads URLs and files on disk only - set flags on_disk=True and ignore_buffer=True when loading sourc")
            try:
                p, f = osp.dirname(s), osp.basename(osp.splitext(s)[0])
            except:
                pass
            try:
                assert (osp.exists(osp.join(p,'%s.shx' % f)) or osp.exists(osp.join(p,'%s.SHX' % f)))   \
                    and (osp.exists(osp.join(p,'%s.prj' % f)) or osp.exists(osp.join(p,'%s.PRJ' % f)))  \
                    and (osp.exists(osp.join(p,'%s.dbf' % f)) or osp.exists(osp.join(p,'%s.DBF' % f)))
            except AssertionError:
                warnings.warn("\n! Companion files [.dbf, .shx, .prj] are required together with shapefile source"
                              " - add companion files to path, e.g. set flags fmt='csv' and 'infer_fmt'=False when loading source")
            except:
                pass
            nkw = Struct.inspect_kwargs(kw, gpd.read_file)
            nkw.update({'driver': 'shapefile'})
            return gpd.read_file(s, **nkw)
        def _read_geopackage(s, **kw):
            nkw = Struct.inspect_kwargs(kw, gpd.read_file)
            nkw.update({'driver': 'GPKG'})
            return gpd.read_file(s, **nkw)
        def _read_html(s, **kw):
            nkw = Struct.inspect_kwargs(kw, pd.read_html)
            return pd.read_html(s, **nkw)
        def _read_htmltab(s, **kw):
            return cls.from_html_table(s, **kw)
        def _read_xml(s, **kw):
            return cls.from_xml_tree(s, **kw)
        def _read_table(s, **kw):
            nkw = Struct.inspect_kwargs(kw, pd.read_table)
            return pd.read_table(s, **nkw)
        funloads = {'csv':      _read_csv,
                    'xls':      _read_excel,
                    'json':     _read_json,
                    'sql':      _read_sql,
                    'sas':      _read_sas,
                    'geojson':  _read_geojson,
                    'topojson': _read_topojson,
                    'shp':      _read_shapefile,
                    'gpkg':     _read_geopackage,
                    'html':     _read_html,
                    'htmltab':  _read_htmltab,
                    'xml':      _read_xml,
                    'table':    _read_table,
                    }
        for f in ifmt:
            try:
                df = funloads[f](src, **kwargs)
            except FileNotFoundError:
                raise IOError("Impossible to load source data - file '%s' not found" % src)
            except:
                pass
            else:
                warnings.warn("\n! '%s' data loaded in dataframe !" % f.upper())
                return df
        raise IOError("Impossible to load source data - format not recognised")


#==============================================================================
# Class Series
#==============================================================================

class Series(Frame):
    pass


#==============================================================================
# Class GeoFrame
#==============================================================================

class GeoFrame(_Data):
    """Static methods for Input/Output for geographic/vector dataframe processing.
    """

    FORMATS         = { 'geojson':      'geojson',
                        'topojson':     'topojson',
                        'shapefile':    'shp',
                        'geopackage':   'gpkg'
                        }

    DEFFORMAT       = 'geojson'

    #/************************************************************************/
    @staticmethod
    def to_geojson(df, columns=None, latlon=['lat', 'lon']):
        """GEOJSON output formatting.
        """
        try:
            assert columns is None or isinstance(columns, string_types)     or \
                (isinstance(columns, Sequence) and all([isinstance(c,string_types) for c in columns]))
        except:
            raise IOError("Wrong format for input columns")
        try:
            lat, lon = latlon
            assert isinstance(lat, string_types) and isinstance(lon, string_types)
        except:
            raise TypeError("Wrong format for input lat/lon columns")
        if isinstance(columns, string_types):
            columns == [columns,]
        if columns in (None,[]):
            columns = list(set(df.columns))
        columns = list(set(columns).intersection(set(df.columns)).difference(set([lat,lon])))
        # df.reindex(columns = columns) # not necessary
        if _is_geojson_imported is True:
            features = df.apply(
                    lambda row: Feature(geometry=Point((float(row[lon]), float(row[lat])))),
                    axis=1).tolist()
            properties = df[columns].to_dict('records') # columns used as properties
            # properties = df.drop([lat, lon], axis=1).to_dict('records')
            geom = FeatureCollection(features=features, properties=properties)
        else:
            geom = {'type':'FeatureCollection', 'features':[]}
            for _, row in df.iterrows():
                feature = {'type':'Feature',
                           'properties':{},
                           'geometry':{'type':'Point',
                                       'coordinates':[]}}
                feature['geometry']['coordinates'] = [float(row[lon]), float(row[lat])]
                for col in columns:
                    feature['properties'][col] = row[col]
                geom['features'].append(feature)
        return geom

    #/************************************************************************/
    @staticmethod
    def from_data(src, **kwargs):
        """
        """
        ifmt = kwargs.pop('fmt', None)
        infer_fmt= kwargs.pop('infer_fmt', False)
        if infer_fmt is True:
            # note that the default infer_fmt here may differ from the one in
            # from_file method
            infer_fmt = ['geojson', 'shapefile']
        try:
            ifmt = File.check_format(ifmt, infer_fmt = infer_fmt)
        except:
            raise IOError("Data format FMT not recognised: '%s'" % ifmt)
        def _read_geojson(s, **kw):
            if _is_geopandas_imported is True:
                nkw = Struct.inspect_kwargs(kw, gpd.read_file)
                nkw.update({'driver': 'GeoJSON'})
                return gpd.read_file(s, **nkw)
            else:
                nkw = Struct.inspect_kwargs(kw, geojson.load)
                # note that geojson.load is a wrapper around the core json.load function
                # with the same name, and will pass through any additional arguments
                return geojson.load(s, **nkw)
        def _read_topojson(s, **kw):
            nkw = Struct.inspect_kwargs(kw, gpd.read_file)
            nkw.update({'driver': 'TopoJSON'})
            #with fiona.MemoryFile(s) as f:  #with fiona.ZipMemoryFile(s) as f:
            #    return gpd.GeoDataFrame.from_features(f, crs=f.crs, **nkw)
            return gpd.read_file(s, **nkw)
        def _read_shapefile(s, **kw):
            try:
                assert osp.exists(s) is True # Misc.File.file_exists(s)
            except:
                warnings.warn("\n! GeoPandas reads URLs and files on disk only - set flags on_disk=True and ignore_buffer=True when loading sourc")
            try:
                p, f = osp.dirname(s), osp.basename(osp.splitext(s)[0])
            except:
                pass
            try:
                assert (osp.exists(osp.join(p,'%s.shx' % f)) or osp.exists(osp.join(p,'%s.SHX' % f)))   \
                    and (osp.exists(osp.join(p,'%s.prj' % f)) or osp.exists(osp.join(p,'%s.PRJ' % f)))  \
                    and (osp.exists(osp.join(p,'%s.dbf' % f)) or osp.exists(osp.join(p,'%s.DBF' % f)))
            except AssertionError:
                warnings.warn("\n! Companion files [.dbf, .shx, .prj] are required together with shapefile source"
                              " - add companion files to path, e.g. set flags fmt='csv' and 'infer_fmt'=False when loading source")
            except:
                pass
            nkw = Struct.inspect_kwargs(kw, gpd.read_file)
            nkw.update({'driver': 'shapefile'})
            return gpd.read_file(s, **nkw)
        def _read_geopackage(s, **kw):
            nkw = Struct.inspect_kwargs(kw, gpd.read_file)
            nkw.update({'driver': 'GPKG'})
            return gpd.read_file(s, **nkw)
        funloads = {'geojson':  _read_geojson,
                    'topojson': _read_topojson,
                    'shp':      _read_shapefile,
                    'gpkg':     _read_geopackage
                    }
        for f in ifmt:
            try:
                df = funloads[f](src, **kwargs)
            except FileNotFoundError:
                raise IOError("Impossible to load source data - file '%s' not found" % src)
            except:
                pass
            else:
                warnings.warn("\n! '%s' data loaded in dataframe !" % f.upper())
                return df
        raise IOError("Impossible to load source data - format not recognised")

    #/************************************************************************/
    @staticmethod
    def to_file(df, dest, **kwargs):
        ofmt = kwargs.pop('fmt', None)
        infer_fmt = kwargs.pop('infer_fmt', False)
        if infer_fmt is True:
            infer_fmt = ['geojson'] # list(FORMATS.values())
        try:
            ofmt = File.check_format(ofmt, infer_fmt = infer_fmt)
        except:
            raise IOError("Data format FMT not recognised: '%s'" % ofmt)
        encoding = kwargs.pop('encoding', None) or kwargs.pop('enc', None) or 'utf-8'
        def _to_geojson(df, d, **kw):
            if _is_geojson_imported is True:
                nkw = Struct.inspect_kwargs(kwargs, gpd.to_file)
                df.to_file(d, driver='GeoJSON', **nkw)
            else:
                nkw = Struct.inspect_kwargs(kwargs, Frame.to_json)
                res = Frame.to_json(df, **nkw)
                with open(d, 'w', encoding=encoding) as f:
                    json.dump(res, f, ensure_ascii=False)
        def _to_geopackage(df, d, **kw):
            nkw = Struct.inspect_kwargs(kwargs, gpd.to_file)
            df.to_file(d, driver='GPKG', **nkw)
        fundumps = {'geojson':  _to_geojson,
                    'gpkg':     _to_geopackage
                    }
        for f in ofmt:
            try:
                assert not osp.exists(dest)
            except:
                warnings.warn("\n! Output file '%s' already exist - will be overwritten")
            try:
                fundumps[f](dest, **kwargs)
            except:
                warnings.warn("\n! Impossible to write to %s !" % f.upper())
            else:
                if ofmt == f:       return
                else:               ofmt.remove(f)
        raise IOError("Impossible to save data - input format not recognised")


