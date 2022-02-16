#!/usr/bin/python3

from bottom_deposits_radiocontamination.src.geo import Map as Mymap
from bottom_deposits_radiocontamination.src.shorelines import (
    ShorelinesFinder as Finder,
)

if __name__ == "__main__":
    mymap = Mymap(r"water.tif")
    # mymap.plot()
    Finder(map=mymap, approx_error=4).plot()
