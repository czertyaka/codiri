#!/usr/bin/python3

import cv2 as cv
from matplotlib import pyplot as plt
from matplotlib.ticker import AutoMinorLocator
from .geo import Coordinate
from shapely import geometry
import numpy as np


def _log(msg):
    print("shorelines: " + msg)


class Basin(object):
    """Holds data on single basin such

    Arguments:
    contour is list of (x, y) couples,
    map_contour is list of (x, y) couples
    """

    def __init__(self, contour, map_contour=None):
        self.__body = geometry.Polygon(contour)

        body_contour = geometry.LinearRing(contour)
        if map_contour is None:
            self.__shoreline = body_contour
            return

        map_contour = geometry.LinearRing(map_contour)
        if geometry.Polygon(map_contour.coords[:-1]).contains(
            self.body
        ) is not True or body_contour.equals(map_contour):
            raise ValueError("map doesn't contain basin")

        # body is within map or touching it in one or more points
        if body_contour.disjoint(map_contour) or body_contour.intersection(
            map_contour
        ).geom_type in ("Point", "MultiPoint"):
            self.__shoreline = body_contour
            return

        # map does not cover all the body
        self.__shoreline = body_contour.difference(map_contour)

    @property
    def body(self):
        return self.__body

    @property
    def shoreline(self):
        if self.shoreline_segments_count > 1:
            return self.__shoreline.geoms
        else:
            return [self.__shoreline]

    @property
    def is_closed(self):
        return self.shoreline[0].geom_type == "LinearRing"

    @property
    def shoreline_segments_count(self):
        return (
            1
            if self.__shoreline.geom_type != "MultiLineString"
            else len(self.__shoreline.geoms)
        )

    def __eq__(self, other):
        ret = (
            self.body.equals(other.body)
            and self.shoreline_segments_count == other.shoreline_segments_count
        )
        for i in range(self.shoreline_segments_count):
            ret &= self.shoreline[i].equals(other.shoreline[i])
        return ret

    def __repr__(self):
        return f"<body: {self.body}; shoreline: {self.shoreline}>"


class BasinsFinder(object):
    """Makes basins objects for all basins presented on map"""

    def __init__(self, map, approx_error=3):
        self.__approx_error = approx_error
        self.__map = map
        pix_cnts = self.__find_contours()
        self.__calc_basins(pix_cnts)

    def __find_contours(self):
        pix_cnts, hierarchy = cv.findContours(
            self.map.data, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE
        )
        _log(f"found {len(pix_cnts)} basins")
        return pix_cnts

    def __calc_basins(self, pix_cnts):
        _log(
            "Douglas-Peucker approximation algorithm epsilon = "
            f"{self.__approx_error}%"
        )
        self.__basins = []
        map_contour = self.__get_map_contour()
        for pix_cnt in pix_cnts:
            pix_cnt = cv.approxPolyDP(pix_cnt, self.__approx_error, True)
            if len(pix_cnt) < 3:
                continue
            coord_cnt = []
            for pix_vertice in pix_cnt:
                pix_vertice = pix_vertice[0]
                coord_vertice = self.map.img.xy(
                    pix_vertice[1], pix_vertice[0], offset="ul"
                )
                coord_vertice = Coordinate(
                    coord_vertice[0], coord_vertice[1], self.map.img.crs
                )
                coord_cnt.append([coord_vertice.lon, coord_vertice.lat])
            try:
                self.__basins.append(
                    Basin(
                        contour=coord_cnt,
                        map_contour=map_contour,
                    )
                )
            except ValueError as e:
                _log(f"{e}")
        _log(f"added {len(self.basins)} basins")

    def __get_map_contour(self):
        left, top = self.map.img.xy(0, 0, offset="ul")
        right, bottom = self.map.img.xy(
            self.map.img.width - 1, self.map.img.height - 1, offset="ul"
        )
        return [[left, top], [left, bottom], [right, bottom], [right, top]]

    def get_basin(self, coo):
        coo.transform(self.map.img.crs)
        point = geometry.Point(coo.lon, coo.lat)
        for basin in self.basins:
            if basin.body.contains(point):
                return basin
        return None

    def plot(self):
        fig, ax = plt.subplots()
        for basin in self.basins:
            for shoreline_segment in basin.shoreline:
                coords = np.array(shoreline_segment.coords)
                plt.plot(coords[:, 0], coords[:, 1], c="blue")

        ax.set_xlim([self.map.img.bounds.left, self.map.img.bounds.right])
        ax.set_ylim([self.map.img.bounds.bottom, self.map.img.bounds.top])
        ax.xaxis.set_minor_locator(AutoMinorLocator())
        ax.yaxis.set_minor_locator(AutoMinorLocator())
        ax.tick_params(axis="both", which="both")
        ax.tick_params(axis="both", which="minor", grid_linestyle="--")
        plt.grid(visible=True, which="both", axis="both", alpha=0.3)
        plt.axis("scaled")
        plt.show()

    @property
    def basins(self):
        return self.__basins

    @property
    def map(self):
        return self.__map
