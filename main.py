#!/usr/bin/python3

from map import Map as Mymap
from shorelines import ShorelinesFinder as Finder

if __name__ == "__main__":
    map = Mymap(r"water.tif")
    # map.plot()
    Finder(map=map, approx_error=4).plot()
