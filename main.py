#!/usr/bin/python3

from contours import Contours

if __name__ == "__main__":
    cnts = Contours(r"water.tif")
    cnts.plot_image()