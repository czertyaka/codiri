#!/usr/bin/python3

import argparse
import json
from os import mkdir, walk, path
from typing import Dict, List
from datetime import datetime
from shutil import copy
from rasterio.coords import BoundingBox
from matplotlib import pyplot as plt
from matplotlib import ticker
from matplotlib.colors import LogNorm
import numpy as np
from collections import Counter
from copy import deepcopy
from tempfile import TemporaryDirectory
import re
import matplotlib.patches as patches
import scipy.ndimage
import math

from src.model.reference import Reference
from src.geo import Map
from src.basins import BasinsFinder, Basin
from src.geo import Coordinate, distance
from src.activity import ActivityMap
from src.measurement import Measurement, SoilActivity
from src.model.common import pasquill_gifford_classes
from src.model.input import Input
from src.model.model import Model
from math import log10, floor

reference = Reference("data/reference_data.db")
start = datetime.now()
output_directory = TemporaryDirectory()
output_directory_name = output_directory.name
show_plots = True
model_input = dict()


def find_exp(number) -> int:
    base10 = log10(abs(number))
    return floor(base10)


def init_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "-i", "--input", help="JSON file with input data", required=True
    )
    parser.add_argument(
        "-o", "--output", help="make report and put to directory"
    )


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Calculate doses due to wind uplift & transport"
    )
    init_parser(parser)
    args = parser.parse_args()
    return args


def report_dir_name() -> str:
    report_dir_name = f"/report_{start.strftime('%d-%m-%Y_%H-%M-%S')}"
    return output_directory_name + report_dir_name


def report_bin_dir_name() -> str:
    return report_dir_name() + "/bin"


def prepare_output(input_filename: str) -> None:
    mkdir(report_dir_name())
    mkdir(report_bin_dir_name())
    copy(
        input_filename,
        report_dir_name() + "/input.json",
    )


def parse_input(filename: str) -> dict:
    if not path.isfile(filename):
        raise ValueError(f"file {filename} not found")
    with open(filename, "r") as fp:
        return json.load(fp)


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


def make_activity_maps(
    basins: Dict[str, Basin],
    inp: Dict,
    bounds: BoundingBox,
    square_side: float,
) -> List[ActivityMap]:
    maps = dict()
    for basin_data in inp:
        name = basin_data["name"]
        basin = basins[name]
        for measurement_data in basin_data["measurements"]:
            nuclide = measurement_data["nuclide"]
            specific_activity = measurement_data["specific_activity"]
            measurement = Measurement(
                activity=SoilActivity(specific_activity=specific_activity),
                coo=Coordinate(
                    lon=basin.body.exterior.coords[0][0],
                    lat=basin.body.exterior.coords[0][1],
                ),
            )
            if nuclide not in maps.keys():
                maps[nuclide] = ActivityMap(
                    ul=Coordinate(lon=bounds.left, lat=bounds.top),
                    lr=Coordinate(lon=bounds.right, lat=bounds.bottom),
                    step=square_side,
                    nuclide=nuclide,
                )
            maps[nuclide].add_basin(basin=basin, measurements=[measurement])

    return [item for key, item in maps.items()]


def plot_maps(maps: List[ActivityMap]) -> None:
    for i in range(len(maps)):
        actmap = maps[i]
        bounds = actmap.img.bounds
        extent = [bounds[0], bounds[2], bounds[1], bounds[3]]
        data = actmap.img.read(1) / actmap.raster_factor
        plt.figure()
        ax = plt.subplot()
        shw = ax.imshow(
            data,
            cmap=plt.get_cmap("YlGn"),
            norm=LogNorm(vmin=1e7, vmax=data.max()),
            extent=extent,
        )
        plt.colorbar(shw, fraction=0.046, pad=0.04)
        ax.title.set_text(f"{actmap.nuclide} activity, Bq")
        ax.tick_params(axis="x", labelrotation=25)

        if show_plots:
            plt.show()
        else:
            plt.savefig(report_dir_name() + f"/{actmap.nuclide}_actmap.png")


def dict_of_atm_class_arrays(x_len: int, y_len: int) -> dict:
    d = dict()
    for a_class in pasquill_gifford_classes:
        d[a_class] = np.zeros((y_len, x_len))
    return d


