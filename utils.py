from typing import Dict, List

from src.geo import Map, Coordinate
from src.basins import Basin, BasinsFinder
from os import path
import json


def find_basins(raster: Map, inp: List) -> Dict[str, Basin]:
    basins = dict()
    basins_finder = BasinsFinder(map=raster, approx_error=1)
    for basin_data in inp:
        coo = Coordinate(lon=basin_data["lon"], lat=basin_data["lat"])
        name = basin_data["name"]
        basins[name] = basins_finder.get_basin(coo)
        if basins[name] is None:
            raise ValueError(
                f"basin '{name}' weren't found in provided raster data"
            )
    return basins


def parse_input(filename: str) -> dict:
    if not path.isfile(filename):
        raise ValueError(f"file {filename} not found")
    with open(filename, "r", encoding="utf-8") as fp:
        return json.load(fp)
