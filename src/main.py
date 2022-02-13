#!/usr/bin/python3

from geo import Map as Mymap
from shorelines import ShorelinesFinder as Finder

if __name__ == "__main__":
    mymap = Mymap(r"water.tif")
    # mymap.plot()
    Finder(map=mymap, approx_error=4).plot()
