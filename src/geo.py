#!/usr/bin/python3

import rasterio as rsio
import numpy as np
import cv2 as cv
from matplotlib import pyplot as plt
from pyproj import Transformer, Geod
from copy import copy


def _log(msg):
    print("map: " + msg)


def distance(coo0, coo1):
    coo0 = copy(coo0)
    coo0.transform("EPSG:4326")
    coo1 = copy(coo1)
    coo1.transform("EPSG:4326")
    geod = Geod(ellps="WGS84")
    return geod.line_length([coo0.lon, coo1.lon], [coo0.lat, coo1.lat])


class Coordinate(object):
    """Coordinate with datum switching"""

    def __init__(self, lon, lat, crs="EPSG:3857"):
        self.__lon = lon
        self.__lat = lat
        self.__crs = crs

    def transform(self, crs):
        if crs != self.__crs:
            transformer = Transformer.from_crs(self.__crs, crs)
            self.__lat, self.__lon = transformer.transform(
                yy=self.lat, xx=self.lon
            )
            self.__crs = crs

    @property
    def lon(self):
        return self.__lon

    @property
    def lat(self):
        return self.__lat

    @property
    def crs(self):
        return self.__crs

    def __str__(self):
        return f"{{lon: {self.lon}; lat: {self.lat}; crs: {self.crs}}}"


class Map(object):
    """Contains geospatial data for area of interest"""

    def __init__(self, filename):
        self.__img = rsio.open(filename)
        _log(
            f"opened image '{filename}'; bounds = {self.__img.bounds}, "
            f"crs = {self.__img.crs}, width = {self.__img.width} pix, height "
            f"= {self.__img.height} pix"
        )
        self.__data = np.uint8(self.__img.read(1))
        ret, self.__data = cv.threshold(
            self.__data, 2, 0, cv.THRESH_TOZERO_INV
        )
        if not ret:
            _log("failed to reduce cloud/shadow/snow/ice areas")
            exit()
        ret, self.__data = cv.threshold(self.__data, 1, 255, cv.THRESH_BINARY)
        if not ret:
            _log("failed to make image binary")
            exit()

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.img.close()

    def plot(self):
        plt.imshow(self.__data)
        plt.show()

    @property
    def img(self):
        return self.__img

    @property
    def data(self):
        return self.__data
