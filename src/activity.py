#!/usr/bin/python3

from .geo import Coordinate
import math
import numpy as np
from rasterio import Affine, MemoryFile


def _log(msg):
    print("activity: " + msg)


class ActivityMapError(Exception):
    """Generic error for creating activity map instance"""

    pass


class ExceedingStepError(ActivityMapError):
    """Image cell size exceeds one of image sizes"""

    pass


class Measurment(object):
    """Holds info on activity measurement"""

    def __init__(self, activity, coo):
        """[specific activity] = Bq/kg"""
        self.__activity = activity
        coo.transform("EPSG:3857")
        self.__coo = coo

    @property
    def activity(self):
        return self.__activity

    @property
    def coo(self):
        return self.__coo


class ActivityMap(object):
    """Holds discretizated activity distribution"""

    def __init__(self, ul, lr, step):
        self.__init_img(ul, lr, step)

    def add_shoreline(self, shoreline, measurments):
        pass

    def __init_img(self, ul, lr, step):
        ul.transform("EPSG:3857")
        lr.transform("EPSG:3857")
        # since map can't be larger than 100 km flat Earth model is good enough
        # here
        x_res = abs(math.floor((lr.lon - ul.lon) / step))
        y_res = abs(math.floor((ul.lat - lr.lat) / step))
        if x_res == 0 or y_res == 0:
            raise ExceedingStepError

        data = np.zeros((x_res, y_res)).astype("uint8")

        # lower bottom corner doesn't necessary consist with initial lower
        # bottom
        lr = Coordinate(
            lon=ul.lon + x_res * step, lat=ul.lat - y_res * step, crs=lr.crs
        )

        memfile = MemoryFile()
        self.__img = memfile.open(
            driver="GTiff",
            height=data.shape[0],
            width=data.shape[1],
            dtype="uint8",
            crs="EPSG:3857",
            transform=Affine.translation(ul.lon, ul.lat)
            * Affine.scale(step, -step),
            count=1,
        )
        self.img.write(data, 1)

    @property
    def img(self):
        return self.__img
