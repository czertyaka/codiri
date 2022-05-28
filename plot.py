#!/usr/bin/python3

from src.basins import Basin
from utils import find_basins, parse_input
from src.geo import Map

import argparse
from typing import Dict, List, Tuple
import json
import re
from os import walk, path
from os.path import isfile
import rasterio
from matplotlib import pyplot as plt
from matplotlib import ticker
from matplotlib.colors import LogNorm
import matplotlib.patches as patches
import numpy as np
from math import log10, floor
import math
import scipy.ndimage

_report_dir_name = None
_bin_dir_name = None
_save = True
_basins = None
_special_points = None


def _log(msg: str) -> None:
    print(f"plot: {msg}")


def find_exp(number) -> int:
    base10 = log10(abs(number))
    return floor(base10)


def plot_act_maps() -> None:
    raster_factors_filename = path.join(_bin_dir_name, "raster_factors.json")
    if not isfile(raster_factors_filename):
        _log(f"{raster_factors_filename} is missing")
        return

    with open(raster_factors_filename, "r") as f:
        raster_factors = json.load(f)

    regex = re.compile(".*_actmap.tif")
    for _root, _dirs, files in walk(_bin_dir_name):
        found = False
        for file in files:
            if regex.match(file):
                found = True
                nuclide = file.split("_")[0]
                with rasterio.open(
                    path.join(_bin_dir_name, file), "r"
                ) as dataset:
                    bounds = dataset.bounds
                    extent = [bounds[0], bounds[2], bounds[1], bounds[3]]
                    data = dataset.read(1) / raster_factors[nuclide]
                    plt.figure()
                    ax = plt.subplot()
                    shw = ax.imshow(
                        data,
                        cmap=plt.get_cmap("YlGn"),
                        norm=LogNorm(vmin=1e7, vmax=data.max()),
                        extent=extent,
                    )
                    plt.colorbar(shw, fraction=0.046, pad=0.04)
                    ax.title.set_text(f"{nuclide} activity, Bq")
                    ax.tick_params(axis="x", labelrotation=25)

                    if _save:
                        plt.savefig(
                            path.join(
                                _bin_dir_name, "..", f"{nuclide}_actmap.png"
                            )
                        )
                    plt.show()
        if not found:
            _log(f"no files matching '{regex.pattern}'")


def add_special_points(ax, x_0: float, y_0: float) -> None:
    global _special_points
    if _special_points is not None:
        for point in _special_points:
            x = point["lon"] / 1000 - x_0
            y = point["lat"] / 1000 - y_0
            ax.scatter(x, y, c="red")
            ax.annotate(point["name"], (x, y))


def add_basins(ax, x_0: float, y_0: float) -> None:
    global _basins
    for basin_name in _basins:
        basin = _basins[basin_name]
        array = np.transpose(np.array(basin.body.exterior.xy))
        for row in array:
            row[0] = row[0] / 1000 - x_0
            row[1] = row[1] / 1000 - y_0
        patch = patches.Polygon(xy=array, closed=True)
        ax.add_patch(patch)


def make_centralized_coords(
    coords: List[float], num=int
) -> Tuple[float, List[float]]:
    center = (coords[0] + coords[-1]) / 2
    new_coords = (
        np.linspace(
            start=(coords[0] - center), stop=(coords[-1] - center), num=num
        )
        / 1000
    )
    return (center / 1000, new_coords)


def plot_doses_map_heatmap(
    x: List[float], y: List[float], doses: Dict[str, np.ndarray]
) -> None:
    for target in doses:
        plt.figure()
        ax = plt.subplot()
        data = doses[target]

        x_0, dist_x = make_centralized_coords(x, data.shape[0])
        y_0, dist_y = make_centralized_coords(y, data.shape[1])
        extent = [dist_x.min(), dist_x.max(), dist_y.min(), dist_y.max()]
        cb = plt.imshow(
            data, extent=extent, vmin=np.min(data), vmax=np.max(data)
        )
        plt.colorbar(cb)
        plt.title(f"Doses for {target}, Sv")

        add_basins(ax, x_0, y_0)
        add_special_points(ax, x_0, y_0)

        ax.set_xlabel("X, km")
        ax.set_ylabel("Y, km")

        global _save
        if _save:
            global _report_dir_name
            plt.savefig(path.join(_report_dir_name, target + "_heatmap.png"))
        plt.show()


def plot_doses_map_contours(
    x: List[float], y: List[float], doses: Dict[str, np.ndarray]
) -> None:
    count = 0
    for target in doses:
        plt.figure()
        ax = plt.subplot()
        count += 1
        data = doses[target]
        exponent = find_exp(data.max())
        if exponent < 0:
            data = data * math.pow(10, -exponent)

        data = scipy.ndimage.zoom(data, 50)
        x_0, dist_x = make_centralized_coords(x, data.shape[0])
        y_0, dist_y = make_centralized_coords(y, data.shape[1])
        ax.set_title(f"Effective dose for {target}, 1E{exponent} Sv")
        cnt = ax.contour(
            dist_x,
            dist_y,
            data,
            locator=ticker.LogLocator(base=1.00001),
            # levels=10,
            corner_mask=False,
        )
        ax.clabel(cnt, inline_spacing=0)

        add_basins(ax, x_0, y_0)
        add_special_points(ax, x_0, y_0)

        ax.set_xlabel("X, km")
        ax.set_ylabel("Y, km")

        global _save
        if _save:
            global _report_dir_name
            plt.savefig(path.join(_report_dir_name, target + "_contours.png"))
        plt.show()


def plot_doses_maps() -> None:
    coords_filename = path.join(_bin_dir_name, "coords.npy")
    if not isfile(coords_filename):
        _log(f"{coords_filename} is missing")
        return

    with open(coords_filename, "rb") as f:
        data = np.load(f)
        x = data["x"]
        y = data["y"]

    sum_doses = np.zeros((len(y), len(x)))
    regex = re.compile(".*_e_max.npy")
    doses = dict()
    for _root, _dirs, files in walk(_bin_dir_name):
        found = False
        for file in files:
            if regex.match(file):
                found = True
                nuclide = file.split("_")[0]
                with open(path.join(_bin_dir_name, file), "rb") as f:
                    doses[nuclide] = np.load(f)
                    sum_doses += doses[nuclide]
        if not found:
            _log(f"no files matching '{regex.pattern}'")

    doses["sum"] = sum_doses

    plot_doses_map_heatmap(x, y, doses)
    plot_doses_map_contours(x, y, doses)


def make_plots(
    report_dir_name: str, save: bool, basins: Dict[str, Basin] = None
):
    global _report_dir_name
    _report_dir_name = report_dir_name
    global _bin_dir_name
    _bin_dir_name = path.join(report_dir_name, "bin")
    global _save
    _save = save
    inp = parse_input(path.join(report_dir_name, "input.json"))
    if basins is None:
        raster = Map(inp["geotiff_filename"])
        basins = find_basins(raster, inp["basins"])
    if "special" in inp["points"]:
        global _special_points
        _special_points = inp["points"]["special"]
    global _basins
    _basins = basins
    plot_act_maps()
    plot_doses_maps()


def init_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "-r", "--report_dir", help="report directory", required=True
    )
    parser.add_argument(
        "-s",
        "--save",
        action="store_true",
        help="save plots in report directory",
    )


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot data from report")
    init_parser(parser)
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = parse_arguments()
    basins = None
    make_plots(args.report_dir, args.save)
