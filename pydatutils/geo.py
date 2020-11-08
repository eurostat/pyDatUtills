#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
.. _geo

.. Links

.. _geojson: https://github.com/jazzband/geojson
.. |geojson| replace:: `geojson <geojson_>`_

Module implementing miscenalleous geographical/spatial methods.

**Dependencies**

*require*:      :mod:`requests`, :mod:`zipfile`,
                :mod:`hashlib`, :mod:`shutil`, :mod:`geojson`

*optional*:     :mod:`geojson`

*call*:

**Contents**
"""

# *credits*:      `gjacopo <jacopo.grazzini@ec.europa.eu>`_
# *since*:        Sat May 30 19:37:40 2020


try:
    import geojson#analysis:ignore
except ImportError:
    #warnings.warn('\n! missing geosjon package (https://github.com/jazzband/geojson) !')
    _is_geojson_imported = False
else:
    #warnings.warn('\n! geojson help: https://github.com/jazzband/geojson !')
    _is_geojson_imported = True
    from geojson import Feature, Point, FeatureCollection


DEF_FORMATS     = { 'geojson':      'geojson',
                    'topojson':     'topojson',
                    'shapefile':    'shp',
                    'geopackage':   'gpkg'
                    }


POLYLINE            = False
"""Boolean flag set to import the package :mod:`polylines` that will enable you to
generate polylines (see the `package website <https://pypi.python.org/pypi/polyline/>`_).
Not really necessary to generate the routes.
"""

DEF_PROJECTIONS = {'WGS84':             4326,
                   'EPSG4326':          4326,
                   # 'longlat':           4326,
                   'ETRS89':            4258,
                   'EPSG4258':          4258,
                   'longlat':           4258,
                   'Mercator':          3857,
                   'merc':              3857,
                   'EPSG3857':          3857,
                   'LAEA':              3035,
                   'EPSG3035':          3035,
                   'laea':              3035
                   }
"""Projections and EPSG codes currently supported by |GISCO| services.
See http://spatialreference.org for the list of all EPSG codes and corresponding
spatial references.
"""

EU_GEOCENTRE        = [50.033333, 10.35]
"""The German municipality of `Gädheim <https://en.wikipedia.org/wiki/Gädheim>`_
(in the district of Haßberge in Bavaria) serves as the geographical centre of the
European Union (when the United Kingdom leaves on April 2019).

See the Wikipedia  page on the
`geographical midpoint of Europe <https://en.wikipedia.org/wiki/Geographical_midpoint_of_Europe>`_
for discussions on the topic. For the determination of the actual geographical
coordinates (50°02′N 10°21′E), see also
`this page <https://tools.wmflabs.org/geohack/geohack.php?pagename=Gädheim&params=50_02_N_10_21_E_type:city(1272)_region:DE-BY>`_.
"""
EU_AGGREGATES       = { 'EU28':             ['BE', 'BG', 'CZ', 'DK', 'DE', 'EE', 'IE', 'EL', 'ES', 'FR',
                                             'HR', 'IT', 'CY', 'LV', 'LT', 'LU', 'HU', 'MT', 'NL', 'AT',
                                             'PL', 'PT', 'RO', 'SI', 'SK', 'FI', 'SE', 'UK'],
                        'EU27':             ['BE', 'BG', 'CZ', 'DK', 'DE', 'EE', 'IE', 'EL', 'ES', 'FR',
                                             'HR', 'IT', 'CY', 'LV', 'LT', 'LU', 'HU', 'MT', 'NL', 'AT',
                                             'PL', 'PT', 'RO', 'SI', 'SK', 'FI', 'SE'],
                        'EFTA':             ['IS', 'LI', 'NO', 'CH'],
                        'CACO':             ['ME', 'MK', 'AL', 'RS', 'TR']
                        }
"""ISO-codes of countries (Member States) in the EU and other euro area aggregates;
see `this page <https://ec.europa.eu/eurostat/statistics-explained/index.php/Tutorial:Country_codes_and_protocol_order>`_.
"""


#%% Core functions/classes


#==============================================================================
# Class _Tool
#==============================================================================

class _Tool():
    """Dummy base class for geospatial "tools".
    """
    #__metaclass__  = abc.ABCMeta
    pass

#==============================================================================
# Class _Feature
#==============================================================================

class _Feature():
    """Base class for geographic features.

        >>> feat = base._Feature()
    """
    #__metaclass__  = abc.ABCMeta

    #/************************************************************************/
    def __init__(self):
        self.__coord, self.__projection = None, None
        self.__service, self.__mapping, self.__transform = None, None, None
        try:
            self.__transform = _Tool()
            self.__mapping = _Tool()
        except:
            happyWarning('transform/mapping tool(s) not available')
        try:
            self.__service = _Service()
        except:
            happyWarning('web service(s) not available')

    #/************************************************************************/
    @property
    #@abc.abstractmethod
    def service(self):
        """Service property (:data:`getter`) of a :class:`_Feature` instance.
        The :data:`service` property returns an object as an instance of the
        :class:`~happygisco.services.GISCOService` or :class:`~happygisco.services.APIService`
        classes.
        """
        return self.__service
    @service.setter
    def service(self, service):
        self.__service = service

    #/************************************************************************/
    @property
    #@abc.abstractmethod
    def transform(self):
        """Geospatial transform property (:data:`getter`) of a :class:`_Feature` instance.
        The :data:`transform` property returns an object as an instance of the
        :class:`~happygisco.tools.GDALTransform` class.
        """
        return self.__transform
    @transform.setter
    def transform(self, transform):
        self.__transform = transform

    #/************************************************************************/
    @property
    #@abc.abstractmethod
    def mapping(self):
        """Geospatial mapping property (:data:`getter`) of a :class:`_Feature` instance.
        The :data:`mapping` property returns an object as an instance of the
        :class:`~happygisco.tools.FoliumMap` class.
        """
        return self.__mapping
    @mapping.setter
    def mapping(self, mapping):
        self.__mapping = mapping

    #/************************************************************************/
    @property
    #@abc.abstractmethod
    def projection(self):
        """Projection property (:data:`getter`) of a :class:`_Feature` instance.
        """
        return self.__projection
    @projection.setter
    def projection(self, proj):
        self.__projection = proj

    #/************************************************************************/
    @property
    #@abc.abstractmethod
    def coord(self):
        # ignore: this will be overwritten
        """Pair of :literal:`(lat,Lon)` geographic coordinates (:data:`getter`/:data:`setter`)
        of a :class:`_Feature` instance.
        """
        return self.__coord
    @coord.setter
    def coord(self, coord):
        self.__coord = coord

    #/************************************************************************/
    @property
    def coordinates(self):
        """:literal:`(lat,Lon)` geographic coordinates property (:data:`getter`) of
        a :class:`_Feature` instance.
        """
        pass

    #/************************************************************************/
    @property
    def Lon(self):
        """Longitude property (:data:`getter`) of a :class:`_Feature` instance.
        A :data:`Lon` type is (a list of) :class:`float`.
        """
        pass

    #/************************************************************************/
    @property
    def lat(self):
        """Latitude property (:data:`getter`) of a :class:`_Feature` instance.
        A :data:`lat` type is (a list of) :class:`float`.
        """
        pass


