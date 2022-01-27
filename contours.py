#!/usr/bin/python3

import numpy as np
import cv2 as cv
from matplotlib import pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.ticker import AutoMinorLocator
import rasterio as rsio

def _log(msg):
        print("contours: " + msg)

class Contours(object):
    """Extracts shoreline of waterbodies from GeoTIFF file as polygons"""
    approx_error = 10

    def __init__(self, filename):
        img8bit = self.__get_image(filename)
        pix_cnts = self.__find_contours(img8bit)
        self.__coord_cnts(pix_cnts)

    def __get_image(self, filename):
        self.__img = rsio.open(filename)
        _log(f"opened image '{filename}'; bounds = {self.__img.bounds}, crs = {self.__img.crs}, width = {self.__img.width}, height = {self.__img.height}")
        data = self.__img.read(1)
        return np.uint8(data)

    def __find_contours(self, img8bit):
        ret, reduced = cv.threshold(img8bit, 2, 0, cv.THRESH_TOZERO_INV)
        if not ret:
            _log("failed to reduce cloud/shadow/snow/ice areas")
            exit()
        ret, self.__binary_img = cv.threshold(reduced, 1, 255, cv.THRESH_BINARY)
        if not ret:
            _log("failed to make image binary")
            exit
        pix_cnts, hierarchy = cv.findContours(self.__binary_img, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE)
        _log(f"found {len(pix_cnts)} shorelines")
        return pix_cnts

    def __coord_cnts(self, pix_cnts):
        _log(f"Douglas-Peucker approximation algorithm elsilon = {self.approx_error}%")
        self.__cnts = []
        for pix_cnt in pix_cnts:
            pix_cnt = cv.approxPolyDP(pix_cnt, self.approx_error, True)
            if len(pix_cnt) < 3:
                continue
            coord_cnt = []
            for pix_vertice in pix_cnt:
                pix_vertice = pix_vertice[0]
                coord_vertice = self.__img.xy(pix_vertice[1], pix_vertice[0])
                coord_cnt.append(coord_vertice)
            coord_cnt = np.array(coord_cnt)
            self.__cnts.append(coord_cnt)
        _log(f"added {len(self.__cnts)} shorelines")
        self.__cnts = np.array(self.__cnts)

    def plot_contours(self):
        fig,ax = plt.subplots()
        for cnt in self.__cnts:
            polygon = Polygon(cnt, fill=False, ec='blue')
            ax.add_patch(polygon)

        ax.set_xlim([self.__img.bounds.left, self.__img.bounds.right])
        ax.set_ylim([self.__img.bounds.bottom, self.__img.bounds.top])
        ax.xaxis.set_minor_locator(AutoMinorLocator())
        ax.yaxis.set_minor_locator(AutoMinorLocator())
        ax.tick_params(axis='both', which='both')
        ax.tick_params(axis='both', which='minor', grid_linestyle='--')
        plt.grid(visible=True, which='both', axis='both', alpha=0.3)
        plt.axis('scaled')
        plt.show()

    def plot_image(self):
        plt.imshow(self.__binary_img)
        plt.show()

if __name__ == "__main__":
    init("water.tif")