def calculate_dose(actmap: ActivityMap, point: Coordinate) -> float:
    inp = Input()
    inp.square_side = model_input["square_side"]
    inp.precipitation_rate = model_input["precipitation_rate"]
    inp.terrain_type = model_input["terrain_type"]
    inp.blowout_time = model_input["blowout_time"]
    inp.age = model_input["age"]
    ws = dict()
    for ws_data in model_input["wind_speed"]:
        ws[ws_data["a_class"]] = ws_data["value"]
    inp.extreme_windspeeds = ws

    soil_density = model_input["soil_density"]

    model = Model()
    model.reference = reference

    activities = actmap.img.read(1) / actmap.raster_factor
    square_area = pow(inp.square_side, 2)

    e_max = 0
    e_total_10 = dict()
    e_inh = dict()
    e_surface = dict()
    e_cloud = dict()
    concentration_integrals = dict()
    depositions = dict()

    for i in range(actmap.img.width):
        for j in range(actmap.img.height):

            activity = activities[j][i]
            if activity == 0:
                continue

            xy = actmap.img.xy(j, i)

            full_inp = deepcopy(inp)
            full_inp.distance = distance(
                point, Coordinate(lon=xy[0], lat=xy[1])
            )

            contaminated_volume = (
                actmap.contamination_depth / 100 * square_area
            )
            specific_activity = activity / (contaminated_volume * soil_density)

            full_inp.add_specific_activity(
                nuclide=actmap.nuclide, specific_activity=specific_activity
            )
            model.input = full_inp

            if model.calculate():
                e_max += model.results.e_max_10
                e_total_10 = dict(
                    Counter(model.results.e_total_10[actmap.nuclide])
                    + Counter(e_total_10)
                )
                e_inh = dict(
                    Counter(model.results.e_inhalation[actmap.nuclide])
                    + Counter(e_inh)
                )
                e_surface = dict(
                    Counter(model.results.e_surface[actmap.nuclide])
                    + Counter(e_surface)
                )
                e_cloud = dict(
                    Counter(model.results.e_cloud[actmap.nuclide])
                    + Counter(e_cloud)
                )
                concentration_integrals = dict(
                    Counter(
                        model.results.concentration_integrals[actmap.nuclide]
                    )
                    + Counter(concentration_integrals)
                )
                depositions = dict(
                    Counter(model.results.depositions[actmap.nuclide])
                    + Counter(depositions)
                )

    return (
        e_max,
        e_total_10,
        e_inh,
        e_surface,
        e_cloud,
        concentration_integrals,
        depositions,
    )


def make_bin_data_name(nuclide_name: str, value_name: str) -> str:
    return report_bin_dir_name() + "/" + nuclide_name + "_" + value_name


def calculate_doses_map(activity_maps: List[ActivityMap], inp: Dict) -> None:
    res = inp["resolution"]
    x = np.linspace(start=inp["ul"]["lon"], stop=inp["lr"]["lon"], num=res)
    y = np.linspace(start=inp["ul"]["lat"], stop=inp["lr"]["lat"], num=res)

    with open(report_bin_dir_name() + "/coords.npy", "wb") as f:
        np.savez(f, x=x, y=y)

    e_max = np.zeros((len(y), len(x)))
    e_total_10 = dict_of_atm_class_arrays(len(y), len(x))
    e_inh = dict_of_atm_class_arrays(len(y), len(x))
    e_surface = dict_of_atm_class_arrays(len(y), len(x))
    e_cloud = dict_of_atm_class_arrays(len(y), len(x))
    concentration_integrals = dict_of_atm_class_arrays(len(y), len(x))
    depositions = dict_of_atm_class_arrays(len(y), len(x))

    for act_map in activity_maps:
        nuclide = act_map.nuclide
        for j in range(len(x)):
            for i in range(len(y)):
                coo = Coordinate(lon=x[j], lat=y[i])
                results = calculate_dose(act_map, coo)
                e_max[i][j] = results[0]
                for a_class in pasquill_gifford_classes:
                    e_total_10[a_class][i][j] = results[1][a_class]
                    e_inh[a_class][i][j] = results[2][a_class]
                    e_surface[a_class][i][j] = results[3][a_class]
                    e_cloud[a_class][i][j] = results[4][a_class]
                    concentration_integrals[a_class][i][j] = results[5][
                        a_class
                    ]
                    depositions[a_class][i][j] = results[6][a_class]
                print(
                    f"ts: {datetime.now().strftime('%H:%M:%S')};"
                    f" j = {j}/{len(x)}; i = {i}/{len(y)}; coo: {coo}; "
                    f"nuclide: {nuclide}; dose: {e_max[i][j]:.2e} "
                    "Sv"
                )

        with open(make_bin_data_name(nuclide, "e_max.npy"), "wb") as f:
            np.save(f, e_max)
        with open(make_bin_data_name(nuclide, "e_total_10.npz"), "wb") as f:
            np.savez(f, **e_total_10)
        with open(make_bin_data_name(nuclide, "e_inh.npz"), "wb") as f:
            np.savez(f, **e_inh)
        with open(make_bin_data_name(nuclide, "e_surface.npz"), "wb") as f:
            np.savez(f, **e_surface)
        with open(make_bin_data_name(nuclide, "e_cloud.npz"), "wb") as f:
            np.savez(f, **e_cloud)
        with open(
            make_bin_data_name(nuclide, "concentration_integrals.npz"),
            "wb",
        ) as f:
            np.savez(f, **concentration_integrals)
        with open(make_bin_data_name(nuclide, "depositions.npz"), "wb") as f:
            np.savez(f, **depositions)


