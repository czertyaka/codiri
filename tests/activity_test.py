from bottom_deposits_radiocontamination.src.activity import (
    ActivityMap,
    ExceedingStepError,
    Measurment,
)
from bottom_deposits_radiocontamination.src.geo import Coordinate
from bottom_deposits_radiocontamination.src.shorelines import ShorelineContour
import numpy as np
import pytest


def test_measurment():
    measurment = Measurment(
        activity=0, coo=Coordinate(lon=10, lat=10, crs="EPSG:4326")
    )
    assert measurment.coo.crs == "EPSG:3857"


def check_empty_map(ul, lr, new_lr, step, ref_width, ref_height):
    actmap = ActivityMap(ul=ul, lr=lr, step=step).img
    assert actmap.width == ref_width
    assert actmap.height == ref_height
    assert actmap.xy(0, 0, offset="ul") == (ul.lon, ul.lat)
    assert actmap.xy(actmap.width, actmap.height, offset="ul") == (
        new_lr.lon,
        new_lr.lat,
    )

    data = actmap.read(1)
    unique_values = np.unique(data)
    assert unique_values.size == 1
    assert unique_values[0] == 0


def test_map():
    lr = Coordinate(lon=20, lat=10)
    check_empty_map(
        ul=Coordinate(lon=10, lat=20),
        lr=lr,
        new_lr=lr,
        step=1,
        ref_width=10,
        ref_height=10,
    )


def test_map_large_step():
    check_empty_map(
        ul=Coordinate(lon=10, lat=20),
        lr=Coordinate(lon=25, lat=5),
        new_lr=Coordinate(lon=20, lat=10),
        step=10,
        ref_width=1,
        ref_height=1,
    )


def test_map_exceeding_step():
    ul = Coordinate(lon=10, lat=20)
    lr = Coordinate(lon=25, lat=5)
    with pytest.raises(ExceedingStepError):
        ActivityMap(ul, lr, 100)


def check_adding_shoreline(resolution, shorelines, ref_data):
    actmap = ActivityMap(
        ul=Coordinate(lon=0, lat=resolution),
        lr=Coordinate(lon=resolution, lat=0),
        step=1,
    )
    for shoreline in shorelines:
        actmap.add_shoreline(shoreline["cnt"], shoreline["measurments"])
    data = actmap.img.read(1)
    assert (data == ref_data).all()


def test_add_no_shoreline_with_no_measurments():
    res = 4
    check_adding_shoreline(
        resolution=res,
        shorelines=[{"cnt": ShorelineContour(), "measurments": []}],
        ref_data=np.zeros((res, res)).astype("uint8"),
    )


def test_add_no_shoreline_with_measurments():
    res = 4
    check_adding_shoreline(
        resolution=res,
        shorelines=[
            {
                "cnt": ShorelineContour(),
                "measurments": [
                    Measurment(activity=0, coo=Coordinate(res / 2, res / 2)),
                    Measurment(activity=1, coo=Coordinate(res / 2, res / 2)),
                ],
            }
        ],
        ref_data=np.zeros((res, res)).astype("uint8"),
    )


def test_add_no_shorelines_multiple_times():
    res = 4
    check_adding_shoreline(
        resolution=res,
        shorelines=[
            {
                "cnt": ShorelineContour(),
                "measurments": [],
            },
            {
                "cnt": ShorelineContour(),
                "measurments": [],
            },
        ],
        ref_data=np.zeros((res, res)).astype("uint8"),
    )


def test_add_outer_shoreline():
    res = 4
    check_adding_shoreline(
        resolution=res,
        shorelines=[
            {"cnt": ShorelineContour([[6, 6], [7, 7]]), "measurments": []}
        ],
        ref_data=np.zeros((res, res)).astype("uint8"),
    )
    check_adding_shoreline(
        resolution=res,
        shorelines=[
            {
                "cnt": ShorelineContour([[-1, -1], [5, -1], [5, 5], [-1, 5]]),
                "measurments": [],
            }
        ],
        ref_data=np.zeros((res, res)).astype("uint8"),
    )
