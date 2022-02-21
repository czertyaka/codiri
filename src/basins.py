#!/usr/bin/python3

import cv2 as cv
from matplotlib import pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.ticker import AutoMinorLocator
from .geo import Coordinate
from shapely import geometry, ops


def _log(msg):
    print("shorelines: " + msg)


class Basin(object):
    """Holds data on single basin such

    Arguments:
    contour is list of (x, y) couples,
    map_contour is list of (x, y) couples
    """

    def __init__(self, contour, map_contour=None):
        contour = geometry.LinearRing(contour)

        if map_contour is None:
            self.__shoreline_contour = contour
            return

        map_contour = geometry.LinearRing(map_contour)
        self.__contour = contour
        if map_contour.intersects(contour) is not True:
            self.__shoreline_contour = contour
            return

        diff = self.contour.difference(map_contour)
        if diff.geom_type == "LineString":
            if diff.is_empty is True:
                raise ValueError("basin's shoreline is out of map")
            elif diff.coords[0] == diff.coords[-1]:
                self.__shoreline_contour = contour
            else:
                self.__shoreline_contour = diff
        elif diff.geom_type == "MultiLineString":
            merged_linestring = ops.linemerge(diff)
            if merged_linestring.geom_type == "MultiLineString":
                raise ValueError("merging failed")
            self.__shoreline_contour = geometry.LinearRing(
                merged_linestring.coords[:-1]
            )
        else:
            raise ValueError("unexpected difference geometry type")

    @property
    def contour(self):
        return self.__contour

    @property
    def shoreline_contour(self):
        return self.__shoreline_contour

    def __eq__(self, other):
        return self.contour.equals(
            other.contour
        ) and self.shoreline_contour.equals(other.shoreline_contour)

    def __repr__(self):
        return f"contour: {self.contour}; shoreline: {self.shoreline_contour}"


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
            except ValueError:
                pass
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
            polygon = geometry.Polygon(basin.contour.coords[:-1])
            if polygon.contains(point):
                return basin
        return None

    def plot(self):
        fig, ax = plt.subplots()
        for basin in self.basins:
            polygon = Polygon(basin.contour.coords[:-1], fill=False, ec="blue")
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
    def basins(self):
        return self.__basins

    @property
    def map(self):
        return self.__map
