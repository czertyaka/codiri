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


class ExceedingMeasurementProximity(ActivityMapError):
    """Measurement is too far from corresponding shoreline"""

    pass


class InvalidMeasurementLocation(ActivityMapError):
    """Measurement location is not valid"""

    pass


class ActivityMap(object):
    """Holds discretizated activity distribution"""

    def __init__(self, ul, lr, step):
        # setting the proximity of the measurement to the shore to default
        # value (meters)
        self.measurement_proximity = 10
        # default contamination depth is 10 cm
        self.contamination_depth = 10
        self.__init_img(ul, lr, step)

    def add_basin(self, basin, measurements):
        pass

    def __init_img(self, ul, lr, step):
        ul.transform("EPSG:3857")
        lr.transform("EPSG:3857")
        # since map can't be larger than 100 km flat Earth model is good enough
        # here
        x_res = abs(math.floor((lr.lon + 1 - ul.lon) / step))
        y_res = abs(math.floor((ul.lat + 1 - lr.lat) / step))
        if x_res == 0 or y_res == 0:
            raise ExceedingStepError

        data = np.zeros((x_res, y_res)).astype("uint8")

        # lower bottom corner doesn't necessary consist with initial lower
        # bottom
        lr = Coordinate(
            lon=ul.lon + x_res * step - 1,
            lat=ul.lat - y_res * step + 1,
            crs=lr.crs,
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

    @property
    def measurement_proximity(self):
        """[proximity] = m"""
        return self.__measurement_proximity

    @measurement_proximity.setter
    def measurement_proximity(self, value):
        """[value] = m"""
        self.__measurement_proximity = value

    @property
    def contamination_depth(self):
        """[depth] = cm"""
        return self.__contamination_depth

    @contamination_depth.setter
    def contamination_depth(self, value):
        """[value] = cm"""
        self.__contamination_depth = value
