#!/usr/bin/python3

from src.basins import Basin

from typing import Dict, List
import json
import re
from os import walk
import rasterio
from matplotlib import pyplot as plt
from matplotlib import ticker
from matplotlib.colors import LogNorm
import matplotlib.patches as patches
import numpy as np
from math import log10, floor
import math
import scipy.ndimage

_bin_dir_name = None
_show = True
_basins = None


def find_exp(number) -> int:
    base10 = log10(abs(number))
    return floor(base10)


def plot_act_maps() -> None:
    with open(_bin_dir_name + "/raster_factors.json", "r") as f:
        raster_factors = json.load(f)

    regex = re.compile(".*_actmap.tif")
    for _root, _dirs, files in walk(_bin_dir_name):
        for file in files:
            if regex.match(file):
                nuclide = file.split("_")[0]
                with rasterio.open(_bin_dir_name + "/" + file, "r") as dataset:
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

                    plt.savefig(_bin_dir_name + f"/../{nuclide}_actmap.png")
                    if _show:
                        plt.show()


def plot_doses_map_heatmap(
    x: List[float], y: List[float], doses: Dict[str, np.ndarray]
) -> None:
    for target in doses:
        plt.figure()
        ax = plt.subplot()
        data = doses[target]

        extent = [x.min(), x.max(), y.min(), y.max()]
        cb = plt.imshow(
            data, extent=extent, vmin=np.min(data), vmax=np.max(data)
        )
        plt.colorbar(cb)
        plt.title(f"Doses for {target}, Sv")

        for basin_name in _basins:
            basin = _basins[basin_name]
            array = np.transpose(np.array(basin.body.exterior.xy))
            patch = patches.Polygon(xy=array, closed=True)
            ax.add_patch(patch)

        plt.savefig(_bin_dir_name + "/../" + target + "_heatmap.png")
        if _show:
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
        x = np.linspace(start=x[0], stop=x[-1], num=data.shape[0])
        y = np.linspace(start=y[0], stop=y[-1], num=data.shape[1])
        ax.set_title(f"Effective dose for {target}, 1E{exponent} Sv")
        extent = [x.min(), x.max(), y.min(), y.max()]
        cnt = ax.contour(
            x,
            y,
            data,
            extent=extent,
            locator=ticker.LogLocator(base=1.00001),
            # levels=10,
            corner_mask=False,
        )
        ax.clabel(cnt, inline_spacing=0)

        for basin_name in _basins:
            basin = _basins[basin_name]
            array = np.transpose(np.array(basin.body.exterior.xy))
            patch = patches.Polygon(xy=array, closed=True)
            ax.add_patch(patch)

        plt.savefig(_bin_dir_name + "/../" + target + "_contours.png")
        if _show:
            plt.show()


def plot_doses_maps() -> None:
    with open(_bin_dir_name + "/coords.npy", "rb") as f:
        data = np.load(f)
        x = data["x"]
        y = data["y"]

    sum_doses = np.zeros((len(y), len(x)))
    regex = re.compile(".*_e_max.npy")
    doses = dict()
    for _root, _dirs, files in walk(_bin_dir_name):
        for file in files:
            if regex.match(file):
                nuclide = file.split("_")[0]
                with open(_bin_dir_name + "/" + file, "rb") as f:
                    doses[nuclide] = np.load(f)
                    sum_doses += doses[nuclide]

    doses["sum"] = sum_doses

    plot_doses_map_heatmap(x, y, doses)
    plot_doses_map_contours(x, y, doses)


def make_plots(bin_dir_name: str, show: bool, basins: Dict[str, Basin] = None):
    global _bin_dir_name
    _bin_dir_name = bin_dir_name
    global _show
    _show = show
    global _basins
    _basins = basins if basins is not None else dict()
    plot_act_maps()
    plot_doses_maps()


if __name__ == "__main__":
    pass
