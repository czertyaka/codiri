#!/usr/bin/python3

from .geo import Coordinate
import math
import numpy as np
from rasterio import Affine, MemoryFile
from shapely import geometry, ops


def _log(msg):
    print("activity: " + msg)


def blowout_activity_flow(specific_activity: float, windspeed: float) -> float:
    """Blowout activity flow due to wind uplift, Bq/(m^s*sec)
    [specific_activity] = Bq/kg
    [windspeed] = m/sec
    """
    tau = 0.0078  # N/m^2
    critical_windspeed = 5.2  # m/sec
    b_critical = 45e-6
    alpha = 9

    factor = specific_activity * tau * b_critical / windspeed
    exp = math.exp(alpha * (1 - math.pow(critical_windspeed / windspeed, 2)))
    return factor * exp


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

    def __init__(self, ul, lr, step, nuclide):
        # setting the proximity of the measurement to the shore to default
        # value (meters)
        self.measurement_proximity = 10
        # default contamination depth is 10 cm
        self.contamination_depth = 10
        self.__nuclide = nuclide
        self.__step = step
        # activity * raster_factor = raster code of activity
        self.__raster_factor = None
        self.__type = np.uint16
        self.__init_img(ul, lr)

    def add_basin(self, basin, measurements):
        if not measurements:
            return

        self.__check_measurments(basin, measurements)

        surface_activity = self.__calculate_average_surface_activity(
            measurements
        )

        if surface_activity == 0:
            return

        data = self.img.read(1)

        for shoreline_segment in basin.shoreline:
            shoreline_poly = shoreline_segment.buffer(
                basin.shoreline_width / 2,
                cap_style=geometry.CAP_STYLE.square,
                join_style=geometry.JOIN_STYLE.mitre,
            )
            for i in range(self.img.width):
                for j in range(self.img.height):
                    x, y = self.img.xy(i, j)
                    cell_poly = self.__get_cell_poly(x, y)
                    intersection = shoreline_poly.intersection(cell_poly).area
                    if intersection == 0:
                        continue

                    activity = surface_activity * intersection
                    raster_factor = self.__update_raster_factor(activity)
                    if self.__raster_factor is None:
                        self.__raster_factor = raster_factor
                    elif raster_factor != self.__raster_factor:
                        data = (
                            data / self.__raster_factor * raster_factor
                        ).astype(self.__type)
                        self.__raster_factor = raster_factor

                    data[i, j] += raster_factor * activity

        self.img.write(data, 1)

    def __init_img(self, ul, lr):
        ul.transform("EPSG:3857")
        lr.transform("EPSG:3857")
        # since map can't be larger than 100 km flat Earth model is good enough
        # here
        x_res = abs(math.floor((lr.lon - ul.lon) / self.__step))
        y_res = abs(math.floor((ul.lat - lr.lat) / self.__step))
        if x_res == 0 or y_res == 0:
            raise ExceedingStepError

        data = np.zeros((x_res, y_res)).astype(self.__type)

        # lower bottom corner doesn't necessary consist with initial lower
        # bottom
        lr = Coordinate(
            lon=ul.lon + x_res * self.__step,
            lat=ul.lat - y_res * self.__step,
            crs=lr.crs,
        )

        memfile = MemoryFile()
        self.__img = memfile.open(
            driver="GTiff",
            height=data.shape[0],
            width=data.shape[1],
            dtype=self.__type,
            crs="EPSG:3857",
            transform=Affine.translation(ul.lon, ul.lat)
            * Affine.scale(self.__step, -self.__step),
            count=1,
        )
        self.img.write(data, 1)

    def __calculate_average_surface_activity(self, measurements):
        average = 0
        for measurement in measurements:
            average += measurement.activity.surface_1cm
        average *= self.contamination_depth
        average /= len(measurements)
        return average

    def __get_cell_poly(self, x, y):
        top = y + self.__step / 2
        bottom = y - self.__step / 2
        right = x - self.__step / 2
        left = x + self.__step / 2
        cell = geometry.Polygon(
            [
                [right, bottom],
                [right, top],
                [left, top],
                [left, bottom],
            ]
        )
        return cell

    def __update_raster_factor(self, activity):
        max_raster_code = np.iinfo(self.__type).max
        if (
            self.__raster_factor is None
            or self.__raster_factor * activity > max_raster_code
        ):
            return self.__make_raster_factor(activity)
        else:
            return self.__raster_factor

    def __make_raster_factor(self, activity):
        max_raster_code = np.iinfo(self.__type).max
        return max_raster_code / (2 * activity)

    def __check_measurments(self, basin, measurements):
        for measurement in measurements:
            self.__check_measurment_location(measurement, basin)
            self.__check_measurment_proximity(measurement, basin)

    def __check_measurment_location(self, measurement, basin):
        coo = measurement.coo
        if basin.body.contains(geometry.Point(coo.lon, coo.lat)):
            raise InvalidMeasurementLocation

    def __check_measurment_proximity(self, measurement, basin):
        proximate_enough = False
        for shoreline_segment in basin.shoreline:
            measurement_point = geometry.Point(
                measurement.coo.lon, measurement.coo.lat
            )
            (coo1, coo2) = ops.nearest_points(
                measurement_point, shoreline_segment
            )
            distance = coo1.distance(coo2)
            proximate_enough = (
                proximate_enough or distance <= self.__measurement_proximity
            )
        if proximate_enough is False:
            raise ExceedingMeasurementProximity

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

    @property
    def nuclide(self):
        return self.__nuclide

    @property
    def raster_factor(self):
        return self.__raster_factor

    @property
    def step(self) -> int:
        return self.__step
