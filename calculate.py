#!/usr/bin/python3

import argparse
import json
from os import mkdir, path
from typing import Dict, List
from datetime import datetime
from shutil import copy
from rasterio.coords import BoundingBox
import numpy as np
from collections import Counter
from copy import deepcopy
from tempfile import TemporaryDirectory
import rasterio
import csv

from src.model.reference import Reference
from src.database import Database
from src.geo import Map
from src.basins import Basin
from src.geo import Coordinate, distance
from src.activity import ActivityMap
from src.measurement import Measurement, SoilActivity
from src.model.common import pasquill_gifford_classes
from src.model.input import Input
from src.model.model import Model
from plot import make_plots
from utils import find_basins, parse_input

_reference = None
_start = datetime.now()
_output_directory = TemporaryDirectory()
_output_directory_name = _output_directory.name
_model_input = dict()


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
    global _start
    report_dir_name = f"report_{_start.strftime('%d-%m-%Y_%H-%M-%S')}"
    global _output_directory_name
    return path.join(_output_directory_name, report_dir_name)


def report_bin_dir_name() -> str:
    return path.join(report_dir_name(), "bin")


def prepare_output(input_filename: str) -> None:
    mkdir(report_dir_name())
    mkdir(report_bin_dir_name())
    copy(input_filename, path.join(report_dir_name(), "input.json"))


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


def save_act_maps(maps: List[ActivityMap]) -> None:
    raster_factors = dict()
    for mp in maps:
        raster_factors[mp.nuclide] = mp.raster_factor
        raster_filename = path.join(
            report_bin_dir_name(), f"{mp.nuclide}_actmap.tif"
        )
        profile = mp.img.profile
        data = mp.img.read(1)
        with rasterio.open(raster_filename, "w", **profile) as f:
            f.write(data, 1)

    with open(
        path.join(report_bin_dir_name(), "raster_factors.json"), "w"
    ) as f:
        json.dump(raster_factors, f)


def dict_of_atm_class_arrays(x_len: int, y_len: int) -> dict:
    d = dict()
    for a_class in pasquill_gifford_classes:
        d[a_class] = np.zeros((y_len, x_len))
    return d


def list_of_atm_classes_names(prefix: str) -> list:
    lst = list()
    for a_class in pasquill_gifford_classes:
        lst.append(prefix + "_" + a_class)
    return lst


def dict_of_atm_class_to_list(d: Dict[str, float]) -> List[float]:
    lst = list()
    for a_class in pasquill_gifford_classes:
        lst.append(d[a_class])
    return lst


def calculate_dose(actmap: ActivityMap, point: Coordinate) -> float:
    inp = Input()
    global _model_input
    inp.square_side = _model_input["square_side"]
    inp.precipitation_rate = _model_input["precipitation_rate"]
    inp.terrain_type = _model_input["terrain_type"]
    inp.blowout_time = _model_input["blowout_time"]
    inp.age = _model_input["age"]
    ws = dict()
    for ws_data in _model_input["wind_speed"]:
        ws[ws_data["a_class"]] = ws_data["value"]
    inp.extreme_windspeeds = ws

    soil_density = _model_input["soil_density"]

    global _reference
    model = Model(_reference)

    activities = actmap.img.read(1) / actmap.raster_factor
    square_area = pow(inp.square_side, 2)

    e_max = 0
    e_total_10 = dict()
    e_inh = dict()
    e_surface = dict()
    e_cloud = dict()
    concentration_integrals = dict()
    depositions = dict()
    depletions = dict()

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
                depletions = dict(
                    Counter(model.results.full_depletions[actmap.nuclide])
                    + Counter(depletions)
                )

    for a_class in depletions:
        depletions[a_class] = depletions[a_class] / np.count_nonzero(
            activities
        )

    return (
        e_max,
        e_total_10,
        e_inh,
        e_surface,
        e_cloud,
        concentration_integrals,
        depositions,
        depletions,
    )


def make_bin_data_name(nuclide_name: str, value_name: str) -> path:
    return path.join(report_bin_dir_name(), (nuclide_name + "_" + value_name))