def calculate_doses_in_special_points(
    activity_maps: List[ActivityMap], inp: List
) -> None:
    msg = str()
    for point_data in inp:
        coo = Coordinate(lon=point_data["lon"], lat=point_data["lat"])
        row = point_data["name"]
        for act_map in activity_maps:
            dose = calculate_dose(act_map, coo)[0]
            row += f"; {act_map.nuclide}: {dose:.2e}"
        print(row)
        msg += row + "\n"

    with open(report_dir_name() + "/special_points.txt", "w") as f:
        f.write(msg)


def plot_doses_map_heatmap(
    x: List[float],
    y: List[float],
    doses: Dict[str, np.ndarray],
    basins: Dict[str, Basin],
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

        for basin_name in basins:
            basin = basins[basin_name]
            array = np.transpose(np.array(basin.body.exterior.xy))
            patch = patches.Polygon(xy=array, closed=True)
            ax.add_patch(patch)

        plt.savefig(report_dir_name() + "/" + target + "_heatmap.png")
        if show_plots:
            plt.show()


def plot_doses_map_contours(
    x: List[float],
    y: List[float],
    doses: Dict[str, np.ndarray],
    basins: Dict[str, Basin],
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

        for basin_name in basins:
            basin = basins[basin_name]
            array = np.transpose(np.array(basin.body.exterior.xy))
            patch = patches.Polygon(xy=array, closed=True)
            ax.add_patch(patch)

        plt.savefig(report_dir_name() + "/" + target + "_contours.png")
        if show_plots:
            plt.show()


def plot_doses_map(basins: Dict[str, Basin]) -> None:
    with open(report_bin_dir_name() + "/coords.npy", "rb") as f:
        data = np.load(f)
        x = data["x"]
        y = data["y"]

    sum_doses = np.zeros((len(y), len(x)))
    regex = re.compile(".*_e_max.npy")
    doses = dict()
    for _root, _dirs, files in walk(report_bin_dir_name()):
        for file in files:
            if regex.match(file):
                nuclide = file.split("_")[0]
                with open(report_bin_dir_name() + "/" + file, "rb") as f:
                    doses[nuclide] = np.load(f)
                    sum_doses += doses[nuclide]

    doses["sum"] = sum_doses

    plot_doses_map_heatmap(x, y, doses, basins)
    plot_doses_map_contours(x, y, doses, basins)


if __name__ == "__main__":
    args = parse_arguments()
    inp = parse_input(args.input)
    model_input = inp["model"]
    if args.output is not None:
        output_directory_name = args.output
        show_plots = False
    print(f"report directory: {report_dir_name()}")
    prepare_output(args.input)
    raster = Map(inp["geotiff_filename"])
    basins = find_basins(raster, inp["basins"])
    activity_maps = make_activity_maps(
        basins, inp["basins"], raster.img.bounds, inp["model"]["square_side"]
    )
    plot_maps(activity_maps)
    if "map" in inp["points"]:
        calculate_doses_map(activity_maps, inp["points"]["map"])
        plot_doses_map(basins)
    if "special" in inp["points"]:
        calculate_doses_in_special_points(
            activity_maps, inp["points"]["special"]
        )
