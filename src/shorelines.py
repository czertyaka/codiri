#!/usr/bin/python3

import cv2 as cv
from matplotlib import pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.ticker import AutoMinorLocator
from .geo import Coordinate
import shapely.geometry as geom


def _log(msg):
    print("shorelines: " + msg)


class ShorelineContour(object):
    """Holds data on single shoreline contour"""

    def __init__(self, points, closed=True):
        points = points if points is not None else []
        self.__closed = True if closed and len(points) > 2 else False
        self.__figure = (
            geom.LinearRing(points) if self.closed else geom.LineString(points)
        )

    def __eq__(self, other):
        return self.closed == other.closed and sorted(self.points) == sorted(
            other.points
        )

    def __repr__(self):
        return f"{{closed: {self.closed}; points: {self.points}}}"

    @property
    def points(self):
        return self.__figure.coords

    @property
    def closed(self):
        return self.__closed


class ShorelinesFinder(object):
    """Makes polygons for all shorelines presented on map"""

    def __init__(self, map, approx_error=3):
        self.__approx_error = approx_error
        self.__map = map
        pix_cnts = self.__find_contours()
        self.__coord_cnts(pix_cnts)

    def __find_contours(self):
        pix_cnts, hierarchy = cv.findContours(
            self.map.data, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE
        )
        _log(f"found {len(pix_cnts)} shorelines")
        return pix_cnts

    def __coord_cnts(self, pix_cnts):
        _log(
            "Douglas-Peucker approximation algorithm epsilon = "
            f"{self.__approx_error}%"
        )
        self.__cnts = []
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
            # TODO: estimate if contour is opened
            self.__cnts.append(ShorelineContour(points=coord_cnt))
        _log(f"added {len(self.__cnts)} shorelines")

    def get_cnt(self, coo):
        coo.transform(self.map.img.crs)
        point = geom.Point(coo.lon, coo.lat)
        for cnt in self.__cnts:
            polygon = geom.Polygon(cnt.points)
            print(f"{polygon}, {point}")
            if polygon.contains(point):
                return cnt
        return None

    def plot(self):
        fig, ax = plt.subplots()
        for cnt in self.contours:
            polygon = Polygon(cnt.points, fill=False, ec="blue")
            ax.add_patch(polygon)

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
    def contours(self):
        return self.__cnts

    @property
    def map(self):
        return self.__map
