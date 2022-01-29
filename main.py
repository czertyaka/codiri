#!/usr/bin/python3

from map import Map as mymap
from shorelines import ShorelinesFinder as slfinder

if __name__ == "__main__":
    map = mymap(r"water.tif")
    # map.plot()
    slfinder(map=map, approx_error=4).plot()