def calculate_doses_map(activity_maps: List[ActivityMap], inp: Dict) -> None:
    res = inp["resolution"]
    x = np.linspace(start=inp["ul"]["lon"], stop=inp["lr"]["lon"], num=res)
    y = np.linspace(start=inp["ul"]["lat"], stop=inp["lr"]["lat"], num=res)

    with open(path.join(report_bin_dir_name(), "coords.npy"), "wb") as f:
        np.savez(f, x=x, y=y)

    e_max = np.zeros((len(y), len(x)))
    e_total_10 = dict_of_atm_class_arrays(len(y), len(x))
    e_inh = dict_of_atm_class_arrays(len(y), len(x))
    e_surface = dict_of_atm_class_arrays(len(y), len(x))
    e_cloud = dict_of_atm_class_arrays(len(y), len(x))
    concentration_integrals = dict_of_atm_class_arrays(len(y), len(x))
    depositions = dict_of_atm_class_arrays(len(y), len(x))
    depletions = dict_of_atm_class_arrays(len(y), len(x))

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
                    depletions[a_class][i][j] = results[7][a_class]
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
        with open(make_bin_data_name(nuclide, "depletions.npz"), "wb") as f:
            np.savez(f, **depletions)


def calculate_doses_in_special_points(
    activity_maps: List[ActivityMap], inp: List
) -> None:
    f = open(path.join(report_dir_name(), "special_points.csv"), "w")
    writer = csv.writer(
        f, delimiter=";", quotechar="'", quoting=csv.QUOTE_MINIMAL
    )
    e_total_hdr = list_of_atm_classes_names("e_total_10")
    e_inh_hdr = list_of_atm_classes_names("e_inh")
    e_surface_hdr = list_of_atm_classes_names("e_surface")
    e_cloud_hdr = list_of_atm_classes_names("e_cloud")
    concentration_integral_hdr = list_of_atm_classes_names(
        "concentration_integral"
    )
    deposition_hdr = list_of_atm_classes_names("deposition")
    depletion_hdr = list_of_atm_classes_names("depletion")

    writer.writerow(
        [
            "point",
            "x",
            "y",
            "nuclide",
            "E_max",
            *e_total_hdr,
            *e_inh_hdr,
            *e_surface_hdr,
            *e_cloud_hdr,
            *concentration_integral_hdr,
            *deposition_hdr,
            *depletion_hdr,
        ]
    )

    for point_data in inp:
        coo = Coordinate(lon=point_data["lon"], lat=point_data["lat"])
        row = point_data["name"]
        for act_map in activity_maps:
            results = calculate_dose(act_map, coo)
            dose = results[0]
            row += f"; {act_map.nuclide}: {dose:.2e}"
            writer.writerow(
                [
                    point_data["name"],
                    point_data["lon"],
                    point_data["lat"],
                    act_map.nuclide,
                    dose,
                    *dict_of_atm_class_to_list(results[1]),
                    *dict_of_atm_class_to_list(results[2]),
                    *dict_of_atm_class_to_list(results[3]),
                    *dict_of_atm_class_to_list(results[4]),
                    *dict_of_atm_class_to_list(results[5]),
                    *dict_of_atm_class_to_list(results[6]),
                    *dict_of_atm_class_to_list(results[7]),
                ]
            )
        print(row)

    f.close()


if __name__ == "__main__":
    args = parse_arguments()
    inp = parse_input(args.input)
    _model_input = inp["model"]

    _reference = Reference(Database(inp["database_name"]))
    save_plots = False
    if args.output is not None:
        _output_directory_name = args.output
        save_plots = True
    print(f"report directory: {report_dir_name()}")
    prepare_output(args.input)
    raster = Map(inp["geotiff_filename"])
    basins = find_basins(raster, inp["basins"])
    activity_maps = make_activity_maps(
        basins, inp["basins"], raster.img.bounds, inp["model"]["square_side"]
    )
    save_act_maps(activity_maps)
    if "map" in inp["points"]:
        calculate_doses_map(activity_maps, inp["points"]["map"])
    if "special" in inp["points"]:
        calculate_doses_in_special_points(
            activity_maps, inp["points"]["special"]
        )
    make_plots(report_dir_name(), save_plots, basins)
