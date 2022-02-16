#!/usr/bin/python3

from src.geo import Map as Mymap
from src.shorelines import ShorelinesFinder as Finder

if __name__ == "__main__":
    mymap = Mymap(r"data/water.tif")
    mymap.plot()
    Finder(map=mymap, approx_error=4).plot()
